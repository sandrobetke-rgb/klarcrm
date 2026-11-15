"""Rechentests: jeder Rechenweg gegen eine Handrechnung. Läuft bei jedem Push (GitHub Actions)."""
import math

import pytest

from app.analysis import analyze
from app.calc_engine import compute, machine_rate, post_calculate

BASE = {
    "annual_volume": 100000, "lot_size": 10000, "material_price_kg": 3.0, "part_weight_g": 20, "sprue_weight_g": 4,
    "machine_rate_h": 45, "maintenance_rate_h": 5, "cycle_time_s": 30, "cavities": 4, "productivity_pct": 85,
    "operator_factor": 0.3, "labor_rate_h": 38, "setup_time_h": 2, "setup_persons": 1, "setup_rate_h": 48,
    "startup_scrap_pcs": 0, "scrap_pct": 3,
}
PPH = 3600 / 30 * 4 * 0.85  # 408 Stk/h


def hand_price(extra_hk=0.0, extra_sk=0.0, profit=0.07):
    mat = (20 + 4 / 4) / 1000 * 3.0
    fek = (45 + 5 + 38 * 0.3) / PPH + 2 * (45 + 5 + 48) / 10000
    hk = (mat * 1.06 + fek * 1.12 + extra_hk) / 0.97
    sk = hk * (1 + 0.06 + 0.03 + 0.02) + extra_sk
    return hk, sk, sk * (1 + profit)


def test_referenzkalkulation():
    r = compute(BASE)
    _, sk, price = hand_price()
    assert r["pieces_per_hour"] == pytest.approx(PPH, abs=0.1)
    assert r["self_cost"] == pytest.approx(sk, abs=1e-4)
    assert r["unit_price"] == pytest.approx(price, abs=1e-4)
    assert r["unit_price"] == 0.315  # muss zur Referenz im CI-Workflow passen
    assert r["price_per_1000"] == pytest.approx(r["unit_price"] * 1000, abs=0.1)


def test_manueller_preis_gewinn_als_rest():
    r = compute({**BASE, "price_override": 0.30})
    assert r["unit_price"] == 0.30
    assert r["profit_per_piece"] == pytest.approx(0.30 - r["self_cost"], abs=1e-6)
    assert r["price_source"] == "manuell"


def test_qualitaet_und_werkzeugbau_basis():
    r = compute({**BASE, "quality_pct": 1.5, "quality_base": "hk", "toolshop_pct": 2, "toolshop_base": "fek"})
    fek = (45 + 5 + 38 * 0.3) / PPH + 2 * (45 + 5 + 48) / 10000
    hk, _, _ = hand_price(extra_hk=fek * 0.02)
    assert r["values"]["toolshop_f"] == pytest.approx(fek * 0.02, abs=1e-6)
    assert r["values"]["quality_h"] == pytest.approx(hk * 0.015, abs=1e-6)


def test_staffeln_losgroesse_und_jahresmenge():
    inp = {**BASE, "startup_scrap_pcs": 50, "lot_tiers": [2000, 50000], "volume_tiers": [50000, 250000],
           "project_years": 5, "one_time": [{"label": "WZ", "cost": 30000, "price": 30000, "amortize": True}]}
    r = compute(inp)
    lots = {t["lot_size"]: t for t in r["lot_tiers"]}
    assert lots[2000]["unit_price"] > r["unit_price"] > lots[50000]["unit_price"]
    vols = {t["annual_volume"]: t for t in r["volume_tiers"]}
    assert vols[50000]["lot_size"] == 5000 and vols[250000]["lot_size"] == 25000  # Lose/Jahr konstant
    assert vols[50000]["unit_price"] > r["unit_price"] > vols[250000]["unit_price"]


def test_mehrkomponenten():
    r = compute({**BASE, "components": [{"label": "TPE", "price_kg": 4.9, "part_weight_g": 5, "sprue_weight_g": 0}]})
    assert r["values"]["mek_components"] == pytest.approx(0.005 * 4.9, abs=2e-6)
    assert r["kg_per_piece"] == pytest.approx(0.026, abs=2e-6)


