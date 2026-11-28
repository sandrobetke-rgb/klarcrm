"""v1.34 Block 1 Teil 2 „Zusatzblätter“ je Artikel (Kalkulation):

- Werkzeugblatt (REV01-C06): Kosten, Heißkanal/Fühler, Termine FOT/Baumuster/EMPB/PPAP in Wochen, SOP, Standzeit,
  Vergleich Werkzeugangebote WZB 1–4; Übernahme in die Einmalkosten; Termine ins Angebot.
- Risikoanalyse (REV01-C08): 13 Fragen ja/nein, Anteil „ja“ → hoch > 60 % / mittel 35–60 % / niedrig < 35 %,
  getrennt für Fertigungsprozess und Lieferkette.
- Neue Anlagen (REV01-C09): Stundensatz wie Maschinenstundensatz (Kap. 6.1) + Overhead, Auslastung, Kapazitätsprüfung.
- Kickoff (REV01-C10): Stand aller Daten bei Auftrag (Schnappschuss), Aufgabe für den Verantwortlichen.
"""
from datetime import date, datetime, timezone

from .calc_engine import _f, machine_rate

# ------------------------------------------------------------------ Risikoanalyse
RISK_QUESTIONS = [
    # key, Frage, Gruppe (prozess | lieferkette)
    ("new_customer", "Neuer Kunde", "lieferkette"),
    ("new_product", "Neues Produkt / neue Produktart für F&R", "prozess"),
    ("new_material", "Neues Material", "prozess"),
    ("new_equipment", "Neue Anlagen erforderlich", "prozess"),
    ("new_technology", "Neue Technologie / neues Verfahren", "prozess"),
    ("automation", "Automatisierung erforderlich", "prozess"),
    ("supply_issues", "Bekannte Lieferschwierigkeiten (Material, Zukaufteile)", "lieferkette"),
    ("quality_issues", "Bekannte Qualitätsprobleme (ähnliche Teile, Kunde)", "prozess"),
    ("new_supplier", "Neuer Lieferant Zukaufteile", "lieferkette"),
    ("contract", "Vertragsbasis unklar / kein Rahmenvertrag", "lieferkette"),
    ("design_changes", "Designänderungen zu erwarten", "prozess"),
    ("source_change", "Source Change (Verlagerung von anderem Lieferanten)", "lieferkette"),
    ("invest", "Invest über 10.000 €", "prozess"),
]
RISK_LEVELS = (("hoch", 60), ("mittel", 35))


def _level(pct: float) -> str:
    return "hoch" if pct > 60 else ("mittel" if pct >= 35 else "niedrig")


def eval_risk(risk: dict | None, invest: float) -> dict:
    """Anteil der mit „ja“ beantworteten Fragen. Invest > 10.000 € wird aus der Kalkulation vorbelegt
    (Werkzeug/Einmalkosten + Invest F&R neuer Anlagen), solange nicht von Hand beantwortet."""
    ans = dict((risk or {}).get("answers") or {})
    auto = {}
    if ans.get("invest") in (None, ""):
        auto["invest"] = invest > 10000
    out, groups = [], {"prozess": [0, 0], "lieferkette": [0, 0]}
    answered = 0
    for key, text, grp in RISK_QUESTIONS:
        v = ans.get(key)
        val = auto.get(key) if v in (None, "") and key in auto else v
        if val in (True, False):
            answered += 1
        yes = val is True
        groups[grp][1] += 1
        groups[grp][0] += 1 if yes else 0
        out.append({"key": key, "text": text, "group": grp, "value": val, "auto": key in auto and v in (None, ""),
                    "note": ((risk or {}).get("notes") or {}).get(key) or ""})
    yes_all = sum(g[0] for g in groups.values())
    pct = round(100 * yes_all / len(RISK_QUESTIONS), 1)
    g = {k: {"yes": y, "count": n, "pct": round(100 * y / n, 1) if n else 0, "level": _level(100 * y / n if n else 0)}
         for k, (y, n) in groups.items()}
    return {"questions": out, "yes": yes_all, "count": len(RISK_QUESTIONS), "answered": answered,
            "complete": answered == len(RISK_QUESTIONS), "pct": pct, "level": _level(pct), "groups": g,
            "measures": (risk or {}).get("measures") or ""}


