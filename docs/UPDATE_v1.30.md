# KlarCRM – Update auf v1.30 (Anleitung für die IT)

Stand: 24.11.2026 · vorher installiert: v1.24 · Dauer: ca. 15 Minuten · Ausfall des CRM: ca. 2–3 Minuten

## Was ist neu (Kurzfassung)
- Preisliste mit Materialpreisänderungen, Import/Export (Lastenheft Kap. 14)
- Monatsbericht Vertrieb mit Vertriebsziel und PDF (Kap. 15), Teilbeauftragung „Auftrag erhalten“ (Kap. 15.4)
- Korrekturen aus der Testrunde Phase 2 (Kap. 13.4, REV02-01 … 10): Freigabe nur ab 500 T€ Umsatz / 350 T€ Invest,
  Freigabe an eine gewählte Person, Wahrscheinlichkeit von Hand, Uhrzeit (Sommer-/Winterzeit), Protokoll ausgeblendet u. a.

## 1. Sicherung (Pflicht, vor dem Update)
Im Projektordner auf dem Server:
```bash
mkdir -p /backup
docker compose exec -T db pg_dump -U crm crm | gzip > /backup/klarcrm_db_vor_v1.30_$(date +%F).sql.gz
docker run --rm -v klarcrm_uploads:/data -v /backup:/backup alpine tar czf /backup/klarcrm_docs_vor_v1.30_$(date +%F).tgz -C /data .
```
(Volume-Name ggf. mit `docker volume ls` prüfen.) Zusätzlich den bisherigen Projektordner kopieren, z. B.
`cp -a /opt/klarcrm /opt/klarcrm_v1.24` – das ist der Rückweg.

## 2. Dateien einspielen
**Variante ZIP:** Inhalt von `KlarCRM_v1.30_….zip` in den bestehenden Projektordner entpacken und Dateien
überschreiben. Die `.env` ist **nicht** im ZIP und bleibt unverändert – nichts neu eintragen.

**Variante Git:** `git fetch && git checkout release-v1.30`

## 3. Starten
```bash
docker compose up -d --build
docker compose logs -f backend      # warten bis „Application startup complete“, dann Strg+C
```
Hinweis: `docker-compose.yml` hat jetzt die Zeitzone `Europe/Berlin` für Backend und Datenbank. Docker startet
deshalb auch den Datenbank-Container neu – die Daten liegen im Volume und bleiben erhalten.

## 4. Was beim ersten Start automatisch passiert
- neue Tabellen und Spalten werden ergänzt (Preisliste, Monatsbericht, Vertriebsziele, Freigabe-Empfänger …)
- Freigabeschwellen: 250.000 € → **500.000 € Umsatz / 350.000 € Invest** (nur wenn noch 250.000 € eingestellt war)
- Wahrscheinlichkeiten offener Anfragen → „nicht eingeschätzt“ (wurden bisher automatisch gesetzt)
- Änderungsprotokoll: neue Einträge REV02-01 … 10, MB-01/02, PRL-01/02, WUN-0001 zum Prüfen
- Die Anzeige des Änderungsprotokolls (Audit) ist in dieser Version für alle ausgeblendet; aufgezeichnet wird weiter.

## 5. Kurztest nach dem Update
1. Anmelden → Menü **Dokumentation** → Lastenheft zeigt **Version 1.30**.
2. Menü **Monatsbericht** und **Preisliste** sind vorhanden.
3. Eine Aktivität mit Fälligkeit 10:00 anlegen → in der Liste steht 10:00 (nicht 11:00).
4. Kein Menüpunkt „Protokoll“.

## 6. Falls etwas schiefgeht (Rückweg)
```bash
docker compose down
# alten Projektordner zurück (z. B. /opt/klarcrm_v1.24) und dort:
gunzip -c /backup/klarcrm_db_vor_v1.30_*.sql.gz | docker compose exec -T db psql -U crm -d crm   # nach leerer DB
docker compose up -d --build
```
Vor einer Wiederherstellung bitte Rücksprache (Sandro Betke) – die Datenbank muss dafür leer sein.

Bei Fragen oder Fehlermeldungen: Ausgabe von `docker compose logs backend --tail 200` an Sandro schicken.
