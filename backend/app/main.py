from contextlib import asynccontextmanager

import jwt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text

from .auth import hash_password
from .config import settings
from .context import current_user_id
from .database import Base, SessionLocal, engine, ensure_columns
from .models import User
from . import events  # noqa: F401  (Session-Ereignisse registrieren)
from .routers import audit, calc, dashboard, docs, entities, inquiries, monthly, pricelist, imports, procurement, quotes, reports, users, workflow


def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    with SessionLocal() as db:
        # Bestandsmaschinen ohne Art (vor v1.12) sind Spritzgießmaschinen
        db.execute(text("UPDATE machines SET kind = 'spritzguss' WHERE kind IS NULL"))
        db.execute(text("ALTER TABLE contacts ALTER COLUMN first_name DROP NOT NULL"))   # Vorname optional (v1.24)
        # Neuumsatz (stärkstes Lieferjahr) für bestehende Kalkulationen nachtragen
        from .calc_engine import peak_revenue  # noqa: PLC0415
        from .models import Calculation  # noqa: PLC0415
        for c in db.query(Calculation).filter(Calculation.peak_revenue.is_(None)).all():
            ver = next((v for v in c.versions if v.version_no == c.current_version), None)
            c.peak_revenue = peak_revenue(ver.results or {}) if ver else (c.annual_revenue or 0)
        db.commit()
        # Abschlussdatum der Kalkulationen nachtragen (Monatsbericht): Datum der Anfrage, sonst letzte Änderung
        db.execute(text("""UPDATE calculations c SET closed_at = COALESCE(o.closed_at, c.updated_at::date)
                           FROM calculations c2 LEFT JOIN opportunities o ON o.id = c2.opportunity_id
                           WHERE c.id = c2.id AND c.closed_at IS NULL
                             AND c.status IN ('gewonnen', 'verloren', 'kein_angebot')"""))
        db.commit()
        # REV01: Freigabegrenzen von 500.000 € auf 250.000 € (einmalig, nur wenn noch der alte Standard steht)
        from .models import CalcSettings  # noqa: PLC0415
        cs = db.get(CalcSettings, 1)
        if cs and not (cs.data or {}).get("_rev01_thresholds"):
            d = dict(cs.data or {})
            for k in ("big_revenue_threshold", "big_invest_threshold"):
                if float(d.get(k) or 500000) == 500000:
                    d[k] = 250000.0
            d["_rev01_thresholds"] = True
            cs.data = d
            db.commit()
        # REV02-07 (SuperUser fürs Protokoll) zurückgenommen (REV03-07) – Protokoll bleibt ausgeblendet (REV02-10)
        # REV02-01: Freigabe nur noch ab Umsatz 500 T€ / Invest 350 T€ (wenn noch der Stand 250 T€ eingestellt ist)
        cs = db.get(CalcSettings, 1)
        if cs and not (cs.data or {}).get("_rev02_thresholds"):
            d = dict(cs.data or {})
            if float(d.get("big_revenue_threshold") or 250000) == 250000:
                d["big_revenue_threshold"] = 500000.0
            if float(d.get("big_invest_threshold") or 250000) == 250000:
                d["big_invest_threshold"] = 350000.0
            d["_rev02_thresholds"] = True
            cs.data = d
            db.commit()
        # REV02-05: Wahrscheinlichkeiten offener Anfragen wurden bisher automatisch (Phase/Status) gesetzt, nie von Hand
        # → einmalig auf „nicht eingeschätzt“ zurücksetzen; ab jetzt nur noch von Hand
        cs = db.get(CalcSettings, 1)
        if cs and not (cs.data or {}).get("_rev02_probability"):
            from .models import Calculation, Opportunity  # noqa: PLC0415
            for o in db.query(Opportunity).all():
                if o.stage in ("gewonnen", "verloren", "nicht_angeboten"):
                    continue
                o.probability, o.probability_estimated = 0, False
                for c in db.query(Calculation).filter(Calculation.opportunity_id == o.id).all():
                    if c.status not in ("gewonnen", "verloren", "kein_angebot", "zurueckgestellt"):
                        c.probability = 0
            d = dict(cs.data or {})
            d["_rev02_probability"] = True
            cs.data = d
            db.commit()
        # REV01 Phase 2: Kalkulationen einmalig in Anfragen überführen (gruppiert nach Angebot)
        cs = db.get(CalcSettings, 1)
        if cs is None:
            cs = CalcSettings(id=1, data={})
            db.add(cs)
            db.flush()
        if not (cs.data or {}).get("_rev01_phase2"):
            from .inquiry import migrate  # noqa: PLC0415
            stats = migrate(db)
            cs.data = {**(cs.data or {}), "_rev01_phase2": True}
            db.commit()
            print(f"REV01 Phase 2 – Anfragen übernommen: {stats}")
        # Änderungsprotokoll REV01 übernehmen (nur fehlende Punkte, Status aus der Oberfläche bleibt)
        from .rev01 import seed_rev01  # noqa: PLC0415
        seed_rev01(db)
        # REV04-01: Zeitpunkt des Einspielens dieser Version merken
        from .version import remember_install  # noqa: PLC0415
        remember_install(db)
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


from .version import APP_VERSION, version_info  # noqa: E402

app = FastAPI(title="KlarCRM API", version=APP_VERSION, lifespan=lifespan)
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
app.include_router(reports.router, prefix="/api/reports", tags=["Auswertungen"])
app.include_router(procurement.router, prefix="/api/procurement", tags=["Beschaffung"])
app.include_router(imports.router, prefix="/api/import", tags=["Import"])
app.include_router(workflow.router, prefix="/api", tags=["Arbeitsabläufe"])
app.include_router(calc.machines, prefix="/api/machines", tags=["Stammdaten"])
app.include_router(calc.materials, prefix="/api/materials", tags=["Stammdaten"])
app.include_router(calc.purchased_parts, prefix="/api/purchased-parts", tags=["Stammdaten"])
app.include_router(calc.sites, prefix="/api/sites", tags=["Stammdaten"])
app.include_router(calc.router, prefix="/api/calc", tags=["Kalkulation"])
app.include_router(calc.quote_bulk, prefix="/api/calculations-bulk", tags=["Kalkulation"])
app.include_router(calc.calcs, prefix="/api/calculations", tags=["Kalkulation"])
app.include_router(docs.changes, prefix="/api/changes", tags=["Änderungsprotokoll"])
app.include_router(inquiries.router, prefix="/api/inquiries", tags=["Anfragen"])
app.include_router(pricelist.router, prefix="/api/pricelist", tags=["Preisliste"])
app.include_router(monthly.router, prefix="/api/monthly-reports", tags=["Monatsbericht"])
app.include_router(monthly.targets, prefix="/api/sales-targets", tags=["Monatsbericht"])
app.include_router(inquiries.decisions, prefix="/api/calculations", tags=["Anfragen"])
app.include_router(inquiries.followups, prefix="/api/followups", tags=["Angebotsverfolgung"])
app.include_router(docs.router, prefix="/api/docs", tags=["Dokumentation"])
app.include_router(docs.checks, prefix="/api/checks", tags=["Prüfen"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": APP_VERSION}


@app.get("/api/version")
def version():
    """REV04-01 Softwarestand – ohne Anmeldung (auch auf der Anmeldeseite sichtbar)."""
    from .database import SessionLocal  # noqa: PLC0415
    with SessionLocal() as db:
        return version_info(db)
