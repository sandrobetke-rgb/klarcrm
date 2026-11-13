"""Generischer CRUD-Router: Liste mit Suche/Filter/Sortierung/Paging, Detail, Anlegen, Ändern, Löschen."""
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .auth import can_read, can_write
from .database import get_db
from .models import User


def make_crud_router(
    *,
    model,
    create_schema,
    update_schema,
    out_schema,
    search_fields: list[str],
    filter_fields: list[str],
    default_sort: str = "-updated_at",
    before_save: Callable | None = None,
    extra_filters: Callable | None = None,
) -> APIRouter:
    router = APIRouter()
    allowed_sort = {c.name for c in model.__table__.columns}

    @router.get("", response_model=dict)
    def list_items(
        request: Request,
        q: str | None = None,
        sort: str = default_sort,
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db),
        _: User = Depends(can_read),
    ):
        stmt = select(model)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(*[getattr(model, f).ilike(like) for f in search_fields]))
        for f in filter_fields:
            val = request.query_params.get(f)
            if val not in (None, ""):
                col = getattr(model, f)
                if val == "null":
                    stmt = stmt.where(col.is_(None))
                elif "," in val:
                    stmt = stmt.where(col.in_(val.split(",")))
                elif col.type.python_type is bool:
                    stmt = stmt.where(col.is_(val.lower() in ("1", "true", "ja")))
                else:
                    stmt = stmt.where(col == col.type.python_type(val))
        if extra_filters:
            stmt = extra_filters(stmt, request.query_params)

        total = db.scalar(select(func.count()).select_from(stmt.subquery()))
        desc = sort.startswith("-")
        key = sort.lstrip("-")
        if key not in allowed_sort:
            key = default_sort.lstrip("-")
        col = getattr(model, key)
        stmt = stmt.order_by(col.desc().nulls_last() if desc else col.asc().nulls_last(), model.id.desc())
        rows = db.scalars(stmt.offset(offset).limit(limit)).unique().all()
        return {"total": total, "items": [out_schema.model_validate(r).model_dump(mode="json") for r in rows]}

    @router.get("/{item_id}", response_model=out_schema)
    def get_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(404, "Nicht gefunden")
        return obj

    @router.post("", response_model=out_schema, status_code=201)
    def create_item(data: create_schema, db: Session = Depends(get_db), user: User = Depends(can_write)):
        values = data.model_dump()
        if "owner_id" in values and not values.get("owner_id"):
            values["owner_id"] = user.id
        obj = model()
        if before_save:
            values = before_save(values, None)
        for k, v in values.items():
            setattr(obj, k, v)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.patch("/{item_id}", response_model=out_schema)
    def update_item(item_id: int, data: update_schema, db: Session = Depends(get_db), _: User = Depends(can_write)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(404, "Nicht gefunden")
        values = data.model_dump(exclude_unset=True)
        if before_save:
            values = before_save(values, obj)
        for k, v in values.items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    @router.delete("/{item_id}", status_code=204)
    def delete_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(can_write)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(404, "Nicht gefunden")
        db.delete(obj)
        db.commit()

    return router