def test_familienwerkzeug_halbiert_maschinenanteil():
    a, b = compute(BASE), compute({**BASE, "family_share_pct": 50})
    for k in ("machine", "maintenance", "labor"):
        assert b["values"][k] == pytest.approx(a["values"][k] / 2, abs=2e-6)
    assert b["machine_hours_year"] == pytest.approx(a["machine_hours_year"] / 2, abs=0.2)


def test_werkzeugamortisation():
    r = compute({**BASE, "project_years": 5, "one_time": [
        {"label": "WZ", "cost": 30000, "price": 32000, "amortize": True}, {"label": "EMPB", "cost": 1800, "price": 1800}]})
    assert r["amortization_per_piece"] == pytest.approx(32000 / 500000, abs=2e-6)
    assert r["one_time_price"] == 1800 and r["one_time_cost"] == 31800
    _, _, price = hand_price()
    assert r["unit_price"] == pytest.approx(price + 32000 / 500000, abs=1e-4)  # ohne Gewinnaufschlag


def test_verpackung_und_transport():
    det = compute({**BASE, "pack_parts_per_unit": 500, "pack_cost_per_unit": 1.2, "pack_time_s": 30,
                   "pack_units_per_pallet": 24, "transport_mode": "palette", "transport_cost_per_pallet": 68})
    assert det["values"]["packaging"] == pytest.approx(1.2 / 500 + 30 / 3600 * 38 / 500, abs=2e-6)
    assert det["values"]["transport"] == pytest.approx(68 / 12000, abs=2e-6)
    lief = compute({**BASE, "transport_mode": "lieferung", "transport_cost_per_delivery": 180, "transport_deliveries_per_year": 24})
    assert lief["values"]["transport"] == pytest.approx(180 * 24 / 100000, abs=2e-6)
    pct = compute({**BASE, "pack_mode": "prozent", "pack_pct": 1.5, "transport_mode": "prozent", "transport_pct": 2})
    hk = pct["values"]["hk"]
    assert pct["values"]["packaging"] == pytest.approx(hk * 0.015, abs=2e-6)
    assert pct["values"]["transport"] == pytest.approx(hk * 0.02, abs=2e-6)


def test_co2_fussabdruck():
    r = compute({**BASE, "startup_scrap_pcs": 50, "co2_material_kg_kg": 6.5, "machine_power_kw": 14,
                 "co2_grid_kg_kwh": 0.3, "transport_km": 300, "co2_transport_kg_tkm": 0.1})
    c, kg = r["co2"], 0.021
    assert c["material"] == pytest.approx(kg * 6.5 / 0.97 + kg * 6.5 * 50 / 10000, abs=1e-6)
    kwh = 14 * (1 / PPH / 0.97 + 2 / 10000)
    assert c["kwh_per_piece"] == pytest.approx(kwh, abs=1e-6)
    assert c["energy"] == pytest.approx(kwh * 0.3, abs=1e-6)
    assert c["transport"] == pytest.approx(20 / 1e6 * 300 * 0.1, abs=2e-6)
    assert c["per_lot_kg"] == pytest.approx(c["total"] * 10000, abs=0.01)
    assert r["unit_price"] == compute({**BASE, "startup_scrap_pcs": 50})["unit_price"]  # CO₂ ändert den Preis nicht


def test_nachkalkulation_ampel():
    plan = compute(BASE)
    settings = {"nk_green_pct": 3, "nk_red_pct": 10}
    _, gruen = post_calculate(BASE, plan, {"cycle_time_s": 30}, settings)
    assert gruen == "gruen"
    res, rot = post_calculate(BASE, plan, {"cycle_time_s": 40, "scrap_pct": 8}, settings)
    assert rot == "rot" and res["deviation_sk_pct"] > 10


