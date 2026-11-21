"""Monatsbericht: Neuumsatz = Spitzenjahr, Zielampel."""
from app.calc_engine import peak_revenue
from app.monthly import target_light


def test_peak_revenue_takes_highest_year():
    # Beispiel aus der Vorgabe: 0,5 / 1,0 / 1,5 Mio. € → 1,5 Mio. € Neuumsatz
    res = {"price_years": [{"revenue": 500_000}, {"revenue": 1_000_000}, {"revenue": 1_500_000}], "annual_revenue": 500_000}
    assert peak_revenue(res) == 1_500_000
    # Spitze in der Mitte (Auslauf)
    assert peak_revenue({"price_years": [{"revenue": 400}, {"revenue": 900}, {"revenue": 300}]}) == 900


def test_peak_revenue_without_years_uses_annual():
    assert peak_revenue({"annual_revenue": 123456.789}) == 123456.79
    assert peak_revenue({}) == 0


def test_target_light():
    assert target_light(1_000_000, 1_000_000) == "gruen"
    assert target_light(900_000, 1_000_000) == "gelb"   # ≥ 85 % vom Soll
    assert target_light(800_000, 1_000_000) == "rot"
