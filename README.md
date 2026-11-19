# KlarCRM – schlankes CRM für Vertriebsteams

Einfaches, selbst gehostetes CRM nach dem Vorbild von Salesforce – ohne Lizenzkosten pro Nutzer.
Ausgelegt für ein Vertriebsteam von bis zu ca. 12 Personen plus eine reine Lese-Ansicht für Gesellschafter.

**Stack:** Python FastAPI · PostgreSQL 16 · React 18 (Vite) · Docker Compose

📄 **Anforderungen und Änderungshistorie: [docs/LASTENHEFT.md](docs/LASTENHEFT.md)** – wird bei jeder Änderung mitgezogen.

## Funktionen

| Modul | Inhalt |
|---|---|
| **Dashboard** | Offene Pipeline (gesamt + gewichtet), Quartals-Forecast, gewonnener Umsatz lfd. Jahr, Gewinnquote, offene Angebote, überfällige Aufgaben, Umsatz je Monat, Pipeline je Phase, Vergleich der Vertriebsmitarbeiter, anstehende Abschlüsse. Filterbar je Mitarbeiter. |
| **Firmen** | Kunden, Interessenten, Partner, Lieferanten mit Stammdaten. Detailseite mit allen Kontakten, Chancen, Angeboten und dem Aktivitätsverlauf. |
| **Kontakte** | Ansprechpartner je Firma, Suche, Sortierung. |
| **Pipeline** | Kanban-Board mit Drag & Drop (Lead → Qualifiziert → Angebot → Verhandlung → Gewonnen/Verloren) und Listenansicht. Wahrscheinlichkeit wird je Phase automatisch gesetzt (überschreibbar), Abschlussdatum beim Gewinnen/Verlieren automatisch. |
| **Aktivitäten** | Anrufe, Termine, E-Mails, Aufgaben, Notizen mit Fälligkeit; Filter überfällig / heute / 7 Tage; Abhaken direkt in der Liste. |
| **Angebote** | Positionen mit Menge, Einheit, Einzelpreis, Rabatt; Netto/MwSt./Brutto; automatische Nummer (A26-0001, Revisionen A26-0001-R1), Duplizieren, Status, Druckansicht → PDF über den Browser. |
| **Kalkulation** | Anfragen mit Kalkulationsnummer (K26-0001), Zuschlagskalkulation Spritzguss (Material, MGK, Maschine, Instandhaltung, Personal, Rüsten, Montage, **Vorserienpreis**, **Jahresabschläge**, **Auswertungen** (Maschinengröße, Kunden, Absagegründe …), **Datenimport aus Excel/CSV**, **mehrere Standorte** mit eigenen Sätzen und Standortvergleich, **Beschaffung** von Werkzeugen und Anlagen mit Werkzeuganfrage und Angebotsvergleich, **weitere Arbeitsgänge 1 … N (Montagelinie, Schweißen, Prüfung …)**, **Zukaufteile aus Stammdaten**, FGK, Ausschuss, Verwaltung, Vertrieb, Projektmanagement, Qualität, Werkzeugbau, Gewinn), Werte je Stück/100/1.000, Versionen mit Vergleich, Verlustgründe, Anrufhistorie mit Ergebnis und Wiedervorlage, Übernahme in Verkaufschance, Angebot per Klick, Nachkalkulation mit Ampel, Staffelpreise je Losgröße, Machbarkeit und „Kein Angebot“ mit Gründen, Artikelanalyse (Schließkraft, Kühlzeit, passende Maschinen, Checkliste), **Sammelangebot** aus mehreren Artikeln per Mehrfachauswahl, Verpackung & Transport, **CO₂-Fußabdruck je Teil/Los/Jahr** mit Ausweis im Angebot. |
| **Auslastung** | Maschinenauslastung der nächsten Jahre: Bestand, gewonnene und offene Kalkulationen (gewichtet/maximal) gegen verfügbare Stunden. |
| **Stammdaten** | Maschinen (Stundensatz, Instandhaltung, Produktivität, Bedienfaktor), Materialien (€/kg), Parameter (Standard-Zuschläge, Gewinn 7 %, Lohnsätze, Ampel-Schwellen). Alles in der Kalkulation überschreibbar. |
| **Änderungswünsche** | Testrückmeldungen (REV01 ff.) und neue Wünsche mit Status, Umsetzung, Prüfanweisung und Prüfergebnis; Export CSV. |
| **Dokumentation** | Benutzerbeschreibung und Lastenheft im Programm, Download als Word. |
| **Benutzer** | Anlegen, Rollen, Deaktivieren, Passwort zurücksetzen. Jeder Nutzer kann sein Passwort selbst ändern. |

### Rollen

| Rolle | Darf |
|---|---|
| `admin` | alles, inkl. Benutzerverwaltung |
| `vertrieb` | alle Daten sehen, anlegen, ändern, löschen |
| `gesellschafter` | alles sehen (Dashboard, Pipeline, Firmen, Angebote), **nichts ändern** – wird im Backend erzwungen (HTTP 403) |

## Start mit Docker (empfohlen)

```bash
cp .env.example .env        # Passwörter und SECRET_KEY setzen!
docker compose up -d --build
```

Danach im Browser: **http://localhost:8080** – Login mit `ADMIN_EMAIL` / `ADMIN_PASSWORD` aus der `.env`.
Der erste Admin wird beim ersten Start automatisch angelegt.

**Demo-Daten** (optional, nur in eine leere Datenbank):

```bash
docker compose exec backend python -m app.seed
```

Demo-Logins: `anna.berg@firma.de` / `demo1234` (Vertrieb), `gesellschafter@firma.de` / `demo1234` (nur lesen).

