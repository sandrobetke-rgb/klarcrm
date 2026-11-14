# Lastenheft KlarCRM

| | |
|---|---|
| **Projekt** | KlarCRM – schlankes CRM mit Spritzguss-Kalkulation |
| **Auftraggeber** | Friedrichs & Rath (F&R), Geschäftsführung |
| **Dokumentversion** | 1.1 |
| **Stand** | 14.11.2026 |
| **Status** | Testphase (GitHub Codespaces) |

> Dieses Lastenheft wird bei **jeder** Änderung am System mitgezogen. Neue Anforderungen, geänderte Regeln und
> umgesetzte Punkte werden in der Änderungshistorie (Kapitel 12) dokumentiert. Anforderungen tragen eine feste ID
> (z. B. `KAL-12`), damit Änderungen nachvollziehbar bleiben.

---

## 1. Ausgangslage und Ziel

F&R benötigt ein CRM für Vertrieb und Gesellschafter, das in der Funktion an Salesforce angelehnt, aber deutlich
einfacher und ohne Lizenzkosten pro Nutzer ist. Zusätzlich soll die **Angebotskalkulation für Spritzgussteile**
im selben System erfolgen, damit

- jede Anfrage mit Kalkulationsnummer, Versionen und Status transparent nachverfolgt wird,
- die kalkulierten Preise direkt in die Umsatz- und Pipeline-Übersicht einfließen,
- Verlustgründe systematisch ausgewertet werden können und
- jede gewonnene Kalkulation einer **Nachkalkulation** mit Ampel unterzogen wird.

**Leitprinzip:** maximale Transparenz – jeder Wert ist sichtbar, nachvollziehbar und überschreibbar; Abweichungen
von Standardwerten werden markiert; jede Änderung an einer Kalkulation erzeugt eine neue Version.

## 2. Nutzer und Rollen

| ID | Rolle | Rechte |
|---|---|---|
| ROL-1 | Administrator | Alles inkl. Benutzerverwaltung und Kalkulations-Parameter (Standardsätze) |
| ROL-2 | Vertrieb | Alle Daten sehen, anlegen, ändern, löschen; Stammdaten Maschinen/Materialien pflegen |
| ROL-3 | Gesellschafter | Alles sehen (Dashboard, Pipeline, Kalkulationen, Nachkalkulation), **nichts ändern** |

- ROL-4: Rechte werden serverseitig erzwungen (HTTP 403), nicht nur in der Oberfläche.
- ROL-5: Auslegung für bis zu ca. 12 gleichzeitige Nutzer.

## 3. Systemübersicht

| Modul | Kurzbeschreibung |
|---|---|
| Dashboard | Vertriebs-KPIs, Forecast, Kalkulations-KPIs, Vergleich der Mitarbeiter |
| Firmen / Kontakte | Kunden, Interessenten, Partner, Lieferanten und Ansprechpartner |
| Pipeline | Verkaufschancen (Projekte) als Kanban-Board und Liste |
| Aktivitäten | Anrufe, Termine, E-Mails, Aufgaben, Notizen mit Fälligkeit |
| **Kalkulation** | Anfragen, Kalkulationsschema Spritzguss, Versionen, Nachkalkulation |
| **Stammdaten** | Maschinen, Materialien, Kalkulations-Parameter |
| Angebote | Angebote mit Positionen, Druck/PDF, Erzeugung aus Kalkulation |
| Benutzer | Konten, Rollen, Passwörter |

## 4. CRM-Grundfunktionen (umgesetzt in v1.0)

- CRM-1: Firmen mit Typ (Interessent/Kunde/Partner/Lieferant), Adresse, Branche, Verantwortlichem, Notizen.
- CRM-2: Firmen-Detailseite mit Kontakten, Verkaufschancen, **Kalkulationen**, Angeboten und Aktivitätsverlauf.
- CRM-3: Kontakte mit Anrede, Position, Telefon, E-Mail, Zuordnung zur Firma.
- CRM-4: Verkaufschancen mit Phasen Lead → Qualifiziert → Angebot → Verhandlung → Gewonnen/Verloren; Wahrscheinlichkeit
  je Phase automatisch (überschreibbar); Abschlussdatum wird beim Gewinnen/Verlieren gesetzt.
