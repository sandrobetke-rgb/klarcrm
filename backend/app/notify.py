"""Benachrichtigungen: in der Anwendung und – falls SMTP konfiguriert – per E-Mail."""
import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from .config import settings
from .models import Notification, User

log = logging.getLogger("klarcrm.notify")


def send_mail(to: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST or not to:
        return False
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = settings.SMTP_FROM, to, subject
        msg.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            if settings.SMTP_STARTTLS:
                s.starttls()
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
        return True
    except Exception as e:  # Mailversand darf den Ablauf nie blockieren
        log.warning("E-Mail an %s fehlgeschlagen: %s", to, e)
        return False


def notify(db: Session, user_id: int, title: str, body: str | None = None, link: str | None = None, mail: bool = True):
    db.add(Notification(user_id=user_id, title=title, body=body, link=link))
    if mail:
        user = db.get(User, user_id)
        if user and user.email:
            url = f"{settings.APP_URL.rstrip('/')}{link}" if link and settings.APP_URL else ""
            send_mail(user.email, f"[KlarCRM] {title}", f"{body or ''}\n\n{url}".strip())
