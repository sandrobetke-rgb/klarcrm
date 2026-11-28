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
  + Verpackung (detailliert: Kosten je Verpackungseinheit / Teile je VE + Packzeit; oder pauschal % auf HK) und
    Transport (je Palette, je Lieferung oder % auf HK; „ab Werk“ = 0) als Sondereinzelkosten des Vertriebs
  + weitere Sondereinzelkosten Vertrieb (Zusatzpositionen)
  = Selbstkosten (SK)
  + Gewinn (% auf SK)          = Barverkaufspreis
  ÷ (1 − Skonto) ÷ (1 − Rabatt) = Angebotspreis je Stück
Ein manuell gesetzter Verkaufspreis (price_override) ersetzt den errechneten Preis; der Gewinn
ergibt sich dann als Rest.
Einmalkosten (Werkzeug, Bemusterung, Prüfmittel …) werden separat mit Kosten und Preis ausgewiesen.
"""
from __future__ import annotations

import math

DEFAULT_SETTINGS = {
    "labor_rate_h": 38.0,          # Lohnsatz Maschinenbediener €/h (Vollkosten)
    "setup_rate_h": 48.0,          # Lohnsatz Einrichter €/h
    "assembly_rate_h": 34.0,       # Lohnsatz Montage €/h
    "handling_rate_h": 34.0,       # Lohnsatz Mitarbeiter Handling €/h
    "automation_rate_h": 55.0,     # Lohnsatz Mitarbeiter Automatisierung €/h
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
    # CO₂ (Richtwerte – durch eigene Werte ersetzen)
    "co2_grid_kg_kwh": 0.30,        # Strom kg CO₂e/kWh (Stromkennzeichnung des Versorgers; Ökostrom marktbasiert 0)
    "co2_scope1_kg_h": 0.0,         # sonstige Werksemissionen (Heizung/Gas) kg CO₂e je Maschinenstunde
    "co2_masterbatch_kg_kg": 3.0,   # Masterbatch kg CO₂e/kg
    "co2_transport_kg_tkm": 0.10,   # Lkw kg CO₂e je Tonnenkilometer
    "pack_pct": 1.5,                # Verpackung pauschal % auf HK (wenn Details unbekannt)
    # Zukaufteile: eigener MGK-Satz (leer = wie MGK) und Nebenkalkulation für teure Zukaufteile
    "purchased_mgk_pct": None,
    "side_mgk_pct": 3.0, "side_quality_pct": 1.0, "side_scrap_pct": 1.0, "side_markup_pct": 0.0,
    "space_cost_m2_year": 90.0,     # Raumkosten €/m² und Jahr (Herleitung Maschinenstundensatz)
    "energy_price_kwh": 0.20,       # Strompreis €/kWh (Herleitung Maschinenstundensatz)
    "escalation_threshold_pct": 5.0,  # Preisgleitung: Anpassung ab Materialpreisänderung ± %
    "approval_enabled": 0,          # REV03-03: Freigabe-Workflow (Vier-Augen) 0 = aus, 1 = an – vorerst aus
    "clamp_t_per_cm2": 0.55,         # REV03-08: F&R-Standard Schließkraft je cm² projizierter Fläche (≙ 550 bar)
    "approval_min_margin_pct": 3.0,  # Marge darunter → rote Markierung (seit REV02 kein Freigabegrund mehr)
    "transport_pct": 2.0,           # Transport pauschal % auf HK (wenn Details unbekannt)
    "big_revenue_threshold": 500000.0,  # Großprojekt + Freigabe: Jahresumsatz ab … € (REV02-01)
    "big_invest_threshold": 350000.0,   # Großprojekt + Freigabe: Invest (Einmalkosten Werkzeug etc.) ab … €
    "machine_rate_pct": 100.0,
    "followup_workdays": 5.0,         # Angebotsverfolgung: Rücksprache Kunde n Arbeitstage nach Versand (REV01-P06)
    "lead_time_target_workdays": 10.0,  # Ziel-Durchlaufzeit Anfrage → Angebot (REV01-R01)  # Standortfaktor Maschinenstundensatz, wenn am Standort keine eigene Maschine hinterlegt ist
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
    # Weitere Personalanteile an der Maschine (0 … 100 % je Maschine), je mit eigenem Stundensatz.
    # Vorgabe 0, damit ältere Versionen unverändert rechnen; neue Kalkulationen erhalten die Sätze aus den Parametern.
    "handling_pct": 0.0, "handling_rate_h": 0.0, "automation_pct": 0.0, "automation_rate_h": 0.0,
    # Rüsten
    "setup_time_h": 2.0, "setup_persons": 1.0, "setup_rate_h": 48.0, "startup_scrap_pcs": 50.0,
    # Personalzeit beim Rüsten: Einrichter-Minuten je Rüstvorgang (None = gesamte Rüstzeit), Automatisierer-Minuten
    "setup_staff_min": None, "automation_setup_min": 0.0,
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
    "volume_tiers": [],  # Staffelpreise nach Jahresmenge, z. B. [50000, 100000, 250000]
    # Mehrkomponenten (2K/3K …): weitere Komponenten zusätzlich zu Komponente A (Hauptmaterial)
    "components": [],  # [{label, material_id, material_name, price_kg, part_weight_g, sprue_weight_g, regrind_pct, co2_kg_kg}]
    # Familienwerkzeug: Anteil dieses Artikels an Maschinenzeit/Rüsten (100 % = eigenes Werkzeug)
    "family_share_pct": 100.0, "family_group": "",
    # Weitere Arbeitsgänge (Montagelinie, Nachbearbeitung, Prüfung …), je mit eigener Maschine/Anlage
    "operations": [],  # [{machine_id, name, kind, rate_h, maintenance_h, cycle_s, parts_per_cycle, productivity_pct,
                       #   operator_factor, labor_rate_h, setup_h, setup_persons, power_kw}]
    # Zukaufteile aus Stammdaten: [{part_id, part_no, name, qty, price_per_piece, co2_kg_per_piece}]
    # Jährliche Preisabschläge (Produktivität an den Kunden) ab Jahr 2 in %, z. B. [2, 3, 3]
    "price_reductions": [], "price_reductions_basis": "jahr1",  # "jahr1" = ggü. Preis Jahr 1, "vorjahr" = ggü. Vorjahr
    "price_reductions_preload": True,   # Abschläge vorab einrechnen
    "price_reductions_preload_mode": "durchschnitt",  # "durchschnitt" (Ø = kalk. Preis) | "letztes_jahr" (kein Jahr darunter)
    "side_price_reductions": [],        # eigene Abschläge für Zukaufteile in der Nebenkalkulation
    # Preis Jahr 1: "kalkuliert" (= Serienpreis, optional mit Vorab-Einrechnung) oder "manuell" (fester Anlaufpreis;
    # ab Jahr 2 gilt der kalkulierte Serienpreis × Faktor des Jahres)
    "price_year1_mode": "kalkuliert", "price_year1_manual": None,
    "site_id": None,  # Fertigungsstandort (Sätze/Maschinen des Standorts)
    # Grenzkostenkalkulation: Strompreis für die Energiekosten (0 = ohne Energie, ältere Versionen)
    "energy_price_kwh": 0.0,
    # Vorserie: Kleinstmengen vor Serienstart (0 = kein Vorserienpreis)
    "preseries_qty": 0, "preseries_lot": None, "preseries_productivity_pct": None, "preseries_scrap_pct": None,
    "preseries_setup_h": None, "preseries_surcharge_pct": 0.0,
    "preseries_price_manual": None,     # fester Vorserienpreis €/Stk (kalkulierter Wert bleibt als Orientierung)
    "purchased_items": [],  # je Position optional "side": true = Nebenkalkulation statt voller Kalkulation
                            # v1.33 (C01): je Position "supplier" und "tiers": [{qty, price}] = Staffelpreise nach Jahresbedarf
    # v1.33 C03: Material mit Lieferant, Angebotsnummer, Staffelpreisen nach Jahresbedarf kg; Masterbatch mit Bezeichnung
    "material_supplier": "", "material_offer_no": "", "material_tiers": [],   # [{kg, price}]
    "masterbatch_name": "", "masterbatch_supplier": "",
    # v1.33 C02/C04: Mengen und Losgrößen je Lieferjahr (leer = Jahresmenge bzw. Losgröße oben); Angebot: Preise je Jahr zeigen
    "year_volumes": [], "year_lots": [], "quote_show_years": False,
    # Eigener MGK-Satz auf Zukaufteile (None = wie MGK)
    "purchased_mgk_pct": None,
    # Nebenkalkulation teurer Zukaufteile: nur MGK, Qualität, Ausschuss, Aufschlag – keine FGK/VwGK/VtGK/PM/Gewinn
    "side_mgk_pct": 0.0, "side_quality_pct": 0.0, "side_scrap_pct": 0.0, "side_markup_pct": 0.0,
    # Werkzeugamortisation: Einmalkosten mit amortize=true werden über diese Stückzahl umgelegt (0 = Jahresmenge × Laufzeit)
    "amort_quantity": 0,
    # Verpackung (Vorgabe leer = 0, damit ältere Versionen unverändert rechnen)
    "pack_mode": "detail",  # detail | prozent
    "pack_pct": 0.0,
    "pack_type": "", "pack_parts_per_unit": 0, "pack_cost_per_unit": 0.0, "pack_reusable": False,
    "pack_time_s": 0.0, "pack_units_per_pallet": 0,
    # CO₂-Fußabdruck (Vorgabe 0 = nicht berechnet; neue Kalkulationen erhalten Werte aus Stammdaten/Parametern)
    "co2_material_kg_kg": 0.0, "co2_masterbatch_kg_kg": 0.0, "machine_power_kw": 0.0, "co2_grid_kg_kwh": 0.0,
    "co2_scope1_kg_h": 0.0, "co2_purchased_parts": 0.0, "co2_pack_per_unit": 0.0, "transport_km": 0.0,
    "co2_transport_kg_tkm": 0.0, "co2_on_quote": True,
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
    out["components"] = [e for e in (out.get("components") or []) if isinstance(e, dict)]
    out["operations"] = [e for e in (out.get("operations") or []) if isinstance(e, dict)]
    out["purchased_items"] = [e for e in (out.get("purchased_items") or []) if isinstance(e, dict)]
    out["price_reductions"] = [e for e in (out.get("price_reductions") or []) if e not in (None, "")]
    out["side_price_reductions"] = [e for e in (out.get("side_price_reductions") or []) if e not in (None, "")]
    out["material_tiers"] = [e for e in (out.get("material_tiers") or []) if isinstance(e, dict)]
    out["year_volumes"] = list(out.get("year_volumes") or [])
    out["year_lots"] = list(out.get("year_lots") or [])
    return out


def _tier_price(base: float, tiers: list, need: float, key: str) -> dict:
    """Staffelpreis nach Jahresbedarf (v1.33 C01/C03). Gilt die höchste Staffel, deren Menge erreicht ist; unter der
    kleinsten Staffel gilt deren Preis. Liegt eine günstigere Staffel knapp darüber, wird geprüft, ob sich die größere
    Einkaufsmenge rechnet (Mehrmenge kostet weniger als der Bedarf zum aktuellen Preis)."""
    rows = sorted((_f(t.get(key)), _f(t.get("price"))) for t in tiers or [] if _f(t.get(key)) > 0 and _f(t.get("price")) > 0)
    if not rows:
        return {"price": base, "tier": None, "hint": None}
    applied = rows[0]
    for q, p in rows:
        if need >= q:
            applied = (q, p)
    price = applied[1]
    hint = None
    for q, p in rows:
        if q > need and p < price:
            now, alt = need * price, q * p
            if alt < now:
                hint = {"qty": q, "price": p, "cost_now": round(now, 2), "cost_alt": round(alt, 2),
                        "saves": round(now - alt, 2), "extra": round(q - need, 2)}
            break
    return {"price": price, "tier": applied[0], "hint": hint}


def compute(raw: dict) -> dict:
    res = _compute(raw)
    i = normalize(raw)
    tiers = []
    for lot in [t for t in (i.get("lot_tiers") or []) if _f(t) > 0][:5]:
        # Staffeln immer kalkuliert (ohne manuellen Preis), damit die Wirkung der Losgröße sichtbar ist
        sub = _compute({**i, "lot_size": _f(lot), "price_override": None, "lot_tiers": [], "volume_tiers": []})
        tiers.append({
            "lot_size": _f(lot),
            "setup_per_piece": sub["values"]["setup"],
            "self_cost": sub["self_cost"],
            "unit_price": sub["unit_price"],
            "price_per_1000": sub["price_per_1000"],
            "margin_pct": sub["margin_pct"],
            "lots_per_year": sub["lots_per_year"],
        })
    vtiers = []
    base_annual, base_lot = _f(i["annual_volume"]), _f(i["lot_size"])
    for vol in [t for t in (i.get("volume_tiers") or []) if _f(t) > 0][:5]:
        # gleiche Abrufhäufigkeit: Lose pro Jahr bleiben gleich, Losgröße wächst mit der Jahresmenge
        lot_v = base_lot * _f(vol) / base_annual if base_annual > 0 and base_lot > 0 else base_lot
        sub = _compute({**i, "annual_volume": _f(vol), "lot_size": lot_v, "price_override": None,
                        "lot_tiers": [], "volume_tiers": []})
        vtiers.append({"annual_volume": _f(vol), "lot_size": round(lot_v), "unit_price": sub["unit_price"], "price_per_1000": sub["price_per_1000"],
                       "self_cost": sub["self_cost"], "margin_pct": sub["margin_pct"], "annual_revenue": sub["annual_revenue"],
                       "lots_per_year": sub["lots_per_year"], "machine_hours_year": sub["machine_hours_year"],
                       "amortization_per_piece": sub["amortization_per_piece"]})
    base = _compute({**i, "price_override": None, "lot_tiers": [], "volume_tiers": []})["unit_price"] if (tiers or vtiers) else 0
    for t in tiers + vtiers:
        t["delta_pct"] = round((t["unit_price"] - base) / base * 100, 2) if base else 0
    res["lot_tiers"] = sorted(tiers, key=lambda t: t["lot_size"])
    res["volume_tiers"] = sorted(vtiers, key=lambda t: t["annual_volume"])
    res["base_calculated_price"] = base
    res["preseries"] = _preseries(i, res)
    res.update(_price_years(i, res))
    res["years"] = _years(i, res)
    res["project_revenue_years"] = round(sum(y["revenue"] for y in res["years"]), 2)
    return res


def _direct_costs(i: dict, d: dict) -> dict:
    """Grenzkosten (direkte Artikelkosten) je Stück für den Verhandlungsüberblick: nur Kosten, die für die Herstellung
    des Artikels zusätzlich anfallen – ohne Abschreibung/Zinsen/Raum der Maschine, ohne Gemeinkosten, Verwaltung,
    Vertrieb, Projektmanagement, Gewinn und Einmalkosten."""
    lot, pph, share = d["lot"], d["pph"], d["share"]
    var_run = d["labor"] + d["maintenance"]                      # Personal + Instandhaltung je Stück
    startup = _f(i["startup_scrap_pcs"]) / lot if lot > 0 else 0.0
    kw = _f(i["machine_power_kw"])
    hours = ((1 / pph if pph > 0 else 0) + (_f(i["setup_time_h"]) / lot if lot > 0 else 0)) * share
    energy = (kw * hours + sum(o["power_kw"] * o["hours_piece"] for o in d["ops"])) * _f(i.get("energy_price_kwh"))
    setup = (d["staff_lot"] + d["auto_lot"]) / lot if lot > 0 else 0.0
    setup_scrap = startup * (d["material"] + var_run)            # Anfahrteile: Material + variable Fertigung
    ops = sum(o["variable"] for o in d["ops"])
    production = d["material"] + d["purchased"] + var_run + energy + setup + setup_scrap + d["assembly"] + ops
    scrap = production / (1 - d["scrap_rate"]) - production if d["scrap_rate"] < 1 else 0.0
    side = d["side"] / (1 - d["side_scrap_rate"]) if d["side_scrap_rate"] < 1 else d["side"]
    total = production + scrap + side + d["packaging"] + d["transport"]
    price, annual = d["price"], d["annual"]
    rows = [("material", "Material inkl. Komponenten", d["material"]), ("purchased", "Zukaufteile", d["purchased"] + side),
            ("labor", "Personal Maschine (Bediener, Handling, Automatisierung)", d["labor"]),
            ("maintenance", "Instandhaltung", d["maintenance"]), ("energy", "Energie (Strom)", energy),
            ("setup", "Rüsten Personal + Anfahrteile", setup + setup_scrap), ("assembly", "Montage (Handarbeit)", d["assembly"]),
            ("operations", "Weitere Arbeitsgänge (Personal, Instandhaltung)", ops), ("scrap", "Ausschuss", scrap),
            ("packaging", "Verpackung", d["packaging"]), ("transport", "Transport", d["transport"])]
    db = price - total
    return {
        "lines": [{"key": k, "label": l, "value": round(v, 6)} for k, l, v in rows if abs(v) > 1e-12],
        "total": round(total, 6), "per_1000": round(total * 1000, 2),
        "contribution": round(db, 6), "contribution_pct": round(db / price * 100, 2) if price else 0,
        "contribution_year": round(db * annual, 2), "fixed_share": round(d["sk"] - total, 6),
        "energy_price_kwh": _f(i.get("energy_price_kwh")),
    }


def _factors(reds: list, years: int, basis: str) -> list:
    """Preisfaktor je Jahr (Jahr 1 = 1) aus den Abschlägen ab Jahr 2."""
    vals = [_f(r) for r in reds if r not in (None, "")]
    out, f = [1.0], 1.0
    for y in range(2, years + 1):
        r = vals[y - 2] if y - 2 < len(vals) else None
        if basis == "vorjahr":
            f *= 1 - (r or 0) / 100
        elif r is not None:
            f = 1 - r / 100
        out.append(f)
    return out


def _preload(f: list, idx: list, mode: str) -> float:
    """Aufschlag-Faktor, damit die Abschläge vorab eingerechnet sind.
    durchschnitt: Ø der Jahre = Ausgangspreis; letztes_jahr: kein Jahr unter dem Ausgangspreis."""
    vals = [f[n] for n in idx]
    if not vals:
        return 1.0
    if mode == "letztes_jahr":
        return 1 / min(vals) if min(vals) > 0 else 1.0
    return len(vals) / sum(vals) if sum(vals) else 1.0


def peak_revenue(res: dict) -> float:
    """Seit v1.33: aus der Tabelle der Lieferjahre (Menge je Jahr), sonst wie bisher. Neuumsatz = Umsatz des stärksten Lieferjahres (Vertriebsziel). Ohne Jahrespreise = Jahresumsatz."""
    years = [y.get("revenue") or 0 for y in (res.get("years") or res.get("price_years") or [])]
    return round(max(years + [0]) if years else float(res.get("annual_revenue") or 0), 2)


def _years_count(i: dict) -> int:
    return min(max(int(math.ceil(_f(i["project_years"], 1))), 1), 15)


def _year_volumes(i: dict) -> list:
    """Menge je Lieferjahr (C02) – leere Felder = Jahresmenge."""
    yv = i.get("year_volumes") or []
    return [(_f(yv[y]) if y < len(yv) and yv[y] not in (None, "") and _f(yv[y]) > 0 else _f(i["annual_volume"]))
            for y in range(_years_count(i))]


def _years(i: dict, res: dict) -> list:
    """Lieferjahre (v1.33 C02/C04/C05): Menge, Losgröße, Preis, Umsatz, Selbstkosten, Marge, Stunden, Material, Zukaufteile.
    Weicht Menge oder Losgröße eines Jahres von der Kalkulationsmenge ab, wird das Jahr mit diesen Werten nachgerechnet
    (Rüstanteil, Amortisation, Stunden); der Preis kommt aus der Kalkulation (inkl. Abschläge je Jahr)."""
    vols, yl = _year_volumes(i), i.get("year_lots") or []
    annual, lot = _f(i["annual_volume"]), _f(i["lot_size"])
    py = {r["year"]: r for r in res.get("price_years") or []}
    pcs_piece = sum(x["qty"] for x in res.get("purchased_items") or [])
    out = []
    for y, q in enumerate(vols):
        l_in = yl[y] if y < len(yl) else None
        lot_y = _f(l_in) if l_in not in (None, "") and _f(l_in) > 0 else lot
        same = abs(q - annual) < 1e-9 and abs(lot_y - lot) < 1e-9
        sub = res if same else _compute({**i, "annual_volume": q, "lot_size": lot_y, "price_override": None,
                                         "lot_tiers": [], "volume_tiers": []})
        # ohne Jahrespreise: exakter Preis wie im Jahresumsatz (nicht der auf 4 Stellen gerundete Stückpreis)
        price = py[y + 1]["price"] if y + 1 in py else (res["annual_revenue"] / annual if annual > 0 else res["unit_price"])
        sk = _f(sub.get("self_cost"))
        out.append({"year": y + 1, "qty": q, "lot": lot_y, "lot_manual": l_in not in (None, "") and _f(l_in) > 0,
                    "lot_suggestion": round(q / 12) if y > 0 and q > 0 else None,
                    "price": round(price, 4), "revenue": round(price * q, 2), "self_cost": round(sk, 4),
                    "margin_pct": round((price - sk) / price * 100, 2) if price else 0, "profit": round((price - sk) * q, 2),
                    "machine_hours": _f(sub.get("machine_hours_year")), "material_kg": _f(sub.get("material_kg_year")),
                    "purchased_pcs": round(pcs_piece * q, 0), "lots": round(q / lot_y, 1) if lot_y > 0 else 0})
    return out


def _price_years(i: dict, res: dict) -> dict:
    """Serienpreis je Lieferjahr: optional manueller Anlaufpreis Jahr 1, Abschläge je Jahr (vorab eingerechnet),
    Zukaufteile der Nebenkalkulation mit eigenen Abschlägen. Marge je Jahr gegen die Selbstkosten."""
    main_reds = [r for r in i.get("price_reductions") or [] if r not in (None, "")]
    side_reds = [r for r in i.get("side_price_reductions") or [] if r not in (None, "")]
    manual = i.get("price_year1_mode") == "manuell" and _f(i.get("price_year1_manual")) > 0
    if not main_reds and not side_reds and not manual:
        return {"price_years": [], "price_year1": res["unit_price"], "preload_pct": 0}
    years = min(max(int(math.ceil(_f(i["project_years"], 1))), 1), 15)
    basis = i.get("price_reductions_basis") or "jahr1"
    fm, fs = _factors(main_reds, years, basis), _factors(side_reds, years, basis)
    side = _f(res.get("price_side_part"))
    main = res["unit_price"] - side
    preload = i.get("price_reductions_preload", True) not in (False, "false", 0)
    mode = i.get("price_reductions_preload_mode") or "durchschnitt"
    idx = list(range(1, years)) if manual else list(range(years))  # bei manuellem Anlaufpreis: Jahre ab 2
    km = _preload(fm, idx, mode) if preload else 1.0
    ks = _preload(fs, idx, mode) if preload else 1.0
    annual, sk = _f(i["annual_volume"]), _f(res.get("self_cost"))
    rows = []
    for y in range(years):
        pm, ps = main * km * fm[y], side * ks * fs[y]
        if manual and y == 0:  # fester Anlaufpreis Jahr 1
            pm, ps = _f(i["price_year1_manual"]) - side, side
        price = pm + ps
        rows.append({"year": y + 1, "price": round(price, 4), "main": round(pm, 4), "side": round(ps, 4),
                     "factor": round(fm[y], 4), "factor_side": round(fs[y], 4), "revenue": round(price * annual, 2),
                     "manual": bool(manual and y == 0),
                     "margin_pct": round((price - sk) / price * 100, 2) if price else 0,
                     "profit": round((price - sk) * annual, 2), "below_calc": price < res["unit_price"] - 1e-9,
                     "contribution": round((price - _f((res.get("direct_costs") or {}).get("total"))) * annual, 2)})
    p1 = rows[0]["price"] if manual else main * km + side * ks
    series_uplift = (main * km + side * ks) / res["unit_price"] - 1 if res["unit_price"] else 0
    return {"price_years": rows, "price_year1": round(p1, 4), "price_year1_manual": manual,
            "preload_pct": round(series_uplift * 100, 2),
            "preload_mode": mode if preload else None,
            "project_revenue_reductions": round(sum(r["revenue"] for r in rows), 2),
            "years_below_cost": [r["year"] for r in rows if r["margin_pct"] < 0]}


def _preseries(i: dict, res: dict) -> dict | None:
    """Vorserienpreis für Kleinstmengen: eigene Menge/Los, optional schlechtere Produktivität, Ausschuss, Rüstzeit."""
    qty = _f(i.get("preseries_qty"))
    if qty <= 0:
        return None
    over = {"annual_volume": qty, "lot_size": _f(i.get("preseries_lot")) or qty, "price_override": None,
            "lot_tiers": [], "volume_tiers": [], "price_reductions": [], "side_price_reductions": [],
            "one_time": [{**o, "amortize": False} for o in i.get("one_time") or []]}
    for src, dst in (("preseries_productivity_pct", "productivity_pct"), ("preseries_scrap_pct", "scrap_pct"),
                     ("preseries_setup_h", "setup_time_h")):
        if i.get(src) not in (None, ""):
            over[dst] = _f(i[src])
    sub = _compute({**i, **over})
    calc_price = sub["unit_price"] * (1 + _f(i.get("preseries_surcharge_pct")) / 100)
    manual = _f(i.get("preseries_price_manual")) > 0
    price = _f(i["preseries_price_manual"]) if manual else calc_price
    return {"qty": qty, "lot_size": over["lot_size"], "self_cost": sub["self_cost"], "calc_price": round(calc_price, 4),
            "manual": manual, "margin_pct": round((price - sub["self_cost"]) / price * 100, 1) if price else 0,
            "unit_price": round(price, 4), "price_per_1000": round(price * 1000, 2), "total": round(price * qty, 2),
            "setup_per_piece": sub["values"]["setup"], "pieces_per_hour": sub["pieces_per_hour"],
            "delta_pct": round((price / res["unit_price"] - 1) * 100, 1) if res["unit_price"] else 0}


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
    scrap_pre = min(_f(i["scrap_pct"]) / 100, 0.95)
    need_kg = kg_piece * annual / (1 - scrap_pre)            # Jahresbedarf Material inkl. Anguss und Ausschuss
    mtier = _tier_price(_f(i["material_price_kg"]), i.get("material_tiers"), need_kg * (1 - mb), "kg")
    price_kg = mtier["price"] * (1 - mb) + _f(i["masterbatch_price_kg"]) * mb
    purchase = {"need_kg": round(need_kg * (1 - mb), 1), "price_kg": round(mtier["price"], 4), "tier_kg": mtier["tier"],
                "hint": mtier["hint"], "supplier": i.get("material_supplier") or "", "offer_no": i.get("material_offer_no") or "",
                "masterbatch_kg": round(need_kg * mb, 1), "masterbatch_name": i.get("masterbatch_name") or ""}
    mek_material = kg_piece * price_kg
    comps = []
    for c in i.get("components") or []:
        if not isinstance(c, dict):
            continue
        ckg = (_f(c.get("part_weight_g")) + (_f(c.get("sprue_weight_g")) / cavities if cavities else 0)
               * (1 - _f(c.get("regrind_pct")) / 100)) / 1000
        comps.append({"label": c.get("label") or c.get("material_name") or "Komponente", "kg": ckg,
                      "cost": ckg * _f(c.get("price_kg")), "co2_kg_kg": _f(c.get("co2_kg_kg")),
                      "material_name": c.get("material_name") or "", "part_weight_g": _f(c.get("part_weight_g"))})
    mek_components = sum(c["cost"] for c in comps)
    kg_total = kg_piece + sum(c["kg"] for c in comps)
    pitems = []
    for p_ in i.get("purchased_items") or []:
        if not isinstance(p_, dict):
            continue
        qty = _f(p_.get("qty"), 1)
        pneed = qty * annual                                   # Jahresbedarf Stück (C01)
        pt = _tier_price(_f(p_.get("price_per_piece")), p_.get("tiers"), pneed, "qty")
        pr = pt["price"]
        pitems.append({"name": p_.get("name") or p_.get("part_no") or "Zukaufteil", "part_no": p_.get("part_no") or "",
                       "qty": qty, "price_per_piece": pr, "cost": qty * pr, "side": bool(p_.get("side")),
                       "co2": qty * _f(p_.get("co2_kg_per_piece")), "need_year": round(pneed, 0), "tier_qty": pt["tier"],
                       "hint": pt["hint"], "supplier": p_.get("supplier") or ""})
    purchased = _f(i["purchased_parts"]) + sum(x["cost"] for x in pitems if not x["side"])
    mek = mek_material + mek_components + purchased
    own_pmgk = i.get("purchased_mgk_pct") not in (None, "")
    pmgk_pct = _f(i["purchased_mgk_pct"]) if own_pmgk else _f(i["mgk_pct"])
    mgk = (mek - purchased) * _f(i["mgk_pct"]) / 100
    mgk_purchased = purchased * pmgk_pct / 100
    if not own_pmgk:  # gemeinsame Zeile wie bisher
        mgk, mgk_purchased = mgk + mgk_purchased, 0.0

    # --- Nebenkalkulation teurer Zukaufteile (wird nur mit eigenen Zuschlägen auf den Preis gerechnet)
    side_items = [x for x in pitems if x["side"]]
    side_cost = sum(x["cost"] for x in side_items)
    side_mgk = side_cost * _f(i["side_mgk_pct"]) / 100
    side_quality = side_cost * _f(i["side_quality_pct"]) / 100
    side_base = side_cost + side_mgk + side_quality
    side_scrap_rate = min(_f(i["side_scrap_pct"]) / 100, 0.95)
    side_scrap = side_base / (1 - side_scrap_rate) - side_base
    side_sk = side_base + side_scrap
    side_markup = side_sk * _f(i["side_markup_pct"]) / 100

    # --- Fertigung
    share = min(max(_f(i.get("family_share_pct"), 100), 0), 100) / 100 or 1.0
    machine = per(_f(i["machine_rate_h"])) * share
    maintenance = per(_f(i["maintenance_rate_h"])) * share
    labor = per(_f(i["labor_rate_h"]) * _f(i["operator_factor"])) * share
    labor_handling = per(_f(i["handling_rate_h"]) * _f(i["handling_pct"]) / 100) * share
    labor_automation = per(_f(i["automation_rate_h"]) * _f(i["automation_pct"]) / 100) * share
    run_cost_piece = machine + maintenance + labor + labor_handling + labor_automation
    setup_h = _f(i["setup_time_h"])
    staff_h = _f(i["setup_staff_min"]) / 60 if i.get("setup_staff_min") not in (None, "") else setup_h
    setup_machine_lot = setup_h * (_f(i["machine_rate_h"]) + _f(i["maintenance_rate_h"])) * share
    setup_staff_lot = staff_h * _f(i["setup_rate_h"]) * _f(i["setup_persons"]) * share
    setup_auto_lot = _f(i["automation_setup_min"]) / 60 * _f(i["automation_rate_h"]) * share
    setup_scrap_lot = _f(i["startup_scrap_pcs"]) * (mek_material + mek_components + run_cost_piece)
    setup_lot = setup_machine_lot + setup_staff_lot + setup_auto_lot + setup_scrap_lot
    if lot <= 0:
        warnings.append("Losgröße fehlt – Rüstkosten werden nicht umgelegt.")
    setup = setup_lot / lot if lot > 0 else 0.0
    ap = _f(i["assembly_productivity_pct"], 100) / 100
    assembly = (_f(i["assembly_time_s"]) / 3600 * _f(i["assembly_rate_h"]) * _f(i["assembly_persons"]) / ap) if ap > 0 else 0.0
    # --- Weitere Arbeitsgänge (1 … N Maschinen/Anlagen)
    ops = []
    for o in i.get("operations") or []:
        if not isinstance(o, dict):
            continue
        cyc, ppc = _f(o.get("cycle_s")), max(_f(o.get("parts_per_cycle"), 1), 0)
        oprod = _f(o.get("productivity_pct"), 100) / 100
        opph = 3600 / cyc * ppc * oprod if cyc > 0 else 0
        rate = _f(o.get("rate_h")) + _f(o.get("maintenance_h")) + _f(o.get("labor_rate_h")) * _f(o.get("operator_factor"))
        run = rate / opph if opph > 0 else 0.0
        osetup_lot = _f(o.get("setup_h")) * (_f(o.get("rate_h")) + _f(o.get("maintenance_h"))
                                              + _f(o.get("labor_rate_h")) * _f(o.get("setup_persons"), 1))
        osetup = osetup_lot / lot if lot > 0 else 0.0
        if cyc <= 0:
            warnings.append(f"Arbeitsgang „{o.get('name') or 'ohne Name'}“: Taktzeit fehlt.")
        ovar = ((_f(o.get("maintenance_h")) + _f(o.get("labor_rate_h")) * _f(o.get("operator_factor"))) / opph if opph > 0 else 0.0) \
            + (_f(o.get("setup_h")) * _f(o.get("labor_rate_h")) * _f(o.get("setup_persons"), 1) / lot if lot > 0 else 0.0)
        ops.append({"name": o.get("name") or "Arbeitsgang", "machine_id": o.get("machine_id"), "kind": o.get("kind") or "",
                    "pieces_per_hour": opph, "run": run, "setup": osetup, "cost": run + osetup, "variable": ovar,
                    "hours_year": (annual / opph if opph > 0 else 0) + (annual / lot if lot > 0 else 0) * _f(o.get("setup_h")),
                    "power_kw": _f(o.get("power_kw")),
                    "hours_piece": (1 / opph if opph > 0 else 0) + (_f(o.get("setup_h")) / lot if lot > 0 else 0)})
    operations = sum(x["cost"] for x in ops)
    fek = run_cost_piece + setup + assembly + operations
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
    hk_pre = mek + mgk + mgk_purchased + fek + fgk + quality_f + toolshop_f + sek_f
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
    pack_pct_mode = i.get("pack_mode") == "prozent"
    if pack_pct_mode:
        packaging = hk * _f(i["pack_pct"]) / 100
    else:
        pack_material = _f(i["pack_cost_per_unit"]) / ppu if ppu > 0 else 0.0
        pack_labor = _f(i["pack_time_s"]) / 3600 * _f(i["labor_rate_h"]) / ppu if ppu > 0 else 0.0
        packaging = pack_material + pack_labor
    if not pack_pct_mode and (_f(i["pack_cost_per_unit"]) or _f(i["pack_time_s"])) and ppu <= 0:
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
    sk_main = hk + vwgk + vtgk + pm + quality_h + toolshop_h + packaging + transport + sek_v
    sk = sk_main + side_sk

    # --- Werkzeugamortisation (Einmalkosten mit amortize=true, ohne Gewinnaufschlag umgelegt)
    yv = _year_volumes(i)
    amort_qty = _f(i.get("amort_quantity")) or (sum(yv) if any(_f(v) > 0 for v in i.get("year_volumes") or []) else
                                                 annual * max(_f(i["project_years"], 1), 1))
    amort_total = sum(_f(o.get("price")) or _f(o.get("cost")) for o in i["one_time"] if o.get("amortize"))
    amortization = amort_total / amort_qty if amort_qty > 0 else 0.0
    if amort_total and amort_qty <= 0:
        warnings.append("Werkzeugamortisation: Stückzahl fehlt.")

    sd = _f(i["cash_discount_pct"]) / 100
    rb = _f(i["rebate_pct"]) / 100
    if i.get("price_override") not in (None, ""):
        price = _f(i["price_override"])
        net = price * (1 - sd) * (1 - rb)
        profit = net - sk - amortization
        price_source = "manuell"
    else:
        profit = sk_main * _f(i["profit_pct"]) / 100 + side_markup
        net = sk + profit + amortization
        price = net / (1 - sd) / (1 - rb) if sd < 1 and rb < 1 else net
        price_source = "kalkuliert"
    discounts = price - net
    if profit < 0:
        warnings.append("Verkaufspreis liegt unter den Selbstkosten.")

    # --- Einmalkosten
    one_time = [{"label": o.get("label") or "Einmalkosten", "cost": _f(o.get("cost")),
                 "price": _f(o.get("price"), o.get("cost")), "amortize": bool(o.get("amortize"))} for o in i["one_time"]]
    ot_cost = sum(o["cost"] for o in one_time)
    ot_price = sum(o["price"] for o in one_time if not o["amortize"])

    lines = [
        ("mek_material", "Material" + (" Komponente A" if comps else "") + " (inkl. Angussanteil)", "material", mek_material),
        ("mek_components", "Material weitere Komponenten (" + ", ".join(c["label"] for c in comps) + ")" if comps else
         "Material weitere Komponenten", "material", mek_components),
        ("purchased", "Zukaufteile" + (f" ({len(pitems) - len(side_items)} Pos.)" if len(pitems) > len(side_items) else ""),
         "material", purchased),
        ("mgk", f"Materialgemeinkosten {_p(i['mgk_pct'])} %" + (" auf Material" if own_pmgk else ""), "material", mgk),
        ("mgk_purchased", f"MGK Zukaufteile {_p(pmgk_pct)} %", "material", mgk_purchased),
        ("machine", "Maschine", "fertigung", machine),
        ("maintenance", "Instandhaltung", "fertigung", maintenance),
        ("labor", f"Personal Bediener {_p(_f(i['operator_factor']) * 100)} %", "fertigung", labor),
        ("labor_handling", f"Personal Handling {_p(i['handling_pct'])} %", "fertigung", labor_handling),
        ("labor_automation", f"Personal Automatisierung {_p(i['automation_pct'])} %", "fertigung", labor_automation),
        ("setup", "Rüsten (je Los umgelegt)", "fertigung", setup),
        ("assembly", "Montage (Handarbeit)", "fertigung", assembly),
        *[(f"op_{n}", f"Arbeitsgang: {x['name']}", "fertigung", x["cost"]) for n, x in enumerate(ops)],
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
        ("packaging", (f"Verpackung {_p(i['pack_pct'])} % auf HK" if pack_pct_mode else
                       "Verpackung" + (f" ({i.get('pack_type')})" if i.get("pack_type") else "")), "gemeinkosten", packaging),
        ("transport", {"palette": "Transport je Palette", "lieferung": "Transport je Lieferung",
                       "prozent": f"Transport {_p(i['transport_pct'])} % auf HK"}.get(mode, "Transport"), "gemeinkosten", transport),
        ("sek_v", "Sondereinzelkosten Vertrieb", "gemeinkosten", sek_v),
        ("side_purchased", f"Zukaufteile Nebenkalkulation ({len(side_items)} Pos.)", "nebenkalkulation", side_sk),
        ("sk", "Selbstkosten", "summe", sk),
        ("profit", "Gewinn" + (f" {_p(i['profit_pct'])} %" + (" (+ Aufschlag Nebenkalk.)" if side_markup else "")
                               if price_source == "kalkuliert" else " (Rest)"), "ergebnis", profit),
        ("amortization", "Werkzeugamortisation (ohne Aufschlag)", "ergebnis", amortization),
        ("discounts", "Skonto / Rabatt", "ergebnis", discounts),
        ("price", "Verkaufspreis", "summe", price),
    ]
    co2 = _co2(i, kg_piece, pph, scrap_rate, lot, annual, ppu, comps, share, ops, pitems)
    rnd = lambda v: round(v, 6)  # noqa: E731
    lots_year = annual / lot if lot > 0 else 0
    machine_hours = ((annual / pph if pph > 0 else 0) + lots_year * _f(i["setup_time_h"])) * share
    return {
        "lines": [{"key": k, "label": lbl, "group": g, "per_piece": rnd(v), "per_100": rnd(v * 100),
                   "per_1000": rnd(v * 1000), "share_pct": round(v / price * 100, 2) if price else 0}
                  for k, lbl, g, v in lines],
        "values": {k: rnd(v) for k, _, _, v in lines},
        "unit_price": round(price, 4),
        "direct_costs": _direct_costs(i, dict(
            material=mek_material + mek_components, purchased=purchased, side=side_cost, side_scrap_rate=side_scrap_rate,
            labor=labor + labor_handling + labor_automation, maintenance=maintenance, pph=pph, lot=lot, share=share,
            staff_lot=setup_staff_lot, auto_lot=setup_auto_lot, assembly=assembly, ops=ops, scrap_rate=scrap_rate,
            packaging=packaging, transport=transport, price=price, sk=sk, annual=annual)),
        "price_side_part": round((side_sk + side_markup) / (1 - sd) / (1 - rb) if sd < 1 and rb < 1 else side_sk + side_markup, 6),
        "price_per_100": round(price * 100, 2),
        "price_per_1000": round(price * 1000, 2),
        "price_source": price_source,
        "self_cost": round(sk, 4),
        "profit_per_piece": round(profit, 4),
        "margin_pct": round(profit / price * 100, 2) if price else 0,
        "kg_per_piece": round(kg_total, 6),
        "kg_main_per_piece": round(kg_piece, 6),
        "components": [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in c.items()} for c in comps],
        "shot_weight_g": round((_f(i["part_weight_g"]) + sum(c["part_weight_g"] for c in comps)) * cavities
                               + _f(i["sprue_weight_g"]), 2),
        "family_share_pct": round(share * 100, 2),
        "operations": [{**x, "pieces_per_hour": round(x["pieces_per_hour"], 1), "run": round(x["run"], 6),
                        "setup": round(x["setup"], 6), "cost": round(x["cost"], 6), "hours_year": round(x["hours_year"], 1),
                        "hours_piece": round(x["hours_piece"], 8)} for x in ops],
        "operations_cost": round(operations, 6),
        "purchased_side": {"items": len(side_items), "cost": round(side_cost, 6), "mgk": round(side_mgk, 6),
                           "quality": round(side_quality, 6), "scrap": round(side_scrap, 6), "self_cost": round(side_sk, 6),
                           "markup": round(side_markup, 6), "total": round(side_sk + side_markup, 6),
                           "mgk_pct": _f(i["side_mgk_pct"]), "quality_pct": _f(i["side_quality_pct"]),
                           "scrap_pct": _f(i["side_scrap_pct"]), "markup_pct": _f(i["side_markup_pct"])},
        "purchased_items": [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in x.items()} for x in pitems],
        "material_purchase": purchase,
        "lot_suggestion": round(annual / 12) if annual > 0 else 0,
        "amortization_per_piece": round(amortization, 6),
        "amortization_total": round(amort_total, 2),
        "amortization_quantity": round(amort_qty, 0),
        "pieces_per_hour_theoretical": round(pph_theo, 1),
        "pieces_per_hour": round(pph, 1),
        "setup_cost_per_lot": round(setup_lot, 2),
        "setup_breakdown": {"machine": round(setup_machine_lot, 2), "setter": round(setup_staff_lot, 2),
                            "automation": round(setup_auto_lot, 2), "startup_scrap": round(setup_scrap_lot, 2),
                            "setter_h": round(staff_h, 3)},
        "lots_per_year": round(lots_year, 2),
        "machine_hours_year": round(machine_hours, 1),
        "material_kg_year": round(kg_total * annual / (1 - scrap_rate), 1),
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
        "co2": co2,
        "warnings": warnings,
    }


def _co2(i: dict, kg_piece: float, pph: float, scrap_rate: float, lot: float, annual: float, ppu: float,
         comps: list | None = None, share: float = 1.0, ops: list | None = None, pitems: list | None = None) -> dict:
    """CO₂-Fußabdruck je Gutteil (Cradle-to-Gate + optional Transport zum Kunden), in kg CO₂e.

    Material:   Gewicht je Teil inkl. Angussanteil × Emissionsfaktor (Mischung mit Masterbatch) / (1 − Ausschuss)
                + Anfahrausschuss je Los
    Strom:      (Leistung kW / Stück je h / (1 − Ausschuss) + Rüstzeit × kW / Losgröße) × Stromfaktor   → Scope 2
    Werk:       Maschinenstunden je Teil × kg CO₂e je Maschinenstunde                                   → Scope 1
    Zukauf/Verpackung: Werte je Stück bzw. je Verpackungseinheit / Teile je VE                          → Scope 3
    Transport:  Teilgewicht in t × km × kg CO₂e/tkm                                                     → Scope 3 (downstream)
    """
    good = 1 - scrap_rate if scrap_rate < 1 else 1
    mb = _f(i["masterbatch_pct"]) / 100
    factor = _f(i["co2_material_kg_kg"]) * (1 - mb) + _f(i["co2_masterbatch_kg_kg"]) * mb
    startup = _f(i["startup_scrap_pcs"]) / lot if lot > 0 else 0
    comps = comps or []
    mat_co2 = kg_piece * factor + sum(c["kg"] * c["co2_kg_kg"] for c in comps)
    material = mat_co2 / good + mat_co2 * startup
    hours_piece = ((1 / pph / good if pph > 0 else 0) + (_f(i["setup_time_h"]) / lot if lot > 0 else 0)) * share
    kwh = _f(i["machine_power_kw"]) * hours_piece + sum(o["power_kw"] * o["hours_piece"] for o in ops or [])
    energy = kwh * _f(i["co2_grid_kg_kwh"])
    scope1 = hours_piece * _f(i["co2_scope1_kg_h"])
    purchased = _f(i["co2_purchased_parts"]) + sum(x["co2"] for x in pitems or [])
    packaging = _f(i["co2_pack_per_unit"]) / ppu if ppu > 0 else 0.0
    weight_g = _f(i["part_weight_g"]) + sum(c["part_weight_g"] for c in comps)
    transport = weight_g / 1e6 * _f(i["transport_km"]) * _f(i["co2_transport_kg_tkm"])
    s12 = scope1 + energy
    gate = s12 + material + purchased + packaging
    total = gate + transport
    deliveries = _f(i.get("transport_deliveries_per_year"))
    r6 = lambda v: round(v, 6)  # noqa: E731
    return {
        "material": r6(material), "energy": r6(energy), "scope1": r6(scope1), "purchased": r6(purchased),
        "packaging": r6(packaging), "transport": r6(transport),
        "scope12": r6(s12), "cradle_to_gate": r6(gate), "total": r6(total),
        "kwh_per_piece": r6(kwh), "kwh_year": round(kwh * annual, 1),
        "per_1000_kg": round(total * 1000, 3),
        "per_lot_kg": round(total * lot, 2),
        "per_year_t": round(total * annual / 1000, 3),
        "scope12_year_t": round(s12 * annual / 1000, 3),
        "per_delivery_kg": round(total * annual / deliveries, 2) if deliveries > 0 else None,
        "per_kg_part": round(total / (weight_g / 1000), 3) if weight_g > 0 else None,
        "material_factor": round(factor, 3),
        "active": bool(factor or _f(i["machine_power_kw"]) or any(c["co2_kg_kg"] for c in comps)
                       or any(x["co2"] for x in pitems or [])),
    }


# Felder, die in der Nachkalkulation durch Ist-Werte ersetzt werden können
ACTUAL_FIELDS = (
    "cycle_time_s", "cavities", "productivity_pct", "scrap_pct", "material_price_kg", "part_weight_g",
    "sprue_weight_g", "setup_time_h", "lot_size", "assembly_time_s", "labor_rate_h", "operator_factor",
    "machine_rate_h", "maintenance_rate_h", "purchased_parts",
    "pack_cost_per_unit", "pack_parts_per_unit", "transport_cost_per_pallet", "transport_cost_per_delivery",
    "transport_deliveries_per_year", "pack_pct", "transport_pct",
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



def machine_rate(m: dict, st: dict) -> dict:
    """Herleitung Maschinenstundensatz (ohne Personal) und Instandhaltungssatz je Stunde.
    Abschreibung = Wiederbeschaffungswert / Nutzungsdauer; Zinsen = WBW / 2 × Zins %; Raum = m² × €/m²·Jahr;
    Energie = kW × €/kWh je Stunde; sonstige Fixkosten; Umlage Kostenstelle; alles / verfügbare Stunden je Jahr.
    Umlagen nur hier ODER über den FGK-Zuschlag erfassen – nicht doppelt."""
    hours = _f(m.get("available_hours_year"), 6000) or 6000
    wbw, life = _f(m.get("acquisition_value")), _f(m.get("useful_life_years"))
    parts = {
        "depreciation": (wbw / life) / hours if life > 0 else 0.0,
        "interest": (wbw / 2 * _f(m.get("interest_pct")) / 100) / hours,
        "space": _f(m.get("floor_space_m2")) * _f(st.get("space_cost_m2_year")) / hours,
        "energy": _f(m.get("power_kw")) * _f(st.get("energy_price_kwh")),
        "other": _f(m.get("other_fixed_cost_year")) / hours,
        "allocation": _f(m.get("allocation_cost_year")) / hours,
    }
    maint = _f(m.get("maintenance_cost_year")) / hours
    rate = sum(parts.values())
    return {"parts": {k: round(v, 2) for k, v in parts.items()}, "hourly_rate": round(rate, 2),
            "maintenance_rate": round(maint, 2), "hours": hours,
            "complete": bool(wbw and life), "current_hourly_rate": m.get("hourly_rate"),
            "current_maintenance_rate": m.get("maintenance_rate")}