- CRM-5: Pipeline als Kanban mit Drag & Drop und als Liste; Summen und gewichtete Summen je Phase.
- CRM-6: Aktivitäten mit Fälligkeit; Filter überfällig/heute/7 Tage; Abhaken in der Liste.
- CRM-7: Angebote mit automatischer Nummer (AN-JJJJ-NNNN), Positionen, Rabatt, MwSt., Duplizieren, Druckansicht (PDF).
- CRM-8: Dashboard mit offener Pipeline, Quartals-Forecast, gewonnenem Umsatz, Gewinnquote, Umsatz je Monat,
  Pipeline je Phase, Vergleich je Vertriebsmitarbeiter, anstehenden Abschlüssen; filterbar je Mitarbeiter.

## 5. Stammdaten für die Kalkulation

### 5.1 Maschinen
- STM-1: Je Maschine: Nummer, Bezeichnung, Schließkraft, Standort, **Maschinenstundensatz €/h (ohne Personal)**,
  **Instandhaltung €/h**, **Standard-Produktivität %**, **Standard-Bedienfaktor** (Personen je Maschine), aktiv/inaktiv.
- STM-2: Bei Auswahl einer Maschine in der Kalkulation werden Stundensatz, Instandhaltung, Produktivität und
  Bedienfaktor sofort übernommen und der Preis neu berechnet.
- STM-3: Inaktive Maschinen sind in neuen Kalkulationen nicht auswählbar; bestehende Kalkulationen bleiben unverändert.

### 5.2 Materialien
- STM-4: Je Material: Bezeichnung, Werkstoffgruppe, Lieferant, **Preis €/kg**, Dichte, aktiv/inaktiv.
- STM-5: Bei Auswahl wird der Materialpreis übernommen (überschreibbar).

### 5.3 Parameter (Standardwerte)
- STM-6: Lohnsätze Bediener, Einrichter, Montage (€/h).
- STM-7: Zuschläge MGK, FGK, Ausschuss, Verwaltung, Vertrieb, Projektmanagement (%).
- STM-8: Gewinn (Standard **7 %**), Skonto, Rabatt.
- STM-9: Fertigungs-Standards: Produktivität, Montage-Produktivität, Rüstzeit, Einrichter je Rüstvorgang, Anfahrausschuss.
- STM-10: Ampel-Schwellen der Nachkalkulation (Standard grün bis +3 %, rot ab +10 %).
- STM-11: Nur Administratoren ändern Parameter. Änderungen wirken auf **neue** Kalkulationen; gespeicherte Versionen
  enthalten ihre Werte selbst und bleiben reproduzierbar.

## 6. Kalkulation (Anfrage → Kalkulation → Angebot → Auftrag)

### 6.1 Kopfdaten einer Kalkulation
- KAL-1: Automatische **Kalkulationsnummer** KA-JJJJ-NNNN.
- KAL-2: Artikelbezeichnung, **Artikelnummer des Kunden**, eigene Artikelnummer.
- KAL-3: Kunde, **Ansprechpartner des Kunden**, verknüpfte Verkaufschance (Projekt), Verantwortlicher.
- KAL-4: Status: Anfrage, In Kalkulation, Angeboten, Verhandlung, Gewonnen, Verloren, Zurückgestellt.
- KAL-5: **Wahrscheinlichkeit** des Auftrags in % – beim Statuswechsel vorgeschlagen, frei änderbar.
- KAL-6: **Verlustgrund** (bei Status Verloren):
  Artikelpreis zu hoch · Werkzeug zu teuer · Investition zu teuer · Kunde hat Projekt nicht gewonnen ·
  Projekt beim Kunden eingestellt · Lieferzeit/Kapazität · Technisch nicht machbar · Sonstiges.
- KAL-7: Bemerkungsfeld, Anfragedatum, Angebotsabgabe bis, Serienstart (SOP).
- KAL-8: **Zuletzt angerufen** – per Schaltfläche „Anruf dokumentieren“ mit Gesprächsnotiz; legt zusätzlich eine
  Aktivität beim Kunden an. In der Liste rot markiert, wenn offene Anfrage > 14 Tage nicht angerufen.

