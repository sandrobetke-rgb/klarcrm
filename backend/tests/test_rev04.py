"""REV04: Kalkulation gilt als berechnet (Schrittleiste), Prüfpunkte und Überholt-Zuordnung, Softwarestand."""
from types import SimpleNamespace

from app.models import Calculation
from app.rev01 import CHECKS, ITEMS, SUPERSEDED
from app.version import APP_VERSION, RELEASES


def _calc(cur, inputs):
    return SimpleNamespace(current_version=cur, versions=[SimpleNamespace(version_no=cur, inputs=inputs)])


def test_empty_first_version_is_not_calculated():
    assert Calculation.is_calculated.fget(_calc(1, {"part_weight_g": 0})) is False


def test_first_version_with_weight_is_calculated():
    assert Calculation.is_calculated.fget(_calc(1, {"part_weight_g": 12.5})) is True
    assert Calculation.is_calculated.fget(_calc(1, {"components": [{"part_weight_g": 3}]})) is True
    assert Calculation.is_calculated.fget(_calc(2, {})) is True


def test_checks_reference_existing_items_in_order():
    codes = {i[0] for i in ITEMS}
    assert set(CHECKS) <= codes
    orders = sorted(c[1] for c in CHECKS.values() if c[0] == APP_VERSION)
    assert orders == list(range(1, len(orders) + 1))
    assert all(c[2].startswith("/") and c[3] and c[4] for c in CHECKS.values())


def test_superseded_points_to_known_items():
    codes = {i[0] for i in ITEMS}
    assert set(SUPERSEDED) <= codes and set(SUPERSEDED.values()) <= codes


def test_version_is_first_release():
    assert RELEASES[0][0] == APP_VERSION
