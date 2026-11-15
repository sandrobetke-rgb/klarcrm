"""Arbeitsabläufe: Dokumente, Benachrichtigungen, Outlook-Kalender (ICS), Firmeneinstellungen."""
import os
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import admin_only, can_read, can_write, get_current_user
from ..config import settings
from ..database import get_db
from ..models import Activity, AppSettings, Attachment, Calculation, Notification, Quote, User

router = APIRouter()

ENTITIES = {"calculations", "accounts", "quotes", "opportunities", "procurement", "app"}
BLOCKED = {".exe", ".bat", ".cmd", ".com", ".msi", ".ps1", ".vbs", ".js", ".jar", ".scr", ".sh", ".dll"}
DOC_TYPES = {"zeichnung": "Zeichnung", "3d": "3D-Daten", "anfrage": "Kundenanfrage", "lastenheft": "Lastenheft Kunde",
             "pruefplan": "Prüfplan / Messkonzept", "muster": "Musterbericht / EMPB", "sonstiges": "Sonstiges", "logo": "Logo"}


# ---------------- Dokumente ----------------
def _att(a: Attachment) -> dict:
    return {"id": a.id, "entity": a.entity, "entity_id": a.entity_id, "filename": a.filename, "size": a.size,
            "content_type": a.content_type, "doc_type": a.doc_type, "doc_type_label": DOC_TYPES.get(a.doc_type or "", a.doc_type),
            "revision": a.revision, "note": a.note, "uploaded_by": a.uploaded_by.name if a.uploaded_by else None,
            "created_at": a.created_at.isoformat()}


