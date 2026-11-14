"""
Rechenkern Spritzguss-Kalkulation (Zuschlagskalkulation).

Alle Eingaben kommen als flaches dict (siehe DEFAULT_INPUTS). Jeder Wert ist überschreibbar;
Maschinen-/Material-/Parameter-Stammdaten liefern nur die Vorbelegung.

Schema je Stück:
  Materialeinzelkosten (MEK)  = Gewicht je Stück inkl. Angussanteil × Materialpreis (+ Masterbatch) + Zukaufteile
  Materialgemeinkosten (MGK)  = MEK × MGK-%
  Fertigungseinzelkosten (FEK) = Maschine + Instandhaltung + Personal (je Stück über Stück/h)
                                 + Rüsten (je Los / Losgröße) + Montage
  Fertigungsgemeinkosten (FGK) = FEK × FGK-%
  Qualität / Werkzeugbau       = je % auf FEK (dann Teil der Herstellkosten) oder auf HK (dann nach den HK)
  Sondereinzelkosten Fertigung = Zusatzpositionen „Fertigung“ (Peripherie, Nacharbeit, Bedrucken …)
  Herstellkosten vor Ausschuss = Summe
  Ausschuss                    = HK vor Ausschuss / (1 − Ausschuss-%) − HK vor Ausschuss
  Herstellkosten (HK)
  + Verwaltungsgemeinkosten, Vertriebsgemeinkosten, Projektmanagement (je % auf HK)
  + Verpackung (Kosten je Verpackungseinheit / Teile je VE + Packzeit) und Transport (je Palette, je Lieferung
    oder % auf HK; „ab Werk“ = 0) als Sondereinzelkosten des Vertriebs
  + weitere Sondereinzelkosten Vertrieb (Zusatzpositionen)
  = Selbstkosten (SK)
  + Gewinn (% auf SK)          = Barverkaufspreis
  ÷ (1 − Skonto) ÷ (1 − Rabatt) = Angebotspreis je Stück
Ein manuell gesetzter Verkaufspreis (price_override) ersetzt den errechneten Preis; der Gewinn
ergibt sich dann als Rest.
Einmalkosten (Werkzeug, Bemusterung, Prüfmittel …) werden separat mit Kosten und Preis ausgewiesen.
"""
from __future__ import annotations

DEFAULT_SETTINGS = {
    "labor_rate_h": 38.0,          # Lohnsatz Maschinenbediener €/h (Vollkosten)
    "setup_rate_h": 48.0,          # Lohnsatz Einrichter €/h
    "assembly_rate_h": 34.0,       # Lohnsatz Montage €/h
    "mgk_pct": 6.0,
    "fgk_pct": 12.0,
    "scrap_pct": 3.0,
    "vwgk_pct": 6.0,
    "vtgk_pct": 3.0,
    "pm_pct": 2.0,
    "quality_pct": 1.5,            # Qualität (Prüfung, Messtechnik, QS)
    "toolshop_pct": 2.0,           # Werkzeugbau (Wartung, Instandhaltung Werkzeuge)
    "profit_pct": 7.0,
    "cash_discount_pct": 0.0,
    "rebate_pct": 0.0,
    "productivity_pct": 85.0,
    "assembly_productivity_pct": 85.0,
    "setup_time_h": 2.0,
    "setup_persons": 1.0,
    "startup_scrap_pcs": 50.0,
    "tool_markup_pct": 0.0,        # Aufschlag auf Werkzeugkosten für den Kundenpreis
    "nk_green_pct": 3.0,           # Nachkalkulation: Abweichung SK bis +3 % = grün
    "nk_red_pct": 10.0,            # ab +10 % = rot (dazwischen gelb); Verlust = immer rot
    "big_revenue_threshold": 500000.0,  # Großprojekt: Jahresumsatz ab … €
    "big_invest_threshold": 500000.0,   # Großprojekt: Invest (Einmalkosten Werkzeug etc.) ab … €
}

