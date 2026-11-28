"""REV04-01 Softwarestand: Version dieses Programmstands und die Auslieferungen (wie Lastenheft Kap. 13.0)."""
APP_VERSION = "1.34"

RELEASES = [
    ("1.34", "28.11.2026", "Zusatzblätter: Werkzeugblatt, Risikoanalyse, neue Anlagen, Kickoff bei Auftrag"),
    ("1.33", "28.11.2026", "Kalkulation rechnen: Mengen je Lieferjahr, Losgröße, Staffelpreise Material/Zukaufteile, Varianten; Prüfbericht"),
    ("1.32", "27.11.2026", "Prüfseite je Update, Softwarestand, Vertriebsziel auf der Startseite, Pipeline mit allen Phasen (REV04)"),
    ("1.31", "25.11.2026", "Korrekturen Testrunde 3 (REV03-01 … 09)"),
    ("1.30.1", "25.11.2026", "Hotfix: Fehler 500 in Pipeline und Anfragen (REV03-01)"),
    ("1.30", "24.11.2026", "Preisliste, Monatsbericht mit Vertriebsziel, Teilbeauftragung, Korrekturen Phase 2 (REV02)"),
    ("1.24", "19.11.2026", "REV01 Phase 2: Anfrage → Angebot → Pipeline"),
    ("1.23", "17.11.2026", "REV01 Phase 1"),
]


def remember_install(db) -> None:
    """Merkt sich beim ersten Start einer Version den Zeitpunkt (= eingespielt am). Ein Neustart ändert ihn nicht."""
    from datetime import datetime, timezone  # noqa: PLC0415
    from .models import CalcSettings  # noqa: PLC0415
    cs = db.get(CalcSettings, 1)
    if cs is None:
        return
    inst = dict((cs.data or {}).get("_installed") or {})
    if APP_VERSION not in inst:
        inst[APP_VERSION] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cs.data = {**(cs.data or {}), "_installed": inst}
        db.commit()


def version_info(db) -> dict:
    from .models import CalcSettings  # noqa: PLC0415
    cs = db.get(CalcSettings, 1)
    inst = ((cs.data or {}).get("_installed") or {}) if cs else {}
    return {"version": APP_VERSION, "installed_at": inst.get(APP_VERSION),
            "releases": [{"version": v, "date": d, "content": c, "installed_at": inst.get(v)} for v, d, c in RELEASES]}