def test_maschinenstundensatz_herleitung():
    m = {"available_hours_year": 6000, "acquisition_value": 190000, "useful_life_years": 10, "interest_pct": 6,
         "floor_space_m2": 24, "power_kw": 14, "other_fixed_cost_year": 3500, "allocation_cost_year": 60000,
         "maintenance_cost_year": 24000}
    r = machine_rate(m, {"space_cost_m2_year": 90, "energy_price_kwh": 0.2})
    hand = (19000 + 190000 / 2 * 0.06 + 24 * 90 + 3500 + 60000) / 6000 + 14 * 0.2
    assert r["hourly_rate"] == pytest.approx(hand, abs=0.01)
    assert r["maintenance_rate"] == pytest.approx(4.0, abs=0.01)


def test_artikelanalyse_schliesskraft():
    r = analyze({"material_family": "PA6", "projected_area_cm2": 40, "wall_max_mm": 2.5, "wall_min_mm": 1.5,
                 "flow_length_mm": 120}, {"cavities": 4, "machine_id": 1},
                [{"id": 1, "name": "110t", "clamping_force_t": 110}, {"id": 2, "name": "250t", "clamping_force_t": 250}])
    assert r["clamping_force_t"] == pytest.approx(40 * 4 * 500 / 1000 * 1.2, abs=0.1)
    assert r["suitable_machines"][0]["id"] == 1
    a = 0.12
    cool = 2.5 ** 2 / (math.pi ** 2 * a) * math.log(8 / math.pi ** 2 * (270 - 80) / (160 - 80))
    assert r["cooling_time_s"] == pytest.approx(cool, abs=0.1)


def test_weitere_arbeitsgaenge_montagelinie():
    op = {"name": "Montagelinie", "rate_h": 25, "maintenance_h": 2, "cycle_s": 12, "parts_per_cycle": 1,
          "productivity_pct": 90, "operator_factor": 2, "labor_rate_h": 34, "setup_h": 0.5, "setup_persons": 1, "power_kw": 6}
    base = compute(BASE)
    r = compute({**BASE, "operations": [op, {**op, "name": "Prüfung", "cycle_s": 6}]})
    pph = 3600 / 12 * 0.9
    hand = (25 + 2 + 34 * 2) / pph + 0.5 * (27 + 34) / BASE["lot_size"]
    assert r["operations"][0]["cost"] == pytest.approx(hand, abs=2e-6)
    assert r["operations"][0]["hours_year"] == pytest.approx(BASE["annual_volume"] / pph + BASE["annual_volume"] / BASE["lot_size"] * 0.5, abs=0.1)
    assert r["operations_cost"] == pytest.approx(r["operations"][0]["cost"] + r["operations"][1]["cost"], abs=2e-6)
    assert r["unit_price"] > base["unit_price"]
    assert sum(1 for l in r["lines"] if l["key"].startswith("op_")) == 2


def test_zukaufteile_liste_mit_co2():
    items = [{"name": "Buchse M4", "qty": 2, "price_per_piece": 0.045, "co2_kg_per_piece": 0.004},
             {"name": "Clip", "qty": 1, "price_per_piece": 0.032, "co2_kg_per_piece": 0.006}]
    r = compute({**BASE, "purchased_parts": 0.01, "purchased_items": items})
    assert r["values"]["purchased"] == pytest.approx(0.09 + 0.032 + 0.01, abs=2e-6)
    r0 = compute({**BASE, "purchased_parts": 0.01})
    assert r["co2"]["purchased"] - r0["co2"]["purchased"] == pytest.approx(0.014, abs=1e-6)
    assert r["co2"]["active"]


