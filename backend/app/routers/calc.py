"""Kalkulation: Stammdaten, Parameter, Kalkulationen mit Versionen, Nachkalkulation."""
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .. import schemas as s
from ..auth import admin_only, can_read, can_write
from ..calc_engine import DEFAULT_INPUTS, DEFAULT_SETTINGS, compute, normalize, post_calculate
from ..crud import make_crud_router
from ..database import get_db
from ..models import (
    STAGE_PROBABILITY, Activity, CalcSettings, Calculation, CalculationCall, CalculationVersion, Machine, Material,
    Opportunity, PostCalculation, Quote, QuoteItem, User,
)
from .quotes import next_number as next_quote_number

machines = make_crud_router(
    model=Machine, create_schema=s.MachineBase, update_schema=s.MachineUpdate, out_schema=s.MachineOut,
    search_fields=["name", "number", "location"], filter_fields=["active"], default_sort="name",
)
materials = make_crud_router(
    model=Material, create_schema=s.MaterialBase, update_schema=s.MaterialUpdate, out_schema=s.MaterialOut,
    search_fields=["name", "family", "supplier"], filter_fields=["active", "family"], default_sort="name",
)

router = APIRouter()      # /api/calc  (Parameter, Vorschau)
calcs = APIRouter()       # /api/calculations

STATUS_TO_STAGE = {
    "anfrage": "lead", "kalkulation": "qualifiziert", "angeboten": "angebot",
    "verhandlung": "verhandlung", "gewonnen": "gewonnen", "verloren": "verloren", "zurueckgestellt": "qualifiziert",
}
STATUS_PROBABILITY = {"anfrage": 10, "kalkulation": 20, "angeboten": 40, "verhandlung": 60,
                      "gewonnen": 100, "verloren": 0, "zurueckgestellt": 5}
REASON_LABELS = {
    "artikelpreis_zu_hoch": "Artikelpreis zu hoch", "werkzeug_zu_teuer": "Werkzeug zu teuer",
    "investition_zu_teuer": "Investition zu teuer", "projekt_kunde_nicht_gewonnen": "Kunde hat Projekt nicht gewonnen",
    "projekt_eingestellt": "Projekt beim Kunden eingestellt", "lieferzeit": "Lieferzeit / Kapazität",
    "technik": "Technisch nicht machbar", "sonstiges": "Sonstiges",
}


# ---------------- Parameter ----------------
def get_settings(db: Session) -> dict:
    row = db.get(CalcSettings, 1)
    if not row:
        row = CalcSettings(id=1, data=dict(DEFAULT_SETTINGS))
        db.add(row)
        db.commit()
    return {**DEFAULT_SETTINGS, **(row.data or {})}


@router.get("/settings")
def read_settings(db: Session = Depends(get_db), _: User = Depends(can_read)):
    return get_settings(db)


