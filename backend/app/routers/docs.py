"""Änderungsprotokoll (REV01 ff.) und Dokumentation (Lastenheft, Benutzerbeschreibung) im Programm, Word-Export."""
import io
import re
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas as s
from ..auth import can_read
from ..crud import make_crud_router
from ..database import get_db
from ..models import ChangeRequest, User


KIND_KEYS = {"fehler": "fehler", "wunsch": "wunsch", "doku": "doku", "dokumentation": "doku"}


def _cr_before_save(values: dict, obj):
    """Neue Wünsche bekommen automatisch eine Nummer (WUN-0001), Prüfdatum beim Setzen auf „geprüft“.
    Art: Fehler/Wunsch/Dokumentation werden als Schlüssel gespeichert, alles andere als Freitext."""
    if values.get("kind"):
        k = values["kind"].strip()
        values["kind"] = KIND_KEYS.get(k.lower(), k)
    if obj is None and not values.get("code"):
        values["code"] = None  # Nummer WUN-0001 … nach dem Anlegen (number_new_requests)
    if values.get("status") == "geprueft" and not values.get("tested_at") and not (obj and obj.tested_at):
        values["tested_at"] = date.today()
    return values


changes = make_crud_router(
    model=ChangeRequest, create_schema=s.ChangeRequestBase, update_schema=s.ChangeRequestUpdate, out_schema=s.ChangeRequestOut,
    search_fields=["code", "title", "description", "area", "solution"], filter_fields=["status", "priority", "phase", "revision", "kind", "area"],
    default_sort="code", before_save=_cr_before_save, after_create=lambda db, obj: number_new_requests(db),
)


def number_new_requests(db: Session):
    """Einträge ohne Code (in der Oberfläche angelegt) erhalten WUN-0001 …"""
    rows = db.scalars(select(ChangeRequest).where(ChangeRequest.code.is_(None))).all()
    if not rows:
        return
    last = [int(c[4:]) for c in db.scalars(select(ChangeRequest.code).where(ChangeRequest.code.like("WUN-%"))).all() if c[4:].isdigit()]
    n = max(last, default=0)
    for r in rows:
        n += 1
        r.code = f"WUN-{n:04d}"
    db.commit()


# ------------------------------------------------------------------ Dokumentation
router = APIRouter()
DOCS = {"lastenheft": ("LASTENHEFT.md", "Lastenheft"), "beschreibung": ("BESCHREIBUNG.md", "Benutzerbeschreibung")}


def _docs_dir() -> Path:
    here = Path(__file__).resolve()
    for cand in (here.parents[2] / "docs", here.parents[3] / "docs", Path("/app/docs")):
        if cand.is_dir():
            return cand
    raise HTTPException(404, "Dokumentation nicht gefunden (Ordner docs fehlt im Container)")


def _read(name: str) -> tuple[str, str]:
    if name not in DOCS:
        raise HTTPException(404, "Dokument unbekannt")
    fn, title = DOCS[name]
    p = _docs_dir() / fn
    if not p.exists():
        raise HTTPException(404, f"{fn} nicht gefunden")
    return p.read_text(encoding="utf-8"), title


@router.get("")
def list_docs(_: User = Depends(can_read)):
    out = []
    for key, (fn, title) in DOCS.items():
        try:
            txt = (_docs_dir() / fn).read_text(encoding="utf-8")
            ver = re.search(r"(?:Dokumentversion|Version)\*{0,2}\s*\|\s*(\d+\.\d+)", txt)
            out.append({"key": key, "title": title, "version": ver.group(1) if ver else None})
        except (HTTPException, OSError):
            pass
    return out


@router.get("/{name}")
def get_doc(name: str, _: User = Depends(can_read)):
    md, title = _read(name)
    return {"key": name, "title": title, "markdown": md}


@router.get("/{name}/docx")
def get_doc_docx(name: str, _: User = Depends(can_read)):
    from ..md_docx import markdown_to_docx  # noqa: PLC0415
    md, title = _read(name)
    buf = io.BytesIO()
    markdown_to_docx(md, title).save(buf)
    buf.seek(0)
    fn = f"KlarCRM_{title}_{date.today():%Y-%m-%d}.docx"
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             headers={"Content-Disposition": f'attachment; filename="{fn}"'})
