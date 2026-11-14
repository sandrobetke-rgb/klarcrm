"""Session-Ereignisse: Preishistorie Material und Änderungsprotokoll (Audit-Trail)."""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from .context import current_user_id
from .models import AuditLog, Material, MaterialPrice, User

SKIP_TABLES = {"audit_log"}
SKIP_FIELDS = {"updated_at", "created_at"}
MASK_FIELDS = {"password_hash", "calendar_token"}
SUMMARY_JSON = {"inputs", "results", "analysis_results", "actuals"}  # große Strukturen nur als „geändert“ vermerken
ENTITY_LABELS = {
    "accounts": "Firma", "contacts": "Kontakt", "opportunities": "Verkaufschance", "activities": "Aktivität",
    "quotes": "Angebot", "quote_items": "Angebotsposition", "users": "Benutzer", "machines": "Maschine",
    "materials": "Material", "material_prices": "Materialpreis", "calc_settings": "Kalkulations-Parameter",
    "calculations": "Kalkulation", "calculation_versions": "Kalkulationsversion", "calculation_calls": "Anruf",
    "post_calculations": "Nachkalkulation", "calc_templates": "Vorlage", "attachments": "Dokument",
    "app_settings": "Firmeneinstellungen", "notifications": "Benachrichtigung",
}


@event.listens_for(Session, "before_flush")
def material_price_history(session, flush_context, instances):
    for obj in list(session.new) + list(session.dirty):
        if not isinstance(obj, Material):
            continue
        hist = inspect(obj).attrs.price_per_kg.history
        if obj in session.new or hist.has_changes():
            obj.price_valid_from = obj.price_valid_from if (obj in session.new and obj.price_valid_from) else date.today()
            session.add(MaterialPrice(material=obj, price_per_kg=obj.price_per_kg, valid_from=obj.price_valid_from,
                                      user_id=current_user_id.get(), note="Anlage" if obj in session.new else "Preisänderung"))


def _plain(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _label(obj) -> str | None:
    for attr in ("number", "article_name", "name", "subject", "title", "email", "description", "label"):
        v = getattr(obj, attr, None)
        if v:
            return str(v)[:250]
    if hasattr(obj, "first_name"):
        return f"{obj.first_name} {obj.last_name}"
    return None


def _ref(obj, table: str) -> str:
    for parent, fk in (("calculations", "calculation_id"), ("quotes", "quote_id"), ("materials", "material_id")):
        if getattr(obj, fk, None) and table != parent:
            return f"{parent}:{getattr(obj, fk)}"
    return f"{table}:{getattr(obj, 'id', None)}"


def _changes(obj, created: bool) -> dict:
    out = {}
    state = inspect(obj)
    for attr in state.mapper.column_attrs:
        key = attr.key
        if key in SKIP_FIELDS or key == "id":
            continue
        hist = state.attrs[key].history
        if created:
            new = getattr(obj, key)
            if new in (None, "", [], {}):
                continue
            old = None
        else:
            if not hist.has_changes():
                continue
            old = hist.deleted[0] if hist.deleted else None
            new = hist.added[0] if hist.added else None
        if key in MASK_FIELDS:
            out[key] = ["***", "***"]
        elif key in SUMMARY_JSON or isinstance(new, (dict, list)) or isinstance(old, (dict, list)):
            out[key] = [None, "(geändert)"] if not created else [None, "(angelegt)"]
        else:
            out[key] = [_plain(old), _plain(new)]
    return out


@event.listens_for(Session, "after_flush")
def audit_trail(session, flush_context):
    uid = current_user_id.get()
    rows = []
    groups = (("anlegen", session.new), ("ändern", session.dirty), ("löschen", session.deleted))
    for action, objs in groups:
        for obj in objs:
            table = getattr(obj, "__tablename__", None)
            if not table or table in SKIP_TABLES:
                continue
            if action == "ändern" and not session.is_modified(obj, include_collections=False):
                continue
            changes = {} if action == "löschen" else _changes(obj, action == "anlegen")
            if action == "ändern" and not changes:
                continue
            if action == "löschen":
                changes = {"gelöscht": [_label(obj), None]}
            rows.append({"ts": datetime.now(timezone.utc), "user_id": uid, "user_name": None, "action": action,
                         "entity": table, "entity_id": getattr(obj, "id", None), "label": _label(obj),
                         "ref": _ref(obj, table), "changes": changes})
    if not rows:
        return
    conn = session.connection()
    if uid:
        name = conn.execute(User.__table__.select().with_only_columns(User.name).where(User.id == uid)).scalar()
        for r in rows:
            r["user_name"] = name
    conn.execute(AuditLog.__table__.insert(), rows)