@router.put("/settings")
def write_settings(data: dict, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    current = get_settings(db)
    clean = {k: float(v) for k, v in data.items() if k in DEFAULT_SETTINGS and v not in (None, "")}
    row = db.get(CalcSettings, 1)
    row.data = {**current, **clean}
    db.commit()
    return row.data


def default_inputs(db: Session) -> dict:
    st = get_settings(db)
    inp = dict(DEFAULT_INPUTS)
    for k in ("labor_rate_h", "setup_rate_h", "assembly_rate_h", "mgk_pct", "fgk_pct", "scrap_pct", "vwgk_pct",
              "vtgk_pct", "pm_pct", "quality_pct", "toolshop_pct", "profit_pct", "cash_discount_pct", "rebate_pct", "productivity_pct",
              "assembly_productivity_pct", "setup_time_h", "setup_persons", "startup_scrap_pcs"):
        inp[k] = st[k]
    inp["extras"], inp["one_time"] = [], [{"label": "Spritzgießwerkzeug", "cost": 0, "price": 0}]
    return inp


@router.get("/defaults")
def read_defaults(db: Session = Depends(get_db), _: User = Depends(can_read)):
    return default_inputs(db)


@router.post("/preview")
def preview(inputs: dict, _: User = Depends(can_read)):
    return compute(inputs)


@router.get("/meta")
def meta(_: User = Depends(can_read)):
    return {"close_reasons": REASON_LABELS, "status_probability": STATUS_PROBABILITY,
            "call_results": CALL_RESULT_LABELS}


# ---------------- Kalkulationen ----------------
def next_calc_number(db: Session) -> str:
    prefix = f"KA-{date.today().year}-"
    last = db.scalar(select(Calculation.number).where(Calculation.number.like(f"{prefix}%"))
                     .order_by(Calculation.number.desc()).limit(1))
    return f"{prefix}{(int(last.split('-')[-1]) + 1 if last else 1):04d}"


def apply_results(calc: Calculation, res: dict):
    calc.unit_price = res["unit_price"]
    calc.annual_volume = res["annual_volume"]
    calc.annual_revenue = res["annual_revenue"]
    calc.one_time_revenue = res["one_time_price"]
    calc.margin_pct = res["margin_pct"]


def sync_opportunity(db: Session, calc: Calculation):
    """Umsatz der Kalkulation(en) in die verknüpfte Verkaufschance übernehmen."""
    if not calc.opportunity_id or not calc.sync_opportunity:
        return
    opp = db.get(Opportunity, calc.opportunity_id)
    if not opp:
        return
    linked = db.scalars(select(Calculation).where(Calculation.opportunity_id == opp.id,
                                                  Calculation.sync_opportunity.is_(True))).unique().all()
    total = sum(c.annual_revenue + c.one_time_revenue for c in linked)
    opp.amount = round(total, 2)
    if len(linked) == 1:
        opp.probability = calc.probability
        new_stage = STATUS_TO_STAGE.get(calc.status, opp.stage)
        if new_stage != opp.stage:
            opp.stage = new_stage
            opp.closed_at = date.today() if new_stage in ("gewonnen", "verloren") else None
        opp.lost_reason = REASON_LABELS.get(calc.close_reason) if calc.status == "verloren" else None
    elif total:
        opp.probability = round(sum((c.annual_revenue + c.one_time_revenue) * c.probability for c in linked) / total)


@calcs.get("", response_model=dict)
def list_calcs(
    q: str | None = None, status: str | None = None, close_reason: str | None = None,
    account_id: int | None = None, owner_id: int | None = None, opportunity_id: int | None = None,
    sort: str = "-updated_at", limit: int = Query(100, le=1000), offset: int = 0,
    db: Session = Depends(get_db), _: User = Depends(can_read),
):
    stmt = select(Calculation)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Calculation.number.ilike(like), Calculation.article_name.ilike(like),
                              Calculation.customer_article_no.ilike(like), Calculation.own_article_no.ilike(like),
                              Calculation.remark.ilike(like)))
    if status:
        stmt = stmt.where(Calculation.status.in_(status.split(",")))
    if close_reason:
        stmt = stmt.where(Calculation.close_reason == close_reason)
    for col, val in ((Calculation.account_id, account_id), (Calculation.owner_id, owner_id),
                     (Calculation.opportunity_id, opportunity_id)):
        if val:
            stmt = stmt.where(col == val)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    key = sort.lstrip("-")
    col = getattr(Calculation, key, Calculation.updated_at)
    stmt = stmt.order_by(col.desc().nulls_last() if sort.startswith("-") else col.asc().nulls_last())
    rows = db.scalars(stmt.offset(offset).limit(limit)).unique().all()
    return {"total": total, "items": [s.CalcOut.model_validate(r).model_dump(mode="json") for r in rows]}


