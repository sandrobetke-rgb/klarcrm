"""Monatsbericht (Vertrieb, Ziele, Handlungsbedarf, Auslastung) und Vertriebsziele."""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import admin_only, can_read, can_write
from ..database import get_db
from ..models import MonthlyReport, SalesTarget, User
from ..monthly import compute

router = APIRouter()      # /api/monthly-reports
targets = APIRouter()     # /api/sales-targets


def _clean(o):
    """JSON-taugliche Kopie (Datumswerte als Text)."""
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean(v) for v in o]
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    return o


def _check(year: int, month: int):
    if not (1 <= month <= 12) or not (2000 <= year <= 2100):
        raise HTTPException(400, "Ungültiger Monat")


@router.get("/live")
def live(year: int, month: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Bericht für einen Monat mit aktuellem Datenstand (nicht gespeichert)."""
    _check(year, month)
    return _clean(compute(db, year, month))


def _out(r: MonthlyReport, users: dict, full: bool = False) -> dict:
    d = {"id": r.id, "year": r.year, "month": r.month, "status": r.status, "comment": r.comment,
         "created_at": r.created_at, "updated_at": r.updated_at, "by": users.get(r.created_by_id),
         "released_by": users.get(r.released_by_id), "released_at": r.released_at, "label": (r.data or {}).get("label")}
    if full:
        d["data"] = r.data
    return d


@router.get("")
def list_reports(db: Session = Depends(get_db), _: User = Depends(can_read)):
    users = {u.id: u.name for u in db.scalars(select(User)).all()}
    return [_out(r, users) for r in db.scalars(select(MonthlyReport).order_by(MonthlyReport.year.desc(), MonthlyReport.month.desc(), MonthlyReport.id.desc())).all()]


@router.get("/{rid}")
def get_report(rid: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    r = db.get(MonthlyReport, rid)
    if not r:
        raise HTTPException(404, "Bericht nicht gefunden")
    return _out(r, {u.id: u.name for u in db.scalars(select(User)).all()}, True)


class ReportIn(BaseModel):
    year: int
    month: int
    comment: str | None = None


@router.post("", status_code=201)
def save_report(data: ReportIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Stand einfrieren: Entwurf desselben Monats wird überschrieben, freigegebene Berichte bleiben unverändert."""
    _check(data.year, data.month)
    r = db.scalars(select(MonthlyReport).where(MonthlyReport.year == data.year, MonthlyReport.month == data.month,
                                               MonthlyReport.status == "entwurf")).first()
    snap = _clean(compute(db, data.year, data.month))
    if r:
        r.data, r.created_by_id = snap, user.id
        if data.comment is not None:
            r.comment = data.comment
    else:
        r = MonthlyReport(year=data.year, month=data.month, data=snap, comment=data.comment, created_by_id=user.id)
        db.add(r)
    db.commit()
    return _out(r, {u.id: u.name for u in db.scalars(select(User)).all()}, True)


class ReportPatch(BaseModel):
    comment: str | None = None
    status: str | None = None


@router.patch("/{rid}")
def patch_report(rid: int, data: ReportPatch, db: Session = Depends(get_db), user: User = Depends(can_write)):
    r = db.get(MonthlyReport, rid)
    if not r:
        raise HTTPException(404, "Bericht nicht gefunden")
    if r.status == "freigegeben" and user.role != "admin":
        raise HTTPException(409, "Freigegebener Bericht – Änderung nur durch Administrator")
    if data.comment is not None:
        r.comment = data.comment
    if data.status in ("entwurf", "freigegeben") and data.status != r.status:
        if user.role != "admin" and not user.can_approve:
            raise HTTPException(403, "Freigabe nur durch Geschäftsführung / Freigabeberechtigte")
        r.status = data.status
        r.released_by_id, r.released_at = (user.id, datetime.now(timezone.utc)) if data.status == "freigegeben" else (None, None)
    db.commit()
    return _out(r, {u.id: u.name for u in db.scalars(select(User)).all()}, True)


@router.delete("/{rid}", status_code=204)
def delete_report(rid: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    r = db.get(MonthlyReport, rid)
    if r:
        db.delete(r)
        db.commit()


# ------------------------------------------------------------------ Vertriebsziele
class TargetIn(BaseModel):
    year: int = Field(ge=2000, le=2100)
    user_id: int | None = None
    revenue_target: float = Field(ge=0)
    one_time_target: float | None = None
    note: str | None = None


def _t(t: SalesTarget, users: dict) -> dict:
    return {"id": t.id, "year": t.year, "user_id": t.user_id, "user": users.get(t.user_id) if t.user_id else "Gesamt",
            "revenue_target": t.revenue_target, "one_time_target": t.one_time_target, "note": t.note}


@targets.get("")
def list_targets(year: int | None = None, db: Session = Depends(get_db), _: User = Depends(can_read)):
    users = {u.id: u.name for u in db.scalars(select(User)).all()}
    q = select(SalesTarget).order_by(SalesTarget.year.desc(), SalesTarget.user_id.nullsfirst())
    if year:
        q = q.where(SalesTarget.year == year)
    return [_t(t, users) for t in db.scalars(q).all()]


@targets.post("", status_code=201)
def save_target(data: TargetIn, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    """Ziel anlegen oder ändern (je Jahr und Mitarbeiter genau eines)."""
    t = db.scalars(select(SalesTarget).where(SalesTarget.year == data.year, SalesTarget.user_id.is_(None) if data.user_id is None
                                             else SalesTarget.user_id == data.user_id)).first()
    if not t:
        t = SalesTarget(year=data.year, user_id=data.user_id)
        db.add(t)
    t.revenue_target, t.one_time_target, t.note = data.revenue_target, data.one_time_target, data.note
    db.commit()
    return _t(t, {u.id: u.name for u in db.scalars(select(User)).all()})


@targets.delete("/{tid}", status_code=204)
def delete_target(tid: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    t = db.get(SalesTarget, tid)
    if t:
        db.delete(t)
        db.commit()
