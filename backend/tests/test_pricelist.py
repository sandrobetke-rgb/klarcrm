"""Preisliste: Handrechnung der Materialdifferenz (Vorlage „Annual Price Inquiry List“, korrigiert)."""
import pytest

from app.pricelist import annual_effect, detect, material_delta, part_delta


def test_material_delta_hand():
    # PA6 GF30: 2,95 → 3,10 €/kg, Schussgewicht 12,5 g, PE 100, MGK 8 %
    # (3,10 − 2,95) × 12,5/1000 × 100 × 1,08 = 0,15 × 1,25 × 1,08 = 0,2025 € je 100 Stk
    assert material_delta(3.10, 2.95, 12.5, 100, 8) == pytest.approx(0.2025)
    # Senkung wird negativ, ohne MGK
    assert material_delta(2.80, 2.95, 12.5, 100, 0) == pytest.approx(-0.1875)
    # ohne Basis oder Gewicht keine Aussage
    assert material_delta(3.10, None, 12.5, 100, 8) == 0
    assert material_delta(3.10, 2.95, None, 100, 8) == 0


def test_part_and_annual():
    # 4 Buchsen je Teil, 0,021 → 0,024 €/Stk, PE 100: 0,003 × 4 × 100 = 1,20 € je 100 Stk
    assert part_delta(0.024, 0.021, 4, 100) == pytest.approx(1.2)
    # Jahreseffekt: 0,2025 €/100 Stk × 120.000 Stk = 243 €
    assert annual_effect(0.2025, 120000, 100) == pytest.approx(243.0)


def test_detect_template_and_generic():
    head = ["Item", "Location \n(ISO Country Code)", "Part Number of Contract Product", "", "Part Description", "x", "Price Unit",
            "Contract Price 2026", "Currency", "y", "Currency", "Country", "MOQ", "Comment", "Shot Weight [g/pc]",
            "Part/ Net Weight [g/pc]", "F&R Mat\nNumber", "Resin - Type - Grade - Name"]
    i, mp, tpl = detect([["Annual Price Inquiry List Year 2027"], [], head], [])
    assert tpl and i == 2 and mp["2"] == "customer_part_no" and mp["7"] == "price" and mp["16"] == "mat1_number"
    from app.pricelist import ART_FIELDS
    i, mp, tpl = detect([["Kunde", "Artikel-Nr. F&R", "Preis je PE", "Material"]], [(k, l, a) for k, l, a in ART_FIELDS])
    assert not tpl and mp == {"0": "account", "1": "article_no", "2": "price", "3": "mat1_name"}
