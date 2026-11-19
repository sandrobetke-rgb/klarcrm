"""Preisliste (lebende VK-Preisliste): Rechenregeln, Preisänderungsvorgänge, Import.

Rechenregel (aus der Vorlage „Annual Price Inquiry List“ von F&R, korrigiert):
  Δ Material je Preiseinheit = (neuer − bisheriger Materialpreis €/kg) × Einsatzgewicht g/1000 × Preiseinheit × (1 + MGK %)
  Δ Zukaufteil je Preiseinheit = (neuer − bisheriger Stückpreis) × Stück je Teil × Preiseinheit
  Jahreseffekt = Δ je Preiseinheit × Planmenge / Preiseinheit
Material 2 und Zukaufteile zählen mit (in der Excel-Vorlage fehlten sie in der Preisformel, MGK nur in Zeile 8).
"""
import io
import re
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .importer import norm, parse_date, parse_number
from .models import (Account, Material, MaterialPriceHistory, PriceArticle, PriceArticleHistory, PriceArticleMaterial,
                     PriceArticlePart, PriceChange, PriceImpact)

STATUSES = {
    "offen": "offen",
    "weitergegeben": "an Kunden weitergegeben",
    "vertraglich_gebunden": "nicht weitergegeben – vertraglich gebunden",
    "sonstiges": "Sonstiges",
}


# ------------------------------------------------------------------ reine Rechenregeln (getestet)
def material_delta(new_price: float, basis: float | None, weight_g: float | None, price_unit: int, mgk_pct: float | None) -> float:
    if basis is None or not weight_g:
        return 0.0
    return (new_price - basis) * weight_g / 1000 * price_unit * (1 + (mgk_pct or 0) / 100)


def part_delta(new_price: float, basis: float | None, qty: float, price_unit: int) -> float:
    if basis is None:
        return 0.0
    return (new_price - basis) * (qty or 0) * price_unit


def annual_effect(delta: float, forecast_qty: float | None, price_unit: int) -> float:
    return delta * (forecast_qty or 0) / (price_unit or 1)


def r4(x: float | None) -> float | None:
    return None if x is None else round(x, 4)


def article_delta(a: PriceArticle, mat_prices: dict[int, float]) -> tuple[float, list]:
    """Δ je Preiseinheit eines Artikels für neue Materialpreise {material_id: €/kg}."""
    total, detail = 0.0, []
    for m in a.materials:
        if m.material_id in mat_prices:
            d = material_delta(mat_prices[m.material_id], m.price_basis, m.weight_g, a.price_unit, a.mgk_pct)
            total += d
            detail.append({"type": "material", "material_id": m.material_id, "name": m.material.name if m.material else m.name,
                           "basis": m.price_basis, "new": mat_prices[m.material_id], "weight_g": m.weight_g, "delta": r4(d)})
    return total, detail


def open_gap(a: PriceArticle) -> float:
    """Noch nicht weitergegebene Materialdifferenz je Preiseinheit (aktueller Materialpreis gegen Basis im VK-Preis)."""
    return sum(material_delta(m.material.price_per_kg, m.price_basis, m.weight_g, a.price_unit, a.mgk_pct)
               for m in a.materials if m.material and m.price_basis is not None)


# ------------------------------------------------------------------ Nummern
def next_change_number(db: Session) -> str:
    prefix = f"PA{date.today():%y}-"
    nums = db.scalars(select(PriceChange.number).where(PriceChange.number.like(f"{prefix}%"))).all()
    n = max((int(x[len(prefix):]) for x in nums if x[len(prefix):].isdigit()), default=0) + 1
    return f"{prefix}{n:04d}"


def add_history(db: Session, a: PriceArticle, new_price: float, source: str, user, valid_from: date | None = None,
                note: str | None = None, change_id: int | None = None):
    db.add(PriceArticleHistory(article_id=a.id, price=new_price, old_price=a.price if source != "erstanlage" else None,
                               price_unit=a.price_unit, valid_from=valid_from or date.today(), source=source, note=note,
                               change_id=change_id, created_by_id=user.id if user else None))
    a.price, a.price_valid_from = new_price, valid_from or date.today()


# ------------------------------------------------------------------ Materialpreisänderung
def affected_articles(db: Session, material_ids: list[int]) -> list[PriceArticle]:
    ids = db.scalars(select(PriceArticleMaterial.article_id).where(PriceArticleMaterial.material_id.in_(material_ids))).all()
    if not ids:
        return []
    return db.scalars(select(PriceArticle).where(PriceArticle.id.in_(set(ids)), PriceArticle.active.is_(True))
                      .order_by(PriceArticle.account_id, PriceArticle.article_no)).unique().all()


