# KlarCRM – Update auf v1.31 (Anleitung für die IT)

Stand: 25.11.2026 · vorher installiert: v1.30 oder v1.30.1 · Dauer: ca. 10 Minuten · CRM ca. 1–2 Minuten nicht erreichbar

## Was ist neu (Kurzfassung) – Korrekturen aus dem Test (Lastenheft Kap. 13.5)
- Pipeline/Anfragen ohne Fehler 500 (falls v1.30.1 noch nicht eingespielt war)
- Angebot lässt sich erstellen (keine Sperre durch fehlende Entscheidung oder Freigabe)
- Freigabe-Workflow abgeschaltet (Stammdaten › Parameter, 0 = aus)
- Artikelanalyse: Speichern oben; Schließkraft nach F&R-Standard 0,55 t/cm²
- Vertriebsziel sichtbar, auch wenn nur Ziele je Vertriebler hinterlegt sind
- Wahrscheinlichkeit als Einschätzung direkt am Angebot

## 1. Sicherung (Pflicht)
```bash
docker compose exec -T db pg_dump -U crm crm | gzip > /backup/klarcrm_db_vor_v1.31_$(date +%F).sql.gz
cp -a /opt/klarcrm /opt/klarcrm_v1.30      # Projektordner sichern (Pfad ggf. anpassen)
```

## 2. Dateien einspielen
ZIP `KlarCRM_v1.31_….zip` in den Projektordner entpacken und überschreiben (`.env` bleibt) – oder per Git:
`git fetch && git checkout release-v1.31`

## 3. Starten
```bash
docker compose up -d --build
docker compose logs -f backend      # bis „Application startup complete“, dann Strg+C
```

## 4. Kurztest
1. Dokumentation → Lastenheft zeigt **Version 1.31**.
2. **Pipeline** und **Anfragen** öffnen – kein „Fehler 500“.
3. Eine Kalkulation → Reiter „1 · Artikelanalyse“: oben steht die Leiste „💾 Analyse speichern“.

## 5. Rückweg
`docker compose down`, alten Projektordner zurück, `docker compose up -d --build`. Datenbank nur nach Rücksprache
(Sandro Betke) aus der Sicherung zurückspielen.
