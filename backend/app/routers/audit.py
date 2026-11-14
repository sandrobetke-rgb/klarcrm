"""Änderungsprotokoll abfragen."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..auth import can_read, get_current_user
from ..database import get_db
from ..events import ENTITY_LABELS
from ..models import AuditLog, User

router = APIRouter()


def _out(a: AuditLog) -> dict:
    return {"id": a.id, "ts": a.ts.isoformat(), "user": a.user_name or ("System" if not a.user_id else f"#{a.user_id}"),
            "action": a.action, "entity": a.entity, "entity_label": ENTITY_LABELS.get(a.entity, a.entity),
            "entity_id": a.entity_id, "label": a.label, "ref": a.ref, "changes": a.changes or {}}


@router.get("")
def list_audit(entity: str | None = None, user_id: int | None = None, q: str | None = None,
               date_from: date | None = None, date_to: date | None = None,
               limit: int = Query(100, le=1000), offset: int = 0,
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not (user.role in ("admin", "gesellschafter") or user.can_approve):
        raise HTTPException(403, "Protokoll nur für Administration, Geschäftsführung und Freigebende")
    stmt = select(AuditLog)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if q:
        stmt = stmt.where(or_(AuditLog.label.ilike(f"%{q}%"), AuditLog.ref.ilike(f"%{q}%")))
    if date_from:
        stmt = stmt.where(AuditLog.ts >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        stmt = stmt.where(AuditLog.ts < datetime.combine(date_to + timedelta(days=1), datetime.min.time()))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(AuditLog.ts.desc(), AuditLog.id.desc()).offset(offset).limit(limit)).all()
    return {"total": total, "items": [_out(a) for a in rows], "entities": ENTITY_LABELS}


@router.get("/ref/{entity}/{entity_id}")
def audit_for(entity: str, entity_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Verlauf eines Datensatzes inkl. untergeordneter Datensätze (z. B. Kalkulation mit Versionen, Anrufen)."""
    key = f"{entity}:{entity_id}"
    rows = db.scalars(select(AuditLog).where(or_(AuditLog.ref == key, (AuditLog.entity == entity) & (AuditLog.entity_id == entity_id)))
                      .order_by(AuditLog.ts.desc(), AuditLog.id.desc()).limit(500)).all()
    return [_out(a) for a in rows]
