"""Teilbeauftragung (MB-30 … MB-35): Ergebnis je Artikel aus dem Kalkulationsstatus."""
from types import SimpleNamespace as N

from app.routers.quotes import OUTCOMES, _outcome


def test_outcome_mapping():
    assert _outcome(N(status="gewonnen", close_reason=None)) == "gewonnen"
    assert _outcome(N(status="verloren", close_reason="artikelpreis_zu_hoch")) == "verloren"
    assert _outcome(N(status="verloren", close_reason="andere_variante")) == "andere_variante"   # kein Verlust
    assert _outcome(N(status="angeboten", close_reason=None)) == "offen"
    assert set(OUTCOMES) == {"gewonnen", "verloren", "andere_variante", "offen"}
