"""Import von Firmen, Kontakten, Maschinen, Materialien und Zukaufteilen aus CSV/Excel:
Vorlage → Vorschau (neu / Aktualisierung / Fehler) → Übernahme. Alle Änderungen landen im Änderungsprotokoll."""
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import can_write
from ..database import get_db
from ..importer import ENTITIES, auto_mapping, parse_rows, read_table, template_csv
from ..models import Account, Contact, Machine, Material, PurchasedPart, Site, User

router = APIRouter()
MODELS = {"accounts": Account, "contacts": Contact, "machines": Machine, "materials": Material,
          "purchased-parts": PurchasedPart}
MAX_ROWS = 5000


def _cfg(entity: str) -> dict:
    if entity not in ENTITIES:
        raise HTTPException(404, "Unbekannter Importtyp")
    return ENTITIES[entity]


def _check_rights(entity: str, user: User):
    if ENTITIES[entity].get("admin") and user.role != "admin":
        raise HTTPException(403, "Stammdaten-Import nur für Administratoren")


def _resolve(db: Session, entity: str, parsed: list[dict]) -> list[dict]:
    """Referenzen auflösen (Firma, Standort) und bestehende Datensätze finden (neu / aktualisieren)."""
    model = MODELS[entity]
    accounts = {a.name.strip().lower(): a.id for a in db.scalars(select(Account)).unique()}
    sites = {}
    for st in db.scalars(select(Site)):
        sites[st.name.strip().lower()] = st.id
        sites[st.code.strip().lower()] = st.id
    seen = {}
    for p in parsed:
        v = p["values"]
        if "account_id" in v:
            aid = accounts.get(str(v["account_id"]).strip().lower())
            if aid:
                p["ref_label"] = v["account_id"]
                v["account_id"] = aid
            else:
                p["errors"].append(f"Firma „{v['account_id']}“ nicht gefunden – zuerst Firmen importieren")
                v.pop("account_id")
        if "site_id" in v:
            sid = sites.get(str(v["site_id"]).strip().lower())
            if sid:
                v["site_id"] = sid
            else:
                p["errors"].append(f"Standort „{v['site_id']}“ unbekannt")
                v.pop("site_id")
        existing = None
        if entity == "contacts":
            if v.get("email"):
                existing = db.scalars(select(Contact).where(func.lower(Contact.email) == v["email"].lower())).first()
            if not existing and v.get("last_name") and v.get("account_id"):
                existing = db.scalars(select(Contact).where(Contact.account_id == v["account_id"],
                                                            func.lower(Contact.last_name) == v["last_name"].lower(),
                                                            func.lower(Contact.first_name) == (v.get("first_name") or "").lower())).first()
            key = (v.get("email") or "").lower() or f"{v.get('account_id')}|{v.get('last_name')}|{v.get('first_name')}".lower()
        else:
            for f in ENTITIES[entity]["match"]:
                if v.get(f):
                    existing = db.scalars(select(model).where(func.lower(getattr(model, f)) == str(v[f]).lower())).first()
                    if existing:
                        break
            key = "|".join(str(v.get(f) or "").lower() for f in ENTITIES[entity]["match"])
        if key and key in seen:
            p["errors"].append(f"doppelt in der Datei (wie Zeile {seen[key]})")
        elif key:
            seen[key] = p["row"]
        p["id"] = existing.id if existing else None
        p["status"] = "fehler" if p["errors"] else ("aktualisieren" if existing else "neu")
        if existing and not p["errors"]:
            p["changes"] = {k: [_plain(getattr(existing, k, None)), _plain(val)] for k, val in v.items()
                            if _plain(getattr(existing, k, None)) != _plain(val)}
            if not p["changes"]:
                p["status"] = "unverändert"
    return parsed


def _plain(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


def _prepare(entity, file_bytes, filename, mapping_json, db):
    head, rows = read_table(file_bytes, filename)
    if not head:
        raise HTTPException(400, "Datei ist leer oder nicht lesbar (CSV mit Semikolon oder Excel .xlsx)")
    if len(rows) > MAX_ROWS:
        raise HTTPException(400, f"Höchstens {MAX_ROWS} Zeilen je Import")
    mapping = json.loads(mapping_json) if mapping_json else auto_mapping(entity, head)
    return head, rows, mapping, _resolve(db, entity, parse_rows(entity, rows, mapping))


@router.get("/{entity}/template")
def template(entity: str, _: User = Depends(can_write)):
    _cfg(entity)
    return Response(template_csv(entity), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="Vorlage_{entity}.csv"'})


@router.get("/{entity}/fields")
def fields(entity: str, _: User = Depends(can_write)):
    cfg = _cfg(entity)
    return {"label": cfg["label"], "fields": [{"key": k, "label": l, "required": r} for k, l, _t, r, _a in cfg["fields"]]}


@router.post("/{entity}/preview")
async def preview(entity: str, file: UploadFile = File(...), mapping: str | None = Form(None),
                  db: Session = Depends(get_db), user: User = Depends(can_write)):
    _cfg(entity)
    _check_rights(entity, user)
    head, rows, mp, parsed = _prepare(entity, await file.read(), file.filename or "", mapping, db)
    counts = {}
    for p in parsed:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    return {"headers": head, "mapping": mp, "rows": [{**p, "values": {k: _plain(v) for k, v in p["values"].items()},
                                                       "raw": rows[i]} for i, p in enumerate(parsed[:500])],
            "total": len(parsed), "counts": counts}


@router.post("/{entity}/commit")
async def commit(entity: str, file: UploadFile = File(...), mapping: str | None = Form(None),
                 update_existing: bool = Form(True), db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Übernimmt alle fehlerfreien Zeilen; Zeilen mit Fehlern werden übersprungen und gemeldet."""
    _cfg(entity)
    _check_rights(entity, user)
    _, _, _, parsed = _prepare(entity, await file.read(), file.filename or "", mapping, db)
    model = MODELS[entity]
    created = updated = skipped = 0
    for p in parsed:
        if p["status"] == "fehler":
            skipped += 1
            continue
        if p["id"]:
            if not update_existing or p["status"] == "unverändert":
                continue
            obj = db.get(model, p["id"])
            for k, v in p["values"].items():
                setattr(obj, k, v)
            updated += 1
        else:
            vals = dict(p["values"])
            if entity in ("accounts", "contacts"):
                vals.setdefault("owner_id", user.id)
            if entity == "contacts":
                vals.setdefault("first_name", "")
            if entity == "accounts":
                vals.setdefault("type", "kunde")
            db.add(model(**vals))
            created += 1
    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped,
            "errors": [{"row": p["row"], "errors": p["errors"]} for p in parsed if p["status"] == "fehler"][:200]}
