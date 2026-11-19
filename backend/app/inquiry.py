"""Anfrage / Projekt (REV01 Phase 2).

Eine Kundenanfrage ist eine Pipeline-Karte (Tabelle opportunities) mit n Artikeln (Kalkulationen) und genau einem
Angebot mit n Positionen (Revisionen -R1 …). Dieses Modul enthält die Regeln:

- Nummer AF26-0001, Art „anfrage“ (mit Artikeln) oder „lead“ (Potenzial ohne Anfrage, manuell)
- Entscheidung je Artikel vor Kalkulationsstart: anbieten · nicht anbieten (mit Grund) · anderer Standort · Sonstiges
- Phase automatisch: Neue Anfrage → Qualifiziert (≥ 1 Artikel freigegeben) → Angebot (versendet) → Verhandlung (manuell,
  Endrunde) → Gewonnen / Verloren / Nicht angeboten
- Wahrscheinlichkeit gilt für den ganzen Auftrag; Umsätze werden nicht damit gewichtet (REV01-P09)
- Angebotsverfolgung: ab „versendet“ Aufgabe nach 5 Arbeitstagen mit Ampel; „niemanden erreicht“ → nächster Arbeitstag
"""
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import CLOSED_STAGES, STAGE_PROBABILITY, Activity, Calculation, Opportunity, Quote

DECISIONS = {
    "anbieten": "Artikel wird angeboten",
    "nicht_anbieten": "Nicht angeboten",
    "anderer_standort": "Angeboten von anderem Standort",
    "sonstiges": "Sonstiges",
}
RELEASED = ("anbieten", "anderer_standort", "sonstiges")      # Kalkulation freigegeben
CALC_CLOSED = ("verloren", "kein_angebot", "gewonnen", "zurueckgestellt")
STAGE_ORDER = {s: i for i, s in enumerate(("lead", "neue_anfrage", "qualifiziert", "angebot", "verhandlung"))}


# ------------------------------------------------------------------ Hilfen
def add_workdays(d: date, n: int) -> date:
    """n Arbeitstage (Mo–Fr) nach d."""
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def next_workday(d: date) -> date:
    return add_workdays(d, 1)


def workdays_between(a: date, b: date) -> int:
    """Arbeitstage von a bis b (b > a positiv, sonst negativ)."""
    if a == b:
        return 0
    sign, (x, y) = (1, (a, b)) if b > a else (-1, (b, a))
    n = 0
    while x < y:
        x += timedelta(days=1)
        if x.weekday() < 5:
            n += 1
    return sign * n


def next_inquiry_number(db: Session, year: int | None = None) -> str:
    prefix = f"AF{(year or date.today().year) % 100:02d}-"
    nums = db.scalars(select(Opportunity.number).where(Opportunity.number.like(f"{prefix}%"))).all()
    n = max((int(x[len(prefix):]) for x in nums if x and x[len(prefix):].isdigit()), default=0) + 1
    return f"{prefix}{n:04d}"


def calcs_of(db: Session, opp_id: int) -> list[Calculation]:
    return db.scalars(select(Calculation).where(Calculation.opportunity_id == opp_id).order_by(Calculation.id)).unique().all()


def quote_of(db: Session, opp_id: int) -> Quote | None:
    """Das aktuelle Angebot der Anfrage (neueste nicht ersetzte Fassung)."""
    return db.scalars(select(Quote).where(Quote.opportunity_id == opp_id, Quote.status != "ersetzt")
                      .order_by(Quote.id.desc()).limit(1)).first()


def followup_light(due: datetime | None, done: bool = False) -> str | None:
    """Ampel der Angebotsverfolgung: grün > 1 Arbeitstag Luft, gelb heute/morgen fällig, rot überfällig."""
    if done or not due:
        return None
    d = due.date() if isinstance(due, datetime) else due
    left = workdays_between(date.today(), d)
    return "rot" if d < date.today() else ("gelb" if left <= 1 else "gruen")