### 6.2 Kalkulationsschema (Zuschlagskalkulation)
Alle Eingaben sind überschreibbar. Abweichungen vom Standardwert (Maschine, Material, Parameter) werden gelb markiert
und lassen sich per Klick auf den Standard zurücksetzen (KAL-20).

**Eingaben**

| Bereich | Felder |
|---|---|
| Mengen | Jahresmenge, Losgröße, Projektlaufzeit (Jahre) |
| Material | Material (Stammdaten), Preis €/kg, Teilgewicht g, Anguss je Schuss g, Mahlgut-Rückführung %, Masterbatch-Anteil % und -Preis, Zukaufteile €/Stk |
| Maschine & Fertigung | Maschine (Stammdaten), Maschinenstundensatz €/h, Instandhaltung €/h, **Zykluszeit s**, **Fachzahl**, **Produktivität %**, Bedienfaktor, Lohnsatz Bediener |
| Rüsten | Rüstzeit je Los h, Einrichter, Lohnsatz Einrichter, Anfahrausschuss je Los Stk |
| Montage | Montagezeit je Stück s, Personen, Lohnsatz, Produktivität Montage % |
| Zuschläge | MGK, FGK, Ausschuss, Verwaltung, Vertrieb, Projektmanagement, Gewinn, Skonto, Rabatt (%) |
| Zusatzpositionen | frei: Bezeichnung, Betrag, Bezug (je Stück / je 1.000 / je Los / je Jahr), Art (Fertigung oder Vertrieb) – z. B. Peripherie, Nacharbeit, Bedrucken, Verpackung, Transport |
| Einmalkosten | frei: Bezeichnung, Kosten, Preis an Kunde – z. B. Werkzeug, Erstbemusterung, Prüfmittel |
| Verkaufspreis | optional manuell festgelegt (Gewinn ergibt sich dann als Rest) |

**Rechenweg je Stück** (KAL-21)

| Schritt | Formel |
|---|---|
| Ausbringung | Stück/h = 3600 / Zykluszeit × Fachzahl × Produktivität |
| Material (MEK) | (Teilgewicht + Anguss/Fachzahl × (1 − Mahlgut %)) / 1000 × Mischpreis €/kg + Zukaufteile; Mischpreis = Materialpreis × (1 − MB %) + MB-Preis × MB % |
| MGK | MEK × MGK % |
| Maschine | Maschinenstundensatz / Stück/h |
| Instandhaltung | Instandhaltung €/h / Stück/h |
| Personal | Lohnsatz × Bedienfaktor / Stück/h |
| Rüsten | [Rüstzeit × (Maschinensatz + Instandhaltung + Lohnsatz Einrichter × Einrichter) + Anfahrausschuss × (Material + Maschine + Instandhaltung + Personal je Stück)] / Losgröße |
| Montage | Montagezeit/3600 × Lohnsatz × Personen / Produktivität Montage |
| FEK | Maschine + Instandhaltung + Personal + Rüsten + Montage |
| FGK | FEK × FGK % |
| SEK Fertigung | Zusatzpositionen „Fertigung“ |
| HK vor Ausschuss | MEK + MGK + FEK + FGK + SEK Fertigung |
| Ausschuss | HK vor Ausschuss / (1 − Ausschuss %) − HK vor Ausschuss |
| Herstellkosten | HK vor Ausschuss + Ausschuss |
| Verwaltung / Vertrieb / PM | je HK × % |
| SEK Vertrieb | Zusatzpositionen „Vertrieb“ |
| Selbstkosten | HK + Verwaltung + Vertrieb + PM + SEK Vertrieb |
| Gewinn | SK × Gewinn % (bzw. Rest bei manuellem Preis) |
| Verkaufspreis | (SK + Gewinn) / (1 − Skonto) / (1 − Rabatt) |

