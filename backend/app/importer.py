"""Daten-Import aus CSV/Excel: Datei lesen, Spalten zuordnen, Werte prüfen und umwandeln.
Reine Funktionen ohne Datenbank – die Datenbankseite liegt in routers/imports.py."""
import csv
import io
import re
import unicodedata
from datetime import date, datetime

# Feld: (Schlüssel, Bezeichnung, Typ, Pflicht, weitere Spaltennamen)
# Typen: text | number | int | date | bool | choice:<a>=<Label>|… | ref:<Ziel>
ENTITIES = {
    "accounts": {
        "label": "Firmen", "match": ["name"],
        "fields": [
            ("name", "Firmenname", "text", True, ["firma", "kunde", "name", "unternehmen", "firmenname"]),
            ("type", "Typ", "choice:kunde=Kunde|interessent=Interessent|partner=Partner|lieferant=Lieferant", False, ["art", "kategorie"]),
            ("industry", "Branche", "text", False, ["branche", "industrie"]),
            ("street", "Straße", "text", False, ["strasse", "straße", "anschrift", "adresse"]),
            ("zip", "PLZ", "text", False, ["plz", "postleitzahl"]),
            ("city", "Ort", "text", False, ["ort", "stadt"]),
            ("country", "Land", "text", False, ["land"]),
            ("phone", "Telefon", "text", False, ["telefon", "tel", "telefonnummer"]),
            ("email", "E-Mail", "text", False, ["e-mail", "email", "mail"]),
            ("website", "Website", "text", False, ["website", "internet", "homepage", "www"]),
            ("notes", "Notizen", "text", False, ["notiz", "bemerkung", "kommentar"]),
        ],
        "example": ["Musterkunde GmbH", "Kunde", "Automotive", "Hauptstraße 1", "32657", "Lemgo", "Deutschland",
                    "+49 5261 0000", "info@musterkunde.example", "www.musterkunde.example", ""],
    },
    "contacts": {
        "label": "Kontakte", "match": ["email", "name+account"],
        "fields": [
            ("account_id", "Firma", "ref:account", True, ["firma", "firmenname", "kunde", "unternehmen"]),
            ("salutation", "Anrede", "text", False, ["anrede"]),
            ("first_name", "Vorname", "text", False, ["vorname"]),
            ("last_name", "Nachname", "text", True, ["nachname", "name", "familienname"]),
            ("position", "Position", "text", False, ["position", "funktion", "abteilung"]),
            ("email", "E-Mail", "text", False, ["e-mail", "email", "mail"]),
            ("phone", "Telefon", "text", False, ["telefon", "tel", "durchwahl"]),
            ("mobile", "Mobil", "text", False, ["mobil", "handy", "mobiltelefon"]),
            ("notes", "Notizen", "text", False, ["notiz", "bemerkung"]),
        ],
        "example": ["Musterkunde GmbH", "Frau", "Erika", "Musterfrau", "Einkauf", "e.musterfrau@musterkunde.example",
                    "+49 5261 0001", "", ""],
    },
    "machines": {
        "label": "Maschinen & Anlagen", "match": ["number"], "admin": True,
        "fields": [
            ("number", "Maschinen-Nr.", "text", True, ["nr", "nummer", "maschinennr", "maschinen-nr"]),
            ("name", "Bezeichnung", "text", True, ["bezeichnung", "maschine", "name"]),
            ("kind", "Art", "choice:spritzguss=Spritzgießmaschine|montage=Montagelinie|nachbearbeitung=Nachbearbeitung|pruefung=Prüfstation|sonstige=Sonstige", False, ["art", "typ"]),
            ("site_id", "Standort", "ref:site", False, ["standort", "werk"]),
            ("clamping_force_t", "Schließkraft t", "number", False, ["schließkraft", "schliesskraft", "tonnage", "t"]),
            ("hourly_rate", "Maschinenstundensatz €/h", "number", True, ["stundensatz", "maschinenstundensatz", "€/h", "satz"]),
            ("maintenance_rate", "Instandhaltung €/h", "number", False, ["instandhaltung", "ih"]),
            ("productivity_pct", "Produktivität %", "number", False, ["produktivität", "nutzungsgrad", "oee"]),
            ("operator_factor", "Bediener-Anteil %", "pct_factor", False, ["bediener", "bedienfaktor", "personal"]),
            ("handling_pct", "Handling-Anteil %", "number", False, ["handling"]),
            ("automation_pct", "Automatisierung-Anteil %", "number", False, ["automatisierung"]),
            ("power_kw", "Leistung kW", "number", False, ["kw", "leistung", "anschlussleistung"]),
            ("available_hours_year", "Verfügbare Stunden/Jahr", "number", False, ["stunden", "kapazität", "h/jahr"]),
            ("base_load_pct", "Grundauslastung %", "number", False, ["grundauslastung", "grundlast", "auslastung"]),
            ("location", "Halle / Bereich", "text", False, ["halle", "bereich"]),
            ("active", "Aktiv", "bool", False, ["aktiv"]),
        ],
        "example": ["M10", "Spritzgießmaschine 200 t", "Spritzgießmaschine", "Stammwerk", "200", "55,00", "5,00", "85", "30",
                    "0", "0", "25", "6000", "60", "Halle 2", "ja"],
    },
    "materials": {
        "label": "Materialien", "match": ["name"], "admin": True,
        "fields": [
            ("name", "Bezeichnung", "text", True, ["material", "werkstoff", "bezeichnung", "name"]),
            ("number", "Material-Nr.", "text", False, ["materialnummer", "material-nr", "mat nr", "rm number"]),
            ("family", "Werkstoffgruppe", "text", False, ["familie", "gruppe", "werkstoffgruppe", "typ"]),
            ("supplier", "Lieferant", "text", False, ["lieferant", "hersteller"]),
            ("price_per_kg", "Preis €/kg", "number", True, ["preis", "€/kg", "preis/kg", "kilopreis"]),
            ("density", "Dichte g/cm³", "number", False, ["dichte"]),
            ("co2_kg_per_kg", "CO₂ kg/kg", "number", False, ["co2", "co₂", "pcf", "emissionsfaktor"]),
            ("price_valid_from", "Preis gültig ab", "date", False, ["gültig ab", "stand", "datum"]),
            ("notes", "Notizen", "text", False, ["notiz", "bemerkung"]),
            ("active", "Aktiv", "bool", False, ["aktiv"]),
        ],
        "example": ["PA6 GF30 schwarz", "RM05930", "PA6", "Rahmenvertrag", "3,40", "1,36", "6,5", "01.01.2027", "", "ja"],
    },
    "purchased-parts": {
        "label": "Zukaufteile", "match": ["part_no", "name"], "admin": True,
        "fields": [
            ("part_no", "Artikel-Nr.", "text", False, ["artikelnummer", "art.-nr.", "artikel-nr", "nr", "teilenummer"]),
            ("name", "Bezeichnung", "text", True, ["bezeichnung", "name", "artikel"]),
            ("supplier", "Lieferant", "text", False, ["lieferant"]),
            ("supplier_part_no", "Artikel-Nr. Lieferant", "text", False, ["lieferanten-nr", "lieferantenartikel"]),
            ("price", "Preis €", "number", True, ["preis", "ek", "einkaufspreis"]),
            ("price_basis", "Preiseinheit Stk", "int", False, ["preiseinheit", "pe", "je"]),
            ("unit", "Mengeneinheit", "text", False, ["einheit", "me"]),
            ("moq", "Mindestbestellmenge", "number", False, ["moq", "mindestmenge"]),
            ("lead_time_days", "Wiederbeschaffungszeit Tage", "int", False, ["wbz", "lieferzeit"]),
            ("co2_kg_per_piece", "CO₂ kg/Stk", "number", False, ["co2", "co₂", "pcf"]),
            ("price_valid_from", "Preis gültig ab", "date", False, ["gültig ab", "stand"]),
            ("active", "Aktiv", "bool", False, ["aktiv"]),
        ],
        "example": ["ZK-3001", "Gewindebuchse M5", "Metallwaren Schulte", "GB-M5-8", "52,00", "1000", "Stk", "10000", "21",
                    "0,005", "01.01.2027", "ja"],
    },
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or "")).strip().lower().rstrip("* ").strip()
    return re.sub(r"[\s_.:]+", " ", s).strip()