# ------------------------------------------------------------------ Phase / Summen
def refresh_inquiry(db: Session, opp: Opportunity):
    """Summen, Wahrscheinlichkeit und Phase der Anfrage aus ihren Artikeln ableiten (nur vorwärts / Abschluss)."""
    calcs = calcs_of(db, opp.id)
    if not calcs:
        return
    if opp.kind != "anfrage":
        opp.kind = "anfrage"
    live = [c for c in calcs if c.status not in ("verloren", "kein_angebot")]
    opp.amount = round(sum(c.annual_revenue + c.one_time_revenue for c in (live or calcs)), 2)
    opp.tech_talk = any((c.analysis or {}).get("tech_talk") for c in calcs)
    if all(c.status in CALC_CLOSED for c in calcs):
        if any(c.status == "gewonnen" for c in calcs):
            new = "gewonnen"
        elif all(c.status == "kein_angebot" for c in calcs):
            new = "nicht_angeboten"
            opp.lost_reason = "Nicht angeboten: " + "; ".join(
                sorted({(c.decision_note or c.no_bid_note or c.no_bid_reason or "ohne Grund") for c in calcs}))[:250]
        elif all(c.status == "zurueckgestellt" for c in calcs):
            new = opp.stage
        else:
            from .routers.calc import REASON_LABELS  # noqa: PLC0415
            new = "verloren"
            lost = [c for c in calcs if c.status == "verloren"]
            if lost and not opp.lost_reason:
                c = lost[0]
                opp.lost_code = c.close_reason
                opp.lost_reason = (REASON_LABELS.get(c.close_reason) or "Verloren") + (f": {c.close_note}" if c.close_note else "")
        set_stage(opp, new)
    else:
        target = opp.stage
        if opp.stage in CLOSED_STAGES:          # Artikel wieder geöffnet → Anfrage wieder offen
            target = "qualifiziert"
        if any(c.decision in RELEASED for c in calcs):
            target = max(target, "qualifiziert", key=lambda s: STAGE_ORDER.get(s, 0))
        else:
            target = max(target, "neue_anfrage", key=lambda s: STAGE_ORDER.get(s, 0)) if target == "lead" else target
        q = quote_of(db, opp.id)
        if q and q.status in ("versendet", "angenommen", "abgelehnt"):
            target = max(target, "angebot", key=lambda s: STAGE_ORDER.get(s, 0))
        if target != opp.stage:
            set_stage(opp, target)
    # Wahrscheinlichkeit des ganzen Auftrags gilt für alle offenen Artikel (Auslastung „erwartet“)
    for c in calcs:
        if c.status not in CALC_CLOSED:
            c.probability = opp.probability


def set_stage(opp: Opportunity, stage: str, keep_probability: bool = False):
    if stage == opp.stage:
        return
    opp.stage = stage
    if not keep_probability:
        opp.probability = STAGE_PROBABILITY[stage]
    if stage == "verhandlung":
        opp.final_round = True
    opp.closed_at = date.today() if stage in CLOSED_STAGES else None
    if stage not in ("verloren", "nicht_angeboten"):
        opp.lost_reason, opp.lost_code = None, None


def cascade_stage(db: Session, opp: Opportunity, old_stage: str | None):
    """Pipeline-Karte von Hand verschoben → offene Artikel nachziehen (Gewonnen, Verloren, Nicht angeboten)."""
    if opp.stage == old_stage:
        return
    if opp.stage == "verhandlung":
        opp.final_round = True
    for c in calcs_of(db, opp.id):
        if c.status in ("verloren", "kein_angebot", "gewonnen"):
            continue
        if opp.stage == "gewonnen":
            c.status, c.probability = "gewonnen", 100
        elif opp.stage == "verloren":
            c.status, c.probability = "verloren", 0
            c.close_reason = opp.lost_code or "sonstiges"
            c.close_note = c.close_note or (opp.lost_reason or "").split(": ", 1)[-1]
        elif opp.stage == "nicht_angeboten":
            c.status, c.probability = "kein_angebot", 0
            c.decision = c.decision or "nicht_anbieten"
            c.no_bid_reason = c.no_bid_reason or opp.lost_code or "sonstiges"
            c.no_bid_note = c.no_bid_note or opp.lost_reason
        elif opp.stage == "verhandlung" and c.status == "angeboten":
            c.status = "verhandlung"


