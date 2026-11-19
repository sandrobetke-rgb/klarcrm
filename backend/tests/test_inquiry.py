"""Regeln der Anfrage / Angebotsverfolgung (REV01 Phase 2): Arbeitstage und Ampel."""
from datetime import date, datetime, timedelta, timezone

from app.inquiry import add_workdays, followup_light, next_workday, workdays_between


def test_add_workdays_skips_weekend():
    assert add_workdays(date(2026, 11, 19), 5) == date(2026, 11, 26)   # Do + 5 AT = Do der Folgewoche
    assert add_workdays(date(2026, 11, 20), 1) == date(2026, 11, 23)   # Fr + 1 AT = Mo
    assert next_workday(date(2026, 11, 21)) == date(2026, 11, 23)      # Sa → Mo


def test_workdays_between():
    assert workdays_between(date(2026, 11, 16), date(2026, 11, 27)) == 9   # Mo → Fr nächste Woche
    assert workdays_between(date(2026, 11, 27), date(2026, 11, 16)) == -9
    assert workdays_between(date(2026, 11, 21), date(2026, 11, 22)) == 0  # Sa → So


def test_followup_light():
    today = date.today()
    at = lambda d: datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)  # noqa: E731
    assert followup_light(at(today - timedelta(days=1))) == "rot"
    assert followup_light(at(today)) == "gelb"
    assert followup_light(at(add_workdays(today, 3))) == "gruen"
    assert followup_light(at(today), done=True) is None
