# KlarCRM – Update auf v1.32 (Anleitung für die IT)

Stand: 27.11.2026 · vorher installiert: v1.31 · Dauer: ca. 10 Minuten · CRM ca. 1–2 Minuten nicht erreichbar

## Was ist neu (Kurzfassung) – Lastenheft Kap. 13.6
- Neue Seite **Prüfen** (Menü System): Punkte des Updates nacheinander prüfen und abhaken
- **Softwarestand** unten links und auf der Anmeldeseite: „KlarCRM v1.32 · eingespielt am …“
- **Vertriebsziel** groß oben auf der Startseite
- **Pipeline** zeigt wieder alle Spalten inkl. „Verloren“
- Kleinigkeiten: Freigabe-Schalter als Häkchen, Schrittleiste „Kalkulation“ in der Anfrage

Beim ersten Start ergänzt das CRM selbst einige Spalten in der Tabelle der Änderungswünsche und stellt ersetzte
Altpunkte auf „überholt“. Keine Handarbeit in der Datenbank nötig. **Wichtig:** Das Datum „eingespielt am“ ist der
Zeitpunkt dieses ersten Starts – bitte das Update also erst starten, wenn es wirklich eingespielt wird.

## 1. Sicherung (Pflicht)
```bash
docker compose exec -T db pg_dump -U crm crm | gzip > /backup/klarcrm_db_vor_v1.32_$(date +%F).sql.gz
cp -a /opt/klarcrm /opt/klarcrm_v1.31      # Projektordner sichern (Pfad ggf. anpassen)
```

## 2. Dateien einspielen
ZIP `KlarCRM_v1.32_….zip` in den Projektordner entpacken und überschreiben (`.env` bleibt) – oder per Git:
`git fetch && git checkout release-v1.32`

## 3. Starten
```bash
docker compose up -d --build
docker compose logs -f backend      # bis „Application startup complete“, dann Strg+C
```

## 4. Kurztest
1. Anmeldeseite: unten steht **KlarCRM v1.32 · eingespielt am** (heutiges Datum).
2. Anmelden → Menü links unter „System“ gibt es **Prüfen** mit einer Zahl.
3. **Pipeline** öffnen – rechts außen die Spalte „Verloren“; **Anfragen** öffnen – kein „Fehler 500“.

Die eigentliche Prüfung macht die Geschäftsführung auf der Seite **Prüfen**.

## 5. Rückweg
`docker compose down`, alten Projektordner zurück, `docker compose up -d --build`. Datenbank nur nach Rücksprache
(Sandro Betke) aus der Sicherung zurückspielen. Die neuen Spalten stören v1.31 nicht.