# ------------------------------------------------------------------ Werkzeugblatt
TOOL_COST_FIELDS = [
    ("design_cnc", "Konstruktion / CNC"),
    ("sampling", "Abmustern / Prüfbericht"),
    ("sensors", "Druck- / Temperaturfühler"),
    ("hot_runner", "Heißkanal"),
    ("external", "Werkzeugkosten extern (Werkzeugbauer)"),
]
TOOL_WEEKS = [("fot", "FOT (erste Teile vom Werkzeug)"), ("sample", "Baumuster / EMPB"), ("ppap", "PPAP")]


def eval_tool(sheet: dict | None, inputs: dict, results: dict) -> dict:
    """Kosten = Summe der Positionen; ist ein Werkzeugangebot (WZB) gewählt, ersetzt es „Werkzeugkosten extern“.
    Marge = Angebotspreis − Kosten. Standzeit: Schüsse über die Laufzeit = Summe Jahresmengen ÷ Fachzahl."""
    s = sheet or {}
    offers = [o for o in (s.get("offers") or []) if isinstance(o, dict)][:4]
    chosen = next((o for o in offers if o.get("chosen")), None)
    costs = {k: _f(s.get(k)) for k, _ in TOOL_COST_FIELDS}
    if chosen:
        costs["external"] = _f(chosen.get("price"))
    total = round(sum(costs.values()), 2)
    price = _f(s.get("offer_price"))
    years = results.get("years") or []
    pieces = sum(_f(y.get("qty")) for y in years) or _f(inputs.get("annual_volume")) * max(_f(inputs.get("project_years"), 1), 1)
    cav = max(_f(inputs.get("cavities"), 1), 1)
    shots = pieces / cav
    life = _f(s.get("tool_life_shots"))
    cheapest = min((o for o in offers if _f(o.get("price")) > 0), key=lambda o: _f(o.get("price")), default=None)
    one_time = [o for o in inputs.get("one_time") or [] if "werkzeug" in (o.get("label") or "").lower()]
    return {"costs": costs, "total": total, "offer_price": price, "margin": round(price - total, 2) if price else None,
            "margin_pct": round((price - total) / price * 100, 1) if price else None,
            "chosen": chosen.get("supplier") if chosen else None,
            "cheapest": {"supplier": cheapest.get("supplier"), "price": _f(cheapest.get("price"))} if cheapest else None,
            "shots_project": round(shots), "tool_life_shots": life,
            "life_ok": None if not life else shots <= life,
            "life_pct": round(100 * shots / life, 1) if life else None,
            "in_calc": {"cost": round(sum(_f(o.get("cost")) for o in one_time), 2),
                        "price": round(sum(_f(o.get("price")) or _f(o.get("cost")) for o in one_time), 2)},
            "weeks": {k: _f(s.get(f"weeks_{k}")) or None for k, _ in TOOL_WEEKS}}


def apply_tool(sheet: dict, inputs: dict) -> dict:
    """Werkzeugkosten und Angebotspreis als Einmalkosten „Werkzeug“ in die Kalkulation (eine Zeile, Amortisation bleibt)."""
    ev = eval_tool(sheet, inputs, {})
    rows = [dict(o) for o in inputs.get("one_time") or []]
    idx = next((n for n, o in enumerate(rows) if "werkzeug" in (o.get("label") or "").lower()), None)
    row = {"label": "Werkzeug (lt. Werkzeugblatt)", "cost": ev["total"], "price": ev["offer_price"] or ev["total"],
           "amortize": bool(rows[idx].get("amortize")) if idx is not None else False}
    if idx is None:
        rows.append(row)
    else:
        rows[idx] = {**rows[idx], **row}
    return {**inputs, "one_time": rows}


# ------------------------------------------------------------------ Neue Anlagen
CAPACITY_CHECKS = [("liquidity", "Liquidität"), ("space", "Fläche"), ("staff", "Personal")]