**Ausgaben**
- KAL-22: Jede Position je **Stück, je 100, je 1.000** und als Anteil am Preis in %.
- KAL-23: Kennzahlen: Verkaufspreis, Jahresumsatz, Gewinn p. a., Marge, Projektumsatz (× Laufzeit), Einmalumsatz,
  Umsatz 1. Jahr gesamt, Stück/h (theoretisch und real), Maschinenstunden p. a., Materialbedarf kg p. a.,
  Rüstkosten je Los, Lose p. a., Schussgewicht.
- KAL-24: Warnhinweise bei fehlender Ausbringung/Losgröße und wenn der Preis unter den Selbstkosten liegt.
- KAL-25: Die Berechnung erfolgt **live** beim Eingeben (Server-Rechenkern, eine Quelle der Wahrheit).
- KAL-26: Druckansicht der Kalkulation.

### 6.3 Versionen
- KAL-30: Jede gespeicherte Änderung erzeugt eine **neue Version** (V1, V2, …) mit Änderungsnotiz, Benutzer, Zeitpunkt.
- KAL-31: Versionen sind unveränderlich und enthalten alle Eingaben und Ergebnisse (reproduzierbar, auch wenn sich
  Stammdaten später ändern).
- KAL-32: Jede ältere Version kann als Basis geladen und als neue Version weiterbearbeitet werden.
- KAL-33: **Versionsvergleich** A/B: geänderte Eingaben und Auswirkung auf Preis, Selbstkosten, Marge, Stück/h,
  Umsatz, Gewinn, Einmalumsatz, Maschinenstunden (absolut und %).

### 6.4 Übernahme in Umsatzübersicht und Angebot
- KAL-40: Kalkulation kann mit einer Verkaufschance verknüpft oder per Klick eine Verkaufschance anlegen.
- KAL-41: Bei aktivierter Synchronisation übernimmt die Verkaufschance automatisch: Volumen = Summe (Jahresumsatz +
  Einmalumsatz) aller verknüpften Kalkulationen; Wahrscheinlichkeit (bei einer Kalkulation direkt, bei mehreren
  umsatzgewichtet); Phase entsprechend Status; Verlustgrund als Text.
- KAL-42: **Angebot aus Kalkulation**: erzeugt ein Angebot mit Artikelposition (Jahresmenge × Stückpreis, Kunden-
  Artikelnummer, Material, Kalkulationsnummer/Version, Preis je 1.000) und je Einmalkosten-Position; Status der
  Kalkulation wechselt auf „Angeboten“.

### 6.5 Kalkulationsliste (Anfragenübersicht)
- KAL-50: Spalten: Kalk.-Nr. und Version, Artikel und eigene Art.-Nr., **Art.-Nr. Kunde**, Kunde und Ansprechpartner,
  Status und Verlustgrund, €/Stk, Menge p. a., Umsatz p. a. (+ Einmalumsatz), Wahrscheinlichkeit und gewichteter
  Umsatz, **zuletzt angerufen**, Bemerkung, Ampel der letzten Nachkalkulation.
- KAL-51: Suche (Nummer, Artikel, Artikelnummern, Bemerkung), Filter Status und Verlustgrund, Sortierung je Spalte.
- KAL-52: Kennzahlen: offene Anfragen, nicht angerufene > 14 Tage, Potenzial (offen, gewichtet), offene
  Werkzeugumsätze, gewonnen, verloren, Trefferquote, Ampelverteilung.
- KAL-53: Auswertung **Verlustgründe** (verlorener Jahresumsatz und Anzahl je Grund).
- KAL-54: Kalkulations-KPIs auch im Dashboard (für Gesellschafter).

## 7. Nachkalkulation
- NK-1: Zu jeder Kalkulation beliebig viele Nachkalkulationen (z. B. je Fertigungsauftrag oder Zeitraum) mit
  Referenz, Zeitraum, Bemerkung und Bezug auf eine Version.
- NK-2: Erfasst werden nur abweichende **Ist-Werte**: Zykluszeit, Fachzahl, Produktivität, Ausschuss, Materialpreis,
  Teil- und Angussgewicht, Rüstzeit, Losgröße, Montagezeit, Lohnsatz, Bedienfaktor, Maschinen- und
  Instandhaltungssatz, Zukaufteile, produzierte Menge, zusätzliche Ist-Kosten gesamt, erzielter Preis.
