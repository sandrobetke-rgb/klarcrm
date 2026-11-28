"""Änderungsprotokoll (REV01 ff.) und Dokumentation (Lastenheft, Benutzerbeschreibung) im Programm, Word-Export."""
import io
import re
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import schemas as s
from ..auth import can_read, can_write
from ..crud import make_crud_router
from ..database import get_db
from ..models import ChangeRequest, User


KIND_KEYS = {"fehler": "fehler", "wunsch": "wunsch", "doku": "doku", "dokumentation": "doku"}


def _cr_before_save(values: dict, obj, user=None):
    """Neue Wünsche bekommen automatisch eine Nummer (WUN-0001) und den Melder; Prüfer und Prüfdatum werden beim
    Prüfergebnis automatisch gesetzt (WUN-0001). Neue Wünsche sind „eingereicht“, bis ein Administrator sie freigibt.
    Art: Fehler/Wunsch/Dokumentation werden als Schlüssel gespeichert, alles andere als Freitext."""
    from fastapi import HTTPException  # noqa: PLC0415
    is_admin = bool(user and user.role == "admin")
    if values.get("kind"):
        k = values["kind"].strip()
        values["kind"] = KIND_KEYS.get(k.lower(), k)
    if obj is None:
        if not values.get("code"):
            values["code"] = None  # Nummer WUN-0001 … nach dem Anlegen (number_new_requests)
        if user and not (values.get("requested_by") or "").strip():
            values["requested_by"] = user.name
        if not is_admin:
            values["status"] = "eingereicht"
        elif values.get("status") in (None, "", "offen", "eingereicht"):
            values["status"] = "freigegeben"     # vom Administrator angelegt = gleich freigegeben
    new_status = values.get("status")
    old_status = obj.status if obj else None
    if new_status and new_status != old_status:
        if new_status == "freigegeben" and not is_admin:
            raise HTTPException(403, "Änderungswünsche gibt nur ein Administrator frei")
        if old_status == "eingereicht" and new_status not in ("freigegeben", "abgelehnt", "eingereicht") and not is_admin:
            raise HTTPException(403, "Erst nach Freigabe durch einen Administrator bearbeiten")
        if new_status in ("geprueft", "nachbessern"):
            if new_status == "nachbessern" and not (values.get("test_result") or "").strip():
                raise HTTPException(400, "„Nicht in Ordnung“: bitte beschreiben, was nicht passt")
            if user:
                values["tested_by"] = user.name
            values["tested_at"] = date.today()
    return values


changes = make_crud_router(
    model=ChangeRequest, create_schema=s.ChangeRequestBase, update_schema=s.ChangeRequestUpdate, out_schema=s.ChangeRequestOut,
    search_fields=["code", "title", "description", "area", "solution"], filter_fields=["status", "priority", "phase", "revision", "kind", "area", "check_version"],
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


# ------------------------------------------------------------------ REV04-02 Prüfseite je Update
checks = APIRouter()
CHECK_FIELDS = ("id", "code", "area", "kind", "title", "description", "solution", "test_steps", "expected", "check_link",
                "check_order", "status", "test_result", "tested_by", "tested_at", "superseded_by")


def _accepted(db: Session) -> dict:
    from ..models import CalcSettings  # noqa: PLC0415
    cs = db.get(CalcSettings, 1)
    return dict((cs.data or {}).get("_accepted") or {}) if cs else {}


@checks.get("")
def check_list(version: str | None = None, db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Punkte eines Updates in Prüfreihenfolge, Zähler und Abnahme."""
    from ..version import APP_VERSION  # noqa: PLC0415
    v = version or APP_VERSION
    rows = db.scalars(select(ChangeRequest).where(ChangeRequest.check_version == v,
                                                  ChangeRequest.status.not_in(("ueberholt", "abgelehnt")))
                      .order_by(ChangeRequest.check_order, ChangeRequest.code)).all()
    items = [{k: getattr(r, k) for k in CHECK_FIELDS} for r in rows]
    versions = sorted({x for (x,) in db.query(ChangeRequest.check_version).filter(ChangeRequest.check_version.is_not(None)).all()},
                      key=lambda x: [int(p) for p in x.split(".") if p.isdigit()], reverse=True)
    older = db.scalar(select(func.count()).select_from(ChangeRequest).where(
        ChangeRequest.status.in_(("umgesetzt", "nachbessern")),
        (ChangeRequest.check_version.is_(None)) | (ChangeRequest.check_version != v))) or 0
    # v1.34: offene Prüfpunkte anderer Updates (z. B. wenn ein Update übersprungen und das nächste direkt eingespielt wurde)
    open_by = {}
    for (cv,) in db.query(ChangeRequest.check_version).filter(ChangeRequest.check_version.is_not(None), ChangeRequest.check_version != v,
                                                             ChangeRequest.status.in_(("umgesetzt", "nachbessern"))).all():
        open_by[cv] = open_by.get(cv, 0) + 1
    return {"version": v, "current": APP_VERSION, "versions": versions or [v], "items": items, "total": len(items),
            "open_by_version": dict(sorted(open_by.items(), reverse=True)),
            "done": sum(1 for i in items if i["status"] == "geprueft"),
            "failed": sum(1 for i in items if i["status"] == "nachbessern"),
            "accepted": _accepted(db).get(v), "older_open": older}


@checks.post("/accept")
def check_accept(payload: dict, db: Session = Depends(get_db), user: User = Depends(can_read)):
    """„v1.xx abgenommen“ – nur Administrator, nur wenn alle Punkte „passt“."""
    from ..models import CalcSettings  # noqa: PLC0415
    if user.role != "admin":
        raise HTTPException(403, "Die Abnahme eines Updates erklärt ein Administrator")
    v = str(payload.get("version") or "")
    data = check_list(v, db, user)
    if not data["total"] or data["done"] < data["total"]:
        raise HTTPException(400, "Erst alle Punkte mit „✓ passt“ prüfen")
    cs = db.get(CalcSettings, 1)
    acc = _accepted(db)
    from datetime import datetime, timezone  # noqa: PLC0415
    acc[v] = {"by": user.name, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    cs.data = {**(cs.data or {}), "_accepted": acc}
    db.commit()
    return acc[v]


@checks.post("/{item_id}")
def check_item(item_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(can_write)):
    """✓ passt / ✗ passt nicht (dann Text Pflicht) / ok = null: zurücksetzen. Prüfer und Datum werden gesetzt."""
    cr = db.get(ChangeRequest, item_id)
    if not cr:
        raise HTTPException(404, "Punkt nicht gefunden")
    ok, note = payload.get("ok"), (payload.get("note") or "").strip()
    if ok is None:
        cr.status, cr.tested_by, cr.tested_at = "umgesetzt", None, None
    elif ok:
        cr.status, cr.test_result = "geprueft", note or "passt"
        cr.tested_by, cr.tested_at = user.name, date.today()
    else:
        if not note:
            raise HTTPException(400, "„Passt nicht“: bitte kurz beschreiben, was nicht passt")
        cr.status, cr.test_result = "nachbessern", note
        cr.tested_by, cr.tested_at = user.name, date.today()
    db.commit()
    return {k: getattr(cr, k) for k in CHECK_FIELDS}
