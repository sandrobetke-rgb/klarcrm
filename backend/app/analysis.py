"""
Artikelanalyse / Machbarkeit Spritzguss.

Abschätzungen (Richtwerte, ersetzen keine Füllsimulation):
- Schließkraft [t] = projizierte Fläche je Kavität [cm²] × Fachzahl × Werkzeuginnendruck [bar] / 1000 × Sicherheitsfaktor
  (1 bar auf 1 cm² ≈ 1 kp ≈ 0,001 t)
- Fließweg/Wandstärke-Verhältnis gegen werkstofftypische Grenze
- Kühlzeit [s] ≈ s² / (π² · a) · ln( 8/π² · (T_M − T_W) / (T_E − T_W) )  (Platte, beidseitig gekühlt)
  s = max. Wandstärke [mm], a = Temperaturleitfähigkeit [mm²/s]
- Zykluszeit-Richtwert ≈ Kühlzeit × 1,35 + Nebenzeit
"""
import math

# Werkstoffkennwerte (Richtwerte): Innendruck bar, Fließweg/Wandstärke max., a mm²/s, Massetemp., Werkzeugtemp., Entformungstemp.
MATERIAL_DEFAULTS = {
    "PP":     {"pressure_bar": 300, "flow_ratio_max": 250, "a": 0.085, "t_melt": 230, "t_mold": 40, "t_eject": 100},
    "ABS":    {"pressure_bar": 400, "flow_ratio_max": 180, "a": 0.100, "t_melt": 240, "t_mold": 60, "t_eject": 95},
    "PC/ABS": {"pressure_bar": 450, "flow_ratio_max": 150, "a": 0.110, "t_melt": 260, "t_mold": 70, "t_eject": 105},
    "PC":     {"pressure_bar": 550, "flow_ratio_max": 120, "a": 0.120, "t_melt": 300, "t_mold": 90, "t_eject": 130},
    "PA6":    {"pressure_bar": 500, "flow_ratio_max": 160, "a": 0.120, "t_melt": 270, "t_mold": 80, "t_eject": 160},
    "PA66":   {"pressure_bar": 550, "flow_ratio_max": 150, "a": 0.120, "t_melt": 290, "t_mold": 85, "t_eject": 170},
    "POM":    {"pressure_bar": 500, "flow_ratio_max": 150, "a": 0.090, "t_melt": 205, "t_mold": 90, "t_eject": 140},
    "PBT":    {"pressure_bar": 500, "flow_ratio_max": 150, "a": 0.110, "t_melt": 260, "t_mold": 70, "t_eject": 150},
    "TPE":    {"pressure_bar": 250, "flow_ratio_max": 200, "a": 0.090, "t_melt": 210, "t_mold": 30, "t_eject": 70},
    "sonstiges": {"pressure_bar": 400, "flow_ratio_max": 150, "a": 0.100, "t_melt": 250, "t_mold": 60, "t_eject": 110},
}

CHECKLIST = [
    ("drawing", "Zeichnung / 3D-Daten vollständig"),
    ("draft", "Entformungsschrägen ausreichend"),
    ("undercuts", "Hinterschnitte / Schieber / Kernzüge"),
    ("inserts", "Einlegeteile / Umspritzen"),
    ("tolerances", "Toleranzen erreichbar"),
    ("surface", "Oberfläche / Narbung / Sichtteil"),
    ("wall", "Wandstärken gleichmäßig (Einfallstellen, Verzug)"),
    ("gate", "Anspritzpunkt / Werkzeugkonzept (Kalt-/Heißkanal)"),
    ("material", "Materialfreigabe / Normen (UL, Lebensmittel, Automotive)"),
    ("assembly", "Montage / Nachbearbeitung / Bedrucken"),
    ("testing", "Prüfmittel / Messkonzept"),
    ("packaging", "Verpackung / Logistik"),
]


def _f(v, d=0.0):
    try:
        return float(v) if v not in (None, "") else float(d)
    except (TypeError, ValueError):
        return float(d)