# ------------------------------------------------------------------ Entscheidung
def decide(db: Session, calc: Calculation, decision: str, note: str | None, user, site_id: int | None = None,
           no_bid_reason: str | None = None):
    """Entscheidung je Artikel vor Kalkulationsstart (REV01-P02)."""
    if decision not in DECISIONS:
        raise HTTPException(400, "Unbekannte Entscheidung")
    if decision in ("nicht_anbieten", "sonstiges") and not (note or "").strip() and not no_bid_reason:
        raise HTTPException(400, "Bitte Begründung angeben")
    if decision == "anderer_standort" and not site_id:
        raise HTTPException(400, "Bitte den Standort wählen, der anbietet")
    calc.decision, calc.decision_note = decision, (note or "").strip() or None
    calc.decision_by_id, calc.decision_at = user.id, datetime.now(timezone.utc)
    if decision == "nicht_anbieten":
        calc.status, calc.probability = "kein_angebot", 0
        calc.no_bid_reason = no_bid_reason or "sonstiges"
        calc.no_bid_note = calc.decision_note
    else:
        if calc.status == "kein_angebot":
            calc.status, calc.no_bid_reason, calc.no_bid_note = "anfrage", None, None
        if decision == "anderer_standort" and site_id and calc.site_id != site_id:
            _move_site(db, calc, site_id, user)


def _move_site(db: Session, calc: Calculation, site_id: int, user):
    """Artikel an anderen Standort geben: neue Version mit den Sätzen des Standorts."""
    from .calc_engine import compute, normalize  # noqa: PLC0415
    from .models import CalculationVersion, Site  # noqa: PLC0415
    from .routers.calc import apply_results, site_inputs  # noqa: PLC0415
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(404, "Standort nicht gefunden")
    ver = next((v for v in calc.versions if v.version_no == calc.current_version), None)
    if not ver:
        return
    inp, _notes = site_inputs(db, dict(ver.inputs), site, ver.inputs.get("site_id") or calc.site_id)
    inp["site_id"] = site_id
    inp = normalize(inp)
    res = compute(inp)
    no = calc.versions[-1].version_no + 1
    calc.versions.append(CalculationVersion(version_no=no, inputs=inp, results=res, created_by_id=user.id,
                                            change_note=f"Entscheidung: angeboten von Standort {site.name}"))
    calc.current_version = no
    apply_results(calc, res, inp)


def require_decision(db: Session, calc: Calculation):
    """Kalkulieren erst nach Entscheidung (REV01-P02). Altdaten ohne Anfrage-Bezug bleiben bearbeitbar."""
    if calc.decision is None and calc.opportunity_id:
        raise HTTPException(409, "Für diesen Artikel fehlt noch die Entscheidung (anbieten / nicht anbieten / anderer "
                                 "Standort / Sonstiges) – bitte zuerst in der Anfrage oder oben in der Kalkulation entscheiden.")
    if calc.decision == "nicht_anbieten":
        raise HTTPException(409, "Artikel ist als „nicht angeboten“ entschieden – zum Kalkulieren Entscheidung ändern.")


