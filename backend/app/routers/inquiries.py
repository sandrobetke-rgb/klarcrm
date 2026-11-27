"""Anfragen / Projekte (REV01 Phase 2): Übersicht, Artikel, Entscheidung, Angebot, Angebotsverfolgung."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .. import schemas as s
from ..auth import can_read, can_write
from ..database import get_db
from ..inquiry import (DECISIONS, RELEASED, calcs_of, decide, followup_light, followup_result, quote_of,
                       workdays_between)
from ..models import Activity, Calculation, Opportunity, Quote, User
from .calc import STATUS_PROBABILITY, inquiry_quote, sync_opportunity

router = APIRouter()        # /api/inquiries
decisions = APIRouter()     # /api/calculations/{id}/decision
followups = APIRouter()     # /api/followups


def _calc_row(c: Calculation) -> dict:
    return {"id": c.id, "number": c.number, "article_name": c.article_name, "customer_article_no": c.customer_article_no,
            "status": c.status, "decision": c.decision, "decision_note": c.decision_note, "site_id": c.site_id,
            "current_version": c.current_version, "calculated": c.is_calculated, "unit_price": c.unit_price, "annual_volume": c.annual_volume,
            "annual_revenue": c.annual_revenue, "one_time_revenue": c.one_time_revenue, "margin_pct": c.margin_pct,
            "feasibility": c.feasibility, "analysis_complete": c.analysis_complete,
            "tech_talk": bool((c.analysis or {}).get("tech_talk")),
            "suggested_size_t": (c.analysis_results or {}).get("suggested_size_t"),
            "approval_reasons": c.approval_reasons, "is_approved": c.is_approved, "approval_status": c.approval_status,
            "approval_to": c.approval_to.name if c.approval_to else None,
            "analysis_missing": c.analysis_missing, "warnings": c.warnings}


def _quote_row(q: Quote | None) -> dict | None:
    if not q:
        return None
    return {"id": q.id, "number": q.number, "status": q.status, "net_total": q.net_total, "sent_at": q.sent_at,
            "quote_date": q.quote_date, "last_contact_at": q.last_contact_at, "last_contact_note": q.last_contact_note,
            "followup": q.followup}


def _summary(db: Session, o: Opportunity, calcs: list[Calculation] | None = None) -> dict:
    calcs = calcs if calcs is not None else calcs_of(db, o.id)
    q = quote_of(db, o.id)
    lead_time = workdays_between(o.inquiry_date, o.offered_at) if o.inquiry_date and o.offered_at else None
    return {
        **s.OpportunityOut.model_validate(o).model_dump(mode="json"),
        "articles": len(calcs),
        "undecided": sum(1 for c in calcs if c.decision is None and c.status not in ("verloren", "kein_angebot")),
        "released": sum(1 for c in calcs if c.decision in RELEASED),
        "quote": _quote_row(q),
        "lead_time_workdays": lead_time,
    }


@router.get("")
def list_inquiries(q: str | None = None, stage: str | None = None, kind: str | None = None, owner_id: int | None = None,
                   account_id: int | None = None, open_only: bool = False, limit: int = Query(200, le=1000),
                   db: Session = Depends(get_db), _: User = Depends(can_read)):
    stmt = select(Opportunity)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Opportunity.name.ilike(like), Opportunity.number.ilike(like), Opportunity.description.ilike(like)))
    if stage:
        stmt = stmt.where(Opportunity.stage.in_(stage.split(",")))
    if kind:
        stmt = stmt.where(Opportunity.kind == kind)
    if owner_id:
        stmt = stmt.where(Opportunity.owner_id == owner_id)
    if account_id:
        stmt = stmt.where(Opportunity.account_id == account_id)
    if open_only:
        stmt = stmt.where(Opportunity.stage.notin_(("gewonnen", "verloren", "nicht_angeboten")))
    rows = db.scalars(stmt.order_by(Opportunity.id.desc()).limit(limit)).unique().all()
    all_calcs = db.scalars(select(Calculation).where(Calculation.opportunity_id.in_([o.id for o in rows]))).unique().all() if rows else []
    by = {}
    for c in all_calcs:
        by.setdefault(c.opportunity_id, []).append(c)
    return {"total": len(rows), "items": [_summary(db, o, by.get(o.id, [])) for o in rows]}


@router.get("/{opp_id}")
def get_inquiry(opp_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    o = db.get(Opportunity, opp_id)
    if not o:
        raise HTTPException(404, "Anfrage nicht gefunden")
    calcs = calcs_of(db, o.id)
    quotes = db.scalars(select(Quote).where(Quote.opportunity_id == o.id).order_by(Quote.id.desc())).unique().all()
    acts = db.scalars(select(Activity).where(or_(Activity.opportunity_id == o.id,
                                                 Activity.quote_id.in_([x.id for x in quotes] or [0])))
                      .order_by(Activity.done, Activity.due_at.desc().nulls_last())).unique().all()
    return {**_summary(db, o, calcs), "calculations": [_calc_row(c) for c in calcs],
            "quotes": [_quote_row(x) for x in quotes],
            "activities": [s.ActivityOut.model_validate(a).model_dump(mode="json") for a in acts],
            "decisions": DECISIONS}


class ArticleIn(BaseModel):
    article_name: str
    customer_article_no: str | None = None
    own_article_no: str | None = None
    copy_from: int | None = None     # bestehende Kalkulation als Vorlage


@router.post("/{opp_id}/articles", status_code=201)
def add_article(opp_id: int, data: ArticleIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Weiteren Artikel (Kalkulation) unter der Anfrage anlegen."""
    from .calc import create_calc  # noqa: PLC0415
    o = db.get(Opportunity, opp_id)
    if not o:
        raise HTTPException(404, "Anfrage nicht gefunden")
    inputs = None
    if data.copy_from:
        src = db.get(Calculation, data.copy_from)
        ver = next((v for v in src.versions if v.version_no == src.current_version), None) if src else None
        inputs = dict(ver.inputs) if ver else None
    calc = create_calc(s.CalcCreate(article_name=data.article_name, customer_article_no=data.customer_article_no,
                                    own_article_no=data.own_article_no, account_id=o.account_id, contact_id=o.contact_id,
                                    opportunity_id=o.id, due_date=o.due_date, inputs=inputs), db, user)
    return {"id": calc.id, "number": calc.number}