def impact_rows(db: Session, prices: dict[int, float]) -> list[dict]:
    """Vorschau: betroffene Artikel mit Δ je Preiseinheit, neuem Preis und Jahreseffekt."""
    out = []
    for a in affected_articles(db, list(prices)):
        d, detail = article_delta(a, prices)
        if abs(d) < 1e-9:
            continue   # Basis entspricht bereits dem neuen Preis – nicht betroffen
        out.append({"article_id": a.id, "article_no": a.article_no, "customer_part_no": a.customer_part_no,
                    "description": a.description, "account": a.account.name if a.account else None,
                    "account_id": a.account_id, "price_unit": a.price_unit, "old_price": a.price, "delta": r4(d),
                    "new_price": r4(a.price + d), "delta_pct": round(100 * d / a.price, 2) if a.price else None,
                    "annual_effect": round(annual_effect(d, a.forecast_qty, a.price_unit), 2),
                    "forecast_qty": a.forecast_qty, "contract_bound": a.contract_bound, "contract_until": a.contract_until,
                    "contract_note": a.contract_note, "detail": detail})
    return out


def create_material_change(db: Session, user, items: list[tuple[Material, float]], valid_from: date | None,
                           note: str | None, kind: str = "material", title: str | None = None) -> PriceChange:
    """Neue Materialpreise übernehmen (Historie, Stammdaten) und Vorgang mit allen betroffenen Artikeln anlegen."""
    items = [(m, p) for m, p in items if p is not None and abs((m.price_per_kg or 0) - p) > 1e-9]
    if not items:
        raise HTTPException(400, "Keine Preisänderung – neuer Preis entspricht dem aktuellen")
    prices = {m.id: p for m, p in items}
    rows = impact_rows(db, prices)
    ch = PriceChange(number=next_change_number(db), kind=kind, valid_from=valid_from or date.today(), note=note,
                     created_by_id=user.id if user else None,
                     title=title or ("Materialpreis " + ", ".join(f"{m.name} {(m.price_per_kg or 0):.2f} → {p:.2f} €/kg" for m, p in items))[:200],
                     details=[{"material_id": m.id, "name": m.name, "number": m.number, "old": m.price_per_kg, "new": p} for m, p in items])
    db.add(ch)
    db.flush()
    for m, p in items:
        db.add(MaterialPriceHistory(material_id=m.id, price_per_kg=p, old_price=m.price_per_kg, valid_from=ch.valid_from,
                                    source="import" if kind == "material_import" else "manuell", note=note, change_id=ch.id,
                                    created_by_id=user.id if user else None))
        m.price_per_kg, m.price_valid_from = p, ch.valid_from
    for r in rows:
        ch.impacts.append(PriceImpact(article_id=r["article_id"], old_price=r["old_price"], delta=r["delta"],
                                      new_price=r["new_price"], annual_effect=r["annual_effect"], detail=r["detail"]))
    return ch


# ------------------------------------------------------------------ Kennzeichnung
def decide_impact(db: Session, imp: PriceImpact, status: str, note: str | None, passed_price: float | None,
                  effective_date: date | None, user):
    """Kennzeichnen: weitergegeben (Preis wird übernommen) · vertraglich gebunden · Sonstiges (Freitext) · offen."""
    if status not in STATUSES:
        raise HTTPException(400, "Unbekannter Status")
    if status == "sonstiges" and not (note or "").strip():
        raise HTTPException(400, "Bei „Sonstiges“ bitte Freitext angeben")
    ch = db.get(PriceChange, imp.change_id)
    a = imp.article
    if imp.status == "weitergegeben" and status != "weitergegeben" and ch.kind != "vk_import":
        raise HTTPException(409, "Bereits weitergegeben – der Artikelpreis wurde geändert. Bitte den Preis im Artikel korrigieren.")
    if status == "weitergegeben" and imp.status != "weitergegeben" and ch.kind != "vk_import":
        price = passed_price if passed_price is not None else imp.new_price
        add_history(db, a, price, "preisaenderung", user, effective_date or ch.valid_from,
                    f"{ch.number}: {ch.title}" + (f" – {note}" if note else ""), ch.id)
        imp.passed_price = price
        # die weitergegebenen Materialpreise sind jetzt die Basis im VK-Preis
        for d in imp.detail or []:
            for m in a.materials:
                if d.get("type") == "material" and m.material_id == d.get("material_id"):
                    m.price_basis = d.get("new")
    elif status == "weitergegeben" and ch.kind == "vk_import":
        imp.passed_price = imp.new_price
    imp.status, imp.note = status, (note or "").strip() or None
    imp.effective_date = effective_date or imp.effective_date or ch.valid_from
    imp.decided_by_id, imp.decided_at = (user.id if user else None), datetime.now(timezone.utc)


