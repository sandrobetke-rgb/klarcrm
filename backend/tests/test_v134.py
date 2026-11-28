"""v1.34 Zusatzblätter – Handrechnungen."""
from app.sheets import RISK_QUESTIONS, apply_tool, eval_equipment, eval_risk, eval_tool

ST = {"space_cost_m2_year": 90.0, "energy_price_kwh": 0.20}


def test_risk_levels_and_invest_auto():
    yes = {q[0]: True for q in RISK_QUESTIONS[:8]}            # 8 von 13 = 61,5 % → hoch
    e = eval_risk({"answers": yes}, 0)
    assert e["pct"] == 61.5 and e["level"] == "hoch"
    e = eval_risk({"answers": {"new_customer": True}}, 15000)  # Invest automatisch ja → 2 / 13 = 15,4 %
    assert e["yes"] == 2 and e["level"] == "niedrig" and not e["complete"]
    e = eval_risk({"answers": {q[0]: (n < 5) for n, q in enumerate(RISK_QUESTIONS)}}, 0)   # 5/13 = 38,5 %
    assert e["level"] == "mittel" and e["complete"]


def test_tool_sheet_costs_and_chosen_offer():
    s = {"design_cnc": 8000, "sampling": 3000, "external": 60000, "offer_price": 90000, "tool_life_shots": 100000,
         "offers": [{"supplier": "A", "price": 58000}, {"supplier": "B", "price": 49000, "chosen": True}]}
    e = eval_tool(s, {"annual_volume": 50000, "project_years": 5, "cavities": 2}, {})
    assert e["total"] == 60000 and e["margin"] == 30000          # 8.000 + 3.000 + 49.000 (gewählt)
    assert e["shots_project"] == 125000 and e["life_ok"] is False  # 250.000 Stk ÷ 2-fach > 100.000 Schuss
    inp = apply_tool(s, {"one_time": [{"label": "Werkzeug 2-fach", "cost": 1, "price": 1, "amortize": True}]})
    assert inp["one_time"][0]["cost"] == 60000 and inp["one_time"][0]["price"] == 90000 and inp["one_time"][0]["amortize"]


def test_equipment_rate_dedicated_vs_shared():
    row = {"name": "US", "invest_fr": 100000, "useful_life_years": 10, "interest_pct": 0, "available_hours_year": 5000,
           "availability_pct": 100, "time_per_piece_s": 36, "overhead_pct": 10}
    inp = {"annual_volume": 100000}
    # nur für diesen Artikel: 100.000 × 36 s = 1.000 h; AfA 10.000 €/a ÷ 1.000 h = 10 €/h + 10 % = 11 €/h
    e = eval_equipment([row], ST, inp, {})["rows"][0]
    assert e["need_hours"] == 1000 and e["rate"] == 11.0 and e["utilization_pct"] == 20.0
    e = eval_equipment([{**row, "dedicated": False}], ST, inp, {})["rows"][0]   # auch für andere: ÷ 5.000 h = 2 + 10 %
    assert e["rate"] == 2.2