- NK-3: Die Ist-Rechnung nutzt **dasselbe Schema** wie die Vorkalkulation (vergleichbar).
- NK-4: Plan/Ist-Vergleich je Position (€/Stk, Δ €/Stk, Δ %), Stück/h, Marge Ist, Ergebnis gesamt (Menge × Gewinn).
- NK-5: **Ampel**: grün bis Grün-Schwelle Abweichung der Selbstkosten, gelb bis Rot-Schwelle, rot darüber oder wenn
  der Preis die Ist-Selbstkosten nicht deckt. Schwellen in den Parametern (STM-10).
- NK-6: Live-Vorschau der Ampel vor dem Speichern.

## 8. Nicht-funktionale Anforderungen
- NFA-1: Web-Anwendung (Desktop und Tablet), deutschsprachig, Zahlen im deutschen Format.
- NFA-2: Selbst gehostet (Docker), keine Lizenzkosten je Nutzer; Daten bleiben auf eigenem Server (DSGVO).
- NFA-3: Anmeldung per E-Mail/Passwort, Passwörter mit bcrypt gehasht, Sitzungen per Token (12 h).
- NFA-4: Betrieb hinter HTTPS-Reverse-Proxy; tägliches Datenbank-Backup.
- NFA-5: Automatischer Build- und Starttest bei jedem Push (GitHub Actions).
- NFA-6: API vollständig dokumentiert (Swagger unter /docs).

## 9. Technik
- Backend: Python FastAPI, SQLAlchemy, PostgreSQL 16; Rechenkern in `backend/app/calc_engine.py`.
- Frontend: React 18 (Vite), Auslieferung über nginx.
- Testumgebung: GitHub Codespaces (Demo-Daten, Logins siehe README).

## 10. Abgrenzung / noch nicht umgesetzt
- Kein E-Mail-Versand von Angeboten aus dem System.
- Kein Import aus ERP/BDE; Ist-Werte der Nachkalkulation werden manuell erfasst.
- Keine Mehrwährung; Euro.
- Keine Datenbank-Migrationen (Alembic) – neue Spalten in bestehenden Tabellen erfordern manuellen Schritt.

## 11. Offene Punkte / Ideen für die finale Version
- [ ] Abgleich des Kalkulationsschemas mit der bestehenden F&R-Excel-Kalkulation (Positionen, Zuschlagsbasen).
- [ ] Staffelpreise (mehrere Jahresmengen / Losgrößen in einer Kalkulation).
- [ ] Werkzeugamortisation über Stückzahl als Option.
- [ ] Mehrere Artikel je Anfrage in einer Kalkulationsmappe.
- [ ] Übernahme von Ist-Werten aus BDE/MES für die Nachkalkulation.
- [ ] CSV-/Excel-Import und -Export (Firmen, Kontakte, Kalkulationsliste).
- [ ] Wiedervorlage-Automatik (Aufgabe, wenn > 14 Tage kein Anruf).
- [ ] Rechte: Kalkulation nur für bestimmte Rollen sichtbar machen (z. B. Gewinnsätze).

## 12. Änderungshistorie

| Version | Datum | Änderung |
|---|---|---|
| 1.0 | 13.11.2026 | Erstversion CRM: Firmen, Kontakte, Pipeline, Aktivitäten, Angebote, Dashboard, Rollen, Docker, Codespaces-Testumgebung |
| 1.1 | 14.11.2026 | Modul **Kalkulation**: Stammdaten Maschinen/Materialien/Parameter, Zuschlagskalkulation Spritzguss (Material, MGK, Maschine, Instandhaltung, Personal, Rüsten, Montage, FGK, Ausschuss, Verwaltung, Vertrieb, Projektmanagement, Gewinn 7 % Standard), Zusatz- und Einmalkosten, Werte je Stück/100/1.000, Versionen mit Vergleich, Kalkulationsliste mit Verlustgründen und „zuletzt angerufen“, Übernahme in Verkaufschance, Angebot aus Kalkulation, Nachkalkulation mit Ampel, KPIs im Dashboard. Lastenheft eingeführt. |
