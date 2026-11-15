"""Tests für den CSV-/Excel-Import (ohne Datenbank)."""
import io

import pytest

from app.importer import auto_mapping, convert, parse_number, parse_rows, read_table, template_csv


def test_zahlen_deutsch_und_englisch():
    assert parse_number("1.234,56") == 1234.56
    assert parse_number("1,234.56") == 1234.56
    assert parse_number("3,40 €") == 3.4
    assert parse_number("85 %") == 85


def test_csv_semikolon_windows_kodierung_und_zuordnung():
    data = "Firmenname;Ort;PLZ;Branche\r\nMüller Kunststoff GmbH;Lemgo;32657;Automotive\r\n".encode("cp1252")
    head, rows = read_table(data, "kunden.csv")
    assert head == ["Firmenname", "Ort", "PLZ", "Branche"] and rows[0][0] == "Müller Kunststoff GmbH"
    mp = auto_mapping("accounts", head)
    assert mp == {"0": "name", "1": "city", "2": "zip", "3": "industry"}


def test_vorlage_wird_wieder_erkannt():
    head, rows = read_table(template_csv("machines"))
    mp = auto_mapping("machines", head)
    assert len(mp) == len(head)  # jede Spalte der Vorlage wird zugeordnet
    p = parse_rows("machines", rows, mp)[0]
    assert p["errors"] == []
    assert p["values"]["hourly_rate"] == 55 and p["values"]["operator_factor"] == pytest.approx(0.3)
    assert p["values"]["kind"] == "spritzguss" and p["values"]["active"] is True


def test_pflichtfelder_und_typfehler():
    rows = [["", "abc"], ["PA6", "3,4"]]
    p = parse_rows("materials", rows, {"0": "name", "1": "price_per_kg"})
    assert "Bezeichnung fehlt" in p[0]["errors"] and any("Preis" in e for e in p[0]["errors"])
    assert p[1]["errors"] == [] and p[1]["values"] == {"name": "PA6", "price_per_kg": 3.4}


def test_auswahl_datum_und_excel():
    assert convert("choice:kunde=Kunde|lieferant=Lieferant", "Lieferant") == "lieferant"
    assert convert("date", "01.02.2027").isoformat() == "2027-02-01"
    from openpyxl import Workbook
    wb = Workbook()
    wb.active.append(["Bezeichnung", "Preis €"])
    wb.active.append(["Clip", 0.032])
    buf = io.BytesIO()
    wb.save(buf)
    head, rows = read_table(buf.getvalue(), "teile.xlsx")
    assert head == ["Bezeichnung", "Preis €"] and rows == [["Clip", "0.032"]]