# ------------------------------------------------------------------ Import
# Felder der Preisliste (generisches CSV/Excel). Die F&R-Vorlage „Annual Price Inquiry List“ wird an ihren Spaltentiteln
# erkannt und fest zugeordnet (TEMPLATE_COLUMNS).
ART_FIELDS = [
    ("account", "Kunde", ["kunde", "firma", "customer", "kundenname"]),
    ("article_no", "Artikel-Nr. F&R", ["artikelnummer", "artikel nr", "artikel-nr", "art nr", "f&r artikel", "artikel"]),
    ("customer_part_no", "Artikel-Nr. Kunde", ["kunden artikelnummer", "kundenartikel", "sachnummer", "part number", "part number of contract product"]),
    ("description", "Bezeichnung", ["bezeichnung", "beschreibung", "part description", "artikelbezeichnung"]),
    ("location", "Fertigungsort", ["location", "standort", "werk", "location (iso country code)"]),
    ("price", "Preis je PE", ["preis", "vk-preis", "vk preis", "verkaufspreis", "price", "contract price"]),
    ("price_unit", "Preiseinheit", ["pe", "preiseinheit", "price unit"]),
    ("currency", "Währung", ["währung", "currency"]),
    ("valid_from", "gültig ab", ["gültig ab", "gueltig ab", "valid from", "preis ab"]),
    ("forecast_qty", "Planmenge p. a.", ["planmenge", "jahresmenge", "forecast", "forecasted quantity", "menge"]),
    ("qty_last_year", "Menge Vorjahr", ["menge vorjahr"]),
    ("revenue_last_year", "Umsatz Vorjahr", ["umsatz vorjahr", "umsatz"]),
    ("moq", "MOQ", ["moq", "mindestmenge"]),
    ("shot_weight_g", "Schussgewicht g", ["schussgewicht", "shot weight", "shot weight [g/pc]"]),
    ("part_weight_g", "Teilgewicht g", ["teilgewicht", "part weight", "net weight", "part/ net weight [g/pc]"]),
    ("mat1_number", "Material-Nr.", ["material-nr", "materialnummer", "mat nr", "f&r mat number"]),
    ("mat1_name", "Material", ["material", "werkstoff", "resin", "resin - type - grade - name"]),
    ("mat1_basis", "Materialpreis €/kg (im Preis)", ["materialpreis", "materialbasis", "last material price basis", "alter mat preis"]),
    ("mat1_weight", "Materialgewicht g", ["materialgewicht", "einsatzgewicht"]),
    ("mat2_name", "Material 2", ["material 2", "masterbatch"]),
    ("mat2_weight", "Gewicht Material 2 g", ["gewicht material 2"]),
    ("mat2_basis", "Preis Material 2 €/kg", ["preis material 2"]),
    ("part1", "Zukaufteil", ["zukaufteil", "zukaufteil 1"]),
    ("part2", "Zukaufteil 2", ["zukaufteil 2"]),
    ("mgk_pct", "MGK %", ["mgk"]),
    ("surcharge_pct", "NK-Zuschlag %", ["nk zuschlag", "nachkalkulation"]),
    ("ratio_per_unit", "Ratio je PE", ["ratio", "rationalisierung"]),
    ("contract_bound", "Preisbindung (ja/nein)", ["preisbindung", "festpreis", "vertraglich gebunden"]),
    ("contract_until", "Preisbindung bis", ["preisbindung bis", "festpreis bis"]),
    ("contract_note", "Vertrag", ["vertrag", "contract", "vertragsart"]),
    ("comment", "Bemerkung", ["bemerkung", "kommentar", "comment"]),
]
NUM = {"price", "price_unit", "forecast_qty", "qty_last_year", "revenue_last_year", "moq", "shot_weight_g", "part_weight_g",
       "mat1_basis", "mat1_weight", "mat2_weight", "mat2_basis", "mgk_pct", "surcharge_pct", "ratio_per_unit"}
# F&R-Vorlage „Annual Price Inquiry List“ (Kopfzeile 7): Spalte → Feld
TEMPLATE_COLUMNS = {"B": "location", "C": "customer_part_no", "D": "article_no", "E": "description", "F": "forecast_qty",
                    "G": "price_unit", "H": "price", "I": "currency", "M": "moq", "N": "comment", "O": "shot_weight_g",
                    "P": "part_weight_g", "Q": "mat1_number", "R": "mat1_name", "S": "mat1_basis", "W": "revenue_last_year",
                    "X": "qty_last_year", "AF": "mat2_name", "AG": "mat2_weight", "AH": "mat2_basis", "AJ": "surcharge_pct",
                    "AL": "ratio_per_unit", "AM": "part1", "AO": "part2", "AV": "contract_note", "L": "_origin", "Y": "_plan_next"}