def analyze(a: dict, inputs: dict, machines: list[dict]) -> dict:
    a = a or {}
    family = a.get("material_family") or "sonstiges"
    md = {**MATERIAL_DEFAULTS.get(family, MATERIAL_DEFAULTS["sonstiges"]), **{k: a[k] for k in (
        "pressure_bar", "flow_ratio_max", "a", "t_melt", "t_mold", "t_eject") if a.get(k) not in (None, "")}}
    cav = max(_f(inputs.get("cavities"), 1), 1)
    area = _f(a.get("projected_area_cm2"))
    # REV02-04: ohne CAD-Wert Schätzung aus Länge × Breite (umschließendes Rechteck, eher zu hoch → Schließkraft sicher)
    length, width = _f(a.get("length_mm")), _f(a.get("width_mm"))
    area_est = round(length * width / 100, 1) if length > 0 and width > 0 else 0.0
    area_estimated = area <= 0 and area_est > 0
    if area_estimated:
        area = area_est
    safety = _f(a.get("safety_factor"), 1.2)
    force_t = area * cav * _f(md["pressure_bar"]) / 1000 * safety
    wall_max, wall_min = _f(a.get("wall_max_mm")), _f(a.get("wall_min_mm"))
    flow = _f(a.get("flow_length_mm"))
    flow_ratio = flow / wall_min if wall_min > 0 else 0
    issues, hints = [], []

    cooling = cycle_est = 0.0
    if wall_max > 0:
        tm, tw, te = _f(md["t_melt"]), _f(md["t_mold"]), _f(md["t_eject"])
        if te > tw and tm > tw:
            cooling = wall_max ** 2 / (math.pi ** 2 * _f(md["a"])) * math.log(8 / math.pi ** 2 * (tm - tw) / (te - tw))
            cooling = max(cooling, 0)
            cycle_est = cooling * 1.35 + _f(a.get("handling_time_s"), 4)
    cycle_in = _f(inputs.get("cycle_time_s"))
    if cycle_est and cycle_in and cycle_in < cycle_est * 0.8:
        issues.append(f"Kalkulierte Zykluszeit {cycle_in:g} s liegt deutlich unter dem Richtwert {cycle_est:.1f} s.")
    if flow_ratio and flow_ratio > _f(md["flow_ratio_max"]):
        issues.append(f"Fließweg/Wandstärke {flow_ratio:.0f} über Richtwert {md['flow_ratio_max']:g} – Füllung kritisch, Anspritzpunkte prüfen.")
    if wall_max and wall_min and wall_max / wall_min > 2:
        hints.append("Wandstärkensprung > 1:2 – Einfallstellen/Verzug möglich.")
    if wall_max > 4:
        hints.append("Wandstärke > 4 mm – lange Kühlzeit, Lunker/Einfallstellen prüfen.")

    active = [m for m in machines if m.get("active", True) and m.get("clamping_force_t")]
    suitable = sorted([m for m in active if _f(m["clamping_force_t"]) >= force_t], key=lambda m: _f(m["clamping_force_t"]))
    max_force = max([_f(m["clamping_force_t"]) for m in active], default=0)
    selected = next((m for m in machines if m["id"] == inputs.get("machine_id")), None)
    selected_ok = None
    if selected and selected.get("clamping_force_t") and force_t:
        selected_ok = _f(selected["clamping_force_t"]) >= force_t
        if not selected_ok:
            (hints if area_estimated else issues).append(
                f"Gewählte Maschine ({_f(selected['clamping_force_t']):g} t) zu klein – benötigt ca. {force_t:.0f} t"
                + (" (mit geschätzter Fläche – genaue Fläche aus CAD eintragen)." if area_estimated else "."))
        elif _f(selected["clamping_force_t"]) > force_t * 3 and suitable and suitable[0]["id"] != selected["id"]:
            hints.append(f"Gewählte Maschine ist deutlich überdimensioniert – {suitable[0]['name']} würde reichen (niedrigerer Stundensatz).")
    capacity_ok = True
    if force_t and active and force_t > max_force:
        if area_estimated:   # REV02-04: Schätzung (Rechteck) ist eher zu hoch → kein „nicht herstellbar“ allein daraus
            hints.append(f"Mit geschätzter Fläche ≥ {force_t:.0f} t nötig (größte Maschine {max_force:g} t) – genaue Fläche aus CAD eintragen.")
        else:
            capacity_ok = False
            issues.append(f"Keine Maschine mit ≥ {force_t:.0f} t vorhanden (größte: {max_force:g} t).")

    checks = a.get("checklist") or {}
    critical = [lbl for key, lbl in CHECKLIST if (checks.get(key) or {}).get("status") == "kritisch"]
    open_ = [lbl for key, lbl in CHECKLIST if (checks.get(key) or {}).get("status") in (None, "", "offen")]
    if critical:
        issues.append("Kritische Punkte: " + ", ".join(critical))

    if not capacity_ok:
        suggestion = "nicht_herstellbar"
    elif any(i for i in issues):
        suggestion = "anpassungen_erforderlich"
    elif hints or open_:
        suggestion = "bedingt_herstellbar"
    else:
        suggestion = "herstellbar"

    return {
        "material_family": family, "material_params": md,
        "clamping_force_t": round(force_t, 1),
        "projected_area_cm2": round(area, 1), "projected_area_est_cm2": area_est, "area_estimated": area_estimated,
        "force_formula": f"{area:,.1f} cm² × Fachzahl {cav:g} × {_f(md['pressure_bar']):g} bar ÷ 1000 × {safety:g} = {force_t:,.1f} t"
                         .replace(",", "X").replace(".", ",").replace("X", "."),
        "flow_ratio": round(flow_ratio, 1), "flow_ratio_max": md["flow_ratio_max"],
        "cooling_time_s": round(cooling, 1), "cycle_estimate_s": round(cycle_est, 1),
        "suitable_machines": [{"id": m["id"], "name": m["name"], "number": m.get("number"),
                               "clamping_force_t": m["clamping_force_t"], "hourly_rate": m.get("hourly_rate")} for m in suitable],
        "selected_machine_ok": selected_ok, "capacity_ok": capacity_ok,
        # Vorschlag Maschinengröße (REV01-P03): kleinste passende Maschine bzw. nötige Schließkraftklasse
        "suggested_machine": ({"id": suitable[0]["id"], "name": suitable[0]["name"], "clamping_force_t": suitable[0]["clamping_force_t"]}
                              if suitable else None),
        "suggested_size_t": next((c for c in (25, 50, 80, 100, 150, 200, 250, 300, 400, 500, 650, 800, 1000, 1300, 1600, 2000)
                                  if c >= force_t), round(force_t)),
        "issues": issues, "hints": hints, "open_checks": len(open_), "critical_checks": len(critical),
        "suggestion": suggestion,
        "checklist_items": [{"key": k, "label": l} for k, l in CHECKLIST],
        "families": list(MATERIAL_DEFAULTS.keys()),
    }