@calcs.get("/stats")
def calc_stats(owner_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(can_read)):
    stmt = select(Calculation)
    if owner_id:
        stmt = stmt.where(Calculation.owner_id == owner_id)
    rows = db.scalars(stmt).unique().all()
    open_ = [c for c in rows if c.status not in ("gewonnen", "verloren", "zurueckgestellt")]
    won = [c for c in rows if c.status == "gewonnen"]
    lost = [c for c in rows if c.status == "verloren"]
    rev = lambda c: c.annual_revenue  # noqa: E731
    reasons = {}
    for c in lost:
        k = c.close_reason or "sonstiges"
        reasons.setdefault(k, {"reason": k, "label": REASON_LABELS.get(k, k), "count": 0, "revenue": 0})
        reasons[k]["count"] += 1
        reasons[k]["revenue"] += rev(c)
    lights = {"gruen": 0, "gelb": 0, "rot": 0}
    for c in rows:
        if c.last_traffic_light:
            lights[c.last_traffic_light] += 1
    decided = len(won) + len(lost)
    return {
        "count_total": len(rows), "count_open": len(open_),
        "open_revenue": round(sum(rev(c) for c in open_), 2),
        "open_weighted": round(sum(rev(c) * c.probability / 100 for c in open_), 2),
        "open_tooling": round(sum(c.one_time_revenue for c in open_), 2),
        "won_count": len(won), "won_revenue": round(sum(rev(c) for c in won), 2),
        "lost_count": len(lost), "lost_revenue": round(sum(rev(c) for c in lost), 2),
        "hit_rate": round(100 * len(won) / decided, 1) if decided else None,
        "lost_by_reason": sorted(reasons.values(), key=lambda r: -r["revenue"]),
        "traffic_lights": lights,
        "overdue_calls": sum(1 for c in open_ if not c.last_call_at or
                             c.last_call_at < datetime.now(timezone.utc) - timedelta(days=14)),
    }