MAT_FIELDS = [
    ("number", "Material-Nr.", ["material-nr", "materialnummer", "mat nr", "f&r mat number", "rm number", "nummer"]),
    ("name", "Bezeichnung", ["bezeichnung", "material", "werkstoff", "resin", "name"]),
    ("price", "Preis €/kg", ["preis", "preis €/kg", "€/kg", "price", "materialpreis", "new material price basis"]),
    ("valid_from", "gültig ab", ["gültig ab", "gueltig ab", "valid from", "datum"]),
    ("supplier", "Lieferant", ["lieferant", "supplier"]),
]


def _col_index(letter: str) -> int:
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_sheet(data: bytes, filename: str) -> list[list[str]]:
    """Alle Zeilen als Text (CSV oder erstes Excel-Blatt, berechnete Werte)."""
    from .importer import _cell  # noqa: PLC0415
    if filename.lower().endswith((".xlsx", ".xlsm")) or data[:2] == b"PK":
        from openpyxl import load_workbook  # noqa: PLC0415
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = next((w for w in wb.worksheets if "inquiry" in w.title.lower() or "preis" in w.title.lower()), wb.worksheets[0])
        return [["" if v is None else _cell(v) for v in r] for r in ws.iter_rows(values_only=True)]
    from .importer import read_table  # noqa: PLC0415
    head, body = read_table(data, filename)
    return [head] + body


def detect(rows: list[list[str]], fields: list) -> tuple[int, dict, bool]:
    """Kopfzeile finden (erste 15 Zeilen) und Spalten zuordnen. Rückgabe: Zeilenindex, {Spalte: Feld}, Vorlage erkannt."""
    for i, r in enumerate(rows[:15]):
        hs = [norm(c) for c in r]
        if "part number of contract product" in hs and any("resin" in h for h in hs):
            return i, {str(_col_index(k)): v for k, v in TEMPLATE_COLUMNS.items()}, True
    best, best_i, best_map = -1, 0, {}
    for i, r in enumerate(rows[:15]):
        mp, used = {}, set()
        for j, h in enumerate(r):
            nh = norm(re.sub(r"\s*\*$", "", h))
            if not nh:
                continue
            for key, label, aliases in fields:
                if key in used:
                    continue
                if nh in {norm(label), norm(key)} | {norm(a) for a in aliases}:
                    mp[str(j)] = key
                    used.add(key)
                    break
        if len(mp) > best:
            best, best_i, best_map = len(mp), i, mp
    return best_i, best_map, False


def parse_values(row: list[str], mapping: dict, numeric: set, dates: set = frozenset(), bools: set = frozenset()) -> tuple[dict, list]:
    vals, errs = {}, []
    for col, key in mapping.items():
        if not key:
            continue
        raw = str(row[int(col)] if int(col) < len(row) else "").strip()
        if raw == "" or raw.startswith("="):
            continue
        try:
            if key in numeric:
                vals[key] = parse_number(raw)
            elif key in dates:
                vals[key] = parse_date(raw)
            elif key in bools:
                vals[key] = norm(raw) in ("ja", "j", "x", "1", "true", "yes", "wahr")
            else:
                vals[key] = raw
        except ValueError as e:
            errs.append(f"{key}: {e}")
    return vals, errs


def find_material(db: Session, number: str | None, name: str | None) -> Material | None:
    if number:
        m = db.scalars(select(Material).where(Material.number == number)).first()
        if m:
            return m
    if name:
        return db.scalars(select(Material).where(Material.name.ilike(name))).first()
    return None


def find_account(db: Session, name: str | None) -> Account | None:
    return db.scalars(select(Account).where(Account.name.ilike(name.strip()))).first() if name else None


def match_article(db: Session, v: dict, account_id: int | None) -> PriceArticle | None:
    if v.get("article_no"):
        q = select(PriceArticle).where(PriceArticle.article_no == v["article_no"])
        if account_id:
            q = q.where(PriceArticle.account_id == account_id)
        a = db.scalars(q).first()
        if a:
            return a
    if v.get("customer_part_no") and account_id:
        return db.scalars(select(PriceArticle).where(PriceArticle.customer_part_no == v["customer_part_no"],
                                                     PriceArticle.account_id == account_id)).first()
    return None
