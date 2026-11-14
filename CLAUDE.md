# Hinweise für die Arbeit an KlarCRM

- Sprache: Deutsch (Oberfläche, Doku, Commit-Nachrichten).
- **Lastenheft immer mitziehen:** Jede Änderung an Funktionen, Regeln oder Rechenweg wird in `docs/LASTENHEFT.md`
  dokumentiert – Anforderung mit ID ergänzen/ändern, Dokumentversion und Stand erhöhen, Zeile in der Änderungshistorie.
- Rechenkern der Kalkulation: `backend/app/calc_engine.py`. Änderungen am Rechenweg auch in Lastenheft Kap. 6.2
  (Formeltabelle) nachziehen; die Referenzkalkulation im CI-Workflow muss weiter passen.
- Neue Spalten in bestehenden Tabellen werden nicht automatisch angelegt (kein Alembic) – im Lastenheft/README vermerken.