DEFAULT_INPUTS = {
    # Mengen
    "annual_volume": 100000, "lot_size": 10000, "project_years": 5,
    # Material
    "material_id": None, "material_name": "", "material_price_kg": 0.0,
    "part_weight_g": 0.0, "sprue_weight_g": 0.0, "regrind_pct": 0.0,
    "masterbatch_pct": 0.0, "masterbatch_price_kg": 0.0, "purchased_parts": 0.0,
    # Maschine & Fertigung
    "machine_id": None, "machine_name": "", "machine_rate_h": 0.0, "maintenance_rate_h": 0.0,
    "cycle_time_s": 30.0, "cavities": 1, "productivity_pct": 85.0,
    "operator_factor": 0.3, "labor_rate_h": 38.0,
    # Rüsten
    "setup_time_h": 2.0, "setup_persons": 1.0, "setup_rate_h": 48.0, "startup_scrap_pcs": 50.0,
    # Montage
    "assembly_time_s": 0.0, "assembly_persons": 1.0, "assembly_rate_h": 34.0, "assembly_productivity_pct": 85.0,
    # Zuschläge
    "mgk_pct": 6.0, "fgk_pct": 12.0, "scrap_pct": 3.0, "vwgk_pct": 6.0, "vtgk_pct": 3.0,
    "pm_pct": 2.0, "profit_pct": 7.0, "cash_discount_pct": 0.0, "rebate_pct": 0.0,
    # Qualität / Werkzeugbau: 0 als Vorgabe, damit ältere Versionen unverändert rechnen;
    # neue Kalkulationen erhalten die Werte aus den Parametern. Basis: "fek" oder "hk".
    "quality_pct": 0.0, "quality_base": "hk", "toolshop_pct": 0.0, "toolshop_base": "fek",
    "price_override": None,
    # Listen
    "extras": [],     # [{label, amount, basis: stueck|tausend|los|jahr, category: fertigung|vertrieb}]
    "one_time": [],   # [{label, cost, price}]
    "lot_tiers": [],  # Staffelpreise: weitere Losgrößen, z. B. [2000, 5000, 20000]
    # Verpackung (Vorgabe leer = 0, damit ältere Versionen unverändert rechnen)
    "pack_type": "", "pack_parts_per_unit": 0, "pack_cost_per_unit": 0.0, "pack_reusable": False,
    "pack_time_s": 0.0, "pack_units_per_pallet": 0,
    # Transport: keine (ab Werk) | palette | lieferung | prozent
    "incoterm": "", "transport_mode": "keine", "transport_cost_per_pallet": 0.0,
    "transport_cost_per_delivery": 0.0, "transport_deliveries_per_year": 0, "transport_pct": 0.0,
}


def _f(v, default=0.0) -> float:
    try:
        if v is None or v == "":
            return float(default)
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _p(v) -> str:
    """Prozentwert für Beschriftungen im deutschen Format (1,5)."""
    return f"{_f(v):g}".replace(".", ",")


def normalize(inputs: dict) -> dict:
    out = {**DEFAULT_INPUTS, **(inputs or {})}
    out["extras"] = [e for e in (out.get("extras") or []) if isinstance(e, dict)]
    out["one_time"] = [e for e in (out.get("one_time") or []) if isinstance(e, dict)]
    return out


def compute(raw: dict) -> dict:
    res = _compute(raw)
    i = normalize(raw)
    tiers = []
    for lot in [t for t in (i.get("lot_tiers") or []) if _f(t) > 0][:5]:
        # Staffeln immer kalkuliert (ohne manuellen Preis), damit die Wirkung der Losgröße sichtbar ist
        sub = _compute({**i, "lot_size": _f(lot), "price_override": None, "lot_tiers": []})
        tiers.append({
            "lot_size": _f(lot),
            "setup_per_piece": sub["values"]["setup"],
            "self_cost": sub["self_cost"],
            "unit_price": sub["unit_price"],
            "price_per_1000": sub["price_per_1000"],
            "margin_pct": sub["margin_pct"],
            "lots_per_year": sub["lots_per_year"],
        })
    base = _compute({**i, "price_override": None, "lot_tiers": []})["unit_price"] if tiers else 0
    for t in tiers:
        t["delta_pct"] = round((t["unit_price"] - base) / base * 100, 2) if base else 0
    res["lot_tiers"] = sorted(tiers, key=lambda t: t["lot_size"])
    res["base_calculated_price"] = base
    return res


