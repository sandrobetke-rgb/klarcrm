"""Preisliste: VK-Artikel, Materialpreise, Preisänderungsvorgänge, Import und Export."""
import io
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..auth import can_read, can_write
from ..database import get_db
from ..models import (Material, MaterialPriceHistory, PriceArticle, PriceArticleHistory, PriceArticleMaterial,
                      PriceArticlePart, PriceChange, PriceImpact, User)
from ..pricelist import (ART_FIELDS, MAT_FIELDS, NUM, STATUSES, add_history, annual_effect, create_material_change,
                         decide_impact, detect, find_account, find_material, impact_rows, match_article, next_change_number, open_gap,
                         parse_values, r4, read_sheet)

router = APIRouter()


# ------------------------------------------------------------------ Schemas
class MatLine(BaseModel):
    material_id: int | None = None
    name: str | None = None
    weight_g: float | None = None
    price_basis: float | None = None


class PartLine(BaseModel):
    name: str = Field(min_length=1)
    qty_per_part: float = 1
    price_basis: float | None = None
    current_price: float | None = None
    supplier: str | None = None


class ArticleIn(BaseModel):
    account_id: int | None = None
    article_no: str | None = None
    customer_part_no: str | None = None
    description: str | None = None
    location: str | None = None
    price_unit: int = Field(default=100, ge=1)
    currency: str = "EUR"
    price: float = 0
    price_valid_from: date | None = None
    forecast_qty: float | None = None
    qty_last_year: float | None = None
    revenue_last_year: float | None = None
    moq: float | None = None
    shot_weight_g: float | None = None
    part_weight_g: float | None = None
    mgk_pct: float | None = 8
    surcharge_pct: float | None = 0
    ratio_per_unit: float | None = 0
    contract_bound: bool | None = False
    contract_until: date | None = None
    contract_note: str | None = None
    calculation_id: int | None = None
    comment: str | None = None
    active: bool = True
    materials: list[MatLine] = []
    parts: list[PartLine] = []
    price_note: str | None = None     # Grund bei manueller Preisänderung (Historie)


def article_out(a: PriceArticle, light: bool = False) -> dict:
    gap = open_gap(a)
    d = {"id": a.id, "account_id": a.account_id, "account": a.account.name if a.account else None,
         "article_no": a.article_no, "customer_part_no": a.customer_part_no, "description": a.description,
         "location": a.location, "price_unit": a.price_unit, "currency": a.currency, "price": a.price,
         "price_valid_from": a.price_valid_from, "forecast_qty": a.forecast_qty,
         "annual_revenue": round(a.price * (a.forecast_qty or 0) / (a.price_unit or 1), 2),
         "contract_bound": a.contract_bound, "contract_until": a.contract_until, "contract_note": a.contract_note,
         "active": a.active, "open_gap": r4(gap), "open_gap_annual": round(annual_effect(gap, a.forecast_qty, a.price_unit), 2),
         "materials": [{"material_id": m.material_id, "name": m.material.name if m.material else m.name,
                        "number": m.material.number if m.material else None, "weight_g": m.weight_g, "price_basis": m.price_basis,
                        "current_price": m.material.price_per_kg if m.material else None} for m in a.materials],
         "parts": [{"name": p.name, "qty_per_part": p.qty_per_part, "price_basis": p.price_basis,
                    "current_price": p.current_price, "supplier": p.supplier} for p in a.parts]}
    if not light:
        d.update({"qty_last_year": a.qty_last_year, "revenue_last_year": a.revenue_last_year, "moq": a.moq,
                  "shot_weight_g": a.shot_weight_g, "part_weight_g": a.part_weight_g, "mgk_pct": a.mgk_pct,
                  "surcharge_pct": a.surcharge_pct, "ratio_per_unit": a.ratio_per_unit, "calculation_id": a.calculation_id,
                  "comment": a.comment})
    return d


def _set_lines(a: PriceArticle, data: ArticleIn):
    a.materials = [PriceArticleMaterial(position=i + 1, **m.model_dump()) for i, m in enumerate(data.materials)
                   if m.material_id or (m.name or "").strip()]
    a.parts = [PriceArticlePart(position=i + 1, **p.model_dump()) for i, p in enumerate(data.parts)]