def eval_equipment(rows: list | None, settings: dict, inputs: dict, results: dict) -> dict:
    """Je neue Anlage: Stundensatz nach Kap. 6.1 (Abschreibung und Zins nur auf den F&R-Anteil des Invests,
    Raum, Energie, Betriebskosten, Instandhaltung) + Overhead-Zuschlag; Stunden je Jahr = Jahresmenge × Zeit je Stück;
    Auslastung = Stunden ÷ verfügbare Stunden."""
    out = []
    annual = _f(inputs.get("annual_volume"))
    years = results.get("years") or []
    peak_qty = max([_f(y.get("qty")) for y in years] + [annual])
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        hours = _f(r.get("available_hours_year"), 6000) or 6000
        avail = min(max(_f(r.get("availability_pct"), 100), 1), 100) / 100
        hours_eff = hours * avail
        t = _f(r.get("time_per_piece_s"))
        need_h = peak_qty * t / 3600
        # Anlage nur für diesen Artikel (Standard): Kosten tragen die Stunden dieses Projekts – sonst verfügbare Stunden
        dedicated = r.get("dedicated", True) not in (False, "false", 0)
        basis_h = min(need_h, hours_eff) if dedicated and need_h > 0 else hours_eff
        m = {"available_hours_year": basis_h, "acquisition_value": _f(r.get("invest_fr")),
             "useful_life_years": _f(r.get("useful_life_years")), "interest_pct": _f(r.get("interest_pct")),
             "floor_space_m2": _f(r.get("floor_space_m2")), "power_kw": _f(r.get("power_kw")),
             "other_fixed_cost_year": _f(r.get("operating_cost_year")), "maintenance_cost_year":
                 _f(r.get("maintenance_pct")) / 100 * (_f(r.get("invest_fr")) + _f(r.get("invest_external")))}
        mr = machine_rate(m, settings)
        base = mr["hourly_rate"] + mr["maintenance_rate"]
        overhead = base * _f(r.get("overhead_pct")) / 100
        rate = round(base + overhead, 2)
        checks = {k: ((r.get("checks") or {}).get(k) or "offen") for k, _ in CAPACITY_CHECKS}
        out.append({"name": r.get("name") or "Neue Anlage", "rate": rate, "parts": mr["parts"], "maintenance_rate": mr["maintenance_rate"],
                    "overhead": round(overhead, 2), "hours_eff": round(hours_eff), "need_hours": round(need_h, 1),
                    "dedicated": dedicated, "basis_hours": round(basis_h, 1),
                    "utilization_pct": round(100 * need_h / hours_eff, 1) if hours_eff else None,
                    "cost_per_piece": round(rate * t / 3600, 4) if t else None,
                    "invest_total": round(_f(r.get("invest_fr")) + _f(r.get("invest_external")), 2),
                    "invest_fr": _f(r.get("invest_fr")), "checks": checks,
                    "checks_ok": all(v == "ja" for v in checks.values()), "checks_open": [k for k, v in checks.items() if v != "ja"]})
    return {"rows": out, "invest_fr": round(sum(x["invest_fr"] for x in out), 2),
            "invest_total": round(sum(x["invest_total"] for x in out), 2)}


def apply_equipment(row_no: int, rows: list, ev: dict, inputs: dict) -> dict:
    """Neue Anlage als Arbeitsgang in die Kalkulation übernehmen (Stundensatz inkl. Instandhaltung/Overhead, Zeit je Stück)."""
    r, e = rows[row_no], ev["rows"][row_no]
    ops = [dict(o) for o in inputs.get("operations") or []]
    name = f"Neue Anlage: {r.get('name') or 'Anlage'}"
    op = {"name": name, "kind": "neue_anlage", "rate_h": e["rate"], "maintenance_h": 0, "cycle_s": _f(r.get("time_per_piece_s")),
          "parts_per_cycle": 1, "productivity_pct": 100, "operator_factor": _f(r.get("operator_factor")),
          "labor_rate_h": _f(inputs.get("labor_rate_h")), "setup_h": 0, "setup_persons": 1, "power_kw": 0}
    idx = next((n for n, o in enumerate(ops) if o.get("name") == name), None)
    if idx is None:
        ops.append(op)
    else:
        ops[idx] = {**ops[idx], **op}
    return {**inputs, "operations": ops}


