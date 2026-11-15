"""Auswertungen über Anfragen/Kalkulationen: Maschinengröße, Kunden, Absagegründe, Werkstoffe, Vertrieb, Monate."""
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import can_read
from ..database import get_db
from ..models import Account, Calculation, Machine, Material, Site, User

router = APIRouter()

WON, LOST, NO_BID = "gewonnen", "verloren", "kein_angebot"
QUOTED = ("angeboten", "verhandlung", WON, LOST)
CLASSES = [(0, 100, "bis 100 t"), (100, 250, "100–250 t"), (250, 500, "250–500 t"), (500, 10 ** 9, "über 500 t")]


def _class(t: float | None) -> str:
    if not t:
        return "ohne Maschine / Schließkraft"
    return next(lbl for lo, hi, lbl in CLASSES if lo < t <= hi or (lo == 0 and t <= hi))


def _empty() -> dict:
    return {"count": 0, "quoted": 0, "won": 0, "lost": 0, "no_bid": 0, "open": 0,
            "revenue": 0.0, "won_revenue": 0.0, "lost_revenue": 0.0, "no_bid_revenue": 0.0}


def _add(b: dict, c: Calculation) -> None:
    rev = float(c.annual_revenue or 0)
    b["count"] += 1
    b["revenue"] += rev
    if c.status in QUOTED:
        b["quoted"] += 1
    if c.status == WON:
        b["won"] += 1
        b["won_revenue"] += rev
    elif c.status == LOST:
        b["lost"] += 1
        b["lost_revenue"] += rev
    elif c.status == NO_BID:
        b["no_bid"] += 1
        b["no_bid_revenue"] += rev
    elif c.status != "zurueckgestellt":
        b["open"] += 1


def _finish(groups: dict, total: dict, key_name: str = "key") -> list:
    rows = []
    for k, b in groups.items():
        decided = b["won"] + b["lost"]
        rows.append({key_name: k, **{x: round(v, 2) if isinstance(v, float) else v for x, v in b.items()},
                     "share_count_pct": round(b["count"] / total["count"] * 100, 1) if total["count"] else 0,
                     "share_revenue_pct": round(b["revenue"] / total["revenue"] * 100, 1) if total["revenue"] else 0,
                     "hit_rate_pct": round(b["won"] / decided * 100, 1) if decided else None,
                     "decline_rate_pct": round((b["no_bid"] + b["lost"]) / b["count"] * 100, 1) if b["count"] else 0})
    return sorted(rows, key=lambda r: (-r["count"], -r["revenue"]))


@router.get("")
def reports(date_from: date | None = Query(None), date_to: date | None = Query(None), owner_id: int | None = None,
            account_id: int | None = None, site_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Kennzahlen gruppiert. Zeitraum bezieht sich auf das Anfragedatum (sonst Anlagedatum)."""
    q = select(Calculation)
    if owner_id:
        q = q.where(Calculation.owner_id == owner_id)
    if account_id:
        q = q.where(Calculation.account_id == account_id)
    if site_id:
        q = q.where(Calculation.site_id == site_id)
    calcs = []
    for c in db.scalars(q).unique():
        d = c.inquiry_date or (c.created_at.date() if c.created_at else None)
        if (date_from and d and d < date_from) or (date_to and d and d > date_to):
            continue
        calcs.append((c, d))
    machines = {m.id: m for m in db.scalars(select(Machine))}
    materials = {m.id: m for m in db.scalars(select(Material))}
    accounts = {a.id: a.name for a in db.scalars(select(Account)).unique()}
    users = {u.id: u.name for u in db.scalars(select(User))}
    sites = {x.id: x.name for x in db.scalars(select(Site))}

    total = _empty()
    g = {k: defaultdict(_empty) for k in ("machine_class", "machine", "customer", "material", "owner", "month", "status",
                                         "feasibility", "site")}
    lost_reasons, no_bid_reasons = defaultdict(_empty), defaultdict(_empty)
    for c, d in calcs:
        _add(total, c)
        ver = next((v for v in c.versions if v.version_no == c.current_version), None)
        inp = ver.inputs if ver else {}
        m = machines.get(inp.get("machine_id"))
        _add(g["machine_class"][_class(m.clamping_force_t if m else None)], c)
        _add(g["machine"][f"{m.number} · {m.name}" if m else "ohne Maschine"], c)
        _add(g["customer"][accounts.get(c.account_id, "ohne Kunde")], c)
        mat = materials.get(inp.get("material_id"))
        _add(g["material"][(mat.family or mat.name) if mat else (inp.get("material_name") or "ohne Material")], c)
        _add(g["owner"][users.get(c.owner_id, "ohne Zuständigen")], c)
        _add(g["month"][d.strftime("%Y-%m") if d else "ohne Datum"], c)
        _add(g["status"][c.status], c)
        _add(g["feasibility"][c.feasibility or "nicht bewertet"], c)
        _add(g["site"][sites.get(c.site_id or inp.get("site_id"), "ohne Standort")], c)
        if c.status == LOST:
            _add(lost_reasons[c.close_reason or "ohne Grund"], c)
        if c.status == NO_BID:
            _add(no_bid_reasons[c.no_bid_reason or "ohne Grund"], c)

    decided = total["won"] + total["lost"]
    out = {k: _finish(v, total) for k, v in g.items()}
    order = [lbl for _, _, lbl in CLASSES] + ["ohne Maschine / Schließkraft"]
    out["machine_class"].sort(key=lambda r: order.index(r["key"]) if r["key"] in order else 99)
    out["month"].sort(key=lambda r: r["key"])
    return {
        "summary": {**{k: round(v, 2) if isinstance(v, float) else v for k, v in total.items()},
                    "hit_rate_pct": round(total["won"] / decided * 100, 1) if decided else None,
                    "quote_rate_pct": round(total["quoted"] / total["count"] * 100, 1) if total["count"] else 0,
                    "no_bid_rate_pct": round(total["no_bid"] / total["count"] * 100, 1) if total["count"] else 0},
        **out,
        "lost_reasons": _finish(lost_reasons, total),
        "no_bid_reasons": _finish(no_bid_reasons, total),
        "filters": {"date_from": date_from, "date_to": date_to, "owner_id": owner_id, "account_id": account_id},
    }
