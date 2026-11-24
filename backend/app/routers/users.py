from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import schemas as s
from ..auth import admin_only, can_read, create_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User

auth_router = APIRouter()
users_router = APIRouter()


@auth_router.post("/login", response_model=s.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == form.username.lower().strip()))
    if not user or not user.active or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "E-Mail oder Passwort falsch")
    return {"access_token": create_token(user), "user": user}


@auth_router.get("/me", response_model=s.UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@auth_router.post("/password", status_code=204)
def change_password(data: s.PasswordChange, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "Altes Passwort ist falsch")
    user.password_hash = hash_password(data.new_password)
    db.commit()


# Benutzerliste (für Auswahlfelder "Verantwortlich") darf jeder lesen
@users_router.get("", response_model=list[s.UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(can_read)):
    return db.scalars(select(User).order_by(User.name)).all()


@users_router.post("", response_model=s.UserOut, status_code=201)
def create_user(data: s.UserCreate, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    if db.scalar(select(User).where(func.lower(User.email) == data.email.lower())):
        raise HTTPException(400, "E-Mail ist bereits vergeben")
    user = User(**data.model_dump(exclude={"password"}), password_hash=hash_password(data.password))
    user.email = user.email.lower()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@users_router.patch("/{user_id}", response_model=s.UserOut)
def update_user(user_id: int, data: s.UserUpdate, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Benutzer nicht gefunden")
    values = data.model_dump(exclude_unset=True)
    # REV02-07: SuperUser (Protokoll) – Konto nur vom SuperUser selbst änderbar, Recht nur von ihm übertragbar
    if "is_superuser" in values:
        if not admin.is_superuser:
            raise HTTPException(403, "Nur der SuperUser kann dieses Recht vergeben")
        if user.id == admin.id and not values["is_superuser"]:
            raise HTTPException(400, "Erst einem anderen Benutzer das SuperUser-Recht geben, dann bei dir entfernen")
    changed = {k for k in ("password", "email", "active", "role") if k in values and values[k] is not None
               and (k == "password" or (str(values[k]).lower() if k == "email" else values[k]) != getattr(user, k))}
    if user.is_superuser and not admin.is_superuser and changed:
        raise HTTPException(403, "Das Konto des SuperUsers kann nur er selbst ändern")
    if user.id == admin.id and (values.get("role", "admin") != "admin" or values.get("active") is False):
        raise HTTPException(400, "Du kannst dir selbst die Admin-Rechte nicht entziehen")
    if pw := values.pop("password", None):
        user.password_hash = hash_password(pw)
    for k, v in values.items():
        setattr(user, k, v.lower() if k == "email" else v)
    db.commit()
    db.refresh(user)
    return user


@users_router.delete("/{user_id}", status_code=204)
def deactivate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    """Benutzer werden nur deaktiviert, damit Zuordnungen erhalten bleiben."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Benutzer nicht gefunden")
    if user.id == admin.id:
        raise HTTPException(400, "Du kannst dich nicht selbst deaktivieren")
    user.active = False
    db.commit()
