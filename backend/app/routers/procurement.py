"""Beschaffung von Werkzeugen, Montagelinien, Vorrichtungen und Prüfmitteln: Anfrage an Lieferanten,
Angebotsvergleich, Entscheidung und Übernahme der Kosten in die Kalkulation."""
import math
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..auth import can_read, can_write
from ..calc_engine import compute, normalize
from ..database import get_db
from ..models import (
    Account, Calculation, CalculationVersion, Contact, Machine, ProcurementOffer, ProcurementRequest, User,
)
from .calc import apply_results, sync_opportunity

router = APIRouter()

KINDS = {"werkzeug": "Spritzgießwerkzeug", "montagelinie": "Montagelinie", "vorrichtung": "Vorrichtung",
         "pruefmittel": "Prüfmittel", "sonstiges": "Sonstiges"}
STATUS = ("offen", "angefragt", "entschieden", "bestellt", "abgebrochen")


class RequestIn(BaseModel):
    calculation_id: int | None = None
    kind: str = "werkzeug"
    title: str | None = None
    status: str | None = None
    spec: dict | None = None
    reply_by: date | None = None
    needed_by: date | None = None
    note: str | None = None


class OfferIn(BaseModel):
    account_id: int | None = None
    supplier_name: str | None = None
    contact_email: str | None = None
    status: str | None = None
    requested_at: date | None = None
    offer_no: str | None = None
    offer_date: date | None = None
    price: float | None = None
    lead_time_weeks: float | None = None
    cavities: int | None = None
    hot_runner: str | None = None
    steel: str | None = None
    tool_life_shots: float | None = None
    warranty: str | None = None
    payment_terms: str | None = None
    location: str | None = None
    rating: int | None = Field(None, ge=1, le=5)
    note: str | None = None


class DecideIn(BaseModel):
    offer_id: int | None = None   # None = Entscheidung zurücknehmen
    note: str | None = None


def _num(db: Session) -> str:
    prefix = f"B{date.today():%y}-"
    last = db.scalar(select(ProcurementRequest.number).where(ProcurementRequest.number.like(f"{prefix}%"))
                     .order_by(ProcurementRequest.number.desc()).limit(1))
    return f"{prefix}{(int(last.split('-')[-1]) + 1 if last else 1):04d}"


def _offer_out(o: ProcurementOffer) -> dict:
    return {c.name: getattr(o, c.name) for c in ProcurementOffer.__table__.columns}


def _out(r: ProcurementRequest, detail: bool = True) -> dict:
    offers = [_offer_out(o) for o in r.offers]
    priced = [o for o in offers if o["price"] and o["status"] != "abgesagt"]
    chosen = next((o for o in offers if o["id"] == r.decided_offer_id), None)
    c = r.calculation
    out = {col.name: getattr(r, col.name) for col in ProcurementRequest.__table__.columns}
    out.update({
        "kind_label": KINDS.get(r.kind, r.kind),
        "calculation": {"id": c.id, "number": c.number, "article_name": c.article_name,
                        "customer_article_no": c.customer_article_no,
                        "account": c.account.name if c.account else None} if c else None,
        "offers_count": len(offers), "offers_priced": len(priced),
        "best_price": min((o["price"] for o in priced), default=None),
        "max_price": max((o["price"] for o in priced), default=None),
        "chosen": chosen,
    })
    if detail:
        out["offers"] = offers
    return out


def _calc_inputs(c: Calculation) -> dict:
    ver = next((v for v in c.versions if v.version_no == c.current_version), None)
    return (ver.inputs if ver else {}) or {}