# ------------------------------------------------------------------ Angebotsverfolgung
def start_followup(db: Session, quote: Quote, user, days: int):
    """Angebot versendet → Aufgabe „Angebotsverfolgung“ in n Arbeitstagen (REV01-P06)."""
    quote.sent_at = quote.sent_at or date.today()
    opp = db.get(Opportunity, quote.opportunity_id) if quote.opportunity_id else None
    if opp and not opp.offered_at:
        opp.offered_at = date.today()
    open_task = db.scalars(select(Activity).where(Activity.quote_id == quote.id, Activity.kind == "angebotsverfolgung",
                                                  Activity.done.is_(False))).first()
    if open_task:
        return open_task
    due = add_workdays(quote.sent_at, days)
    task = Activity(type="anruf", kind="angebotsverfolgung", attempts=0,
                    subject=f"Angebotsverfolgung {quote.number} – Rücksprache Kunde",
                    description=f"Rückmeldung zum Angebot {quote.number} „{quote.title}“ einholen "
                                f"(spätestens {days} Arbeitstage nach Versand).",
                    due_at=datetime.combine(due, time(9, 0), tzinfo=timezone.utc),
                    account_id=quote.account_id, contact_id=quote.contact_id, opportunity_id=quote.opportunity_id,
                    quote_id=quote.id, owner_id=quote.owner_id or (user.id if user else None))
    db.add(task)
    return task


def followup_result(db: Session, task: Activity, result: str, note: str | None, next_date: date | None, user):
    """Ergebnis der Rücksprache: erreicht · niemanden erreicht (→ nächster Arbeitstag) · wieder melden am …"""
    if result not in ("erreicht", "nicht_erreicht", "wieder_melden"):
        raise HTTPException(400, "Unbekanntes Ergebnis")
    if result == "wieder_melden" and not next_date:
        raise HTTPException(400, "Bitte Datum für „wieder melden am“ angeben")
    today = date.today()
    label = {"erreicht": "Kunde erreicht", "nicht_erreicht": "Niemanden erreicht",
             "wieder_melden": f"Kunde meldet sich wieder / Wiedervorlage {next_date:%d.%m.%Y}" if next_date else ""}[result]
    # Gesprächsnotiz als erledigte Aktivität (Historie)
    db.add(Activity(type="anruf", done=True, subject=f"{label} – {task.subject.split(' – ')[0]}",
                    description=note, due_at=datetime.now(timezone.utc), account_id=task.account_id,
                    contact_id=task.contact_id, opportunity_id=task.opportunity_id, quote_id=task.quote_id,
                    owner_id=user.id, kind="rueckmeldung", result=result))
    if task.quote_id:
        q = db.get(Quote, task.quote_id)
        if q:
            q.last_contact_at = datetime.now(timezone.utc)
            q.last_contact_note = f"{label}" + (f": {note}" if note else "")
    task.result = result
    if result == "nicht_erreicht":
        task.attempts = (task.attempts or 0) + 1
        nd = next_date or next_workday(today)
        task.due_at = datetime.combine(nd, time(9, 0), tzinfo=timezone.utc)
    elif result == "wieder_melden":
        task.due_at = datetime.combine(next_date, time(9, 0), tzinfo=timezone.utc)
    else:
        task.done = True
        if next_date:  # erreicht, aber weitere Wiedervorlage gewünscht
            db.add(Activity(type="anruf", kind="angebotsverfolgung", attempts=0, subject=task.subject,
                            description=task.description, due_at=datetime.combine(next_date, time(9, 0), tzinfo=timezone.utc),
                            account_id=task.account_id, contact_id=task.contact_id, opportunity_id=task.opportunity_id,
                            quote_id=task.quote_id, owner_id=task.owner_id))
    return task


def ensure_tech_talk_task(db: Session, opp: Opportunity, user):
    """„Technisches Gespräch erforderlich“ in der Artikelanalyse → Aufgabe anlegen (einmalig je Anfrage)."""
    if not opp or not opp.tech_talk:
        return
    exists = db.scalars(select(Activity).where(Activity.opportunity_id == opp.id, Activity.kind == "technisches_gespraech")).first()
    if exists:
        return
    db.add(Activity(type="termin", kind="technisches_gespraech", subject=f"Technisches Gespräch vereinbaren – {opp.number or opp.name}",
                    description="Laut Artikelanalyse ist vor dem Angebot ein technisches Gespräch mit dem Kunden erforderlich.",
                    due_at=datetime.combine(add_workdays(date.today(), 2), time(9, 0), tzinfo=timezone.utc),
                    account_id=opp.account_id, contact_id=opp.contact_id, opportunity_id=opp.id,
                    owner_id=opp.owner_id or (user.id if user else None)))