@calcs.get("/{calc_id}", response_model=s.CalcDetail)
def get_calc(calc_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    return calc


@calcs.post("", response_model=s.CalcDetail, status_code=201)
def create_calc(data: s.CalcCreate, db: Session = Depends(get_db), user: User = Depends(can_write)):
    meta = data.model_dump(exclude={"inputs"}, exclude_none=True)
    meta.setdefault("status", "anfrage")
    meta.setdefault("probability", STATUS_PROBABILITY[meta["status"]])
    meta.setdefault("owner_id", user.id)
    meta.setdefault("inquiry_date", date.today())
    calc = Calculation(number=next_calc_number(db), **meta)
    inputs = normalize({**default_inputs(db), **(data.inputs or {})})
    res = compute(inputs)
    calc.versions.append(CalculationVersion(version_no=1, inputs=inputs, results=res,
                                            change_note="Erstkalkulation", created_by_id=user.id))
    calc.current_version = 1
    apply_results(calc, res)
    db.add(calc)
    db.flush()
    sync_opportunity(db, calc)
    db.commit()
    db.refresh(calc)
    return calc


@calcs.patch("/{calc_id}", response_model=s.CalcDetail)
def update_calc(calc_id: int, data: s.CalcMeta, db: Session = Depends(get_db), _: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    values = data.model_dump(exclude_unset=True)
    old_opp = calc.opportunity_id
    if "status" in values and "probability" not in values and values["status"] != calc.status:
        values["probability"] = STATUS_PROBABILITY[values["status"]]
    if values.get("status") and values["status"] != "verloren":
        values.setdefault("close_reason", None)
    for k, v in values.items():
        setattr(calc, k, v)
    db.flush()
    sync_opportunity(db, calc)
    if old_opp and old_opp != calc.opportunity_id:  # alte Chance neu summieren
        other = db.scalar(select(Calculation).where(Calculation.opportunity_id == old_opp).limit(1))
        if other:
            sync_opportunity(db, other)
    db.commit()
    db.refresh(calc)
    return calc


@calcs.delete("/{calc_id}", status_code=204)
def delete_calc(calc_id: int, db: Session = Depends(get_db), _: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    db.delete(calc)
    db.commit()


@calcs.post("/{calc_id}/versions", response_model=s.CalcDetail, status_code=201)
def add_version(calc_id: int, data: s.CalcVersionIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    inputs = normalize(data.inputs)
    res = compute(inputs)
    no = (calc.versions[-1].version_no if calc.versions else 0) + 1
    calc.versions.append(CalculationVersion(version_no=no, inputs=inputs, results=res,
                                            change_note=data.change_note, created_by_id=user.id))
    calc.current_version = no
    apply_results(calc, res)
    if calc.status == "anfrage":
        calc.status = "kalkulation"
        calc.probability = max(calc.probability, STATUS_PROBABILITY["kalkulation"])
    db.flush()
    sync_opportunity(db, calc)
    db.commit()
    db.refresh(calc)
    return calc


@calcs.post("/{calc_id}/opportunity", response_model=s.CalcDetail)
def create_opportunity(calc_id: int, db: Session = Depends(get_db), user: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    if not calc.account_id:
        raise HTTPException(400, "Bitte zuerst eine Firma zuordnen")
    stage = STATUS_TO_STAGE.get(calc.status, "lead")
    opp = Opportunity(name=f"{calc.article_name} ({calc.number})", account_id=calc.account_id,
                      contact_id=calc.contact_id, stage=stage, probability=calc.probability,
                      amount=calc.annual_revenue + calc.one_time_revenue, owner_id=calc.owner_id or user.id,
                      close_date=calc.due_date, source="Kalkulation")
    db.add(opp)
    db.flush()
    calc.opportunity_id = opp.id
    calc.sync_opportunity = True
    sync_opportunity(db, calc)
    db.commit()
    db.refresh(calc)
    return calc


@calcs.post("/{calc_id}/quote")
def create_quote(calc_id: int, version_no: int | None = None, db: Session = Depends(get_db),
                 user: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    ver = next((v for v in calc.versions if v.version_no == (version_no or calc.current_version)), None)
    if not ver:
        raise HTTPException(404, "Version nicht gefunden")
    r, inp = ver.results, ver.inputs
    art = calc.article_name + (f"\nIhre Art.-Nr.: {calc.customer_article_no}" if calc.customer_article_no else "")
    art += f"\nMaterial: {inp.get('material_name') or '–'} · Kalkulation {calc.number} V{ver.version_no}"
    art += f"\nPreis je 1.000 Stk: {r['price_per_1000']:.2f} € · Losgröße {inp.get('lot_size'):g} Stk"
    quote = Quote(number=next_quote_number(db), title=calc.article_name, account_id=calc.account_id,
                  contact_id=calc.contact_id, opportunity_id=calc.opportunity_id, owner_id=user.id,
                  status="entwurf", quote_date=date.today(), valid_until=date.today() + timedelta(days=30),
                  tax_rate=19, intro_text="vielen Dank für Ihre Anfrage. Gerne bieten wir Ihnen an:",
                  terms="Preise netto ab Werk, zzgl. gesetzl. MwSt. Werkzeugkosten zahlbar 50 % bei Bestellung, "
                        "50 % bei Freigabe Erstmuster. Zahlungsbedingungen Serienteile: 30 Tage netto.")
    quote.items = [QuoteItem(position=1, description=art, quantity=r["annual_volume"], unit="Stk",
                             unit_price=r["unit_price"])]
    for n, o in enumerate([o for o in r["one_time"] if o["price"]], start=2):
        quote.items.append(QuoteItem(position=n, description=f"{o['label']} (einmalig)", quantity=1,
                                     unit="psch", unit_price=o["price"]))
    db.add(quote)
    if calc.status in ("anfrage", "kalkulation"):
        calc.status = "angeboten"
        calc.probability = max(calc.probability, STATUS_PROBABILITY["angeboten"])
        sync_opportunity(db, calc)
    db.commit()
    return {"quote_id": quote.id, "number": quote.number}


CALL_RESULT_LABELS = {
    "nicht_erreicht": "Nicht erreicht", "rueckruf_vereinbart": "Rückruf vereinbart",
    "kunde_entscheidet_noch": "Kunde entscheidet noch", "preis_nachverhandeln": "Preis nachverhandeln",
    "neu_kalkulieren": "Neu kalkulieren / Änderung", "auftrag_in_aussicht": "Auftrag in Aussicht",
    "auftrag_erhalten": "Auftrag erhalten", "absage": "Absage", "sonstiges": "Sonstiges",
}


@calcs.post("/{calc_id}/call", response_model=s.CalcDetail)
def log_call(calc_id: int, data: s.CallIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Anruf mit Ergebnis dokumentieren: Anrufhistorie, „zuletzt angerufen“, Aktivität, optional Wiedervorlage."""
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    when = data.called_at or datetime.now(timezone.utc)
    contact_id = data.contact_id or calc.contact_id
    calc.calls.append(CalculationCall(called_at=when, result=data.result, note=data.note, contact_id=contact_id,
                                      follow_up=data.follow_up, user_id=user.id))
    if not calc.last_call_at or when >= calc.last_call_at:
        calc.last_call_at = when
    label = CALL_RESULT_LABELS.get(data.result, data.result)
    db.add(Activity(type="anruf", subject=f"Anruf zu {calc.number} {calc.article_name}: {label}",
                    description=data.note, due_at=when, done=True, account_id=calc.account_id,
                    contact_id=contact_id, opportunity_id=calc.opportunity_id, owner_id=user.id))
    if data.follow_up:
        db.add(Activity(type="aufgabe", subject=f"Wiedervorlage {calc.number} {calc.article_name} ({label})",
                        description=data.note, due_at=datetime.combine(data.follow_up, datetime.min.time(), timezone.utc).replace(hour=8),
                        done=False, account_id=calc.account_id, contact_id=contact_id,
                        opportunity_id=calc.opportunity_id, owner_id=calc.owner_id or user.id))
    db.commit()
    db.refresh(calc)
    return calc


@calcs.delete("/{calc_id}/calls/{call_id}", response_model=s.CalcDetail)
def delete_call(calc_id: int, call_id: int, db: Session = Depends(get_db), _: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    call = db.get(CalculationCall, call_id)
    if not calc or not call or call.calculation_id != calc_id:
        raise HTTPException(404, "Anruf nicht gefunden")
    db.delete(call)
    db.flush()
    db.refresh(calc)
    calc.last_call_at = calc.calls[-1].called_at if calc.calls else None
    db.commit()
    db.refresh(calc)
    return calc


@calcs.post("/{calc_id}/postcalcs", response_model=s.CalcDetail, status_code=201)
def add_postcalc(calc_id: int, data: s.PostCalcIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    no = data.version_no or calc.current_version
    ver = next((v for v in calc.versions if v.version_no == no), None)
    if not ver:
        raise HTTPException(404, "Version nicht gefunden")
    res, light = post_calculate(ver.inputs, ver.results, data.actuals, get_settings(db))
    calc.post_calcs.append(PostCalculation(version_no=no, reference=data.reference, period_from=data.period_from,
                                           period_to=data.period_to, actuals=data.actuals, results=res,
                                           traffic_light=light, remark=data.remark, created_by_id=user.id))
    db.commit()
    db.refresh(calc)
    return calc


@calcs.post("/{calc_id}/postcalcs/preview")
def preview_postcalc(calc_id: int, data: s.PostCalcIn, db: Session = Depends(get_db), _: User = Depends(can_read)):
    calc = db.get(Calculation, calc_id)
    ver = calc and next((v for v in calc.versions if v.version_no == (data.version_no or calc.current_version)), None)
    if not ver:
        raise HTTPException(404, "Version nicht gefunden")
    res, light = post_calculate(ver.inputs, ver.results, data.actuals, get_settings(db))
    return {**res, "traffic_light": light}


@calcs.delete("/{calc_id}/postcalcs/{pc_id}", status_code=204)
def delete_postcalc(calc_id: int, pc_id: int, db: Session = Depends(get_db), _: User = Depends(can_write)):
    pc = db.get(PostCalculation, pc_id)
    if not pc or pc.calculation_id != calc_id:
        raise HTTPException(404, "Nachkalkulation nicht gefunden")
    db.delete(pc)
    db.commit()
