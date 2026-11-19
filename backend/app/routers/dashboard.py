from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from .. import schemas as s
from ..auth import can_read
from ..database import get_db
from ..models import CLOSED_STAGES, STAGES, Account, Activity, Opportunity, Quote, User

router = APIRouter()
OPEN_STAGES = [st for st in STAGES if st not in CLOSED_STAGES]


def f(v) -> float:
    return round(float(v or 0), 2)


@router.get("")
def dashboard(owner_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(can_read)):
    today = date.today()
    year_start = date(today.year, 1, 1)
    q_start_month = 3 * ((today.month - 1) // 3) + 1
    quarter_start = date(today.year, q_start_month, 1)
    quarter_end = date(today.year + (q_start_month == 10), (q_start_month + 3 - 1) % 12 + 1, 1) - timedelta(days=1)

    def opp(*conds):
        stmt = select(Opportunity)
        if owner_id:
            stmt = stmt.where(Opportunity.owner_id == owner_id)
        return stmt.where(*conds)

    def agg(*conds):
        sub = opp(*conds).subquery()
        row = db.execute(
            select(func.count(), func.sum(sub.c.amount), func.sum(sub.c.amount * sub.c.probability / 100.0))
        ).one()
        # REV01-P09: keine Umsatzgewichtung – stattdessen Volumen mit hoher Wahrscheinlichkeit (≥ 50 %)
        likely = db.scalar(select(func.sum(sub.c.amount)).where(sub.c.probability >= 50))
        return {"count": row[0], "amount": f(row[1]), "weighted": f(row[2]), "likely": f(likely)}

    open_ = agg(Opportunity.stage.in_(OPEN_STAGES))
    won_ytd = agg(Opportunity.stage == "gewonnen", Opportunity.closed_at >= year_start)
    lost_ytd = agg(Opportunity.stage == "verloren", Opportunity.closed_at >= year_start)
    closed = won_ytd["count"] + lost_ytd["count"]
    forecast_q = agg(
        Opportunity.stage.in_(OPEN_STAGES),
        Opportunity.close_date >= quarter_start, Opportunity.close_date <= quarter_end,
    )
    won_q = agg(Opportunity.stage == "gewonnen", Opportunity.closed_at >= quarter_start)

    by_stage = []
    for st in STAGES:
        a = agg(Opportunity.stage == st)
        by_stage.append({"stage": st, **a})

    # Gewonnener Umsatz je Monat (letzte 12 Monate)
    start12 = date(today.year - 1, today.month, 1) + timedelta(days=32)
    start12 = start12.replace(day=1)
    sub = opp(Opportunity.stage == "gewonnen", Opportunity.closed_at >= start12).subquery()
    rows = db.execute(
        select(extract("year", sub.c.closed_at), extract("month", sub.c.closed_at), func.sum(sub.c.amount))
        .group_by(extract("year", sub.c.closed_at), extract("month", sub.c.closed_at))
    ).all()
    monthly_map = {(int(y), int(m)): f(v) for y, m, v in rows}
    monthly = []
    y, m = start12.year, start12.month
    for _ in range(12):
        monthly.append({"month": f"{y}-{m:02d}", "amount": monthly_map.get((y, m), 0.0)})
        m += 1
        if m > 12:
            y, m = y + 1, 1

    # Je Vertriebsmitarbeiter
    by_owner = []
    for u in db.scalars(select(User).where(User.role != "gesellschafter").order_by(User.name)):
        if owner_id and u.id != owner_id:
            continue
        o = db.execute(
            select(func.count(), func.sum(Opportunity.amount),
                   func.sum(Opportunity.amount * Opportunity.probability / 100.0))
            .where(Opportunity.owner_id == u.id, Opportunity.stage.in_(OPEN_STAGES))
        ).one()
        w = db.scalar(
            select(func.sum(Opportunity.amount)).where(
                Opportunity.owner_id == u.id, Opportunity.stage == "gewonnen",
                Opportunity.closed_at >= year_start)
        )
        if o[0] or w:
            by_owner.append({"user": {"id": u.id, "name": u.name}, "open_count": o[0],
                             "open_amount": f(o[1]), "weighted": f(o[2]), "won_ytd": f(w)})

    top_open = db.scalars(opp(Opportunity.stage.in_(OPEN_STAGES)).order_by(Opportunity.amount.desc()).limit(6)).unique().all()
    closing_soon = db.scalars(
        opp(Opportunity.stage.in_(OPEN_STAGES), Opportunity.close_date <= today + timedelta(days=30))
        .order_by(Opportunity.close_date).limit(8)
    ).unique().all()

    nowt = datetime.now(timezone.utc)
    start_today = nowt.replace(hour=0, minute=0, second=0, microsecond=0)
    act = select(func.count()).select_from(Activity).where(Activity.done.is_(False))
    if owner_id:
        act = act.where(Activity.owner_id == owner_id)
    overdue = db.scalar(act.where(Activity.due_at < nowt))
    due_today = db.scalar(act.where(Activity.due_at >= start_today, Activity.due_at < start_today + timedelta(days=1)))

    qstmt = select(Quote).where(Quote.status == "versendet")
    if owner_id:
        qstmt = qstmt.where(Quote.owner_id == owner_id)
    open_quotes = db.scalars(qstmt).unique().all()

    # Endrunde (Verhandlung / technisches Gespräch): gewonnen/verloren aus der Endrunde (REV01-P01)
    final = {k: db.scalar(select(func.count()).select_from(Opportunity).where(
        Opportunity.final_round.is_(True), Opportunity.stage == k, Opportunity.closed_at >= year_start)) or 0
        for k in ("gewonnen", "verloren")}
    # Angebotsverfolgung mit Ampel – für alle sichtbar
    from ..inquiry import followup_light  # noqa: PLC0415
    fus = db.scalars(select(Activity).where(Activity.kind == "angebotsverfolgung", Activity.done.is_(False))).unique().all()
    followups = {k: sum(1 for a in fus if followup_light(a.due_at) == k) for k in ("rot", "gelb", "gruen")}
    customers = db.scalar(select(func.count()).select_from(Account).where(Account.type == "kunde"))
    new_accounts_30d = db.scalar(
        select(func.count()).select_from(Account).where(Account.created_at >= nowt - timedelta(days=30))
    )

    return {
        "kpis": {
            "open_pipeline": open_,
            "won_ytd": won_ytd,
            "lost_ytd": lost_ytd,
            "win_rate": round(100 * won_ytd["count"] / closed, 1) if closed else None,
            "avg_deal_won": f(won_ytd["amount"] / won_ytd["count"]) if won_ytd["count"] else 0,
            "forecast_quarter": forecast_q,
            "won_quarter": won_q,
            "quarter": f"Q{(today.month - 1) // 3 + 1} {today.year}",
            "open_quotes": {"count": len(open_quotes), "amount": f(sum(q.net_total for q in open_quotes))},
            "activities_overdue": overdue,
            "activities_today": due_today,
            "customers": customers,
            "new_accounts_30d": new_accounts_30d,
            "final_round": final,
            "followups": followups,
        },
        "by_stage": by_stage,
        "monthly_won": monthly,
        "by_owner": by_owner,
        "top_open": [s.OpportunityOut.model_validate(o).model_dump(mode="json") for o in top_open],
        "closing_soon": [s.OpportunityOut.model_validate(o).model_dump(mode="json") for o in closing_soon],
    }
