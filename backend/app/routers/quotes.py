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
    if quote.status in ("angenommen", "teilweise", "abgelehnt", "ersetzt"):
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
    probability: str | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(can_read),
):
    stmt = select(Quote)
    # REV03-09: Filter nach Einschätzung „wie wahrscheinlich wird uns das Angebot vergeben“ (z. B. 75 oder „keine“)
    if probability:
        from ..models import Opportunity  # noqa: PLC0415
        stmt = stmt.join(Opportunity, Quote.opportunity_id == Opportunity.id, isouter=probability == "keine")
        if probability == "keine":
            stmt = stmt.where(or_(Opportunity.id.is_(None), Opportunity.probability_estimated.isnot(True)))
        else:
            stmt = stmt.where(Opportunity.probability_estimated.is_(True), Opportunity.probability == int(probability))
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


# ---------------- Auftrag erhalten: Ergebnis je Artikel (Teilbeauftragung, Varianten) – MB-30 … MB-35
OUTCOMES = ("gewonnen", "verloren", "andere_variante", "offen")


def _award_calcs(db: Session, quote: Quote):
    from ..inquiry import calcs_of  # noqa: PLC0415
    from ..models import Calculation  # noqa: PLC0415
    ids = []
    for it in quote.items:
        if it.calculation_id and it.calculation_id not in ids:
            ids.append(it.calculation_id)
    calcs = [c for c in (db.get(Calculation, i) for i in ids) if c]
    if not calcs and quote.opportunity_id:
        calcs = [c for c in calcs_of(db, quote.opportunity_id) if c.status != "kein_angebot"]
    return calcs


def _outcome(c) -> str:
    if c.status == "gewonnen":
        return "gewonnen"
    if c.status == "verloren":
        return "andere_variante" if c.close_reason == "andere_variante" else "verloren"
    return "offen"


@router.get("/{quote_id}/award")
def award_preview(quote_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    return [{"calculation_id": c.id, "number": c.number, "name": c.article_name, "status": c.status, "outcome": _outcome(c),
             "reason": c.close_reason if c.status == "verloren" else None, "note": c.close_note if c.status == "verloren" else None,
             "peak_revenue": float(c.peak_revenue if c.peak_revenue is not None else (c.annual_revenue or 0)),
             "one_time_revenue": float(c.one_time_revenue or 0)} for c in _award_calcs(db, quote)]


@router.post("/{quote_id}/award", response_model=s.QuoteOut)
def award(quote_id: int, data: dict, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Auftrag erhalten: je Artikel gewonnen / verloren (mit Grund) / andere Variante beauftragt / noch offen.
    Angebot → „angenommen“ (alle gewonnen) oder „teilweise“ (mindestens einer gewonnen)."""
    from ..inquiry import refresh_inquiry  # noqa: PLC0415
    from ..models import Activity, Opportunity  # noqa: PLC0415
    from .calc import REASON_LABELS  # noqa: PLC0415
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    if quote.status in ("entwurf", "ersetzt"):
        raise HTTPException(400, "Auftrag nur für versendete Angebote erfassen")
    calcs = {c.id: c for c in _award_calcs(db, quote)}
    lines = data.get("lines") or []
    if calcs and {ln.get("calculation_id") for ln in lines} != set(calcs):
        raise HTTPException(400, "Bitte für jeden Artikel des Angebots ein Ergebnis wählen")
    if calcs and not any(ln.get("outcome") == "gewonnen" for ln in lines):
        raise HTTPException(400, "Mindestens ein Artikel muss beauftragt sein – sonst Angebot als „abgelehnt“ speichern")
    summary = {"gewonnen": [], "verloren": [], "andere_variante": [], "offen": []}
    for ln in lines:
        c, out = calcs[ln["calculation_id"]], ln.get("outcome")
        if out not in OUTCOMES:
            raise HTTPException(400, f"Unbekanntes Ergebnis „{out}“")
        if out == "gewonnen":
            c.status, c.probability = "gewonnen", 100
        elif out == "verloren":
            code = ln.get("reason") or "sonstiges"
            if code == "sonstiges" and not (ln.get("note") or "").strip():
                raise HTTPException(400, f"{c.number}: Verlustgrund „Sonstiges“ braucht einen Freitext")
            c.status, c.probability, c.close_reason, c.close_note = "verloren", 0, code, (ln.get("note") or None)
        elif out == "andere_variante":
            c.status, c.probability, c.close_reason, c.close_note = "verloren", 0, "andere_variante", (ln.get("note") or None)
        elif c.status in ("gewonnen", "verloren"):        # wieder geöffnet
            c.status, c.close_reason, c.close_note = "verhandlung", None, None
        summary[out].append(c.number)
    old = quote.status
    quote.status = "angenommen" if not summary["verloren"] + summary["andere_variante"] + summary["offen"] else "teilweise"
    db.flush()
    opp = db.get(Opportunity, quote.opportunity_id) if quote.opportunity_id else None
    if quote.status == "angenommen" or not calcs:
        quote.status = "angenommen"
        quote_status_changed(db, quote, old, user)
    else:
        for t in db.query(Activity).filter(Activity.quote_id == quote.id, Activity.kind == "angebotsverfolgung",
                                           Activity.done.is_(False)).all():
            t.done = True
        if opp:
            refresh_inquiry(db, opp)
    text = "; ".join(f"{lbl}: {', '.join(v)}" for lbl, v in (("beauftragt", summary["gewonnen"]), ("verloren", summary["verloren"]),
                     (REASON_LABELS["andere_variante"].lower(), summary["andere_variante"]), ("noch offen", summary["offen"])) if v)
    db.add(Activity(type="notiz", subject=f"Auftrag erhalten zu {quote.number}: {len(summary['gewonnen'])} von {len(lines) or 1} Artikeln",
                    description=(text + (f"\n{data['note']}" if data.get("note") else "")) or None, done=True,
                    account_id=quote.account_id, opportunity_id=quote.opportunity_id, quote_id=quote.id, owner_id=user.id))
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