def _compute(raw: dict) -> dict:
    i = normalize(raw)
    warnings: list[str] = []
    annual = max(_f(i["annual_volume"]), 0)
    lot = max(_f(i["lot_size"]), 0)
    cavities = max(_f(i["cavities"], 1), 0)
    cycle = _f(i["cycle_time_s"])
    prod = _f(i["productivity_pct"]) / 100

    # --- Ausbringung
    pph_theo = 3600 / cycle * cavities if cycle > 0 else 0
    pph = pph_theo * prod
    if pph <= 0:
        warnings.append("Zykluszeit, Fachzahl oder Produktivität fehlen – keine Ausbringung berechenbar.")
    per = (lambda cost_h: cost_h / pph) if pph > 0 else (lambda cost_h: 0.0)

    # --- Material
    sprue_share_g = (_f(i["sprue_weight_g"]) / cavities if cavities else 0) * (1 - _f(i["regrind_pct"]) / 100)
    kg_piece = (_f(i["part_weight_g"]) + sprue_share_g) / 1000
    mb = _f(i["masterbatch_pct"]) / 100
    price_kg = _f(i["material_price_kg"]) * (1 - mb) + _f(i["masterbatch_price_kg"]) * mb
    mek_material = kg_piece * price_kg
    purchased = _f(i["purchased_parts"])
    mek = mek_material + purchased
    mgk = mek * _f(i["mgk_pct"]) / 100

    # --- Fertigung
    machine = per(_f(i["machine_rate_h"]))
    maintenance = per(_f(i["maintenance_rate_h"]))
    labor = per(_f(i["labor_rate_h"]) * _f(i["operator_factor"]))
    run_cost_piece = machine + maintenance + labor
    setup_lot = _f(i["setup_time_h"]) * (
        _f(i["machine_rate_h"]) + _f(i["maintenance_rate_h"]) + _f(i["setup_rate_h"]) * _f(i["setup_persons"])
    ) + _f(i["startup_scrap_pcs"]) * (mek_material + run_cost_piece)
    if lot <= 0:
        warnings.append("Losgröße fehlt – Rüstkosten werden nicht umgelegt.")
    setup = setup_lot / lot if lot > 0 else 0.0
    ap = _f(i["assembly_productivity_pct"], 100) / 100
    assembly = (_f(i["assembly_time_s"]) / 3600 * _f(i["assembly_rate_h"]) * _f(i["assembly_persons"]) / ap) if ap > 0 else 0.0
    fek = run_cost_piece + setup + assembly
    fgk = fek * _f(i["fgk_pct"]) / 100
    q_base = "fek" if i.get("quality_base") == "fek" else "hk"
    t_base = "hk" if i.get("toolshop_base") == "hk" else "fek"
    quality_f = fek * _f(i["quality_pct"]) / 100 if q_base == "fek" else 0.0
    toolshop_f = fek * _f(i["toolshop_pct"]) / 100 if t_base == "fek" else 0.0

    # --- Zusatzpositionen
    def extra_piece(e):
        amt, basis = _f(e.get("amount")), e.get("basis") or "stueck"
        if basis == "tausend":
            return amt / 1000
        if basis == "los":
            return amt / lot if lot > 0 else 0.0
        if basis == "jahr":
            return amt / annual if annual > 0 else 0.0
        return amt
    extras_detail = [{"label": e.get("label") or "Zusatzposition", "category": e.get("category") or "fertigung",
                      "basis": e.get("basis") or "stueck", "amount": _f(e.get("amount")),
                      "per_piece": extra_piece(e)} for e in i["extras"]]
    sek_f = sum(e["per_piece"] for e in extras_detail if e["category"] != "vertrieb")
    sek_v = sum(e["per_piece"] for e in extras_detail if e["category"] == "vertrieb")

    # --- Herstellkosten & Ausschuss
    hk_pre = mek + mgk + fek + fgk + quality_f + toolshop_f + sek_f
    scrap_rate = min(_f(i["scrap_pct"]) / 100, 0.95)
    hk = hk_pre / (1 - scrap_rate)
    scrap = hk - hk_pre

    vwgk = hk * _f(i["vwgk_pct"]) / 100
    vtgk = hk * _f(i["vtgk_pct"]) / 100
    pm = hk * _f(i["pm_pct"]) / 100
    quality_h = hk * _f(i["quality_pct"]) / 100 if q_base == "hk" else 0.0
    toolshop_h = hk * _f(i["toolshop_pct"]) / 100 if t_base == "hk" else 0.0
    # --- Verpackung & Transport (Sondereinzelkosten Vertrieb)
    ppu = _f(i["pack_parts_per_unit"])
    pack_material = _f(i["pack_cost_per_unit"]) / ppu if ppu > 0 else 0.0
    pack_labor = _f(i["pack_time_s"]) / 3600 * _f(i["labor_rate_h"]) / ppu if ppu > 0 else 0.0
    packaging = pack_material + pack_labor
    if (_f(i["pack_cost_per_unit"]) or _f(i["pack_time_s"])) and ppu <= 0:
        warnings.append("Verpackung: Teile je Verpackungseinheit fehlen – Verpackungskosten nicht umgelegt.")
    units_year = annual / ppu if ppu > 0 else 0
    upp = _f(i["pack_units_per_pallet"])
    pcs_pallet = ppu * upp
    pallets_year = annual / pcs_pallet if pcs_pallet > 0 else 0
    mode = i.get("transport_mode") or "keine"
    transport = 0.0
    if mode == "palette":
        if pcs_pallet > 0:
            transport = _f(i["transport_cost_per_pallet"]) / pcs_pallet
        else:
            warnings.append("Transport je Palette: Teile je VE und VE je Palette angeben.")
    elif mode == "lieferung":
        if annual > 0:
            transport = _f(i["transport_cost_per_delivery"]) * _f(i["transport_deliveries_per_year"]) / annual
    elif mode == "prozent":
        transport = hk * _f(i["transport_pct"]) / 100
    sk = hk + vwgk + vtgk + pm + quality_h + toolshop_h + packaging + transport + sek_v

    sd = _f(i["cash_discount_pct"]) / 100
    rb = _f(i["rebate_pct"]) / 100
    if i.get("price_override") not in (None, ""):
        price = _f(i["price_override"])
        net = price * (1 - sd) * (1 - rb)
        profit = net - sk
        price_source = "manuell"
    else:
        profit = sk * _f(i["profit_pct"]) / 100
        net = sk + profit
        price = net / (1 - sd) / (1 - rb) if sd < 1 and rb < 1 else net
        price_source = "kalkuliert"
    discounts = price - net
    if profit < 0:
        warnings.append("Verkaufspreis liegt unter den Selbstkosten.")

    # --- Einmalkosten
    one_time = [{"label": o.get("label") or "Einmalkosten", "cost": _f(o.get("cost")),
                 "price": _f(o.get("price"), o.get("cost"))} for o in i["one_time"]]
    ot_cost = sum(o["cost"] for o in one_time)
    ot_price = sum(o["price"] for o in one_time)

    lines = [
        ("mek_material", "Material (inkl. Angussanteil)", "material", mek_material),
        ("purchased", "Zukaufteile", "material", purchased),
        ("mgk", f"Materialgemeinkosten {_p(i['mgk_pct'])} %", "material", mgk),
        ("machine", "Maschine", "fertigung", machine),
        ("maintenance", "Instandhaltung", "fertigung", maintenance),
        ("labor", "Personal Maschine", "fertigung", labor),
        ("setup", "Rüsten (je Los umgelegt)", "fertigung", setup),
        ("assembly", "Montage", "fertigung", assembly),
        ("fgk", f"Fertigungsgemeinkosten {_p(i['fgk_pct'])} %", "fertigung", fgk),
        ("quality_f", f"Qualität {_p(i['quality_pct'])} % auf FEK", "fertigung", quality_f),
        ("toolshop_f", f"Werkzeugbau {_p(i['toolshop_pct'])} % auf FEK", "fertigung", toolshop_f),
        ("sek_f", "Sondereinzelkosten Fertigung", "fertigung", sek_f),
        ("hk_pre", "Herstellkosten vor Ausschuss", "summe", hk_pre),
        ("scrap", f"Ausschuss {_p(i['scrap_pct'])} %", "fertigung", scrap),
        ("hk", "Herstellkosten", "summe", hk),
        ("vwgk", f"Verwaltungsgemeinkosten {_p(i['vwgk_pct'])} %", "gemeinkosten", vwgk),
        ("vtgk", f"Vertriebsgemeinkosten {_p(i['vtgk_pct'])} %", "gemeinkosten", vtgk),
        ("pm", f"Projektmanagement {_p(i['pm_pct'])} %", "gemeinkosten", pm),
        ("quality_h", f"Qualität {_p(i['quality_pct'])} % auf HK", "gemeinkosten", quality_h),
        ("toolshop_h", f"Werkzeugbau {_p(i['toolshop_pct'])} % auf HK", "gemeinkosten", toolshop_h),
        ("packaging", "Verpackung" + (f" ({i.get('pack_type')})" if i.get("pack_type") else ""), "gemeinkosten", packaging),
        ("transport", {"palette": "Transport je Palette", "lieferung": "Transport je Lieferung",
                       "prozent": f"Transport {_p(i['transport_pct'])} % auf HK"}.get(mode, "Transport"), "gemeinkosten", transport),
        ("sek_v", "Sondereinzelkosten Vertrieb", "gemeinkosten", sek_v),
        ("sk", "Selbstkosten", "summe", sk),
        ("profit", "Gewinn" + (f" {_p(i['profit_pct'])} %" if price_source == "kalkuliert" else " (Rest)"), "ergebnis", profit),
        ("discounts", "Skonto / Rabatt", "ergebnis", discounts),
        ("price", "Verkaufspreis", "summe", price),
    ]
    rnd = lambda v: round(v, 6)  # noqa: E731
    lots_year = annual / lot if lot > 0 else 0
    machine_hours = (annual / pph if pph > 0 else 0) + lots_year * _f(i["setup_time_h"])
    return {
        "lines": [{"key": k, "label": lbl, "group": g, "per_piece": rnd(v), "per_100": rnd(v * 100),
                   "per_1000": rnd(v * 1000), "share_pct": round(v / price * 100, 2) if price else 0}
                  for k, lbl, g, v in lines],
        "values": {k: rnd(v) for k, _, _, v in lines},
        "unit_price": round(price, 4),
        "price_per_100": round(price * 100, 2),
        "price_per_1000": round(price * 1000, 2),
        "price_source": price_source,
        "self_cost": round(sk, 4),
        "profit_per_piece": round(profit, 4),
        "margin_pct": round(profit / price * 100, 2) if price else 0,
        "kg_per_piece": round(kg_piece, 6),
        "shot_weight_g": round(_f(i["part_weight_g"]) * cavities + _f(i["sprue_weight_g"]), 2),
        "pieces_per_hour_theoretical": round(pph_theo, 1),
        "pieces_per_hour": round(pph, 1),
        "setup_cost_per_lot": round(setup_lot, 2),
        "lots_per_year": round(lots_year, 2),
        "machine_hours_year": round(machine_hours, 1),
        "material_kg_year": round(kg_piece * annual / (1 - scrap_rate), 1),
        "packaging_units_year": round(units_year, 1),
        "pieces_per_pallet": round(pcs_pallet, 1),
        "pallets_year": round(pallets_year, 1),
        "packaging_cost_year": round(packaging * annual, 2),
        "transport_cost_year": round(transport * annual, 2),
        "annual_volume": annual,
        "annual_revenue": round(price * annual, 2),
        "annual_profit": round(profit * annual, 2),
        "annual_self_cost": round(sk * annual, 2),
        "project_revenue": round(price * annual * _f(i["project_years"], 1), 2),
        "one_time": one_time,
        "one_time_cost": round(ot_cost, 2),
        "one_time_price": round(ot_price, 2),
        "one_time_margin": round(ot_price - ot_cost, 2),
        "extras": extras_detail,
        "first_year_revenue": round(price * annual + ot_price, 2),
        "warnings": warnings,
    }


