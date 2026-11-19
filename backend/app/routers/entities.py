from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import or_

from .. import schemas as s
from ..auth import admin_only
from ..crud import make_crud_router
from ..models import CLOSED_STAGES, STAGE_PROBABILITY, Account, Activity, Contact, Opportunity

accounts = make_crud_router(
    model=Account,
    create_schema=s.AccountCreate,
    update_schema=s.AccountUpdate,
    out_schema=s.AccountOut,
    search_fields=["name", "city", "industry", "email", "phone"],
    filter_fields=["type", "owner_id", "industry"],
    default_sort="name",
    delete_dependency=admin_only,  # Firmen nur durch Administratoren löschen (mit Protokoll)
)

contacts = make_crud_router(
    model=Contact,
    create_schema=s.ContactCreate,
    update_schema=s.ContactUpdate,
    out_schema=s.ContactOut,
    search_fields=["first_name", "last_name", "email", "position", "phone"],
    filter_fields=["account_id", "owner_id"],
    default_sort="last_name",
)


def opportunity_before_save(values: dict, obj):
    stage = values.get("stage")
    old_stage = obj.stage if obj else None
    # Wahrscheinlichkeit automatisch aus Phase, wenn nicht explizit gesetzt
    if stage and stage != old_stage and values.get("probability") is None:
        values["probability"] = STAGE_PROBABILITY[stage]
    if obj is None and values.get("probability") is None:
        values["probability"] = STAGE_PROBABILITY[values.get("stage") or "lead"]
    if "probability" in values and values["probability"] is None:
        values.pop("probability")
    if stage in ("verloren", "nicht_angeboten") and stage != old_stage and not (values.get("lost_reason") or "").strip():
        # REV01-P05: Verschieben nach „Verloren“ / „Nicht angeboten“ nur mit Grund
        raise HTTPException(400, "Verloren / nicht angeboten nur mit Grund – bitte Grund angeben")
    if stage in CLOSED_STAGES and stage != old_stage:
        values["closed_at"] = date.today()
    elif stage and stage not in CLOSED_STAGES:
        values["closed_at"] = None
        values.setdefault("lost_reason", None)
        values.setdefault("lost_code", None)
    if stage == "verhandlung":
        values["final_round"] = True     # Endrunde merken (Auswertung gewonnen/verloren aus der Endrunde)
    if obj is None:
        values["kind"] = values.get("kind") or ("lead" if (values.get("stage") or "lead") == "lead" else "anfrage")
    return values


def opportunity_after_create(db, obj):
    from ..inquiry import next_inquiry_number  # noqa: PLC0415
    if not obj.number:
        obj.number = next_inquiry_number(db)
        db.commit()


def opportunity_after_update(db, obj, old, user):
    """Karte von Hand verschoben → Artikel nachziehen (Gewonnen / Verloren / Nicht angeboten)."""
    from ..inquiry import calcs_of, cascade_stage  # noqa: PLC0415
    if "stage" in old and old["stage"] != obj.stage:
        cascade_stage(db, obj, old["stage"])
    if "probability" in old:
        for c in calcs_of(db, obj.id):
            if c.status not in ("verloren", "kein_angebot", "gewonnen", "zurueckgestellt"):
                c.probability = obj.probability


opportunities = make_crud_router(
    model=Opportunity,
    create_schema=s.OpportunityCreate,
    update_schema=s.OpportunityUpdate,
    out_schema=s.OpportunityOut,
    search_fields=["name", "number", "source", "description"],
    filter_fields=["stage", "account_id", "owner_id", "contact_id", "kind"],
    default_sort="-updated_at",
    before_save=opportunity_before_save, after_create=opportunity_after_create, after_update=opportunity_after_update,
)


def activity_filters(stmt, params):
    """due=overdue|today|week|open"""
    due = params.get("due")
    nowt = datetime.now(timezone.utc)
    start_today = nowt.replace(hour=0, minute=0, second=0, microsecond=0)
    if due == "overdue":
        stmt = stmt.where(Activity.done.is_(False), Activity.due_at < nowt)
    elif due == "today":
        stmt = stmt.where(Activity.due_at >= start_today, Activity.due_at < start_today + timedelta(days=1))
    elif due == "week":
        stmt = stmt.where(Activity.due_at >= start_today, Activity.due_at < start_today + timedelta(days=7))
    return stmt


def activity_before_save(values: dict, obj):
    return values


activities = make_crud_router(
    model=Activity,
    create_schema=s.ActivityCreate,
    update_schema=s.ActivityUpdate,
    out_schema=s.ActivityOut,
    search_fields=["subject", "description"],
    filter_fields=["type", "done", "account_id", "contact_id", "opportunity_id", "owner_id", "quote_id", "kind"],
    default_sort="due_at",
    extra_filters=activity_filters,
)