def test_zukaufteile_eigener_mgk_satz():
    items = [{"name": "Buchse", "qty": 2, "price_per_piece": 0.05}]
    r = compute({**BASE, "purchased_items": items, "purchased_mgk_pct": 2})
    assert r["values"]["mgk_purchased"] == pytest.approx(0.1 * 0.02, abs=2e-6)
    assert r["values"]["mgk"] == pytest.approx((20 + 4 / 4) / 1000 * 3.0 * 0.06, abs=2e-6)
    # ohne eigenen Satz: eine gemeinsame MGK-Zeile wie bisher
    r2 = compute({**BASE, "purchased_items": items})
    assert r2["values"]["mgk_purchased"] == 0
    assert r2["values"]["mgk"] == pytest.approx(((20 + 4 / 4) / 1000 * 3.0 + 0.1) * 0.06, abs=2e-6)


def test_nebenkalkulation_teure_zukaufteile():
    item = {"name": "Platine", "qty": 1, "price_per_piece": 4.0, "co2_kg_per_piece": 0.5}
    side = {"side_mgk_pct": 3, "side_quality_pct": 1, "side_scrap_pct": 1, "side_markup_pct": 2}
    r = compute({**BASE, **side, "purchased_items": [{**item, "side": True}]})
    sk_side = 4.0 * (1 + 0.03 + 0.01) / 0.99
    assert r["purchased_side"]["self_cost"] == pytest.approx(sk_side, abs=2e-6)
    # Hauptkalkulation unverändert, Nebenkalkulation nur mit eigenen Zuschlägen obenauf
    assert r["unit_price"] == pytest.approx(0.315 + sk_side * 1.02, abs=1e-4)
    assert r["values"]["purchased"] == 0
    full = compute({**BASE, "purchased_items": [item]})
    assert full["unit_price"] > r["unit_price"]
    assert r["co2"]["purchased"] == pytest.approx(0.5, abs=1e-6)


def test_personal_handling_automatisierung_und_ruesten():
    staff = {"handling_pct": 25, "handling_rate_h": 34, "automation_pct": 10, "automation_rate_h": 55,
             "setup_staff_min": 90, "automation_setup_min": 10}
    r = compute({**BASE, **staff})
    assert r["values"]["labor_handling"] == pytest.approx(34 * 0.25 / PPH, abs=2e-6)
    assert r["values"]["labor_automation"] == pytest.approx(55 * 0.10 / PPH, abs=2e-6)
    b = r["setup_breakdown"]
    assert b["machine"] == pytest.approx(2 * (45 + 5), abs=0.01)
    assert b["setter"] == pytest.approx(1.5 * 48, abs=0.01)
    assert b["automation"] == pytest.approx(10 / 60 * 55, abs=0.01)
    assert r["values"]["setup"] == pytest.approx((100 + 72 + 55 / 6) / 10000, abs=2e-6)
    # ohne Angaben: Einrichter über die gesamte Rüstzeit wie bisher
    assert compute(BASE)["setup_breakdown"]["setter"] == pytest.approx(2 * 48, abs=0.01)
    assert compute({**BASE, "operator_factor": 1.2})["values"]["labor"] == pytest.approx(38 * 1.2 / PPH, abs=2e-6)


def test_jahresabschlaege_vorab_eingerechnet():
    r = compute({**BASE, "project_years": 3, "price_reductions": [2, 3]})
    f = [1, 0.98, 0.97]
    k = 3 / sum(f)
    assert [y["price"] for y in r["price_years"]] == pytest.approx([round(0.315 * k * x, 4) for x in f], abs=1e-4)
    assert sum(y["price"] for y in r["price_years"]) / 3 == pytest.approx(0.315, abs=1e-4)  # Ø = kalkulierter Preis
    assert r["preload_pct"] == pytest.approx((k - 1) * 100, abs=0.01)
    # fortlaufend ggü. Vorjahr, ohne Vorab-Einrechnung
    r2 = compute({**BASE, "project_years": 3, "price_reductions": [2, 3], "price_reductions_basis": "vorjahr",
                  "price_reductions_preload": False})
    assert r2["price_years"][0]["price"] == 0.315
    assert r2["price_years"][2]["price"] == pytest.approx(0.315 * 0.98 * 0.97, abs=1e-4)