def _prefill(db: Session, kind: str, c: Calculation | None) -> tuple[str, dict]:
    """Technische Eckdaten der Anfrage aus der Kalkulation vorbelegen."""
    if not c:
        return KINDS.get(kind, "Beschaffung"), {}
    i = _calc_inputs(c)
    title = f"{KINDS.get(kind, 'Beschaffung')} {c.article_name}"
    common = {"part_name": c.article_name, "customer_part_no": c.customer_article_no or "",
              "own_part_no": c.own_article_no or "", "annual_volume": i.get("annual_volume"),
              "project_years": i.get("project_years"), "sop": c.sop_date.isoformat() if c.sop_date else ""}
    if kind != "werkzeug":
        return title, {**common, "scope": "", "cycle_time_s": None, "operations": ", ".join(
            o.get("name", "") for o in i.get("operations") or []), "acceptance": "Vorabnahme beim Lieferanten, Endabnahme im Werk"}
    m = db.get(Machine, i.get("machine_id")) if i.get("machine_id") else None
    cav = int(i.get("cavities") or 1)
    comps = i.get("components") or []
    years = float(i.get("project_years") or 5)
    shots = math.ceil(float(i.get("annual_volume") or 0) * years / max(cav, 1) * 1.2 / 10000) * 10000 if i.get("annual_volume") else None
    return title, {
        **common,
        "material": " + ".join([i.get("material_name") or ""] + [x.get("material_name") or x.get("label") or "" for x in comps]).strip(" +"),
        "part_weight_g": i.get("part_weight_g"), "cavities": cav,
        "tool_type": "2K / Mehrkomponenten" if comps else ("Familienwerkzeug" if i.get("family_group") else "1K Einkomponenten"),
        "hot_runner": "Heißkanal" if not float(i.get("sprue_weight_g") or 0) else "Kaltkanal / Anguss",
        "hot_runner_nozzles": cav if not float(i.get("sprue_weight_g") or 0) else None,
        "hot_runner_make": "", "gate": "", "cycle_time_s": i.get("cycle_time_s"),
        "machine": f"{m.number} {m.name}" if m else (i.get("machine_name") or ""),
        "clamping_force_t": m.clamping_force_t if m else None, "tool_life_shots": shots,
        "steel": "1.2311 / 1.2738 (Formplatten), Einsätze 1.2343 gehärtet", "mold_standard": "Hasco oder Meusburger",
        "slides": "", "cooling": "konturnah, Temperierkreise beschriftet", "ejection": "",
        "surface": "", "sampling": "T0-Bemusterung inkl. 50 Teile, Erstmusterprüfbericht (EMPB/PPAP)",
        "documents": "Zeichnung und 3D-Daten (STEP) als Anlage", "delivery": "DAP Werk F&R",
    }


@router.get("")
def list_requests(calculation_id: int | None = None, kind: str | None = None, status: str | None = None,
                  q: str | None = None, db: Session = Depends(get_db), _: User = Depends(can_read)):
    stmt = select(ProcurementRequest).order_by(ProcurementRequest.id.desc())
    if calculation_id:
        stmt = stmt.where(ProcurementRequest.calculation_id == calculation_id)
    if kind:
        stmt = stmt.where(ProcurementRequest.kind == kind)
    if status:
        stmt = stmt.where(ProcurementRequest.status.in_(status.split(",")))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(ProcurementRequest.title.ilike(like), ProcurementRequest.number.ilike(like)))
    rows = db.scalars(stmt).unique().all()
    return {"total": len(rows), "items": [_out(r, detail=False) for r in rows]}


