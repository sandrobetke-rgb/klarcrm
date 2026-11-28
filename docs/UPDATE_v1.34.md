# KlarCRM – Update auf v1.34 (Anleitung für die IT)

Stand: 28.11.2026 · vorher installiert: v1.32 (v1.33 muss **nicht** vorher eingespielt werden – v1.34 enthält v1.33) · Dauer: ca. 10 Minuten · CRM ca. 1–2 Minuten nicht erreichbar

## Was ist neu (Kurzfassung) – Lastenheft Kap. 13.8 und 13.9
- Kalkulation: Mengen je Lieferjahr, Losgröße-Vorschlag, Staffelpreise für Material und Zukaufteile, Varianten
- Neue Materialien und Zukaufteile aus der Kalkulation landen automatisch in den Stammdaten
- Vertriebsziel auf der Startseite größer, Prüfbericht als PDF/CSV auf der Seite „Prüfen“
- Neu in v1.34: Reiter Werkzeug, Risiko, Neue Anlagen und Kickoff in der Kalkulation; Kickoff entsteht automatisch beim Auftrag

Beim ersten Start ergänzt das CRM selbst sieben Spalten (Staffelpreise bei Material und Zukaufteilen; bei Kalkulationen
Variante von, Werkzeugblatt, Risiko, neue Anlagen, Kickoff). Bestehende Kalkulationen rechnen unverändert. Keine Handarbeit in der Datenbank nötig.
Das Datum „eingespielt am“ ist der erste Start – bitte erst starten, wenn wirklich eingespielt wird.

## 1. Sicherung (Pflicht)
```bash
docker compose exec -T db pg_dump -U crm crm | gzip > /backup/klarcrm_db_vor_v1.34_$(date +%F).sql.gz
cp -a /opt/klarcrm /opt/klarcrm_v1.32      # Projektordner sichern (Pfad ggf. anpassen)
```

## 2. Dateien einspielen
ZIP `KlarCRM_v1.34_….zip` in den Projektordner entpacken und überschreiben (`.env` bleibt) – oder per Git:
`git fetch && git checkout release-v1.34`

## 3. Starten
```bash
docker compose up -d --build
docker compose logs -f backend      # bis „Application startup complete“, dann Strg+C
```

## 4. Kurztest
1. Anmeldeseite: unten **KlarCRM v1.34 · eingespielt am** (heutiges Datum).
2. Eine Kalkulation öffnen → es gibt die Reiter „3 · Werkzeug“ und „4 · Risiko“; im Reiter Kalkulation unter „Mengen“
   steht die Tabelle „Mengen je Lieferjahr“.
3. **Anfragen** und **Pipeline** öffnen – kein „Fehler 500“.

Die eigentliche Prüfung macht die Geschäftsführung auf der Seite **Prüfen**.

## 5. Rückweg
`docker compose down`, alten Projektordner zurück, `docker compose up -d --build`. Datenbank nur nach Rücksprache
(Sandro Betke) aus der Sicherung zurückspielen. Die neuen Spalten stören v1.32 nicht.
