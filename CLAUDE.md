# Hinweise für die Arbeit an KlarCRM

- Sprache: Deutsch (Oberfläche, Doku, Commit-Nachrichten).
- **Lastenheft immer mitziehen:** Jede Änderung an Funktionen, Regeln oder Rechenweg wird in `docs/LASTENHEFT.md`
  dokumentiert – Anforderung mit ID ergänzen/ändern, Dokumentversion und Stand erhöhen, Zeile in der Änderungshistorie.
- Rechenkern der Kalkulation: `backend/app/calc_engine.py`. Änderungen am Rechenweg auch in Lastenheft Kap. 6.2
  (Formeltabelle) nachziehen und in `backend/tests/test_calc_engine.py` mit Handrechnung testen
  (`cd backend && python -m pytest tests`); die Referenzkalkulation im CI-Workflow muss weiter passen.
- Neue Tabellen und neue Spalten werden beim Start automatisch ergänzt (`ensure_columns` in `database.py`, nur additiv).
  Umbenennen/Löschen von Spalten ist manuell und muss im Lastenheft vermerkt werden.