class DecisionIn(BaseModel):
    decision: str
    note: str | None = None
    site_id: int | None = None
    no_bid_reason: str | None = None


@decisions.post("/{calc_id}/decision")
def set_decision(calc_id: int, data: DecisionIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    decide(db, calc, data.decision, data.note, user, data.site_id, data.no_bid_reason)
    db.flush()
    sync_opportunity(db, calc)
    db.commit()
    return _calc_row(calc)


@router.post("/{opp_id}/decision")
def decide_all(opp_id: int, data: DecisionIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Entscheidung für alle noch offenen Artikel der Anfrage (z. B. „alle anbieten“)."""
    o = db.get(Opportunity, opp_id)
    if not o:
        raise HTTPException(404, "Anfrage nicht gefunden")
    n = 0
    for c in calcs_of(db, o.id):
        if c.decision is None:
            decide(db, c, data.decision, data.note, user, data.site_id, data.no_bid_reason)
            n += 1
            last = c
    if n:
        db.flush()
        sync_opportunity(db, last)
    db.commit()
    return {"count": n}


@router.post("/{opp_id}/quote")
def make_quote(opp_id: int, lang: str = "de", db: Session = Depends(get_db), user: User = Depends(can_write)):
    o = db.get(Opportunity, opp_id)
    if not o:
        raise HTTPException(404, "Anfrage nicht gefunden")
    quote, action = inquiry_quote(db, o, user, lang)
    db.commit()
    return {"quote_id": quote.id, "number": quote.number, "action": action}


# ------------------------------------------------------------------ Angebotsverfolgung
class FollowupIn(BaseModel):
    result: str                      # erreicht | nicht_erreicht | wieder_melden
    note: str | None = None
    next_date: date | None = None


@followups.post("/{activity_id}")
def post_followup(activity_id: int, data: FollowupIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    t = db.get(Activity, activity_id)
    if not t:
        raise HTTPException(404, "Aufgabe nicht gefunden")
    followup_result(db, t, data.result, data.note, data.next_date, user)
    db.commit()
    db.refresh(t)
    return s.ActivityOut.model_validate(t).model_dump(mode="json")


@followups.get("")
def list_followups(db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Alle offenen Angebotsverfolgungen mit Ampel – für alle sichtbar, auch Gesellschafter (REV01-P06)."""
    rows = db.scalars(select(Activity).where(Activity.kind == "angebotsverfolgung", Activity.done.is_(False))
                      .order_by(Activity.due_at)).unique().all()
    out = []
    for a in rows:
        q = db.get(Quote, a.quote_id) if a.quote_id else None
        out.append({**s.ActivityOut.model_validate(a).model_dump(mode="json"),
                    "quote_number": q.number if q else None, "quote_total": q.net_total if q else None,
                    "sent_at": q.sent_at.isoformat() if q and q.sent_at else None,
                    "last_contact_note": q.last_contact_note if q else None})
    count = {k: sum(1 for r in out if r["light"] == k) for k in ("rot", "gelb", "gruen")}
    return {"items": out, "count": count}


__all__ = ["router", "decisions", "followups", "followup_light", "STATUS_PROBABILITY"]