# ------------------------------------------------------------------ Kickoff
def build_kickoff(calc, ver, user_name: str, settings: dict, reason: str) -> dict:
    """Schnappschuss aller Daten zum Auftrag (wird gespeichert und nicht mehr nachträglich verändert)."""
    i, r = (ver.inputs or {}), (ver.results or {})
    tool = eval_tool(calc.tool_sheet, i, r) if calc.tool_sheet else None
    eq = eval_equipment((calc.equipment or {}).get("rows"), settings, i, r) if calc.equipment else None
    risk = eval_risk(calc.risk, (calc.invest or 0) + (eq["invest_fr"] if eq else 0)) if calc.risk else None
    an = calc.analysis_results or {}
    return {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "created_by": user_name, "reason": reason,
        "calc": {"id": calc.id, "number": calc.number, "version": ver.version_no, "article": calc.article_name,
                 "customer_article_no": calc.customer_article_no, "own_article_no": calc.own_article_no,
                 "customer": calc.account.name if calc.account else None, "contact": f"{calc.contact.first_name or ''} {calc.contact.last_name}".strip() if calc.contact else None,
                 "owner": calc.owner.name if calc.owner else None, "sop_date": calc.sop_date.isoformat() if calc.sop_date else None},
        "commercial": {"unit_price": r.get("unit_price"), "price_per_1000": r.get("price_per_1000"), "margin_pct": r.get("margin_pct"),
                       "annual_volume": r.get("annual_volume"), "lot_size": i.get("lot_size"), "project_years": i.get("project_years"),
                       "years": [{k: y.get(k) for k in ("year", "qty", "lot", "price", "revenue", "machine_hours", "material_kg")} for y in r.get("years") or []],
                       "one_time": r.get("one_time") or [], "incoterm": i.get("incoterm") or "", "transport_mode": i.get("transport_mode")},
        "production": {"machine": i.get("machine_name") or "", "cavities": i.get("cavities"), "cycle_time_s": i.get("cycle_time_s"),
                       "pieces_per_hour": r.get("pieces_per_hour"), "machine_hours_year": r.get("machine_hours_year"),
                       "clamping_force_t": an.get("clamping_force_t"), "suggested_machine": (an.get("suggested_machine") or {}).get("name"),
                       "operations": [{"name": o.get("name"), "pieces_per_hour": o.get("pieces_per_hour"), "hours_year": o.get("hours_year")} for o in r.get("operations") or []],
                       "pack_type": i.get("pack_type") or "", "pack_parts_per_unit": i.get("pack_parts_per_unit"),
                       "family_group": i.get("family_group") or ""},
        "material": {"name": i.get("material_name") or "", "supplier": i.get("material_supplier") or "", "offer_no": i.get("material_offer_no") or "",
                     "part_weight_g": i.get("part_weight_g"), "sprue_weight_g": i.get("sprue_weight_g"), "need_kg": (r.get("material_purchase") or {}).get("need_kg"),
                     "price_kg": (r.get("material_purchase") or {}).get("price_kg"),
                     "masterbatch": {"name": i.get("masterbatch_name") or "", "pct": i.get("masterbatch_pct"), "supplier": i.get("masterbatch_supplier") or ""},
                     "components": [{"label": c.get("label"), "material": c.get("material_name"), "weight_g": c.get("part_weight_g")} for c in i.get("components") or []]},
        "purchased": [{"name": p.get("name"), "part_no": p.get("part_no"), "supplier": p.get("supplier"), "qty": p.get("qty"),
                       "need_year": p.get("need_year"), "price": p.get("price_per_piece")} for p in r.get("purchased_items") or []],
        "tool": {"sheet": calc.tool_sheet or {}, "eval": tool} if tool else None,
        "equipment": {"rows": (calc.equipment or {}).get("rows") or [], "eval": eq} if eq else None,
        "risk": risk,
        "analysis": {"feasibility": calc.feasibility, "note": calc.feasibility_note, "hints": (an.get("issues") or []) + (an.get("hints") or []),
                     "tech_talk": bool((calc.analysis or {}).get("tech_talk"))},
        "co2_g": round(((r.get("co2") or {}).get("cradle_to_gate") or 0) * 1000, 1) or None,
        "open_points": _open_points(calc, tool, risk, eq),
    }


def _open_points(calc, tool, risk, eq) -> list[str]:
    pts = []
    if not calc.tool_sheet:
        pts.append("Werkzeugblatt fehlt (Termine FOT / PPAP)")
    elif tool and not all(tool["weeks"].values()):
        pts.append("Werkzeugblatt: Termine FOT / Baumuster / PPAP unvollständig")
    if tool and tool["life_ok"] is False:
        pts.append(f"Werkzeugstandzeit reicht nicht ({tool['life_pct']} % der Schüsse) – Ersatzwerkzeug einplanen")
    if not calc.sop_date:
        pts.append("SOP-Datum fehlt")
    if not risk or not risk["complete"]:
        pts.append("Risikoanalyse nicht vollständig")
    elif risk["level"] == "hoch":
        pts.append("Risiko hoch – Maßnahmen im Kickoff festlegen")
    if eq:
        for x in eq["rows"]:
            if not x["checks_ok"]:
                lbl = dict(CAPACITY_CHECKS)
                pts.append(f"{x['name']}: Kapazitätsprüfung offen ({', '.join(lbl.get(k, k) for k in x['checks_open'])})")
    if not calc.analysis_results:
        pts.append("Artikelanalyse fehlt")
    return pts


def today_iso() -> str:
    return date.today().isoformat()
