"""v1.33 Block 1 Kalkulation rechnen – Handrechnungen."""
from app.calc_engine import DEFAULT_INPUTS, _tier_price, compute, peak_revenue

BASE = dict(DEFAULT_INPUTS, part_weight_g=20, material_price_kg=2.5, machine_rate_h=40, cycle_time_s=30, cavities=2,
            scrap_pct=0, regrind_pct=0, sprue_weight_g=0)


def test_tier_price_picks_reached_tier_and_lowest_below():
    t = [{"qty": 10000, "price": 0.12}, {"qty": 50000, "price": 0.09}]
    assert _tier_price(0.15, t, 60000, "qty")["price"] == 0.09
    assert _tier_price(0.15, t, 20000, "qty")["price"] == 0.12
    assert _tier_price(0.15, t, 5000, "qty")["price"] == 0.12      # unter kleinster Staffel gilt deren Preis
    assert _tier_price(0.15, [], 5000, "qty")["price"] == 0.15     # ohne Staffeln Grundpreis


def test_tier_hint_when_bigger_quantity_is_cheaper():
    # Bedarf 4.800 kg à 2,00 = 9.600 €; Staffel ab 5.000 kg à 1,80 = 9.000 € → 600 € günstiger, 200 kg mehr
    h = _tier_price(2.5, [{"kg": 1000, "price": 2.0}, {"kg": 5000, "price": 1.8}], 4800, "kg")["hint"]
    assert h == {"qty": 5000, "price": 1.8, "cost_now": 9600.0, "cost_alt": 9000.0, "saves": 600.0, "extra": 200.0}


def test_purchased_tier_by_annual_need():
    r = compute(dict(BASE, annual_volume=15000, purchased_items=[
        {"name": "Buchse", "qty": 4, "price_per_piece": 0.15, "tiers": [{"qty": 10000, "price": 0.12}, {"qty": 50000, "price": 0.09}]}]))
    p = r["purchased_items"][0]
    assert p["need_year"] == 60000 and p["price_per_piece"] == 0.09 and abs(p["cost"] - 0.36) < 1e-9


def test_material_tier_need_kg():
    # 20 g, kein Anguss/Ausschuss, 100.000 Stk → 2.000 kg → Staffel ab 1.000 kg = 2,00 €/kg
    r = compute(dict(BASE, annual_volume=100000, material_tiers=[{"kg": 1000, "price": 2.0}, {"kg": 5000, "price": 1.8}]))
    assert r["material_purchase"]["need_kg"] == 2000.0 and r["material_purchase"]["price_kg"] == 2.0


def test_years_default_equal_annual_and_peak_unchanged():
    r = compute(dict(BASE))
    assert len(r["years"]) == 5 and all(y["qty"] == 100000 for y in r["years"])
    assert abs(peak_revenue(r) - r["annual_revenue"]) < 0.06


def test_year_volumes_and_amortisation_over_sum():
    r = compute(dict(BASE, annual_volume=50000, year_volumes=[20000, 60000, 60000, 60000, 60000],
                     one_time=[{"label": "Werkzeug", "cost": 26000, "price": 26000, "amortize": True}]))
    assert [y["qty"] for y in r["years"]] == [20000, 60000, 60000, 60000, 60000]
    assert r["amortization_quantity"] == 260000          # Summe der Jahresmengen statt 50.000 × 5
    assert abs(r["amortization_per_piece"] - 0.1) < 1e-9
    assert peak_revenue(r) == r["years"][1]["revenue"]   # stärkstes Jahr
    assert r["years"][1]["lot_suggestion"] == 5000 and r["years"][0]["lot_suggestion"] is None