def test_jahresabschlaege_zukaufteile_eigener_satz():
    side = {"purchased_items": [{"name": "LP", "qty": 1, "price_per_piece": 4.0, "side": True}], "project_years": 3,
            "price_reductions": [2, 3], "side_price_reductions": [0, 0]}
    r = compute({**BASE, **side})
    assert all(y["side"] == pytest.approx(r["price_side_part"], abs=1e-4) for y in r["price_years"])  # Zukauf ohne Abschlag
    assert r["price_years"][2]["main"] < r["price_years"][0]["main"]


def test_vorserienpreis():
    r = compute({**BASE, "preseries_qty": 500, "preseries_productivity_pct": 60, "preseries_surcharge_pct": 10})
    p = r["preseries"]
    assert p["lot_size"] == 500
    sub = compute({**BASE, "annual_volume": 500, "lot_size": 500, "productivity_pct": 60})
    assert p["unit_price"] == pytest.approx(sub["unit_price"] * 1.1, abs=1e-4)
    assert p["unit_price"] > r["unit_price"]
    assert compute(BASE)["preseries"] is None


def test_preis_jahr1_manuell_ab_jahr2_serienpreis():
    r = compute({**BASE, "project_years": 4, "price_year1_mode": "manuell", "price_year1_manual": 0.36,
                 "price_reductions": [0, 2, 4], "price_reductions_preload": False})
    p = [y["price"] for y in r["price_years"]]
    assert p == pytest.approx([0.36, 0.315, 0.315 * 0.98, 0.315 * 0.96], abs=1e-4)
    assert r["price_year1"] == 0.36 and r["preload_pct"] == 0
    # ohne Abschläge: Jahr 1 manuell, danach Serienpreis
    r2 = compute({**BASE, "project_years": 3, "price_year1_mode": "manuell", "price_year1_manual": 0.4})
    assert [y["price"] for y in r2["price_years"]] == pytest.approx([0.4, 0.315, 0.315], abs=1e-4)


def test_vorserienpreis_manuell():
    r = compute({**BASE, "preseries_qty": 500, "preseries_price_manual": 1.25})
    p = r["preseries"]
    assert p["manual"] and p["unit_price"] == 1.25 and p["calc_price"] > 0
    assert p["margin_pct"] == pytest.approx((1.25 - p["self_cost"]) / 1.25 * 100, abs=0.1)



def test_abschlaege_vorab_draufschlagen_kein_minusgeschaeft():
    base = {**BASE, "project_years": 4, "price_reductions": [2, 4, 6]}
    f = [1, 0.98, 0.96, 0.94]
    # Ø-neutral: Durchschnitt = kalkulierter Preis
    r = compute(base)
    assert sum(y["price"] for y in r["price_years"]) / 4 == pytest.approx(0.315, abs=1e-4)
    # letztes Jahr: kein Jahr unter dem kalkulierten Preis
    r2 = compute({**base, "price_reductions_preload_mode": "letztes_jahr"})
    assert r2["price_years"][-1]["price"] == pytest.approx(0.315, abs=1e-4)
    assert r2["price_years"][0]["price"] == pytest.approx(0.315 / 0.94, abs=1e-4)
    assert not any(y["below_calc"] for y in r2["price_years"])
    # manueller Anlaufpreis: Vorab-Einrechnung auf die Serienjahre 2 … n
    r3 = compute({**base, "price_reductions": [0, 2, 4], "price_year1_mode": "manuell", "price_year1_manual": 0.4})
    p = [y["price"] for y in r3["price_years"]]
    assert p[0] == 0.4
    assert sum(p[1:]) / 3 == pytest.approx(0.315, abs=1e-4)
    assert r3["price_years"][1]["margin_pct"] == pytest.approx((p[1] - r3["self_cost"]) / p[1] * 100, abs=0.05)
    assert f  # Faktoren zur Dokumentation