def read_table(data: bytes, filename: str = "") -> tuple[list[str], list[list[str]]]:
    """CSV (Semikolon, Komma oder Tab; UTF-8 oder Windows-1252) oder Excel (.xlsx, erstes Blatt) lesen."""
    if filename.lower().endswith((".xlsx", ".xlsm")) or data[:2] == b"PK":
        from openpyxl import load_workbook
        ws = load_workbook(io.BytesIO(data), read_only=True, data_only=True).worksheets[0]
        rows = [["" if v is None else _cell(v) for v in r] for r in ws.iter_rows(values_only=True)]
    else:
        for enc in ("utf-8-sig", "cp1252"):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        sample = text[:5000]
        delim = max([";", ",", "\t"], key=lambda d: sample.count(d))
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    rows = [[c.strip() for c in r] for r in rows if any(str(c).strip() for c in r)]
    if not rows:
        return [], []
    head, body = rows[0], rows[1:]
    width = len(head)
    return head, [(r + [""] * width)[:width] for r in body]


def _cell(v) -> str:
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def auto_mapping(entity: str, headers: list[str]) -> dict:
    """Spalte → Feld anhand Bezeichnung und bekannter Synonyme."""
    fields = ENTITIES[entity]["fields"]
    out, used = {}, set()
    for i, h in enumerate(headers):
        nh = norm(h)
        for key, label, _t, _req, aliases in fields:
            if key in used:
                continue
            names = {norm(label), norm(key)} | {norm(a) for a in aliases}
            if nh in names or norm(re.sub(r"\(.*?\)|€/?\w*|%", "", label)) == nh:
                out[str(i)] = key
                used.add(key)
                break
    return out