# ------------------------------------------------------------------ Artikel
@router.get("/articles")
def list_articles(q: str | None = None, account_id: int | None = None, material_id: int | None = None,
                  contract: str | None = None, gap: bool = False, active: bool | None = True,
                  limit: int = Query(1000, le=5000), db: Session = Depends(get_db), _: User = Depends(can_read)):
    stmt = select(PriceArticle)
    if active is not None:
        stmt = stmt.where(PriceArticle.active.is_(active))
    if account_id:
        stmt = stmt.where(PriceArticle.account_id == account_id)
    if material_id:
        stmt = stmt.where(PriceArticle.id.in_(select(PriceArticleMaterial.article_id).where(PriceArticleMaterial.material_id == material_id)))
    if contract == "ja":
        stmt = stmt.where(PriceArticle.contract_bound.is_(True))
    elif contract == "nein":
        stmt = stmt.where(or_(PriceArticle.contract_bound.is_(False), PriceArticle.contract_bound.is_(None)))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(PriceArticle.article_no.ilike(like), PriceArticle.customer_part_no.ilike(like),
                              PriceArticle.description.ilike(like), PriceArticle.comment.ilike(like)))
    rows = db.scalars(stmt.order_by(PriceArticle.account_id, PriceArticle.article_no).limit(limit)).unique().all()
    items = [article_out(a, light=True) for a in rows]
    if gap:
        items = [i for i in items if (i["open_gap"] or 0) > 0.00005]
    return {"total": len(items), "items": items,
            "sum": {"annual_revenue": round(sum(i["annual_revenue"] for i in items), 2),
                    "open_gap_annual": round(sum(i["open_gap_annual"] for i in items), 2)}}


