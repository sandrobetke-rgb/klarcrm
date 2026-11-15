"""Kalkulation: Stammdaten, Parameter, Kalkulationen mit Versionen, Nachkalkulation."""
from datetime import date, datetime, timedelta, timezone  # noqa: F401

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .. import schemas as s
from ..auth import admin_only, can_read, can_write, get_current_user
from ..analysis import analyze
from ..calc_engine import DEFAULT_INPUTS, DEFAULT_SETTINGS, compute, machine_rate, normalize, post_calculate
from ..crud import make_crud_router
from ..database import get_db
from ..models import (
    STAGE_PROBABILITY, Activity, CalcSettings, CalcTemplate, Calculation, CalculationCall, CalculationVersion, Machine,
    Material, MaterialPrice,
    Opportunity, PostCalculation, PurchasedPart, Quote, QuoteItem, User,
)
from .quotes import next_number as next_quote_number

machines = make_crud_router(
    model=Machine, create_schema=s.MachineBase, update_schema=s.MachineUpdate, out_schema=s.MachineOut,
    search_fields=["name", "number", "location"], filter_fields=["active", "kind"], default_sort="name",
)
purchased_parts = make_crud_router(
    model=PurchasedPart, create_schema=s.PurchasedPartBase, update_schema=s.PurchasedPartUpdate,
    out_schema=s.PurchasedPartOut, search_fields=["name", "part_no", "supplier", "supplier_part_no"],
    filter_fields=["active", "supplier"], default_sort="name",
)
materials = make_crud_router(
    model=Material, create_schema=s.MaterialBase, update_schema=s.MaterialUpdate, out_schema=s.MaterialOut,
    search_fields=["name", "family", "supplier"], filter_fields=["active", "family"], default_sort="name",
)

router = APIRouter()      # /api/calc  (Parameter, Vorschau)
quote_bulk = APIRouter()  # /api/calculations-bulk
calcs = APIRouter()       # /api/calculations

STATUS_TO_STAGE = {
    "anfrage": "lead", "kalkulation": "qualifiziert", "angeboten": "angebot",
    "verhandlung": "verhandlung", "gewonnen": "gewonnen", "verloren": "verloren", "kein_angebot": "verloren",
    "zurueckgestellt": "qualifiziert",
}
STATUS_PROBABILITY = {"anfrage": 10, "kalkulation": 20, "angeboten": 40, "verhandlung": 60,
                      "gewonnen": 100, "verloren": 0, "kein_angebot": 0, "zurueckgestellt": 5}
CLOSED = ("gewonnen", "verloren", "kein_angebot", "zurueckgestellt")
NO_BID_LABELS = {
    "mengen_zu_klein": "Mengen zu klein", "artikel_zu_klein": "Artikel zu klein", "artikel_zu_gross": "Artikel zu groß",
    "keine_maschine_kapazitaet": "Keine Maschine / Kapazität", "nicht_herstellbar": "Nicht herstellbar",
    "technologie_passt_nicht": "Technologie passt nicht", "termin_nicht_machbar": "Termin nicht machbar",
    "sonstiges": "Sonstiges",
}
FEASIBILITY_LABELS = {"herstellbar": "Herstellbar", "bedingt_herstellbar": "Bedingt herstellbar",
                      "anpassungen_erforderlich": "Anpassungen erforderlich", "nicht_herstellbar": "Nicht herstellbar"}
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
    if "purchased_mgk_pct" in data and data["purchased_mgk_pct"] in (None, ""):
        clean["purchased_mgk_pct"] = None  # leer = wie MGK
    row = db.get(CalcSettings, 1)
    row.data = {**current, **clean}
    db.commit()
    return row.data


def default_inputs(db: Session) -> dict:
    st = get_settings(db)
    inp = dict(DEFAULT_INPUTS)
    for k in ("labor_rate_h", "setup_rate_h", "assembly_rate_h", "handling_rate_h", "automation_rate_h", "mgk_pct", "fgk_pct", "scrap_pct", "vwgk_pct",
              "vtgk_pct", "pm_pct", "quality_pct", "toolshop_pct", "profit_pct", "cash_discount_pct", "rebate_pct", "productivity_pct",
              "assembly_productivity_pct", "setup_time_h", "setup_persons", "startup_scrap_pcs",
              "co2_grid_kg_kwh", "co2_scope1_kg_h", "co2_masterbatch_kg_kg", "co2_transport_kg_tkm",
              "purchased_mgk_pct", "side_mgk_pct", "side_quality_pct", "side_scrap_pct", "side_markup_pct"):
        inp[k] = st.get(k, DEFAULT_SETTINGS.get(k))
    inp["extras"], inp["one_time"] = [], [{"label": "Spritzgießwerkzeug", "cost": 0, "price": 0}]
    # Neue Kalkulationen: Verpackung pauschal mit Standard-%, bis Details bekannt sind; Transport-% vorbelegt
    inp["pack_mode"], inp["pack_pct"], inp["transport_pct"] = "prozent", st["pack_pct"], st["transport_pct"]
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
            "no_bid_reasons": NO_BID_LABELS, "feasibility": FEASIBILITY_LABELS,
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
        if calc.status == "verloren":
            opp.lost_reason = REASON_LABELS.get(calc.close_reason)
        elif calc.status == "kein_angebot":
            opp.lost_reason = "Kein Angebot: " + (NO_BID_LABELS.get(calc.no_bid_reason) or "ohne Grund") + \
                (f" ({calc.no_bid_note})" if calc.no_bid_note else "")
        else:
            opp.lost_reason = None
    elif total:
        opp.probability = round(sum((c.annual_revenue + c.one_time_revenue) * c.probability for c in linked) / total)