def parse_number(s: str) -> float:
    s = str(s).strip().replace("€", "").replace("%", "").replace(" ", "").replace(" ", "")
    if not s:
        raise ValueError("leer")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def parse_date(s: str) -> date:
    s = str(s).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Datum „{s}“ nicht erkannt (TT.MM.JJJJ)")


def parse_bool(s: str) -> bool:
    v = norm(s)
    if v in ("ja", "j", "x", "1", "true", "wahr", "yes", "aktiv"):
        return True
    if v in ("nein", "n", "0", "false", "falsch", "no", "inaktiv", ""):
        return False
    raise ValueError(f"„{s}“ ist nicht ja/nein")


def convert(ftype: str, raw: str):
    """Rohwert in den Feldtyp umwandeln; leer → None. Referenzen bleiben Text (Auflösung in der DB-Schicht)."""
    raw = str(raw or "").strip()
    if raw == "":
        return None
    if ftype == "text" or ftype.startswith("ref:"):
        return raw
    if ftype == "number":
        return parse_number(raw)
    if ftype == "pct_factor":  # Prozent → Faktor (30 → 0,3); Werte ≤ 3 gelten schon als Faktor
        v = parse_number(raw)
        return v / 100 if v > 3 else v
    if ftype == "int":
        return int(round(parse_number(raw)))
    if ftype == "date":
        return parse_date(raw)
    if ftype == "bool":
        return parse_bool(raw)
    if ftype.startswith("choice:"):
        opts = dict(o.split("=", 1) for o in ftype[7:].split("|"))
        n = norm(raw)
        for k, label in opts.items():
            if n in (norm(k), norm(label)) or norm(label).startswith(n):
                return k
        raise ValueError(f"„{raw}“ unbekannt – erlaubt: {', '.join(opts.values())}")
    return raw


def parse_rows(entity: str, rows: list[list[str]], mapping: dict) -> list[dict]:
    """Je Zeile: Werte + Fehler (Pflichtfelder, Typen). Referenzen und Abgleich macht die DB-Schicht."""
    fields = {f[0]: f for f in ENTITIES[entity]["fields"]}
    out = []
    for n, r in enumerate(rows, start=2):  # Zeile 1 = Kopfzeile
        vals, errs = {}, []
        for col, key in mapping.items():
            if not key or key not in fields:
                continue
            raw = r[int(col)] if int(col) < len(r) else ""
            try:
                v = convert(fields[key][2], raw)
            except ValueError as e:
                errs.append(f"{fields[key][1]}: {e}")
                continue
            if v is not None:
                vals[key] = v
        for key, (_, label, _t, req, _a) in fields.items():
            if req and vals.get(key) in (None, "") and not any(f"{label}:" in e for e in errs):
                errs.append(f"{label} fehlt")
        out.append({"row": n, "values": vals, "errors": errs})
    return out


def template_csv(entity: str) -> bytes:
    cfg = ENTITIES[entity]
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    w.writerow([f[1] + (" *" if f[3] else "") for f in cfg["fields"]])
    w.writerow(cfg["example"])
    return ("﻿" + buf.getvalue()).encode("utf-8")