# ------------------------------------------------------------------ Übernahme Altdaten (einmalig)
def migrate(db: Session) -> dict:
    """Bestehende Kalkulationen in Anfragen überführen – gruppiert nach Angebot (Entscheidung REV01 Phase 2)."""
    stats = {"numbered": 0, "created": 0, "linked": 0}
    for o in db.scalars(select(Opportunity).where(Opportunity.number.is_(None)).order_by(Opportunity.id)).all():
        o.number = next_inquiry_number(db, (o.created_at or datetime.now()).year)
        db.flush()
        stats["numbered"] += 1
    calcs = db.scalars(select(Calculation).order_by(Calculation.id)).unique().all()
    by_id = {c.id: c for c in calcs}

    def new_opp(c: Calculation, name: str) -> Opportunity:
        o = Opportunity(name=name, account_id=c.account_id, contact_id=c.contact_id, owner_id=c.owner_id,
                        stage="neue_anfrage", probability=STAGE_PROBABILITY["neue_anfrage"], kind="anfrage",
                        inquiry_date=c.inquiry_date, due_date=c.due_date, close_date=c.due_date, source="Kalkulation",
                        number=next_inquiry_number(db, (c.created_at or datetime.now()).year))
        db.add(o)
        db.flush()
        stats["created"] += 1
        return o

    # 1) je bestehendem Angebot eine Anfrage
    for q in db.scalars(select(Quote).where(Quote.calculation_ids.isnot(None)).order_by(Quote.id)).all():
        members = [by_id[i] for i in (q.calculation_ids or []) if i in by_id]
        if not members:
            continue
        opp_id = q.opportunity_id or next((c.opportunity_id for c in members if c.opportunity_id), None)
        if not opp_id:
            opp_id = new_opp(members[0], q.title or members[0].article_name).id
        for c in members:
            if not c.opportunity_id:
                c.opportunity_id = opp_id
                stats["linked"] += 1
        q.opportunity_id = q.opportunity_id or opp_id
    # 2) übrige Kalkulationen je eine Anfrage
    for c in calcs:
        if not c.opportunity_id:
            c.opportunity_id = new_opp(c, c.article_name).id
            stats["linked"] += 1
    db.flush()
    # 3) Entscheidung aus dem bisherigen Stand ableiten, Phase und Summen neu
    for c in calcs:
        c.sync_opportunity = True
        if c.decision is None:
            if c.status == "kein_angebot":
                c.decision, c.decision_note = "nicht_anbieten", c.no_bid_note or "übernommen aus Altdaten"
            elif c.status != "anfrage" or c.current_version > 1:
                c.decision, c.decision_note = "anbieten", "übernommen aus Altdaten"
    db.flush()
    for o in db.scalars(select(Opportunity)).all():
        has = any(c.opportunity_id == o.id for c in calcs)
        o.kind = "anfrage" if has else ("lead" if o.stage == "lead" else "anfrage")
        if o.stage == "lead" and has:
            o.stage = "neue_anfrage"
        if has:
            refresh_inquiry(db, o)
            q = quote_of(db, o.id)
            if q and q.status == "versendet" and not q.sent_at:
                q.sent_at = q.quote_date
            if q and q.status != "entwurf" and not o.offered_at:
                o.offered_at = q.quote_date
    # bereits versendete Angebote: Angebotsverfolgung nachträglich starten (Frist ab Angebotsdatum)
    from .calc_engine import DEFAULT_SETTINGS  # noqa: PLC0415
    from .models import CalcSettings  # noqa: PLC0415
    row = db.get(CalcSettings, 1)
    days = int(({**DEFAULT_SETTINGS, **((row.data or {}) if row else {})}).get("followup_workdays") or 5)
    for q in db.scalars(select(Quote).where(Quote.status == "versendet")).all():
        q.sent_at = q.sent_at or q.quote_date
        start_followup(db, q, None, days)
    db.commit()
    return stats
