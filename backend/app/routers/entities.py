from datetime import date, datetime, timedelta, timezone

from sqlalchemy import or_

from .. import schemas as s
from ..auth import admin_only
from ..crud import make_crud_router
from ..models import STAGE_PROBABILITY, Account, Activity, Contact, Opportunity

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
    if stage in ("gewonnen", "verloren") and stage != old_stage:
        values["closed_at"] = date.today()
    elif stage and stage not in ("gewonnen", "verloren"):
        values["closed_at"] = None
    return values


opportunities = make_crud_router(
    model=Opportunity,
    create_schema=s.OpportunityCreate,
    update_schema=s.OpportunityUpdate,
    out_schema=s.OpportunityOut,
    search_fields=["name", "source", "description"],
    filter_fields=["stage", "account_id", "owner_id", "contact_id"],
    default_sort="-updated_at",
    before_save=opportunity_before_save,
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
    filter_fields=["type", "done", "account_id", "contact_id", "opportunity_id", "owner_id"],
    default_sort="due_at",
    extra_filters=activity_filters,
)