@router.post("", status_code=201)
def create_request(data: RequestIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    c = db.get(Calculation, data.calculation_id) if data.calculation_id else None
    if data.calculation_id and not c:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    title, spec = _prefill(db, data.kind, c)
    r = ProcurementRequest(number=_num(db), calculation_id=c.id if c else None, kind=data.kind,
                           title=data.title or title, spec={**spec, **(data.spec or {})}, reply_by=data.reply_by,
                           needed_by=data.needed_by, note=data.note, owner_id=user.id, status="offen")
    db.add(r)
    db.commit()
    db.refresh(r)
    return _out(r)


def _get(db: Session, rid: int) -> ProcurementRequest:
    r = db.get(ProcurementRequest, rid)
    if not r:
        raise HTTPException(404, "Beschaffungsvorgang nicht gefunden")
    return r


@router.get("/{rid}")
def get_request(rid: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    return _out(_get(db, rid))


@router.put("/{rid}")
def update_request(rid: int, data: RequestIn, db: Session = Depends(get_db), _: User = Depends(can_write)):
    r = _get(db, rid)
    vals = data.model_dump(exclude_unset=True)
    if "status" in vals and vals["status"] not in STATUS:
        raise HTTPException(400, "Unbekannter Status")
    for k, v in vals.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return _out(r)


@router.delete("/{rid}", status_code=204)
def delete_request(rid: int, db: Session = Depends(get_db), _: User = Depends(can_write)):
    db.delete(_get(db, rid))
    db.commit()


@router.post("/{rid}/offers", status_code=201)
def add_offer(rid: int, data: OfferIn, db: Session = Depends(get_db), _: User = Depends(can_write)):
    r = _get(db, rid)
    vals = data.model_dump()
    acc = db.get(Account, data.account_id) if data.account_id else None
    if not vals.get("supplier_name"):
        if not acc:
            raise HTTPException(400, "Lieferant angeben")
        vals["supplier_name"] = acc.name
    if acc and not vals.get("contact_email"):
        ct = db.scalars(select(Contact).where(Contact.account_id == acc.id, Contact.email.is_not(None))).first()
        vals["contact_email"] = ct.email if ct else None
    vals["status"] = vals.get("status") or ("angebot" if vals.get("price") else "angefragt")
    vals["requested_at"] = vals.get("requested_at") or date.today()
    r.offers.append(ProcurementOffer(**vals))
    if r.status == "offen":
        r.status = "angefragt"
    db.commit()
    db.refresh(r)
    return _out(r)


@router.put("/offers/{oid}")
def update_offer(oid: int, data: OfferIn, db: Session = Depends(get_db), _: User = Depends(can_write)):
    o = db.get(ProcurementOffer, oid)
    if not o:
        raise HTTPException(404, "Angebot nicht gefunden")
    vals = data.model_dump(exclude_unset=True)
    for k, v in vals.items():
        setattr(o, k, v)
    if "price" in vals and vals["price"] and o.status == "angefragt":
        o.status = "angebot"
    db.commit()
    r = _get(db, o.request_id)
    db.refresh(r)
    return _out(r)


@router.delete("/offers/{oid}")
def delete_offer(oid: int, db: Session = Depends(get_db), _: User = Depends(can_write)):
    o = db.get(ProcurementOffer, oid)
    if not o:
        raise HTTPException(404, "Angebot nicht gefunden")
    r = _get(db, o.request_id)
    if r.decided_offer_id == o.id:
        r.decided_offer_id, r.status = None, "angefragt"
    db.delete(o)
    db.commit()
    db.refresh(r)
    return _out(r)


@router.post("/{rid}/decide")
def decide(rid: int, data: DecideIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Lieferant auswählen (Vergabeentscheidung); übrige Angebote werden „nicht gewählt“."""
    r = _get(db, rid)
    if data.offer_id and not any(o.id == data.offer_id for o in r.offers):
        raise HTTPException(400, "Angebot gehört nicht zu diesem Vorgang")
    for o in r.offers:
        if data.offer_id is None:
            o.status = "angebot" if o.price else "angefragt"
        elif o.id == data.offer_id:
            o.status = "gewaehlt"
        elif o.status in ("angebot", "gewaehlt"):
            o.status = "abgelehnt"
    r.decided_offer_id = data.offer_id
    r.decision_note = data.note
    r.decided_by_id = user.id if data.offer_id else None
    r.decided_at = datetime.now(timezone.utc) if data.offer_id else None
    r.status = "entschieden" if data.offer_id else "angefragt"
    db.commit()
    db.refresh(r)
    return _out(r)


@router.post("/{rid}/apply")
def apply_to_calc(rid: int, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Preis des gewählten Angebots als Einmalkosten (Kosten) in eine neue Kalkulationsversion übernehmen."""
    r = _get(db, rid)
    chosen = next((o for o in r.offers if o.id == r.decided_offer_id), None)
    if not r.calculation_id or not chosen or not chosen.price:
        raise HTTPException(400, "Kalkulation und gewähltes Angebot mit Preis erforderlich")
    c = db.get(Calculation, r.calculation_id)
    inp = normalize(dict(_calc_inputs(c)))
    one = [dict(o) for o in inp.get("one_time") or []]
    keys = [r.title.lower(), {"werkzeug": "werkzeug"}.get(r.kind, KINDS.get(r.kind, "").lower())]
    idx = next((n for n, o in enumerate(one) if (o.get("procurement_id") == r.id)), None)
    if idx is None:
        idx = next((n for n, o in enumerate(one) if any(k and k in (o.get("label") or "").lower() for k in keys)), None)
    if idx is None:
        one.append({"label": KINDS.get(r.kind, r.title), "cost": 0, "price": 0})
        idx = len(one) - 1
    old_cost = float(one[idx].get("cost") or 0)
    one[idx]["cost"] = chosen.price
    if not float(one[idx].get("price") or 0):
        one[idx]["price"] = chosen.price
    one[idx]["procurement_id"] = r.id
    inp["one_time"] = one
    res = compute(inp)
    no = (c.versions[-1].version_no if c.versions else 0) + 1
    de = lambda v: f"{v:,.0f}".replace(",", ".")  # noqa: E731
    note = (f"{one[idx]['label']}: Kosten {de(old_cost)} → {de(chosen.price)} € aus Beschaffung {r.number} "
            f"({chosen.supplier_name}{', Angebot ' + chosen.offer_no if chosen.offer_no else ''})")
    c.versions.append(CalculationVersion(version_no=no, inputs=inp, results=res, change_note=note, created_by_id=user.id))
    c.current_version = no
    apply_results(c, res, inp)
    r.applied_version = no
    db.flush()
    sync_opportunity(db, c)
    db.commit()
    return {**_out(r), "version_no": no, "change_note": note}