## Lokale Entwicklung ohne Docker

```bash
# Backend (PostgreSQL muss laufen, DB "crm" / User "crm")
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://crm:crm@localhost:5432/crm
uvicorn app.main:app --reload            # API: http://localhost:8000/docs

# Frontend
cd frontend
npm install
npm run dev                               # http://localhost:5173 (leitet /api an Port 8000 weiter)
```

Die komplette API ist unter **http://localhost:8000/docs** (Swagger) dokumentiert und testbar.

## Betrieb auf dem internen Server (F&R)

1. Server im Firmennetz (Linux-VM, Docker installiert), DNS-Name z. B. `crm.firma.local`.
2. `.env` aus `.env.example` anlegen und ausfüllen – mindestens `DB_PASSWORD`, `SECRET_KEY`, `ADMIN_PASSWORD`,
   `APP_URL=https://crm.firma.local`; für E-Mail-Hinweise den internen Mailserver unter `SMTP_*` eintragen.
3. `docker compose up -d --build` – Datenbank und hochgeladene Dokumente liegen in Docker-Volumes (`pgdata`, `uploads`).
4. HTTPS über den vorhandenen Reverse Proxy / ein internes Zertifikat vor Port 8080.
5. Nach dem ersten Login: **Firma & Layout** (Logo, Briefkopf, Bank, AGB-Text), **Stammdaten** (Maschinen,
   Materialien, Parameter), **Benutzer** (Rollen, Freigabeberechtigung).
6. Outlook: jeder Benutzer findet unter „Mein Profil“ seine Kalender-Adresse („Kalender hinzufügen → Aus dem Internet“).

**Update auf eine neue Version:** freigegebene Stände liegen im Zweig `release-v…` (aktuell `release-v1.24`):
`git fetch && git checkout release-v1.24` und `docker compose up -d --build`. Der Zweig `main` enthält bereits
Funktionen für das nächste große Update (z. B. Preisliste) und ist nicht für den Server gedacht. Neue Tabellen/Spalten werden beim Start
automatisch ergänzt. Ab v1.23 baut das Backend-Image aus der Projektwurzel (damit `docs/` für das Menü
„Dokumentation“ im Image liegt) – `docker compose` erledigt das automatisch, es ist nichts weiter zu tun.

**Backup (Pflicht):** täglich Datenbank **und** Dokumente sichern und die Wiederherstellung regelmäßig testen:
```bash
docker compose exec -T db pg_dump -U crm crm | gzip > /backup/klarcrm_db_$(date +%F).sql.gz
docker run --rm -v klarcrm_uploads:/data -v /backup:/backup alpine tar czf /backup/klarcrm_docs_$(date +%F).tgz -C /data .
```
(Volume-Name ggf. mit `docker volume ls` prüfen.)

## Betrieb im Unternehmen

- **Server:** Eine kleine VM (2 vCPU, 4 GB RAM) reicht für 12 Nutzer locker; z. B. intern im Netz oder bei einem deutschen Hoster.
- **HTTPS:** Vor den Port 8080 einen Reverse Proxy mit Zertifikat stellen (z. B. Caddy, Traefik oder der vorhandene Firmen-Proxy). Ohne HTTPS nicht übers Internet erreichbar machen.
- **Backup:** täglicher Datenbank-Dump, z. B. per Cronjob:
  ```bash
  docker compose exec -T db pg_dump -U crm crm | gzip > backup_$(date +%F).sql.gz
  ```
- **DSGVO:** Es werden personenbezogene Kontaktdaten gespeichert – Verarbeitungsverzeichnis ergänzen, Zugriff nur über Benutzerkonten, Daten bleiben auf eurem Server.
- **Sicherheit:** `SECRET_KEY`, `DB_PASSWORD` und `ADMIN_PASSWORD` in der `.env` unbedingt ändern.

## Projektstruktur

```
backend/app/
  main.py          App, Router, Admin-Anlage beim Start
  models.py        Datenmodell (User, Account, Contact, Opportunity, Activity, Quote, QuoteItem)
  schemas.py       Ein-/Ausgabe-Validierung (Pydantic)
  auth.py          Login (JWT), Passwort-Hashing (bcrypt), Rollenprüfung
  crud.py          Generischer Router: Suche, Filter, Sortierung, Paging
  calc_engine.py   Rechenkern der Kalkulation (Schema und Nachkalkulation)
  routers/         entities.py, quotes.py, users.py, dashboard.py, calc.py
  seed.py          Demo-Daten
frontend/src/
  pages/           Dashboard, Pipeline, Firmen, Kontakte, Aktivitäten, Kalkulationen, Kalkulations-Editor,
                   Nachkalkulation, Stammdaten, Angebote, Benutzer
docs/LASTENHEFT.md Lastenheft mit Änderungshistorie
  components/      Formulare, Listen-Seite, Diagramme, Dialoge
  forms.js         Feld-Definitionen der Formulare (hier neue Felder ergänzen)
```

## Erweitern

Ein neues Feld, z. B. „Kundennummer" bei Firmen:
1. `backend/app/models.py` → Spalte in `Account` ergänzen
2. `backend/app/schemas.py` → Feld in `AccountBase` ergänzen
3. `frontend/src/forms.js` → Eintrag in `accountFields`

Hinweis: Neue Tabellen und neue Spalten werden beim Start automatisch ergänzt. Umbenennen oder Löschen von Spalten
ist ein manueller Schritt (z. B. per SQL).

Mögliche nächste Ausbaustufen: CSV-Import/-Export, E-Mail-Versand von Angeboten, Outlook-Kalender-Sync,
Produktkatalog/Artikelstamm, Anbindung an ERP, Audit-Log.
