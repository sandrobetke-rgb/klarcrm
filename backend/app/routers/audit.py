"""Änderungsprotokoll abfragen."""
from datetime import date, datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..auth import ALGORITHM, get_current_user, verify_password
from ..config import settings
from ..database import get_db
from ..events import ENTITY_LABELS
from ..models import AuditLog, User

router = APIRouter()
UNLOCK_MINUTES = 30


# REV02-07: Protokoll nur für den SuperUser und nur nach erneuter Passworteingabe (Freischaltung 30 Minuten)
def require_audit(x_audit_token: str | None = Header(default=None), user: User = Depends(get_current_user)) -> User:
    if not user.is_superuser:
        raise HTTPException(403, "Das Protokoll ist gesperrt (nur SuperUser)")
    try:
        p = jwt.decode(x_audit_token or "", settings.SECRET_KEY, algorithms=[ALGORITHM])
        if p.get("scope") != "audit" or int(p.get("sub")) != user.id:
            raise ValueError
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(423, "Protokoll gesperrt – bitte Passwort eingeben")
    return user


@router.post("/unlock")
def unlock(data: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_superuser:
        raise HTTPException(403, "Das Protokoll ist gesperrt (nur SuperUser)")
    if not verify_password((data or {}).get("password") or "", user.password_hash):
        raise HTTPException(400, "Passwort falsch")
    exp = datetime.now(timezone.utc) + timedelta(minutes=UNLOCK_MINUTES)
    return {"token": jwt.encode({"sub": str(user.id), "scope": "audit", "exp": exp}, settings.SECRET_KEY, algorithm=ALGORITHM),
            "minutes": UNLOCK_MINUTES}


def _out(a: AuditLog) -> dict:
    return {"id": a.id, "ts": a.ts.isoformat(), "user": a.user_name or ("System" if not a.user_id else f"#{a.user_id}"),
            "action": a.action, "entity": a.entity, "entity_label": ENTITY_LABELS.get(a.entity, a.entity),
            "entity_id": a.entity_id, "label": a.label, "ref": a.ref, "changes": a.changes or {}}


@router.get("")
def list_audit(entity: str | None = None, user_id: int | None = None, q: str | None = None,
               date_from: date | None = None, date_to: date | None = None,
               limit: int = Query(100, le=1000), offset: int = 0,
               db: Session = Depends(get_db), user: User = Depends(require_audit)):
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
def audit_for(entity: str, entity_id: int, db: Session = Depends(get_db), _: User = Depends(require_audit)):
    """Verlauf eines Datensatzes inkl. untergeordneter Datensätze (z. B. Kalkulation mit Versionen, Anrufen)."""
    key = f"{entity}:{entity_id}"
    rows = db.scalars(select(AuditLog).where(or_(AuditLog.ref == key, (AuditLog.entity == entity) & (AuditLog.entity_id == entity_id)))
                      .order_by(AuditLog.ts.desc(), AuditLog.id.desc()).limit(500)).all()
    return [_out(a) for a in rows]
