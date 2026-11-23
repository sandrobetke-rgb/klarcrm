"""REV02-04: geschätzte projizierte Fläche und Schließkraft."""
from app.analysis import analyze


def test_area_estimated_from_length_width():
    r = analyze({"length_mm": 600, "width_mm": 130, "material_family": "PC/ABS", "safety_factor": 1.2}, {"cavities": 1}, [])
    assert r["area_estimated"] is True
    assert r["projected_area_cm2"] == 780.0          # 600 × 130 ÷ 100
    assert "780,0 cm²" in r["force_formula"]


def test_cad_area_overrides_estimate():
    r = analyze({"length_mm": 600, "width_mm": 130, "projected_area_cm2": 390}, {"cavities": 2}, [])
    assert r["area_estimated"] is False
    assert r["projected_area_cm2"] == 390.0


def test_estimated_area_never_says_not_manufacturable():
    machines = [{"id": 1, "name": "M", "clamping_force_t": 100, "active": True, "kind": "spritzguss"}]
    r = analyze({"length_mm": 900, "width_mm": 600}, {"cavities": 4}, machines)
    assert r["suggestion"] != "nicht_herstellbar"