@router.get("/articles/{aid}")
def get_article(aid: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    a = db.get(PriceArticle, aid)
    if not a:
        raise HTTPException(404, "Artikel nicht gefunden")
    hist = db.scalars(select(PriceArticleHistory).where(PriceArticleHistory.article_id == aid)
                      .order_by(PriceArticleHistory.created_at.desc())).all()
    imps = db.scalars(select(PriceImpact).where(PriceImpact.article_id == aid).order_by(PriceImpact.id.desc())).unique().all()
    users = {u.id: u.name for u in db.scalars(select(User)).all()}
    chg = {c.id: c for c in db.scalars(select(PriceChange).where(PriceChange.id.in_([i.change_id for i in imps] or [0]))).unique().all()}
    return {**article_out(a),
            "history": [{"id": h.id, "price": h.price, "old_price": h.old_price, "valid_from": h.valid_from, "source": h.source,
                         "note": h.note, "change_id": h.change_id, "by": users.get(h.created_by_id), "at": h.created_at} for h in hist],
            "impacts": [{"id": i.id, "change_id": i.change_id, "change_number": chg[i.change_id].number,
                         "change_title": chg[i.change_id].title, "delta": i.delta, "new_price": i.new_price,
                         "annual_effect": i.annual_effect, "status": i.status, "note": i.note, "passed_price": i.passed_price,
                         "effective_date": i.effective_date, "by": users.get(i.decided_by_id)} for i in imps]}


@router.post("/articles", status_code=201)
def create_article(data: ArticleIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    a = PriceArticle(**data.model_dump(exclude={"materials", "parts", "price_note", "price"}), price=0)
    _set_lines(a, data)
    db.add(a)
    db.flush()
    add_history(db, a, data.price, "erstanlage", user, data.price_valid_from, data.price_note)
    db.commit()
    return article_out(a)


@router.patch("/articles/{aid}")
def update_article(aid: int, data: ArticleIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    a = db.get(PriceArticle, aid)
    if not a:
        raise HTTPException(404, "Artikel nicht gefunden")
    vals = data.model_dump(exclude={"materials", "parts", "price_note", "price"})
    for k, v in vals.items():
        setattr(a, k, v)
    _set_lines(a, data)
    if abs((a.price or 0) - data.price) > 1e-9:
        add_history(db, a, data.price, "manuell", user, data.price_valid_from or date.today(), data.price_note)
    db.commit()
    return article_out(a)


@router.delete("/articles/{aid}", status_code=204)
def delete_article(aid: int, db: Session = Depends(get_db), user: User = Depends(can_write)):
    a = db.get(PriceArticle, aid)
    if not a:
        raise HTTPException(404, "Artikel nicht gefunden")
    if db.scalars(select(PriceArticleHistory).where(PriceArticleHistory.article_id == aid)).first() and user.role != "admin":
        raise HTTPException(409, "Artikel hat eine Preishistorie – bitte deaktivieren statt löschen (Löschen nur Admin)")
    db.delete(a)
    db.commit()


# ------------------------------------------------------------------ Materialpreise
@router.get("/materials")
def list_materials(db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Materialien mit aktuellem Preis, Anzahl Artikel und letzter Änderung."""
    counts = dict(db.execute(select(PriceArticleMaterial.material_id, func.count(func.distinct(PriceArticleMaterial.article_id)))
                             .group_by(PriceArticleMaterial.material_id)).all())
    last = {}
    for h in db.scalars(select(MaterialPriceHistory).order_by(MaterialPriceHistory.created_at)).all():
        last[h.material_id] = h
    out = []
    for m in db.scalars(select(Material).where(Material.active.is_(True)).order_by(Material.name)).all():
        h = last.get(m.id)
        out.append({"id": m.id, "number": m.number, "name": m.name, "family": m.family, "supplier": m.supplier,
                    "price_per_kg": m.price_per_kg, "price_valid_from": m.price_valid_from, "articles": counts.get(m.id, 0),
                    "last_change": {"old": h.old_price, "new": h.price_per_kg, "valid_from": h.valid_from, "source": h.source} if h else None})
    return out


@router.get("/materials/{mid}/history")
def material_history(mid: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    users = {u.id: u.name for u in db.scalars(select(User)).all()}
    rows = db.scalars(select(MaterialPriceHistory).where(MaterialPriceHistory.material_id == mid)
                      .order_by(MaterialPriceHistory.created_at.desc())).all()
    return [{"price": h.price_per_kg, "old_price": h.old_price, "valid_from": h.valid_from, "source": h.source, "note": h.note,
             "change_id": h.change_id, "by": users.get(h.created_by_id), "at": h.created_at} for h in rows]


class MatChangeItem(BaseModel):
    material_id: int
    new_price: float = Field(gt=0)


class MatChangeIn(BaseModel):
    items: list[MatChangeItem]
    valid_from: date | None = None
    note: str | None = None
    title: str | None = None


@router.post("/material-change/preview")
def material_change_preview(data: MatChangeIn, db: Session = Depends(get_db), _: User = Depends(can_read)):
    """Neuen Materialpreis eingeben → betroffene Artikel mit Δ je PE und Jahreseffekt (ohne zu speichern)."""
    rows = impact_rows(db, {i.material_id: i.new_price for i in data.items})
    return {"rows": rows, "count": len(rows), "annual_effect": round(sum(r["annual_effect"] for r in rows), 2),
            "contract_bound": sum(1 for r in rows if r["contract_bound"])}


@router.post("/material-change", status_code=201)
def material_change(data: MatChangeIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    items = []
    for i in data.items:
        m = db.get(Material, i.material_id)
        if not m:
            raise HTTPException(404, f"Material {i.material_id} nicht gefunden")
        items.append((m, i.new_price))
    ch = create_material_change(db, user, items, data.valid_from, data.note, "material", data.title)
    db.commit()
    return {"id": ch.id, "number": ch.number, "impacts": len(ch.impacts)}


# ------------------------------------------------------------------ Preisänderungsvorgänge
def change_out(c: PriceChange, users: dict, with_impacts: bool = False) -> dict:
    cnt = {k: 0 for k in STATUSES}
    eff = {k: 0.0 for k in STATUSES}
    for i in c.impacts:
        cnt[i.status] = cnt.get(i.status, 0) + 1
        eff[i.status] = eff.get(i.status, 0) + (i.annual_effect or 0)
    d = {"id": c.id, "number": c.number, "kind": c.kind, "title": c.title, "valid_from": c.valid_from, "note": c.note,
         "details": c.details, "created_at": c.created_at, "by": users.get(c.created_by_id), "count": len(c.impacts),
         "status_count": cnt, "effect": {k: round(v, 2) for k, v in eff.items()},
         "annual_effect": round(sum(i.annual_effect or 0 for i in c.impacts), 2)}
    if with_impacts:
        d["impacts"] = [{"id": i.id, "article_id": i.article_id, "article_no": i.article.article_no,
                         "customer_part_no": i.article.customer_part_no, "description": i.article.description,
                         "account": i.article.account.name if i.article.account else None, "account_id": i.article.account_id,
                         "price_unit": i.article.price_unit, "current_price": i.article.price, "old_price": i.old_price,
                         "delta": i.delta, "new_price": i.new_price, "annual_effect": i.annual_effect, "detail": i.detail,
                         "contract_bound": i.article.contract_bound, "contract_note": i.article.contract_note,
                         "status": i.status, "note": i.note, "passed_price": i.passed_price, "effective_date": i.effective_date,
                         "by": users.get(i.decided_by_id), "decided_at": i.decided_at} for i in c.impacts]
    return d


@router.get("/changes")
def list_changes(db: Session = Depends(get_db), _: User = Depends(can_read)):
    users = {u.id: u.name for u in db.scalars(select(User)).all()}
    return [change_out(c, users) for c in db.scalars(select(PriceChange).order_by(PriceChange.id.desc())).unique().all()]


@router.get("/changes/{cid}")
def get_change(cid: int, db: Session = Depends(get_db), _: User = Depends(can_read)):
    c = db.get(PriceChange, cid)
    if not c:
        raise HTTPException(404, "Vorgang nicht gefunden")
    return change_out(c, {u.id: u.name for u in db.scalars(select(User)).all()}, True)


class DecideIn(BaseModel):
    status: str
    note: str | None = None
    passed_price: float | None = None
    effective_date: date | None = None


@router.patch("/impacts/{iid}")
def patch_impact(iid: int, data: DecideIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    imp = db.get(PriceImpact, iid)
    if not imp:
        raise HTTPException(404, "Eintrag nicht gefunden")
    decide_impact(db, imp, data.status, data.note, data.passed_price, data.effective_date, user)
    db.commit()
    return {"ok": True}


class BulkIn(DecideIn):
    impact_ids: list[int]


@router.post("/changes/{cid}/bulk")
def bulk_decide(cid: int, data: BulkIn, db: Session = Depends(get_db), user: User = Depends(can_write)):
    n = 0
    for imp in db.scalars(select(PriceImpact).where(PriceImpact.change_id == cid, PriceImpact.id.in_(data.impact_ids))).unique().all():
        if imp.status == data.status:
            continue
        decide_impact(db, imp, data.status, data.note, None, data.effective_date, user)
        n += 1
    db.commit()
    return {"count": n}


# ------------------------------------------------------------------ Import
def _prepare_articles(db: Session, data: bytes, filename: str, account_id: int | None):
    rows = read_sheet(data, filename)
    hi, mapping, template = detect(rows, [(k, l, a) for k, l, a in ART_FIELDS])
    body = [r for r in rows[hi + 1:] if any(str(c).strip() and not str(c).startswith("=") for c in r)]
    out = []
    for n, r in enumerate(body, start=hi + 2):
        v, errs = parse_values(r, mapping, NUM, {"valid_from", "contract_until"}, {"contract_bound"})
        if template:
            v.pop("_origin", None)
            plan = v.pop("_plan_next", None)
            if not v.get("forecast_qty") and plan:
                v["forecast_qty"] = parse_values([plan], {"0": "x"}, {"x"})[0].get("x")
            if not v.get("description") and not v.get("customer_part_no") and not v.get("article_no"):
                continue  # leere Vorlagenzeile
        acc = find_account(db, v.get("account")) if v.get("account") else None
        acc_id = acc.id if acc else account_id
        if v.get("account") and not acc:
            errs.append(f"Kunde „{v['account']}“ nicht gefunden")
        if not acc_id:
            errs.append("Kunde fehlt – im Dialog wählen oder Spalte „Kunde“")
        if not (v.get("article_no") or v.get("customer_part_no")):
            errs.append("Artikel-Nr. F&R oder Kunde fehlt")
        if v.get("price") is None:
            errs.append("Preis fehlt")
        ex = match_article(db, v, acc_id) if not errs else None
        status = "fehler" if errs else ("neu" if not ex else
                                         ("preis_geaendert" if abs((ex.price or 0) - v["price"]) > 1e-6 else "unveraendert"))
        out.append({"row": n, "values": v, "errors": errs, "status": status, "account_id": acc_id,
                    "existing": {"id": ex.id, "price": ex.price} if ex else None})
    return out, template, mapping, rows[hi] if rows else []


def _apply_article(db: Session, a: PriceArticle, v: dict, user):
    simple = ["article_no", "customer_part_no", "description", "location", "currency", "forecast_qty", "qty_last_year",
              "revenue_last_year", "moq", "shot_weight_g", "part_weight_g", "mgk_pct", "ratio_per_unit", "contract_bound",
              "contract_until", "contract_note", "comment"]
    for k in simple:
        if k in v:
            setattr(a, k, v[k])
    if "price_unit" in v:
        a.price_unit = int(v["price_unit"]) or 100
    if "surcharge_pct" in v:
        a.surcharge_pct = v["surcharge_pct"] * 100 if abs(v["surcharge_pct"]) <= 1 else v["surcharge_pct"]
    # Materialien: Material 1 (Nummer/Name, Gewicht = Materialgewicht oder Schussgewicht), Material 2
    lines = []
    for p in ("mat1", "mat2"):
        num, name = v.get(f"{p}_number"), v.get(f"{p}_name")
        if not (num or name):
            continue
        m = find_material(db, num, name)
        if m and num and not m.number:
            m.number = num     # Materialnummer aus der Preisliste übernehmen
        basis = v.get(f"{p}_basis")
        if not m:   # unbekanntes Material → in den Stammdaten anlegen (Preis = Basis aus der Preisliste)
            m = Material(name=name or num, number=num, price_per_kg=basis or 0, price_valid_from=date.today(),
                         notes="aus Preisliste angelegt")
            db.add(m)
            db.flush()
            db.add(MaterialPriceHistory(material_id=m.id, price_per_kg=m.price_per_kg, valid_from=date.today(),
                                        source="preisliste", note="Erstanlage aus Preisliste", created_by_id=user.id))
        weight = v.get(f"{p}_weight") or (v.get("shot_weight_g") if p == "mat1" else None)
        lines.append(PriceArticleMaterial(position=len(lines) + 1, material_id=m.id, weight_g=weight,
                                          price_basis=basis if basis is not None else m.price_per_kg))
    if lines:
        a.materials = lines
    parts = [PriceArticlePart(position=i + 1, name=v[k], qty_per_part=1) for i, k in enumerate(("part1", "part2")) if v.get(k)]
    if parts and not a.parts:
        a.parts = parts


@router.post("/import/articles/preview")
async def import_articles_preview(file: UploadFile = File(...), account_id: int | None = Form(None),
                                  db: Session = Depends(get_db), _: User = Depends(can_write)):
    parsed, template, mapping, head = _prepare_articles(db, await file.read(), file.filename or "", account_id)
    counts = {}
    for p in parsed:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    labels = {k: l for k, l, _ in ART_FIELDS}
    return {"template": template, "total": len(parsed), "counts": counts,
            "columns": [{"col": (head[int(c)] if int(c) < len(head) else "") or f"Spalte {int(c) + 1}", "field": labels.get(f, f)} for c, f in mapping.items()
                        if not f.startswith("_")],
            "rows": [{**p, "values": {k: (str(x) if isinstance(x, date) else x) for k, x in p["values"].items()}} for p in parsed[:1000]]}


@router.post("/import/articles/commit")
async def import_articles_commit(file: UploadFile = File(...), account_id: int | None = Form(None),
                                 valid_from: str | None = Form(None), note: str | None = Form(None),
                                 db: Session = Depends(get_db), user: User = Depends(can_write)):
    """Neue Artikel anlegen, bestehende aktualisieren. Geänderte Preise → Historie + Vorgang „Import VK-Preise“."""
    parsed, *_ = _prepare_articles(db, await file.read(), file.filename or "", account_id)
    vf = date.fromisoformat(valid_from) if valid_from else date.today()
    created = updated = changed = skipped = 0
    ch = None
    for p in parsed:
        v = p["values"]
        if p["status"] == "fehler":
            skipped += 1
            continue
        if p["existing"]:
            a = db.get(PriceArticle, p["existing"]["id"])
            old = a.price
            _apply_article(db, a, v, user)
            if p["status"] == "preis_geaendert":
                if ch is None:
                    ch = PriceChange(number=next_change_number(db), kind="vk_import",
                                     title=f"Import VK-Preise {vf:%m/%Y}" + (f" – {file.filename}" if file.filename else ""),
                                     valid_from=vf, note=note, created_by_id=user.id)
                    db.add(ch)
                    db.flush()
                d = v["price"] - old
                ch.impacts.append(PriceImpact(article_id=a.id, old_price=old, delta=r4(d), new_price=v["price"],
                                              annual_effect=round(annual_effect(d, a.forecast_qty, a.price_unit), 2),
                                              detail=[{"type": "import", "old": old, "new": v["price"]}]))
                add_history(db, a, v["price"], "import", user, vf, f"Import {file.filename or ''}".strip(), ch.id)
                changed += 1
            updated += 1
        else:
            a = PriceArticle(account_id=p["account_id"], price=0, price_unit=100, mgk_pct=8)
            db.add(a)
            _apply_article(db, a, v, user)
            db.flush()
            add_history(db, a, v["price"], "erstanlage", user, v.get("valid_from") or vf, f"Import {file.filename or ''}".strip())
            created += 1
    db.commit()
    return {"created": created, "updated": updated, "price_changed": changed, "skipped": skipped,
            "change": {"id": ch.id, "number": ch.number} if ch else None}


def _prepare_materials(db: Session, data: bytes, filename: str):
    rows = read_sheet(data, filename)
    hi, mapping, _t = detect(rows, MAT_FIELDS)
    out = []
    for n, r in enumerate(rows[hi + 1:], start=hi + 2):
        v, errs = parse_values(r, mapping, {"price"}, {"valid_from"})
        if not v:
            continue
        m = find_material(db, v.get("number"), v.get("name"))
        if v.get("price") is None:
            errs.append("Preis fehlt")
        status = "fehler" if errs else ("unbekannt" if not m else
                                         ("geaendert" if abs((m.price_per_kg or 0) - v["price"]) > 1e-9 else "unveraendert"))
        out.append({"row": n, "values": v, "errors": errs, "status": status, "material": m})
    return out


@router.post("/import/materials/preview")
async def import_materials_preview(file: UploadFile = File(...), db: Session = Depends(get_db), _: User = Depends(can_write)):
    """Monatlicher Import Materialpreise: geänderte Preise und betroffene Artikel (Jahreseffekt) vorab zeigen."""
    parsed = _prepare_materials(db, await file.read(), file.filename or "")
    prices = {p["material"].id: p["values"]["price"] for p in parsed if p["status"] == "geaendert"}
    rows = impact_rows(db, prices) if prices else []
    per_mat = {}
    for r in rows:
        for d in r["detail"]:
            x = per_mat.setdefault(d["material_id"], {"articles": 0, "effect": 0.0})
            x["articles"] += 1
            x["effect"] += annual_effect(d["delta"], r["forecast_qty"], r["price_unit"])
    counts = {}
    for p in parsed:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    return {"counts": counts, "total": len(parsed), "annual_effect": round(sum(r["annual_effect"] for r in rows), 2),
            "articles": len(rows),
            "rows": [{"row": p["row"], "status": p["status"], "errors": p["errors"],
                      "values": {k: (str(x) if isinstance(x, date) else x) for k, x in p["values"].items()},
                      "material": {"id": p["material"].id, "name": p["material"].name, "number": p["material"].number,
                                   "price": p["material"].price_per_kg} if p["material"] else None,
                      "affected": per_mat.get(p["material"].id, {}).get("articles", 0) if p["material"] else 0,
                      "effect": round(per_mat.get(p["material"].id, {}).get("effect", 0), 2) if p["material"] else 0}
                     for p in parsed]}


@router.post("/import/materials/commit")
async def import_materials_commit(file: UploadFile = File(...), valid_from: str | None = Form(None), note: str | None = Form(None),
                                  create_unknown: bool = Form(False), db: Session = Depends(get_db), user: User = Depends(can_write)):
    parsed = _prepare_materials(db, await file.read(), file.filename or "")
    vf = date.fromisoformat(valid_from) if valid_from else date.today()
    created = 0
    for p in parsed:
        if p["status"] == "unbekannt" and create_unknown and (p["values"].get("name") or p["values"].get("number")):
            v = p["values"]
            m = Material(name=v.get("name") or v["number"], number=v.get("number"), price_per_kg=v["price"],
                         supplier=v.get("supplier"), price_valid_from=v.get("valid_from") or vf, notes="aus Materialpreis-Import")
            db.add(m)
            db.flush()
            db.add(MaterialPriceHistory(material_id=m.id, price_per_kg=m.price_per_kg, valid_from=m.price_valid_from,
                                        source="import", note="Erstanlage aus Import", created_by_id=user.id))
            created += 1
    items = [(p["material"], p["values"]["price"]) for p in parsed if p["status"] == "geaendert"]
    ch = None
    if items:
        ch = create_material_change(db, user, items, vf, note, "material_import",
                                    f"Import Materialpreise {vf:%m/%Y} – {len(items)} Material(ien)")
    db.commit()
    return {"changed": len(items), "created": created, "change": {"id": ch.id, "number": ch.number, "impacts": len(ch.impacts)} if ch else None}


@router.get("/import/{kind}/template")
def import_template(kind: str, _: User = Depends(can_read)):
    import csv  # noqa: PLC0415
    fields = ART_FIELDS if kind == "articles" else MAT_FIELDS
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    w.writerow([f[1] for f in fields])
    if kind == "articles":
        w.writerow(["Musterkunde GmbH", "100-2001", "A 123 456 78", "Gehäuse Sensor", "DE", "45,20", "100", "EUR", "01.01.2027",
                    "120000", "", "", "5000", "12,4", "11,8", "RM05930", "PA6 GF30 schwarz", "2,95", "", "", "", "", "Buchse M4",
                    "", "8", "0", "0", "nein", "", "Preisgleitklausel Material", ""])
    else:
        w.writerow(["RM05930", "PA6 GF30 schwarz", "3,05", "01.12.2026", "Lieferant GmbH"])
    return Response(("﻿" + buf.getvalue()).encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="Vorlage_Preisliste_{kind}.csv"'})


# ------------------------------------------------------------------ Export
@router.get("/export")
def export_xlsx(account_id: int | None = None, material_id: int | None = None, q: str | None = None, contract: str | None = None,
                db: Session = Depends(get_db), user: User = Depends(can_read)):
    """Preisliste als Excel (aktuelle Filter), mit Materialbasis und offener Materialdifferenz."""
    from openpyxl import Workbook  # noqa: PLC0415
    from openpyxl.styles import Font, PatternFill  # noqa: PLC0415
    data = list_articles(q=q, account_id=account_id, material_id=material_id, contract=contract, gap=False, active=True,
                         limit=5000, db=db, _=user)
    wb = Workbook()
    ws = wb.active
    ws.title = "Preisliste"
    head = ["Kunde", "Artikel-Nr. F&R", "Artikel-Nr. Kunde", "Bezeichnung", "Preis je PE", "PE", "Währung", "gültig ab",
            "Planmenge p. a.", "Umsatz p. a.", "Material 1", "Gewicht g", "Basis €/kg", "aktuell €/kg", "Material 2", "Basis €/kg",
            "Zukaufteile", "Preisbindung", "Vertrag", "offene Materialdifferenz je PE", "offene Differenz p. a."]
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DCE6F2")
    for i in data["items"]:
        m1 = i["materials"][0] if i["materials"] else {}
        m2 = i["materials"][1] if len(i["materials"]) > 1 else {}
        ws.append([i["account"], i["article_no"], i["customer_part_no"], i["description"], i["price"], i["price_unit"], i["currency"],
                   i["price_valid_from"], i["forecast_qty"], i["annual_revenue"], m1.get("name"), m1.get("weight_g"),
                   m1.get("price_basis"), m1.get("current_price"), m2.get("name"), m2.get("price_basis"),
                   ", ".join(p["name"] for p in i["parts"]), "ja" if i["contract_bound"] else "nein", i["contract_note"],
                   i["open_gap"], i["open_gap_annual"]])
    for col, w in zip("ABCDEFGHIJKLMNOPQRSTU", (24, 16, 18, 32, 11, 6, 8, 11, 13, 13, 24, 10, 10, 10, 20, 10, 20, 11, 24, 14, 14)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "B2"
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="Preisliste_{date.today():%Y-%m-%d}.xlsx"'})
