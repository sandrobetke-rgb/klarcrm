from contextlib import asynccontextmanager

import jwt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from .auth import hash_password
from .config import settings
from .context import current_user_id
from .database import Base, SessionLocal, engine, ensure_columns
from .models import User
from . import events  # noqa: F401  (Session-Ereignisse registrieren)
from .routers import audit, calc, dashboard, entities, quotes, users, workflow


def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    with SessionLocal() as db:
        if not db.scalar(select(func.count()).select_from(User)):
            db.add(User(
                email=settings.ADMIN_EMAIL.lower(), name="Administrator",
                password_hash=hash_password(settings.ADMIN_PASSWORD), role="admin",
            ))
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="KlarCRM API", version="1.0.0", lifespan=lifespan)
@app.middleware("http")
async def user_context(request, call_next):
    """Angemeldeten Benutzer für Protokolle setzen (gilt für die ganze Anfrage, auch in Threads)."""
    uid = None
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            uid = int(jwt.decode(auth[7:], settings.SECRET_KEY, algorithms=["HS256"])["sub"])
        except Exception:  # ungültiges Token: Prüfung erfolgt in get_current_user
            uid = None
    token = current_user_id.set(uid)
    try:
        return await call_next(request)
    finally:
        current_user_id.reset(token)


app.add_middleware(
    CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(users.auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.users_router, prefix="/api/users", tags=["Benutzer"])
app.include_router(entities.accounts, prefix="/api/accounts", tags=["Firmen"])
app.include_router(entities.contacts, prefix="/api/contacts", tags=["Kontakte"])
app.include_router(entities.opportunities, prefix="/api/opportunities", tags=["Verkaufschancen"])
app.include_router(entities.activities, prefix="/api/activities", tags=["Aktivitäten"])
app.include_router(quotes.router, prefix="/api/quotes", tags=["Angebote"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(audit.router, prefix="/api/audit", tags=["Protokoll"])
app.include_router(workflow.router, prefix="/api", tags=["Arbeitsabläufe"])
app.include_router(calc.machines, prefix="/api/machines", tags=["Stammdaten"])
app.include_router(calc.materials, prefix="/api/materials", tags=["Stammdaten"])
app.include_router(calc.router, prefix="/api/calc", tags=["Kalkulation"])
app.include_router(calc.quote_bulk, prefix="/api/calculations-bulk", tags=["Kalkulation"])
app.include_router(calc.calcs, prefix="/api/calculations", tags=["Kalkulation"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