# Felder, die in der Nachkalkulation durch Ist-Werte ersetzt werden können
ACTUAL_FIELDS = (
    "cycle_time_s", "cavities", "productivity_pct", "scrap_pct", "material_price_kg", "part_weight_g",
    "sprue_weight_g", "setup_time_h", "lot_size", "assembly_time_s", "labor_rate_h", "operator_factor",
    "machine_rate_h", "maintenance_rate_h", "purchased_parts",
    "pack_cost_per_unit", "pack_parts_per_unit", "transport_cost_per_pallet", "transport_cost_per_delivery",
    "transport_deliveries_per_year",
)


def post_calculate(plan_inputs: dict, plan_results: dict, actuals: dict, settings: dict) -> tuple[dict, str]:
    """Ist-Rechnung mit gleichem Schema. Preis = Plan-Preis (oder tatsächlich erzielter Preis)."""
    merged = normalize(plan_inputs)
    for k in ACTUAL_FIELDS:
        if actuals.get(k) not in (None, ""):
            merged[k] = actuals[k]
    merged["price_override"] = actuals.get("actual_price") if actuals.get("actual_price") not in (None, "") else plan_results["unit_price"]
    qty = _f(actuals.get("quantity"))
    extra_total = _f(actuals.get("extra_costs"))
    if qty > 0 and extra_total:
        merged["extras"] = list(merged["extras"]) + [{"label": "Ist-Zusatzkosten", "amount": extra_total / qty,
                                                      "basis": "stueck", "category": "fertigung"}]
    res = compute(merged)
    plan_sk = plan_results.get("self_cost") or 0
    dev = (res["self_cost"] - plan_sk) / plan_sk * 100 if plan_sk else 0
    res["deviation_sk_pct"] = round(dev, 2)
    res["plan_self_cost"] = plan_sk
    res["plan_margin_pct"] = plan_results.get("margin_pct")
    res["quantity"] = qty
    res["result_total"] = round(res["profit_per_piece"] * qty, 2) if qty else None
    green, red = _f(settings.get("nk_green_pct"), 3), _f(settings.get("nk_red_pct"), 10)
    if res["profit_per_piece"] < 0 or dev > red:
        light = "rot"
    elif dev > green:
        light = "gelb"
    else:
        light = "gruen"
    return res, light
