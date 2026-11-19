import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .. import schemas as s
from ..auth import can_read, can_write
from ..config import settings
from ..database import get_db
from ..models import Account, Quote, QuoteItem, User

router = APIRouter()


def next_number(db: Session) -> str:
    """Sprechende Angebotsnummer A26-0001 (A + zweistelliges Jahr, REV01-N01). Revisionen tragen -R1, -R2 …"""
    prefix = f"A{date.today():%y}-"
    nums = db.scalars(select(Quote.number).where(Quote.number.like(f"{prefix}%"))).all()
    n = max((int(m.group(1)) for x in nums if (m := re.match(rf"{prefix}(\d+)", x))), default=0) + 1
    return f"{prefix}{n:04d}"


def quote_status_changed(db: Session, quote: Quote, old: str, user, lost_code=None, lost_reason=None):
    """Status des Angebots steuert Anfrage und Angebotsverfolgung (REV01-P01/P06)."""
    from ..calc_engine import DEFAULT_SETTINGS  # noqa: PLC0415
    from ..inquiry import cascade_stage, refresh_inquiry, set_stage, start_followup  # noqa: PLC0415
    from ..models import Activity, CalcSettings, Opportunity  # noqa: PLC0415
    opp = db.get(Opportunity, quote.opportunity_id) if quote.opportunity_id else None
    if quote.status == "versendet":
        row = db.get(CalcSettings, 1)
        days = int(({**DEFAULT_SETTINGS, **((row.data or {}) if row else {})}).get("followup_workdays") or 5)
        start_followup(db, quote, user, days)
    if quote.status in ("angenommen", "abgelehnt", "ersetzt"):
        for t in db.query(Activity).filter(Activity.quote_id == quote.id, Activity.kind == "angebotsverfolgung",
                                           Activity.done.is_(False)).all():
            t.done = True
    if opp:
        db.flush()
        old_stage = opp.stage
        if quote.status == "angenommen":
            set_stage(opp, "gewonnen")
        elif quote.status == "abgelehnt":
            from .calc import REASON_LABELS  # noqa: PLC0415
            opp.lost_code = lost_code or "sonstiges"
            label = REASON_LABELS.get(opp.lost_code, "Sonstiges")
            opp.lost_reason = f"{label}: {lost_reason}" if lost_reason else label
            set_stage(opp, "verloren")
            opp.lost_code, opp.lost_reason = lost_code or "sonstiges", (f"{label}: {lost_reason}" if lost_reason else label)
        cascade_stage(db, opp, old_stage)
        db.flush()
        refresh_inquiry(db, opp)


def set_items(quote: Quote, items: list[s.QuoteItemIn]):
    quote.items.clear()
    for i, it in enumerate(items, start=1):
        quote.items.append(QuoteItem(position=i, **it.model_dump()))


@router.get("", response_model=dict)
def list_quotes(
    q: str | None = None,
    status: str | None = None,
    account_id: int | None = None,
    opportunity_id: int | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(can_read),
):
    stmt = select(Quote)
    if q:
        stmt = stmt.where(or_(Quote.number.ilike(f"%{q}%"), Quote.title.ilike(f"%{q}%")))
    if status:
        stmt = stmt.where(Quote.status.in_(status.split(",")))
    if account_id:
        stmt = stmt.where(Quote.account_id == account_id)
    if opportunity_id:
        stmt = stmt.where(Quote.opportunity_id == opportunity_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Quote.number.desc()).offset(offset).limit(limit)).unique().all()
    return {"total": total, "items": [s.QuoteOut.model_validate(r).model_dump(mode="json") for r in rows]}


@router.get("/settings")
def quote_settings(_: User = Depends(can_read)):
    return {"company_name": settings.COMPANY_NAME, "default_tax_rate": settings.DEFAULT_TAX_RATE}


@router.get("/{quote_id}", response_model=s.QuoteOut)
def get_quote(quote_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    obj = db.get(Quote, quote_id)
    if not obj:
        raise HTTPException(404, "Angebot nicht gefunden")
    return obj


def _no_supplier(db: Session, account_id: int | None):
    """Angebote gehen an Kunden/Interessenten, nie an Lieferanten (REV01-B04)."""
    acc = db.get(Account, account_id) if account_id else None
    if acc is not None and acc.type == "lieferant":
        raise HTTPException(400, f"„{acc.name}“ ist als Lieferant angelegt – Angebote nur an Kunden oder Interessenten")


@router.post("", response_model=s.QuoteOut, status_code=201)
def create_quote(data: s.QuoteCreate, db: Session = Depends(get_db), user: User = Depends(can_write)):
    _no_supplier(db, data.account_id)
    values = data.model_dump(exclude={"items"})
    values["owner_id"] = values.get("owner_id") or user.id
    values["quote_date"] = values.get("quote_date") or date.today()
    values["valid_until"] = values.get("valid_until") or values["quote_date"] + timedelta(days=30)
    if values.get("tax_rate") is None:
        values["tax_rate"] = settings.DEFAULT_TAX_RATE
    quote = Quote(number=next_number(db), **values)
    set_items(quote, data.items)
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.patch("/{quote_id}", response_model=s.QuoteOut)
def update_quote(quote_id: int, data: s.QuoteUpdate, db: Session = Depends(get_db), user: User = Depends(can_write)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    values = data.model_dump(exclude_unset=True, exclude={"items", "lost_code", "lost_reason"})
    if "account_id" in values:
        _no_supplier(db, values["account_id"])
    old_status = quote.status
    new_status = values.get("status", old_status)
    if new_status == "abgelehnt" and old_status != "abgelehnt" and not (data.lost_code or data.lost_reason):
        raise HTTPException(400, "Abgelehnt nur mit Verlustgrund – bitte Grund angeben")
    for k, v in values.items():
        if k == "tax_rate" and v is None:
            continue
        setattr(quote, k, v)
    if data.items is not None:
        set_items(quote, data.items)
    if new_status != old_status:
        quote_status_changed(db, quote, old_status, user, data.lost_code, data.lost_reason)
    db.commit()
    db.refresh(quote)
    return quote


@router.post("/{quote_id}/duplicate", response_model=s.QuoteOut, status_code=201)
def duplicate_quote(quote_id: int, db: Session = Depends(get_db), user: User = Depends(can_write)):
    src = db.get(Quote, quote_id)
    if not src:
        raise HTTPException(404, "Angebot nicht gefunden")
    copy = Quote(
        number=next_number(db), title=f"{src.title} (Kopie)", account_id=src.account_id,
        contact_id=src.contact_id, opportunity_id=src.opportunity_id, status="entwurf",
        quote_date=date.today(), valid_until=date.today() + timedelta(days=30),
        tax_rate=src.tax_rate, intro_text=src.intro_text, terms=src.terms, owner_id=user.id,
    )
    set_items(copy, [s.QuoteItemIn.model_validate(i, from_attributes=True) for i in src.items])
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


@router.delete("/{quote_id}", status_code=204)
def delete_quote(quote_id: int, db: Session = Depends(get_db), _: User = Depends(can_write)):
    """Nur Entwürfe sind löschbar – versendete/angenommene/abgelehnte Angebote sind Nachweise."""
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    if quote.status != "entwurf":
        raise HTTPException(400, "Versendete oder entschiedene Angebote bleiben als Nachweis erhalten – "
                                 "bitte Status ändern statt löschen")
    db.delete(quote)
    db.commit()
