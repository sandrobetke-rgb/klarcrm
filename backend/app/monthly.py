"""Monatsbericht für Geschäftsführung und Gesellschafter (Wunsch 21.11.2026).

Vertriebsziel = **Neuumsatz**: gewonnene Artikel (Kalkulationen) mit Abschlussdatum closed_at, gemessen am Umsatz des
**stärksten Lieferjahres** (peak_revenue, z. B. 0,5 / 1,0 / 1,5 Mio. € → 1,5 Mio. €), dazu Werkzeug-/Einmalumsatz.
Gewonnene Leads ohne Artikel zählen mit ihrem Volumen als Serienumsatz.
Zielerreichung: Ist seit Jahresbeginn gegen Jahresziel; Soll zum Stichtag = Ziel × Anteil der abgelaufenen Monate.
Ampel: Ist ≥ Soll grün · ≥ 85 % des Solls gelb · darunter rot.
"""
import calendar
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .inquiry import workdays_between
from .models import (Activity, Calculation, CalculationVersion, CLOSED_STAGES, Opportunity, PriceChange, Quote,
                     SalesTarget, User)

MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]


def month_range(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def target_light(actual: float, expected: float) -> str | None:
    if not expected:
        return None
    r = actual / expected
    return "gruen" if r >= 1 else "gelb" if r >= 0.85 else "rot"


def _won_rows(db: Session, start: date, end: date) -> list[dict]:
    """Gewonnene Artikel und Leads ohne Artikel im Zeitraum."""
    out = []
    calcs = db.scalars(select(Calculation).where(Calculation.status == "gewonnen", Calculation.closed_at >= start,
                                                 Calculation.closed_at <= end)).unique().all()
    for c in calcs:
        ver = next((v for v in c.versions if v.version_no == c.current_version), None)
        mid = (ver.inputs or {}).get("machine_id") if ver else None
        out.append({"type": "artikel", "id": c.id, "number": c.number, "name": c.article_name,
                    "account": c.account.name if c.account else None, "owner_id": c.owner_id,
                    "owner": c.owner.name if c.owner else None, "annual": c.peak_revenue if c.peak_revenue is not None else (c.annual_revenue or 0),
                    "first_year": c.annual_revenue or 0, "one_time": c.one_time_revenue or 0, "date": c.closed_at, "sop": c.sop_date, "machine_id": mid, "site_id": c.site_id,
                    "machine_hours": float((ver.results or {}).get("machine_hours_year") or 0) if ver else 0,
                    "inquiry": c.opportunity.number if c.opportunity else None, "inquiry_id": c.opportunity_id})
    with_calcs = {c.opportunity_id for c in db.scalars(select(Calculation).where(Calculation.opportunity_id.isnot(None))).unique()}
    for o in db.scalars(select(Opportunity).where(Opportunity.stage == "gewonnen", Opportunity.closed_at >= start,
                                                  Opportunity.closed_at <= end)).unique().all():
        if o.id in with_calcs:
            continue
        out.append({"type": "lead", "id": o.id, "number": o.number, "name": o.name, "account": o.account.name if o.account else None,
                    "owner_id": o.owner_id, "owner": o.owner.name if o.owner else None, "annual": float(o.amount or 0), "first_year": float(o.amount or 0), "one_time": 0,
                    "date": o.closed_at, "sop": None, "machine_id": None, "site_id": None, "machine_hours": 0,
                    "inquiry": o.number, "inquiry_id": o.id})
    return out


def _sum(rows, key):
    return round(sum(r[key] for r in rows), 2)


def goal_status(db: Session, today: date | None = None) -> dict | None:
    """Stand Vertriebsziel (Neuumsatz, Spitzenjahr) seit 1.1. bis heute – für die Startseite. Soll anteilig nach Kalendertagen."""
    today = today or date.today()
    t = db.scalar(select(SalesTarget).where(SalesTarget.year == today.year, SalesTarget.user_id.is_(None)))
    if not t or not t.revenue_target:
        return None
    rows = _won_rows(db, date(today.year, 1, 1), today)
    ann = _sum(rows, "annual")
    days = (date(today.year, 12, 31) - date(today.year, 1, 1)).days + 1
    exp = t.revenue_target * today.timetuple().tm_yday / days
    return {"year": today.year, "target": t.revenue_target, "achieved": ann, "count": len(rows),
            "pct": round(100 * ann / t.revenue_target, 1), "expected": round(exp, 2), "light": target_light(ann, exp)}


def compute(db: Session, year: int, month: int) -> dict:
    from .models import Machine  # noqa: PLC0415
    from .routers.calc import REASON_LABELS, utilization  # noqa: PLC0415
    m_start, m_end = month_range(year, month)
    y_start = date(year, 1, 1)
    users = {u.id: u.name for u in db.scalars(select(User)).all()}
    machines = {m.id: m for m in db.scalars(select(Machine)).all()}

    won_month = _won_rows(db, m_start, m_end)
    won_ytd = _won_rows(db, y_start, m_end)

    # ---------------- Ziele
    tg = db.scalars(select(SalesTarget).where(SalesTarget.year == year)).all()
    total_t = next((t for t in tg if t.user_id is None), None)
    frac = month / 12
    def target_block(t, rows):  # noqa: E306
        if not t:
            return None
        ann, one = _sum(rows, "annual"), _sum(rows, "one_time")
        exp = (t.revenue_target or 0) * frac
        return {"target": t.revenue_target, "achieved": ann, "pct": round(100 * ann / t.revenue_target, 1) if t.revenue_target else None,
                "expected": round(exp, 2), "gap": round((t.revenue_target or 0) - ann, 2), "light": target_light(ann, exp),
                "one_time_target": t.one_time_target, "one_time_achieved": one,
                "one_time_pct": round(100 * one / t.one_time_target, 1) if t.one_time_target else None,
                "one_time_light": target_light(one, (t.one_time_target or 0) * frac) if t.one_time_target else None}
    by_owner = []
    owner_ids = sorted({r["owner_id"] for r in won_ytd if r["owner_id"]} | {t.user_id for t in tg if t.user_id})
    for uid in owner_ids:
        t = next((x for x in tg if x.user_id == uid), None)
        rows = [r for r in won_ytd if r["owner_id"] == uid]
        by_owner.append({"user_id": uid, "name": users.get(uid, "?"), "annual": _sum(rows, "annual"), "one_time": _sum(rows, "one_time"),
                         "month": _sum([r for r in won_month if r["owner_id"] == uid], "annual"), "target": target_block(t, rows)})

    # ---------------- Verlauf je Monat (kumuliert) im laufenden Jahr gegen die Ziellinie – kein Vorjahresvergleich
    series = []
    cum = 0.0
    for mm in range(1, 13):
        s, e = month_range(year, mm)
        a = sum(r["annual"] for r in won_ytd if s <= r["date"] <= e) if mm <= month else None
        if a is not None:
            cum += a
        series.append({"month": mm, "label": MONTHS[mm - 1][:3], "won": round(a, 2) if a is not None else None,
                       "cum": round(cum, 2) if a is not None else None,
                       "cum_target": round((total_t.revenue_target or 0) * mm / 12, 2) if total_t else None})

    # ---------------- Verloren / nicht angeboten im Monat
    lost_calcs = db.scalars(select(Calculation).where(Calculation.status.in_(("verloren", "kein_angebot")),
                                                      Calculation.closed_at >= m_start, Calculation.closed_at <= m_end)).unique().all()
    lost, nobid, variants, reasons = [], [], [], {}
    for c in lost_calcs:
        row = {"id": c.id, "number": c.number, "name": c.article_name, "account": c.account.name if c.account else None,
               "annual": c.peak_revenue if c.peak_revenue is not None else (c.annual_revenue or 0), "one_time": c.one_time_revenue or 0,
               "owner": c.owner.name if c.owner else None, "final_round": bool(c.opportunity and c.opportunity.final_round), "inquiry_id": c.opportunity_id}
        if c.status == "verloren" and c.close_reason == "andere_variante":   # kein Verlust (MB-33)
            row["reason"] = "andere Variante beauftragt" + (f": {c.close_note}" if c.close_note else "")
            variants.append(row)
        elif c.status == "verloren":
            row["reason"] = REASON_LABELS.get(c.close_reason, c.close_reason or "ohne Grund") + (f": {c.close_note}" if c.close_note else "")
            lbl = REASON_LABELS.get(c.close_reason, "ohne Grund")
            x = reasons.setdefault(lbl, {"reason": lbl, "count": 0, "annual": 0.0})
            x["count"] += 1
            x["annual"] += row["annual"]
            lost.append(row)
        else:
            row["reason"] = c.decision_note or c.no_bid_note or c.no_bid_reason or "ohne Grund"
            nobid.append(row)
    closed_ytd = db.scalars(select(Calculation).where(Calculation.status.in_(("gewonnen", "verloren")), Calculation.closed_at >= y_start,
                                                      Calculation.closed_at <= m_end)).unique().all()
    closed_ytd = [c for c in closed_ytd if c.close_reason != "andere_variante" or c.status != "verloren"]
    won_n = sum(1 for c in closed_ytd if c.status == "gewonnen")
    final = [c for c in closed_ytd if c.opportunity and c.opportunity.final_round]

    # ---------------- Anfragen, Angebote, Durchlaufzeit, kalkulierte Artikel
    opps = db.scalars(select(Opportunity)).unique().all()
    new_inq = [o for o in opps if o.kind == "anfrage" and o.inquiry_date and m_start <= o.inquiry_date <= m_end]
    sent = db.scalars(select(Quote).where(Quote.sent_at >= m_start, Quote.sent_at <= m_end)).unique().all()
    lead_times = [workdays_between(o.inquiry_date, o.offered_at) for o in opps
                  if o.inquiry_date and o.offered_at and m_start <= o.offered_at <= m_end]
    calc_ids = {v.calculation_id for v in db.scalars(select(CalculationVersion).where(
        CalculationVersion.created_at >= datetime.combine(m_start, datetime.min.time(), tzinfo=timezone.utc),
        CalculationVersion.created_at < datetime.combine(m_end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)))}
    from .routers.calc import get_settings  # noqa: PLC0415
    st = get_settings(db)

    # ---------------- Offene Pipeline
    open_opps = [o for o in opps if o.stage not in CLOSED_STAGES]
    from .models import STAGES  # noqa: PLC0415
    pipeline = [{"stage": s, "count": sum(1 for o in open_opps if o.stage == s), "amount": round(sum(float(o.amount or 0) for o in open_opps if o.stage == s), 2)}
                for s in STAGES if s not in CLOSED_STAGES]
    top_open = sorted(open_opps, key=lambda o: -float(o.amount or 0))[:10]
    n_s, n_e = month_range(m_end.year + (m_end.month // 12), m_end.month % 12 + 1)
    due_next = [o for o in open_opps if o.close_date and n_s <= o.close_date <= n_e]
    big_t = float(st.get("big_revenue_threshold") or 250000)

    def opp_row(o):
        return {"id": o.id, "number": o.number, "name": o.name, "account": o.account.name if o.account else None, "stage": o.stage,
                "amount": float(o.amount or 0), "probability": o.probability, "close_date": o.close_date,
                "owner": o.owner.name if o.owner else None, "big": float(o.amount or 0) >= big_t}

    # ---------------- Handlungsbedarf (Stand jetzt)
    from .inquiry import followup_light  # noqa: PLC0415
    today = date.today()
    fus = db.scalars(select(Activity).where(Activity.kind == "angebotsverfolgung", Activity.done.is_(False))).unique().all()
    red = [{"id": a.id, "quote": a.quote.number if a.quote else None, "quote_id": a.quote_id, "account": a.account.name if a.account else None,
            "due": a.due_at.date() if a.due_at else None, "owner": a.owner.name if a.owner else None, "attempts": a.attempts or 0}
           for a in fus if followup_light(a.due_at) == "rot"]
    open_calcs = db.scalars(select(Calculation).where(Calculation.status.notin_(("gewonnen", "verloren", "kein_angebot", "zurueckgestellt")))).unique().all()
    undecided = [{"id": c.id, "number": c.number, "name": c.article_name, "account": c.account.name if c.account else None,
                  "since": c.inquiry_date, "inquiry_id": c.opportunity_id} for c in open_calcs if c.decision is None and c.opportunity_id]
    overdue_due = [opp_row(o) for o in open_opps if o.due_date and o.due_date < today and o.stage in ("neue_anfrage", "qualifiziert")]
    approvals = [{"id": c.id, "number": c.number, "name": c.article_name, "reasons": c.approval_reasons, "status": c.approval_status}
                 for c in open_calcs if c.approval_reasons and not c.is_approved and c.status in ("kalkulation", "anfrage")]
    no_analysis = [{"id": c.id, "number": c.number, "name": c.article_name} for c in open_calcs
                   if c.decision in ("anbieten", "anderer_standort", "sonstiges") and not c.analysis_complete
                   and c.decision_note != "übernommen aus Altdaten"]

    # ---------------- Auslastung kommendes Jahr (nur Bestand + gewonnen) und mit offenen Großprojekten
    util = utilization(years=2, site_id=None, db=db, _=None)
    ny = year + 1 if month >= 10 else year
    idx = util["years"].index(ny) if ny in util["years"] else (1 if len(util["years"]) > 1 else 0)
    big_ids = {o.id for o in open_opps if float(o.amount or 0) >= big_t}
    big_calc = {c.id for c in open_calcs if c.opportunity_id in big_ids}
    util_rows = []
    for r in util["machines"]:
        cell = r["years"][idx]
        if not r["capacity_h"]:
            continue
        big_h = sum(i["years"].get(util["years"][idx], 0) for i in r["items"] if i["id"] in big_calc)
        won_items = [i for i in r["items"] if i["status"] == "gewonnen" and i["years"].get(util["years"][idx])]
        firm = cell["base"] + cell["fixed"]
        util_rows.append({"machine": r["machine"]["name"], "number": r["machine"].get("number"), "capacity_h": r["capacity_h"],
                          "base_h": cell["base"], "won_h": cell["fixed"], "pct_fixed": cell["pct_fixed"],
                          "pct_with_big": round((firm + big_h) / r["capacity_h"] * 100, 1),
                          "won_projects": [f"{i['number']} {i['article_name']}" for i in won_items][:6]})
    util_rows.sort(key=lambda x: -(x["pct_fixed"] or 0))
    tot = util["totals"][idx]

    # ---------------- Preisliste
    pcs = db.scalars(select(PriceChange).where(PriceChange.created_at >= datetime.combine(m_start, datetime.min.time(), tzinfo=timezone.utc),
                                               PriceChange.created_at < datetime.combine(m_end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))).unique().all()
    pl = {"changes": len(pcs), "articles": sum(len(c.impacts) for c in pcs),
          "effect": round(sum(i.annual_effect or 0 for c in pcs for i in c.impacts), 2),
          "passed": round(sum(i.annual_effect or 0 for c in pcs for i in c.impacts if i.status == "weitergegeben"), 2),
          "contract": round(sum(i.annual_effect or 0 for c in pcs for i in c.impacts if i.status == "vertraglich_gebunden"), 2),
          "open": sum(1 for c in pcs for i in c.impacts if i.status == "offen"),
          "items": [{"id": c.id, "number": c.number, "title": c.title, "effect": round(sum(i.annual_effect or 0 for i in c.impacts), 2)} for c in pcs]}

    def won_out(rows):
        return sorted([{**r, "date": r["date"].isoformat() if r["date"] else None, "sop": r["sop"].isoformat() if r["sop"] else None,
                        "machine": machines[r["machine_id"]].name if r["machine_id"] in machines else None} for r in rows],
                      key=lambda r: -r["annual"])

    return {
        "year": year, "month": month, "label": f"{MONTHS[month - 1]} {year}", "period": [m_start.isoformat(), m_end.isoformat()],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kpi": {
            "won_month": {"count": len(won_month), "annual": _sum(won_month, "annual"), "one_time": _sum(won_month, "one_time")},
            "won_ytd": {"count": len(won_ytd), "annual": _sum(won_ytd, "annual"), "one_time": _sum(won_ytd, "one_time")},
            "lost_month": {"count": len(lost), "annual": _sum(lost, "annual")},
            "nobid_month": {"count": len(nobid), "annual": _sum(nobid, "annual")},
            "win_rate_ytd": round(100 * won_n / len(closed_ytd), 1) if closed_ytd else None,
            "final_round_ytd": {"won": sum(1 for c in final if c.status == "gewonnen"), "lost": sum(1 for c in final if c.status == "verloren")},
            "new_inquiries": {"count": len(new_inq), "amount": round(sum(float(o.amount or 0) for o in new_inq), 2)},
            "quotes_sent": {"count": len(sent), "amount": round(sum(float(q.net_total or 0) for q in sent), 2)},
            "lead_time": {"avg": round(sum(lead_times) / len(lead_times), 1) if lead_times else None, "count": len(lead_times),
                          "target": float(st.get("lead_time_target_workdays") or 10),
                          "within": sum(1 for x in lead_times if x <= float(st.get("lead_time_target_workdays") or 10))},
            "articles_calculated": len(calc_ids),
            "open_pipeline": {"count": len(open_opps), "amount": round(sum(float(o.amount or 0) for o in open_opps), 2)},
        },
        "target": target_block(total_t, won_ytd), "by_owner": by_owner, "series": series,
        "won": won_out(won_month), "won_ytd_list": sorted(won_out(won_ytd), key=lambda r: r["date"] or ""),
        "lost": sorted(lost, key=lambda r: -r["annual"]), "nobid": nobid, "variants": variants,
        "reasons": sorted([{**v, "annual": round(v["annual"], 2)} for v in reasons.values()], key=lambda r: -r["annual"]),
        "pipeline": pipeline, "top_open": [opp_row(o) for o in top_open], "due_next": [opp_row(o) for o in due_next],
        "actions": {"followups_red": red, "undecided": undecided, "overdue_due": overdue_due, "approvals": approvals,
                    "analysis_missing": no_analysis},
        "utilization": {"year": util["years"][idx], "machines": util_rows, "pct_fixed": tot["pct_fixed"], "capacity_h": tot["capacity_h"]},
        "pricelist": pl,
    }