@router.get("/attachments")
def list_attachments(entity: str, entity_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    rows = db.scalars(select(Attachment).where(Attachment.entity == entity, Attachment.entity_id == entity_id,
                                               Attachment.deleted.is_(False)).order_by(Attachment.created_at.desc())).unique().all()
    return {"items": [_att(a) for a in rows], "doc_types": DOC_TYPES}


@router.post("/attachments", status_code=201)
async def upload_attachment(entity: str = Form(...), entity_id: int = Form(...), doc_type: str = Form("sonstiges"),
                            revision: str = Form(""), note: str = Form(""), file: UploadFile = File(...),
                            db: Session = Depends(get_db), user: User = Depends(can_write)):
    if entity not in ENTITIES:
        raise HTTPException(400, "Unbekannter Bereich")
    if entity == "app" and user.role != "admin":
        raise HTTPException(403, "Nur Administratoren")
    ext = Path(file.filename or "").suffix.lower()
    if ext in BLOCKED:
        raise HTTPException(400, f"Dateityp {ext} ist nicht erlaubt")
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"Datei größer als {settings.MAX_UPLOAD_MB} MB")
    sub = datetime.now().strftime("%Y/%m")
    folder = Path(settings.UPLOAD_DIR) / sub
    folder.mkdir(parents=True, exist_ok=True)
    stored = f"{sub}/{uuid.uuid4().hex}{ext}"
    (Path(settings.UPLOAD_DIR) / stored).write_bytes(data)
    a = Attachment(entity=entity, entity_id=entity_id, filename=os.path.basename(file.filename or "datei"), stored_name=stored,
                   content_type=file.content_type, size=len(data), doc_type=doc_type, revision=revision or None,
                   note=note or None, uploaded_by_id=user.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return _att(a)


def _file(a: Attachment):
    path = Path(settings.UPLOAD_DIR) / a.stored_name
    if not path.exists():
        raise HTTPException(404, "Datei nicht mehr vorhanden")
    return FileResponse(path, media_type=a.content_type or "application/octet-stream", filename=a.filename)


@router.get("/attachments/{att_id}/download")
def download_attachment(att_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    a = db.get(Attachment, att_id)
    if not a or a.deleted:
        raise HTTPException(404, "Dokument nicht gefunden")
    return _file(a)


@router.delete("/attachments/{att_id}", status_code=204)
def delete_attachment(att_id: int, db: Session = Depends(get_db), user: User = Depends(can_write)):
    a = db.get(Attachment, att_id)
    if not a or a.deleted:
        raise HTTPException(404, "Dokument nicht gefunden")
    if user.role != "admin" and a.uploaded_by_id != user.id:
        raise HTTPException(403, "Nur hochladende Person oder Administrator")
    a.deleted = True  # Datei bleibt erhalten (Nachweis), Eintrag wird ausgeblendet und protokolliert
    db.commit()


@router.get("/public/logo")
def public_logo(db: Session = Depends(get_db)):
    """Firmenlogo (ohne Anmeldung, für Druckansicht und Anmeldeseite)."""
    st = db.get(AppSettings, 1)
    a = db.get(Attachment, (st.data or {}).get("logo_attachment_id")) if st and st.data else None
    if not a or a.deleted:
        raise HTTPException(404, "Kein Logo")
    return _file(a)


# ---------------- Firmeneinstellungen / Angebotslayout ----------------
DEFAULT_APP = {
    "company_name": settings.COMPANY_NAME, "street": "", "zip_city": "", "country": "Deutschland", "phone": "", "email": "",
    "website": "", "register": "", "vat_id": "", "managing_directors": "", "bank_name": "", "iban": "", "bic": "",
    "accent_color": "#1f4b99", "logo_attachment_id": None,
    "intro_de": "vielen Dank für Ihre Anfrage. Gerne unterbreiten wir Ihnen folgendes Angebot:",
    "intro_en": "Thank you for your inquiry. We are pleased to submit the following quotation:",
    "terms_de": "Preise netto ab Werk zzgl. gesetzl. MwSt. Es gelten unsere Allgemeinen Verkaufs- und Lieferbedingungen.",
    "terms_en": "Prices net ex works plus statutory VAT. Our General Terms and Conditions of Sale and Delivery apply.",
    "closing_de": "Mit freundlichen Grüßen", "closing_en": "Kind regards",
}


@router.get("/app-settings")
def get_app_settings(db: Session = Depends(get_db), _: User = Depends(can_read)):
    st = db.get(AppSettings, 1)
    return {**DEFAULT_APP, **((st.data or {}) if st else {})}


@router.put("/app-settings")
def put_app_settings(data: dict, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    st = db.get(AppSettings, 1) or AppSettings(id=1, data={})
    db.add(st)
    st.data = {**DEFAULT_APP, **(st.data or {}), **{k: v for k, v in data.items() if k in DEFAULT_APP}}
    db.commit()
    return st.data


# ---------------- Benachrichtigungen ----------------
@router.get("/notifications")
def notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stored = db.scalars(select(Notification).where(Notification.user_id == user.id)
                        .order_by(Notification.read, Notification.created_at.desc()).limit(40)).all()
    items = [{"id": n.id, "kind": "nachricht", "title": n.title, "body": n.body, "link": n.link, "read": n.read,
              "created_at": n.created_at.isoformat()} for n in stored]
    # Laufende Hinweise (werden berechnet, nicht gespeichert)
    nowt = datetime.now(timezone.utc)
    end_today = nowt.replace(hour=23, minute=59, second=59)
    acts = db.scalars(select(Activity).where(Activity.owner_id == user.id, Activity.done.is_(False),
                                             Activity.due_at <= end_today).order_by(Activity.due_at)).unique().all()
    for a in acts[:15]:
        overdue = a.due_at < nowt
        items.append({"id": f"a{a.id}", "kind": "aufgabe", "title": ("Überfällig: " if overdue else "Heute: ") + a.subject,
                      "body": a.account.name if a.account else None, "link": "/aktivitaeten", "read": False,
                      "created_at": a.due_at.isoformat(), "severity": "critical" if overdue else "info"})
    soon = date.today() + timedelta(days=7)
    for q in db.scalars(select(Quote).where(Quote.owner_id == user.id, Quote.status == "versendet",
                                            Quote.valid_until <= soon)).unique().all():
        items.append({"id": f"q{q.id}", "kind": "angebot", "title": f"Angebot {q.number} läuft ab {q.valid_until.strftime('%d.%m.')}",
                      "body": q.account.name if q.account else None, "link": f"/angebote/{q.id}", "read": False,
                      "created_at": datetime.combine(q.valid_until, datetime.min.time()).isoformat(), "severity": "warning"})
    if user.role == "admin" or user.can_approve:
        n = db.query(Calculation).filter(Calculation.approval_status == "angefragt",
                                         Calculation.approval_requested_by_id != user.id).count()
        if n:
            items.append({"id": "approvals", "kind": "freigabe", "title": f"{n} Freigabe(n) warten auf Entscheidung",
                          "link": "/kalkulationen", "read": False, "created_at": nowt.isoformat(), "severity": "warning"})
    unread = sum(1 for i in items if not i["read"])
    return {"unread": unread, "items": items}


@router.post("/notifications/{nid}/read", status_code=204)
def mark_read(nid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.get(Notification, nid)
    if n and n.user_id == user.id:
        n.read = True
        db.commit()


@router.post("/notifications/read-all", status_code=204)
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for n in db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read.is_(False))):
        n.read = True
    db.commit()


# ---------------- Outlook / iCalendar ----------------
def _ics_escape(t: str) -> str:
    bs = chr(92)  # Backslash
    return (t or "").replace(bs, bs + bs).replace(";", bs + ";").replace(",", bs + ",").replace("\n", bs + "n")


def _vevent(a: Activity) -> str:
    start = (a.due_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    dur = 60 if a.type == "termin" else 15
    end = start + timedelta(minutes=dur)
    f = lambda d: d.strftime("%Y%m%dT%H%M%SZ")  # noqa: E731
    desc = " · ".join(x for x in [a.account.name if a.account else "", a.description or ""] if x)
    link = f"{settings.APP_URL.rstrip('/')}/aktivitaeten" if settings.APP_URL else ""
    return "\r\n".join([
        "BEGIN:VEVENT", f"UID:klarcrm-activity-{a.id}@klarcrm", f"DTSTAMP:{f(datetime.now(timezone.utc))}",
        f"DTSTART:{f(start)}", f"DTEND:{f(end)}", f"SUMMARY:{_ics_escape(a.subject)}",
        f"DESCRIPTION:{_ics_escape(desc + (chr(10) + link if link else ''))}",
        "STATUS:" + ("COMPLETED" if a.done else "CONFIRMED"),
        "BEGIN:VALARM", "TRIGGER:-PT15M", "ACTION:DISPLAY", f"DESCRIPTION:{_ics_escape(a.subject)}", "END:VALARM",
        "END:VEVENT"])


def _calendar(events: list[str], name: str) -> Response:
    body = "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//SB Thinkworks//KlarCRM//DE", "CALSCALE:GREGORIAN",
                        f"X-WR-CALNAME:{_ics_escape(name)}", *events, "END:VCALENDAR"]) + "\r\n"
    return Response(body, media_type="text/calendar; charset=utf-8")


@router.get("/activities/{act_id}/ics")
def activity_ics(act_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    a = db.get(Activity, act_id)
    if not a:
        raise HTTPException(404, "Aktivität nicht gefunden")
    return _calendar([_vevent(a)], "KlarCRM")


@router.get("/calendar/{token}.ics")
def calendar_feed(token: str, db: Session = Depends(get_db)):
    """Kalenderabo für Outlook (Kalender hinzufügen → Aus dem Internet). Token ersetzt die Anmeldung."""
    user = db.scalar(select(User).where(User.calendar_token == token, User.active.is_(True))) if len(token) >= 20 else None
    if not user:
        raise HTTPException(404, "Unbekannter Kalender")
    since = datetime.now(timezone.utc) - timedelta(days=30)
    acts = db.scalars(select(Activity).where(Activity.owner_id == user.id, Activity.due_at.isnot(None),
                                             Activity.due_at >= since, Activity.type != "notiz")).unique().all()
    return _calendar([_vevent(a) for a in acts], f"KlarCRM – {user.name}")


@router.get("/calendar-token")
def get_calendar_token(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.calendar_token:
        user.calendar_token = secrets.token_urlsafe(32)
        db.commit()
    return {"token": user.calendar_token, "path": f"/api/calendar/{user.calendar_token}.ics", "app_url": settings.APP_URL}


@router.post("/calendar-token/renew")
def renew_calendar_token(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.calendar_token = secrets.token_urlsafe(32)
    db.commit()
    return {"token": user.calendar_token, "path": f"/api/calendar/{user.calendar_token}.ics", "app_url": settings.APP_URL}