def is_big(c: Calculation, st: dict) -> list[str]:
    """Gründe, warum eine Kalkulation als Großprojekt gilt (leer = kein Großprojekt)."""
    reasons = []
    if c.annual_revenue >= st["big_revenue_threshold"]:
        reasons.append("umsatz")
    if c.invest >= st["big_invest_threshold"]:
        reasons.append("invest")
    return reasons


@calcs.get("", response_model=dict)
def list_calcs(
    q: str | None = None, status: str | None = None, close_reason: str | None = None, big: bool = False,
    feasibility: str | None = None, no_bid_reason: str | None = None, approval_status: str | None = None,
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
    if feasibility:
        stmt = stmt.where(Calculation.feasibility.is_(None) if feasibility == "null" else Calculation.feasibility == feasibility)
    if no_bid_reason:
        stmt = stmt.where(Calculation.no_bid_reason == no_bid_reason)
    if approval_status:
        stmt = stmt.where(Calculation.approval_status == approval_status)
    for col, val in ((Calculation.account_id, account_id), (Calculation.owner_id, owner_id),
                     (Calculation.opportunity_id, opportunity_id)):
        if val:
            stmt = stmt.where(col == val)
    key = sort.lstrip("-")
    col = getattr(Calculation, key, Calculation.updated_at)
    stmt = stmt.order_by(col.desc().nulls_last() if sort.startswith("-") else col.asc().nulls_last(), Calculation.id.desc())
    if big:  # Großprojekte: Invest steckt in den Versionen, daher Filter in Python (Datenmenge klein)
        st = get_settings(db)
        rows = [r for r in db.scalars(stmt).unique().all() if is_big(r, st)]
        total, rows = len(rows), rows[offset:offset + limit]
    else:
        total = db.scalar(select(func.count()).select_from(stmt.subquery()))
        rows = db.scalars(stmt.offset(offset).limit(limit)).unique().all()
    return {"total": total, "items": [s.CalcOut.model_validate(r).model_dump(mode="json") for r in rows]}


@calcs.get("/stats")
def calc_stats(owner_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(can_read)):
    stmt = select(Calculation)
    if owner_id:
        stmt = stmt.where(Calculation.owner_id == owner_id)
    rows = db.scalars(stmt).unique().all()
    open_ = [c for c in rows if c.status not in CLOSED]
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
    no_bid = [c for c in rows if c.status == "kein_angebot"]
    nb = {}
    for c in no_bid:
        k = c.no_bid_reason or "sonstiges"
        nb.setdefault(k, {"reason": k, "label": NO_BID_LABELS.get(k, k), "count": 0, "revenue": 0})
        nb[k]["count"] += 1
        nb[k]["revenue"] += rev(c)
    feas = {k: 0 for k in FEASIBILITY_LABELS} | {"offen": 0}
    for c in open_:
        feas[c.feasibility or "offen"] += 1
    st = get_settings(db)
    big_open = [c for c in open_ if is_big(c, st)]
    return {
        "approvals_open": sum(1 for c in rows if c.approval_status == "angefragt"),
        "approvals_missing": sum(1 for c in open_ if c.approval_reasons and not c.is_approved and c.approval_status != "angefragt"),
        "no_bid_count": len(no_bid), "no_bid_by_reason": sorted(nb.values(), key=lambda r: -r["count"]),
        "feasibility_open": feas,
        "big_open_count": len(big_open),
        "big_open_revenue": round(sum(rev(c) for c in big_open), 2),
        "big_open_invest": round(sum(c.invest for c in big_open), 2),
        "big_revenue_threshold": st["big_revenue_threshold"], "big_invest_threshold": st["big_invest_threshold"],
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
    if values.get("status") and values["status"] != "kein_angebot":
        values.setdefault("no_bid_reason", None)
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
def delete_calc(calc_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    """Nur Administratoren; die Löschung wird im Änderungsprotokoll festgehalten."""
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
    db.flush()  # Verknüpfung muss für die Summenabfrage sichtbar sein
    sync_opportunity(db, calc)
    db.commit()
    db.refresh(calc)
    return calc


def _de(v, d=2):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


L = {
    "de": {"your_no": "Ihre Art.-Nr.", "material": "Material", "calc": "Kalkulation", "per1000": "Preis je 1.000 Stk",
           "lot": "Losgröße", "pcs": "Stk", "clause": "Preisgleitklausel: Materialbasis", "as_of": "Stand", "index": "Index",
           "adjust": "Anpassung bei Änderung um mehr als ±", "amort": "Inkl. Werkzeugamortisation", "per1000s": "je 1.000 Stk",
           "over": "über", "vol": "Preise je 1.000 Stk nach Jahresmenge", "peryear": "Stk/Jahr", "tiers": "Staffelpreise je 1.000 Stk",
           "lotw": "Los", "pack": "Verpackung", "perunit": "Stk je VE", "delivery": "Lieferbedingung", "exw": "ab Werk",
           "dap": "frei Haus", "lifecycle": "Lebensweg", "recycled": "Rezyklatanteil", "marking": "Werkstoffkennzeichnung",
           "mono": "Monomaterial", "co2": "CO₂-Fußabdruck (Cradle-to-Gate)", "of_which": "davon Scope 1+2",
           "once": "einmalig", "bulk": "Sammelangebot", "articles": "Artikel",
           "years": "Serienpreis je 1.000 Stk nach Lieferjahr", "year": "Jahr", "pre": "Vorserienpreis",
           "pre_note": "gilt für Vorserienmengen bis", "pre_lot": "je Los"},
    "en": {"your_no": "Your part no.", "material": "Material", "calc": "Costing", "per1000": "Price per 1,000 pcs",
           "lot": "Lot size", "pcs": "pcs", "clause": "Price adjustment clause: material basis", "as_of": "as of", "index": "index",
           "adjust": "adjustment if changed by more than ±", "amort": "Incl. tool amortisation", "per1000s": "per 1,000 pcs",
           "over": "over", "vol": "Prices per 1,000 pcs by annual volume", "peryear": "pcs/year", "tiers": "Lot-size prices per 1,000 pcs",
           "lotw": "Lot", "pack": "Packaging", "perunit": "pcs per unit", "delivery": "Delivery terms", "exw": "ex works",
           "dap": "delivered", "lifecycle": "Life cycle", "recycled": "recycled content", "marking": "material marking",
           "mono": "mono-material", "co2": "Carbon footprint (cradle-to-gate)", "of_which": "thereof scope 1+2",
           "once": "one-off", "bulk": "Combined quotation", "articles": "items",
           "years": "Series price per 1,000 pcs by delivery year", "year": "Year", "pre": "Pre-series price",
           "pre_note": "valid for pre-series quantities up to", "pre_lot": "per lot"},
}


def build_quote(db: Session, pairs: list, user: User, lang: str = "de") -> Quote:
    """Angebot aus einer oder mehreren Kalkulationen (je mit Version). Serienteile zuerst, danach Einmalkosten."""
    calcs = [c for c, _ in pairs]
    missing = [f"{c.number} ({', '.join(c.approval_reasons)})" for c in calcs if c.approval_reasons and not c.is_approved]
    if missing:
        raise HTTPException(409, "Freigabe erforderlich (Vier-Augen-Prinzip) für: " + "; ".join(missing))
    first = calcs[0]
    single = len(calcs) == 1
    opp_ids = {c.opportunity_id for c in calcs}
    lang = "en" if lang == "en" else "de"
    t = L[lang]
    nf = _de if lang == "de" else (lambda v, d=2: f"{v:,.{d}f}")  # Zahlenformat je Sprache
    from .workflow import DEFAULT_APP  # noqa: PLC0415 (Standardtexte aus Firmeneinstellungen)
    from ..models import AppSettings
    app_st = {**DEFAULT_APP, **((db.get(AppSettings, 1).data or {}) if db.get(AppSettings, 1) else {})}
    title = first.article_name if single else \
        f"{t['bulk']} {len(calcs)} {t['articles']}" + (f" – {first.account.name}" if first.account else "")
    quote = Quote(number=next_quote_number(db), title=title, account_id=first.account_id,
                  contact_id=first.contact_id, opportunity_id=opp_ids.pop() if len(opp_ids) == 1 else None,
                  owner_id=user.id, status="entwurf", quote_date=date.today(),
                  valid_until=date.today() + timedelta(days=30), tax_rate=19,
                  intro_text=app_st[f"intro_{lang}"], terms=app_st[f"terms_{lang}"], language=lang,
                  calculation_ids=[c.id for c in calcs])
    items, one_time = [], []
    for calc, ver in pairs:
        r, inp = ver.results, ver.inputs
        art = calc.article_name + (f"\n{t['your_no']}: {calc.customer_article_no}" if calc.customer_article_no else "")
        mats = [inp.get('material_name') or '–'] + [c.get("material_name") or c.get("label") or "" for c in inp.get("components") or []]
        art += f"\n{t['material']}: {' + '.join(m for m in mats if m)}" + (f" ({len(mats)}K)" if len(mats) > 1 else "") + \
            f" · {t['calc']} {calc.number} V{ver.version_no}"
        p1000 = (r.get("price_year1") or r["unit_price"]) * 1000 if r.get("price_years") else r["price_per_1000"]
        art += f"\n{t['per1000']}: {nf(p1000)} € · {t['lot']} {nf(float(inp.get('lot_size') or 0), 0)} {t['pcs']}"
        if r.get("price_years"):
            art += f"\n{t['years']}: " + " · ".join(f"{t['year']} {y['year']}: {nf(y['price'] * 1000)} €" for y in r["price_years"])
        if float(inp.get("material_price_kg") or 0) > 0:
            st_ = get_settings(db)
            mat = db.get(Material, inp.get("material_id")) if inp.get("material_id") else None
            same = mat and mat.price_valid_from and abs(float(mat.price_per_kg) - float(inp["material_price_kg"])) < 1e-9
            stand = (mat.price_valid_from if same else ver.created_at.date()).strftime("%d.%m.%Y" if lang == "de" else "%d/%m/%Y")
            art += (f"\n{t['clause']} {nf(float(inp['material_price_kg']))} €/kg ({t['as_of']} {stand}"
                    + (f", {t['index']} {mat.price_index}" if mat and mat.price_index else "")
                    + f"); {t['adjust']} {nf(st_['escalation_threshold_pct'], 0)} %")
        if r.get("amortization_per_piece"):
            art += (f"\n{t['amort']} {nf(r['amortization_per_piece'] * 1000)} € {t['per1000s']} "
                    f"({t['over']} {nf(r['amortization_quantity'], 0)} {t['pcs']})")
        if r.get("volume_tiers"):
            art += f"\n{t['vol']}: " + " · ".join(
                f"{nf(v['annual_volume'], 0)} {t['peryear']}: {nf(v['price_per_1000'])} €" for v in r["volume_tiers"])
        if r.get("lot_tiers"):
            art += f"\n{t['tiers']}: " + " · ".join(
                f"{t['lotw']} {nf(v['lot_size'], 0)}: {nf(v['price_per_1000'])} €" for v in r["lot_tiers"])
        if inp.get("pack_type") or inp.get("pack_parts_per_unit"):
            art += f"\n{t['pack']}: {inp.get('pack_type') or '–'}" + \
                (f", {nf(float(inp['pack_parts_per_unit']), 0)} {t['perunit']}" if inp.get("pack_parts_per_unit") else "")
        if inp.get("incoterm") or (inp.get("transport_mode") or "keine") != "keine":
            art += f"\n{t['delivery']}: " + (inp.get("incoterm") or (t["dap"] if inp.get("transport_mode") != "keine" else t["exw"]))
        lc = calc.lifecycle or {}
        if lc.get("on_quote"):
            bits = []
            if lc.get("recycled_pct"):
                bits.append(f"{t['recycled']} {nf(float(lc['recycled_pct']), 0)} %")
            if lc.get("marking"):
                bits.append(f"{t['marking']} {lc['marking']}")
            if lc.get("eol_route"):
                bits.append({"stofflich": "stofflich verwertbar", "thermisch": "thermische Verwertung"}.get(lc["eol_route"], lc["eol_route"]))
            if not inp.get("components"):
                bits.append(t["mono"])
            if bits:
                art += f"\n{t['lifecycle']}: " + " · ".join(bits)
        co2 = r.get("co2") or {}
        if co2.get("active") and inp.get("co2_on_quote", True):
            art += (f"\n{t['co2']}: {nf(co2['cradle_to_gate'] * 1000, 1)} g CO₂e/{t['pcs']} · "
                    f"{nf(co2['cradle_to_gate'] * 1000, 2)} kg {t['per1000s']} · {t['of_which']} {nf(co2['scope12'] * 1000, 1)} g/{t['pcs']}")
        items.append(dict(description=art, quantity=r["annual_volume"], unit="Stk",
                          unit_price=r.get("price_year1") if r.get("price_years") else r["unit_price"]))
        pre = r.get("preseries")
        if pre:
            items.append(dict(description=f"{t['pre']} – {calc.article_name}\n{t['pre_note']} {nf(pre['qty'], 0)} {t['pcs']}"
                                          f" ({t['lot']} {nf(pre['lot_size'], 0)} {t['pcs']}) · {nf(pre['price_per_1000'])} € {t['per1000s']}",
                              quantity=pre["qty"], unit="Stk", unit_price=pre["unit_price"]))
        for o in [o for o in r["one_time"] if o["price"]]:
            label = o["label"] if single else f"{o['label']} – {calc.article_name}"
            one_time.append(dict(description=f"{label} ({t['once']})", quantity=1, unit="psch", unit_price=o["price"]))
    quote.items = [QuoteItem(position=n, **it) for n, it in enumerate(items + one_time, start=1)]
    db.add(quote)
    for calc in calcs:
        if calc.status in ("anfrage", "kalkulation"):
            calc.status = "angeboten"
            calc.probability = max(calc.probability, STATUS_PROBABILITY["angeboten"])
    db.flush()
    for calc in calcs:
        sync_opportunity(db, calc)
    return quote


@calcs.post("/{calc_id}/quote")
def create_quote(calc_id: int, version_no: int | None = None, lang: str = "de", db: Session = Depends(get_db),
                 user: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    ver = next((v for v in calc.versions if v.version_no == (version_no or calc.current_version)), None)
    if not ver:
        raise HTTPException(404, "Version nicht gefunden")
    quote = build_quote(db, [(calc, ver)], user, lang)
    db.commit()
    return {"quote_id": quote.id, "number": quote.number}


@quote_bulk.post("/quote")
def create_bulk_quote(data: dict, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Sammelangebot aus mehreren Kalkulationen (aktuelle Versionen) desselben Kunden."""
    ids = [int(i) for i in dict.fromkeys(data.get("ids") or [])]
    if not ids:
        raise HTTPException(400, "Bitte mindestens eine Kalkulation auswählen")
    calcs = [db.get(Calculation, i) for i in ids]
    if any(c is None for c in calcs):
        raise HTTPException(404, "Kalkulation nicht gefunden")
    accounts = {c.account_id for c in calcs}
    if None in accounts:
        raise HTTPException(400, "Alle Kalkulationen brauchen einen Kunden: " +
                            ", ".join(c.number for c in calcs if not c.account_id))
    if len(accounts) > 1:
        raise HTTPException(400, "Ein Sammelangebot geht nur an einen Kunden – ausgewählt sind " +
                            ", ".join(sorted({c.account.name for c in calcs})))
    closed = [c.number for c in calcs if c.status in ("verloren", "kein_angebot")]
    if closed:
        raise HTTPException(400, f"Verlorene bzw. nicht angebotene Kalkulationen ausnehmen: {', '.join(closed)}")
    calcs.sort(key=lambda c: c.number)
    pairs = [(c, next(v for v in c.versions if v.version_no == c.current_version)) for c in calcs]
    quote = build_quote(db, pairs, user, (data or {}).get("lang", "de"))
    db.commit()
    return {"quote_id": quote.id, "number": quote.number, "count": len(calcs)}


@calcs.get("/{calc_id}/quotes")
def calc_quotes(calc_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    rows = db.scalars(select(Quote).where(Quote.account_id == calc.account_id).order_by(Quote.number.desc())).unique().all()
    return [{"id": q.id, "number": q.number, "status": q.status, "title": q.title, "quote_date": q.quote_date.isoformat(),
             "net_total": q.net_total, "articles": len(q.calculation_ids or [])}
            for q in rows if calc_id in (q.calculation_ids or [])]


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
def delete_postcalc(calc_id: int, pc_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    pc = db.get(PostCalculation, pc_id)
    if not pc or pc.calculation_id != calc_id:
        raise HTTPException(404, "Nachkalkulation nicht gefunden")
    db.delete(pc)
    db.commit()



# ---------------- Artikelanalyse ----------------
def _machines(db: Session) -> list[dict]:
    return [{"id": m.id, "name": m.name, "number": m.number, "clamping_force_t": m.clamping_force_t,
             "hourly_rate": m.hourly_rate, "active": m.active}
            for m in db.scalars(select(Machine).order_by(Machine.clamping_force_t))]


@router.post("/analyze")
def analyze_preview(data: dict, db: Session = Depends(get_db), _: User = Depends(can_read)):
    return analyze(data.get("analysis") or {}, data.get("inputs") or {}, _machines(db))


@calcs.put("/{calc_id}/analysis", response_model=s.CalcDetail)
def save_analysis(calc_id: int, data: dict, db: Session = Depends(get_db), _: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    ver = next((v for v in calc.versions if v.version_no == calc.current_version), None)
    calc.analysis = data.get("analysis") or {}
    calc.analysis_results = analyze(calc.analysis, ver.inputs if ver else {}, _machines(db))
    if data.get("feasibility") in FEASIBILITY_LABELS:
        calc.feasibility = data["feasibility"]
    if "feasibility_note" in data:
        calc.feasibility_note = data["feasibility_note"]
    db.commit()
    db.refresh(calc)
    return calc


# ---------------- Auslastung ----------------
@router.get("/utilization")
def utilization(years: int = Query(5, ge=1, le=10), db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Maschinenstunden je Jahr: Bestand (Grundauslastung je Maschine mit Auslauf), fest (gewonnene Kalkulationen),
    gewichtet (offen × Wahrscheinlichkeit), potenziell (offen zu 100 %). Laufzeit ab SOP (sonst ab heute bzw. Folgejahr) über die Projektlaufzeit."""
    today = date.today()
    year_list = [today.year + n for n in range(years)]
    machines = {m.id: m for m in db.scalars(select(Machine))}
    rows = {mid: {"machine": {"id": m.id, "name": m.name, "number": m.number,
                              "clamping_force_t": m.clamping_force_t, "kind": m.kind},
                  "capacity_h": float(m.available_hours_year or 6000),
                  "years": {y: {"base": float(m.available_hours_year or 6000) * float(m.base_load_pct or 0) / 100
                                * (1 - float(m.base_load_decline_pct or 0) / 100) ** n,
                                "fixed": 0.0, "weighted": 0.0, "potential": 0.0} for n, y in enumerate(year_list)},
                  "items": []}
            for mid, m in machines.items() if m.active}
    none_row = {"machine": {"id": None, "name": "ohne Maschinenzuordnung", "number": None, "clamping_force_t": None},
                "capacity_h": 0, "years": {y: {"base": 0.0, "fixed": 0.0, "weighted": 0.0, "potential": 0.0} for y in year_list}, "items": []}
    for c in db.scalars(select(Calculation).where(Calculation.status.notin_(("verloren", "kein_angebot", "zurueckgestellt")))).unique():
        ver = next((v for v in c.versions if v.version_no == c.current_version), None)
        if not ver:
            continue
        loads = [(ver.inputs.get("machine_id"), float(ver.results.get("machine_hours_year") or 0), None)]
        loads += [(o.get("machine_id"), float(o.get("hours_year") or 0), o.get("name"))
                  for o in ver.results.get("operations") or [] if isinstance(o, dict)]
        loads = [x for x in loads if x[1] > 0]
        if not loads:
            continue
        start = c.sop_date or (today if c.status == "gewonnen" else date(today.year + 1, 1, 1))
        duration = max(float(ver.inputs.get("project_years") or 1), 0.25)
        end_year_frac = start.year + (start.month - 1) / 12 + duration
        won = c.status == "gewonnen"
        for mid, hours, op_name in loads:
            row = rows.get(mid) or none_row
            item = {"id": c.id, "number": c.number, "article_name": c.article_name, "status": c.status,
                    "operation": op_name, "probability": c.probability, "hours_year": round(hours, 1),
                    "start": start.isoformat(), "project_years": duration, "years": {}}
            for y in year_list:
                # Anteil des Jahres, in dem das Projekt läuft
                overlap = max(0.0, min(y + 1, end_year_frac) - max(y, start.year + (start.month - 1) / 12))
                h = hours * overlap
                if h <= 0:
                    continue
                item["years"][y] = round(h, 1)
                cell = row["years"][y]
                if won:
                    cell["fixed"] += h
                else:
                    cell["weighted"] += h * c.probability / 100
                    cell["potential"] += h
            if item["years"]:
                row["items"].append(item)
    out = []
    for row in list(rows.values()) + ([none_row] if none_row["items"] else []):
        cap = row["capacity_h"]
        for y, cell in row["years"].items():
            for k in ("base", "fixed", "weighted", "potential"):
                cell[k] = round(cell[k], 1)
            firm = cell["base"] + cell["fixed"]
            cell["pct_fixed"] = round(firm / cap * 100, 1) if cap else None
            cell["pct_expected"] = round((firm + cell["weighted"]) / cap * 100, 1) if cap else None
            cell["pct_max"] = round((firm + cell["potential"]) / cap * 100, 1) if cap else None
        row["years"] = [{"year": y, **v} for y, v in row["years"].items()]
        out.append(row)
    totals = []
    cap_total = sum(r["capacity_h"] for r in out)
    for idx, y in enumerate(year_list):
        b = sum(r["years"][idx]["base"] for r in out)
        f = sum(r["years"][idx]["fixed"] for r in out) + b
        w = sum(r["years"][idx]["weighted"] for r in out)
        p = sum(r["years"][idx]["potential"] for r in out)
        totals.append({"year": y, "base": round(b, 1), "fixed": round(f - b, 1), "weighted": round(w, 1), "potential": round(p, 1),
                       "capacity_h": cap_total, "pct_fixed": round(f / cap_total * 100, 1) if cap_total else None,
                       "pct_expected": round((f + w) / cap_total * 100, 1) if cap_total else None,
                       "pct_max": round((f + p) / cap_total * 100, 1) if cap_total else None})
    return {"years": year_list, "machines": out, "totals": totals}



# ---------------- Herleitung Maschinenstundensatz ----------------
def _machine_dict(m: Machine) -> dict:
    return {c.name: getattr(m, c.name) for c in Machine.__table__.columns}


@router.get("/machine-rates")
def machine_rates(db: Session = Depends(get_db), _: User = Depends(can_read)):
    st = get_settings(db)
    return [{"machine": {"id": m.id, "number": m.number, "name": m.name}, **machine_rate(_machine_dict(m), st)}
            for m in db.scalars(select(Machine).order_by(Machine.number, Machine.name))]


@router.post("/machine-rates/{machine_id}/apply")
def apply_machine_rate(machine_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    m = db.get(Machine, machine_id)
    if not m:
        raise HTTPException(404, "Maschine nicht gefunden")
    r = machine_rate(_machine_dict(m), get_settings(db))
    if not r["complete"]:
        raise HTTPException(400, "Wiederbeschaffungswert und Nutzungsdauer fehlen")
    m.hourly_rate, m.maintenance_rate = r["hourly_rate"], r["maintenance_rate"]
    db.commit()
    return machine_rate(_machine_dict(m), get_settings(db))


# ---------------- Rohstoffpreise / Preisgleitung ----------------
@router.get("/material-prices/{material_id}")
def material_price_history(material_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    rows = db.scalars(select(MaterialPrice).where(MaterialPrice.material_id == material_id)
                      .order_by(MaterialPrice.valid_from.desc(), MaterialPrice.id.desc())).unique().all()
    return [{"id": p.id, "price_per_kg": p.price_per_kg, "valid_from": p.valid_from.isoformat(), "note": p.note,
             "user": p.user.name if p.user else None} for p in rows]


def _uses_material(inp: dict, mid: int) -> str | None:
    if inp.get("material_id") == mid:
        return "main"
    for n, c in enumerate(inp.get("components") or []):
        if c.get("material_id") == mid:
            return f"comp{n}"
    return None


def _with_new_price(inp: dict, where: str, price: float) -> dict:
    new = normalize(dict(inp))
    if where == "main":
        new["material_price_kg"] = price
    else:
        n = int(where[4:])
        comps = [dict(c) for c in new["components"]]
        comps[n]["price_kg"] = price
        new["components"] = comps
    return new


@router.get("/escalation")
def escalation(material_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Betroffene Kalkulationen bei Materialpreisänderung: Preisbasis der Version vs. aktueller Materialpreis."""
    mat = db.get(Material, material_id)
    if not mat:
        raise HTTPException(404, "Material nicht gefunden")
    st = get_settings(db)
    out = []
    for c in db.scalars(select(Calculation).where(Calculation.status.notin_(("verloren", "kein_angebot")))).unique():
        ver = next((v for v in c.versions if v.version_no == c.current_version), None)
        where = ver and _uses_material(ver.inputs, mat.id)
        if not where:
            continue
        old_price = float(ver.inputs.get("material_price_kg") if where == "main"
                          else ver.inputs["components"][int(where[4:])].get("price_kg") or 0)
        new_res = compute(_with_new_price(ver.inputs, where, mat.price_per_kg))
        dmat = (mat.price_per_kg - old_price) / old_price * 100 if old_price else 0
        out.append({"id": c.id, "number": c.number, "article_name": c.article_name, "status": c.status,
                    "account": c.account.name if c.account else None, "version": ver.version_no,
                    "component": "Hauptmaterial" if where == "main" else "weitere Komponente",
                    "old_material_price": old_price, "new_material_price": mat.price_per_kg,
                    "material_delta_pct": round(dmat, 2),
                    "old_unit_price": ver.results["unit_price"], "new_unit_price": new_res["unit_price"],
                    "unit_price_delta_pct": round((new_res["unit_price"] - ver.results["unit_price"])
                                                  / ver.results["unit_price"] * 100, 2) if ver.results["unit_price"] else 0,
                    "annual_impact": round((new_res["unit_price"] - ver.results["unit_price"]) * ver.results["annual_volume"], 2),
                    "exceeds_threshold": abs(dmat) >= st["escalation_threshold_pct"]})
    out.sort(key=lambda x: -abs(x["annual_impact"]))
    return {"material": {"id": mat.id, "name": mat.name, "price_per_kg": mat.price_per_kg,
                         "price_valid_from": mat.price_valid_from.isoformat() if mat.price_valid_from else None,
                         "price_index": mat.price_index},
            "threshold_pct": st["escalation_threshold_pct"], "items": out}


@router.post("/escalation/apply")
def escalation_apply(data: dict, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Neue Kalkulationsversion mit aktuellem Materialpreis für ausgewählte Kalkulationen."""
    mat = db.get(Material, int(data.get("material_id") or 0))
    if not mat:
        raise HTTPException(404, "Material nicht gefunden")
    done = []
    for cid in data.get("calc_ids") or []:
        c = db.get(Calculation, int(cid))
        ver = c and next((v for v in c.versions if v.version_no == c.current_version), None)
        where = ver and _uses_material(ver.inputs, mat.id)
        if not where:
            continue
        old = ver.inputs.get("material_price_kg") if where == "main" else ver.inputs["components"][int(where[4:])].get("price_kg")
        inputs = _with_new_price(ver.inputs, where, mat.price_per_kg)
        res = compute(inputs)
        no = ver.version_no + 1
        c.versions.append(CalculationVersion(
            version_no=no, inputs=inputs, results=res, created_by_id=user.id,
            change_note=f"Preisgleitung {mat.name}: {float(old or 0):.2f} → {mat.price_per_kg:.2f} €/kg".replace(".", ",")))
        c.current_version = no
        apply_results(c, res)
        db.flush()
        sync_opportunity(db, c)
        done.append(c.number)
    db.commit()
    return {"updated": done}


# ---------------- Kopieren / Vorlagen ----------------
@calcs.post("/{calc_id}/copy", response_model=s.CalcDetail, status_code=201)
def copy_calc(calc_id: int, data: dict, db: Session = Depends(get_db), user: User = Depends(can_write)):
    src = db.get(Calculation, calc_id)
    if not src:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    ver = next(v for v in src.versions if v.version_no == src.current_version)
    calc = Calculation(number=next_calc_number(db), article_name=data.get("article_name") or f"{src.article_name} (Kopie)",
                       account_id=data.get("account_id", src.account_id), contact_id=src.contact_id if data.get("account_id") in (None, src.account_id) else None,
                       status="anfrage", probability=STATUS_PROBABILITY["anfrage"], owner_id=user.id,
                       inquiry_date=date.today(), remark=f"Kopie von {src.number} V{ver.version_no}")
    inputs = normalize(dict(ver.inputs))
    res = compute(inputs)
    calc.versions.append(CalculationVersion(version_no=1, inputs=inputs, results=res, created_by_id=user.id,
                                            change_note=f"Kopie von {src.number} V{ver.version_no}"))
    calc.current_version = 1
    apply_results(calc, res)
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


@router.get("/templates")
def list_templates(db: Session = Depends(get_db), _: User = Depends(can_read)):
    return [{"id": t.id, "name": t.name, "description": t.description, "source_calc": t.source_calc,
             "created_by": t.created_by.name if t.created_by else None, "created_at": t.created_at.isoformat(),
             "inputs": t.inputs}
            for t in db.scalars(select(CalcTemplate).order_by(CalcTemplate.name)).unique()]


@router.post("/templates", status_code=201)
def create_template(data: dict, db: Session = Depends(get_db), user: User = Depends(can_write)):
    c = db.get(Calculation, int(data.get("calc_id") or 0))
    if not c or not (data.get("name") or "").strip():
        raise HTTPException(400, "Name und Kalkulation angeben")
    ver = next(v for v in c.versions if v.version_no == c.current_version)
    t = CalcTemplate(name=data["name"].strip(), description=data.get("description"), inputs=ver.inputs,
                     source_calc=f"{c.number} V{ver.version_no}", created_by_id=user.id)
    db.add(t)
    db.commit()
    return {"id": t.id, "name": t.name}


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db), _: User = Depends(can_write)):
    t = db.get(CalcTemplate, template_id)
    if not t:
        raise HTTPException(404, "Vorlage nicht gefunden")
    db.delete(t)
    db.commit()



# ---------------- Freigabe (Vier-Augen-Prinzip) ----------------
def _approvers(db: Session) -> list[User]:
    return [u for u in db.scalars(select(User).where(User.active.is_(True))) if u.role == "admin" or u.can_approve]


@calcs.post("/{calc_id}/approval/request", response_model=s.CalcDetail)
def approval_request(calc_id: int, data: dict, db: Session = Depends(get_db), user: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    calc.approval_status, calc.approval_version = "angefragt", calc.current_version
    calc.approval_requested_by_id, calc.approval_requested_at = user.id, datetime.now(timezone.utc)
    calc.approval_comment, calc.approval_by_id, calc.approval_at = (data or {}).get("comment"), None, None
    calc.approval_decision_comment = None
    db.flush()
    try:
        from ..notify import notify
        for u in _approvers(db):
            if u.id != user.id:
                notify(db, u.id, f"Freigabe angefragt: {calc.number} {calc.article_name}",
                       f"V{calc.current_version} · {', '.join(calc.approval_reasons) or 'ohne Pflichtgrund'} · von {user.name}",
                       f"/kalkulationen/{calc.id}")
    except ImportError:
        pass
    db.commit()
    db.refresh(calc)
    return calc


@calcs.post("/{calc_id}/approval/decide", response_model=s.CalcDetail)
def approval_decide(calc_id: int, data: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    if not (user.role == "admin" or user.can_approve):
        raise HTTPException(403, "Keine Freigabeberechtigung")
    if calc.approval_requested_by_id == user.id:
        raise HTTPException(403, "Vier-Augen-Prinzip: Die Freigabe muss eine andere Person erteilen")
    decision = (data or {}).get("decision")
    if decision not in ("freigegeben", "abgelehnt"):
        raise HTTPException(400, "Entscheidung: freigegeben oder abgelehnt")
    if decision == "abgelehnt" and not (data.get("comment") or "").strip():
        raise HTTPException(400, "Bei Ablehnung bitte Begründung angeben")
    calc.approval_status, calc.approval_version = decision, calc.current_version
    calc.approval_by_id, calc.approval_at = user.id, datetime.now(timezone.utc)
    calc.approval_decision_comment = data.get("comment")
    try:
        from ..notify import notify
        if calc.approval_requested_by_id:
            notify(db, calc.approval_requested_by_id, f"{calc.number} {decision}: {calc.article_name}",
                   f"V{calc.current_version} von {user.name}" + (f" · {data.get('comment')}" if data.get("comment") else ""),
                   f"/kalkulationen/{calc.id}")
    except ImportError:
        pass
    db.commit()
    db.refresh(calc)
    return calc


# ---------------- Lebenswegbetrachtung ----------------
@calcs.put("/{calc_id}/lifecycle", response_model=s.CalcDetail)
def save_lifecycle(calc_id: int, data: dict, db: Session = Depends(get_db), _: User = Depends(can_write)):
    calc = db.get(Calculation, calc_id)
    if not calc:
        raise HTTPException(404, "Kalkulation nicht gefunden")
    calc.lifecycle = data.get("lifecycle") or {}
    db.commit()
    db.refresh(calc)
    return calc
