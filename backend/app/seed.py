"""Demo-Daten anlegen:  python -m app.seed   (nur wenn noch keine Firmen existieren)"""
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select

from .auth import hash_password
from .database import SessionLocal
from .main import init_db
from .models import STAGE_PROBABILITY, Account, Activity, Contact, Opportunity, Quote, QuoteItem, User

random.seed(42)


def slug(t: str) -> str:
    t = t.split()[0].lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("á", "a"), ("&", "")):
        t = t.replace(a, b)
    return t

USERS = [
    ("anna.berg@firma.de", "Anna Berg", "vertrieb"),
    ("tim.kraus@firma.de", "Tim Kraus", "vertrieb"),
    ("lea.wolf@firma.de", "Lea Wolf", "vertrieb"),
    ("gesellschafter@firma.de", "Gesellschafter-Ansicht", "gesellschafter"),
]
ACCOUNTS = [
    ("Nordtech Automotive GmbH", "Automotive", "Bielefeld", "kunde"),
    ("Elektra Komponenten AG", "Elektronik", "Paderborn", "kunde"),
    ("Haushaltswaren Lippe KG", "Konsumgüter", "Detmold", "kunde"),
    ("Pack & Form GmbH", "Verpackung", "Hannover", "interessent"),
    ("Sensorik Weser GmbH", "Elektronik", "Hameln", "interessent"),
    ("Mobil Interior Systems", "Automotive", "Wolfsburg", "kunde"),
    ("MediPlast Solutions", "Medizintechnik", "Göttingen", "interessent"),
    ("Gartenwelt Produkte GmbH", "Konsumgüter", "Gütersloh", "interessent"),
    ("Bohemia Trade s.r.o.", "Handel", "Teplice", "partner"),
    ("Kühl & Klima Technik", "Haustechnik", "Kassel", "kunde"),
]
FIRST = ["Jonas", "Maria", "Stefan", "Julia", "Andreas", "Katrin", "Michael", "Sabine", "Petr", "Laura"]
LAST = ["Meyer", "Schulz", "Hoffmann", "Becker", "Novák", "Richter", "Klein", "Wagner", "Krüger", "Lange"]
FEMALE = {"Maria", "Julia", "Katrin", "Sabine", "Laura"}
POS = ["Einkaufsleiter", "Technischer Einkauf", "Geschäftsführer", "Projektleiter", "Qualitätsmanagement"]
DEALS = ["Spritzgussteile Serie", "Gehäuse 2K-Bauteil", "Werkzeugbau + Serie", "Rahmenvertrag 2027",
         "Clip-Halter Nachfolger", "Abdeckkappen Großserie", "Prototypen-Musterung", "Blende Innenraum"]


def run():
    init_db()
    db = SessionLocal()
    if db.scalar(select(func.count()).select_from(Account)):
        print("Es existieren bereits CRM-Daten – Basis-Seed übersprungen.")
        seed_calc(db)
        seed_calls(db)
        return
    users = []
    for email, name, role in USERS:
        u = User(email=email, name=name, role=role, password_hash=hash_password("demo1234"))
        db.add(u)
        users.append(u)
    db.flush()
    sales = [u for u in users if u.role == "vertrieb"]
    today = date.today()
    nowt = datetime.now(timezone.utc)

    for idx, (name, industry, city, typ) in enumerate(ACCOUNTS):
        owner = random.choice(sales)
        acc = Account(name=name, industry=industry, city=city, type=typ, owner_id=owner.id,
                      country="Tschechien" if city == "Teplice" else "Deutschland",
                      phone=f"+49 5{random.randint(100, 999)} {random.randint(10000, 99999)}",
                      website=f"www.{slug(name)}.example")
        db.add(acc)
        db.flush()
        contacts = []
        for _ in range(random.randint(1, 3)):
            fn, ln = random.choice(FIRST), random.choice(LAST)
            c = Contact(account_id=acc.id, salutation="Frau" if fn in FEMALE else "Herr", first_name=fn, last_name=ln, position=random.choice(POS),
                        email=f"{slug(fn)}.{slug(ln)}@{acc.website[4:]}", owner_id=owner.id,
                        phone=acc.phone)
            db.add(c)
            contacts.append(c)
        db.flush()
        for _ in range(random.randint(1, 3)):
            stage = random.choices(list(STAGE_PROBABILITY), weights=[3, 3, 3, 2, 3, 1])[0]
            amount = random.choice([8, 12, 18, 25, 40, 65, 90, 120, 180]) * 1000
            closed = today - timedelta(days=random.randint(5, 300)) if stage in ("gewonnen", "verloren") else None
            o = Opportunity(name=f"{random.choice(DEALS)} – {name.split()[0]}", account_id=acc.id,
                            contact_id=contacts[0].id, stage=stage, amount=amount,
                            probability=STAGE_PROBABILITY[stage], owner_id=owner.id,
                            close_date=closed or today + timedelta(days=random.randint(-5, 120)),
                            closed_at=closed, source=random.choice(["Messe", "Bestandskunde", "Website", "Empfehlung"]))
            db.add(o)
            db.flush()
            if stage in ("angebot", "verhandlung", "gewonnen"):
                qt = Quote(number=f"AN-{today.year}-{o.id:04d}", title=o.name, account_id=acc.id,
                           contact_id=contacts[0].id, opportunity_id=o.id, owner_id=owner.id,
                           status={"angebot": "versendet", "verhandlung": "versendet", "gewonnen": "angenommen"}[stage],
                           quote_date=today - timedelta(days=random.randint(1, 40)),
                           valid_until=today + timedelta(days=20), tax_rate=19)
                qty = random.choice([5000, 10000, 25000])
                qt.items = [
                    QuoteItem(position=1, description="Spritzgießwerkzeug inkl. Bemusterung", quantity=1,
                              unit="Stk", unit_price=round(amount * 0.3, 2)),
                    QuoteItem(position=2, description="Serienteile PA6 GF30", quantity=qty, unit="Stk",
                              unit_price=round(amount * 0.7 / qty, 4)),
                ]
                db.add(qt)
        for _ in range(random.randint(1, 3)):
            typ_a = random.choice(["anruf", "termin", "email", "aufgabe"])
            due = nowt + timedelta(days=random.randint(-6, 14), hours=random.randint(0, 8))
            db.add(Activity(type=typ_a, subject={"anruf": "Rückruf wegen Mengenplanung",
                                                 "termin": "Vor-Ort-Termin Werkzeugabnahme",
                                                 "email": "Muster und Datenblatt senden",
                                                 "aufgabe": "Angebot nachfassen"}[typ_a],
                            due_at=due, done=due < nowt and random.random() < 0.5, account_id=acc.id,
                            contact_id=random.choice(contacts).id, owner_id=owner.id))
    db.commit()
    seed_calc(db)
    seed_calls(db)
    print("Demo-Daten angelegt. Logins: anna.berg@firma.de / demo1234, gesellschafter@firma.de / demo1234")


MACHINE_HOURS = {"M01": 6000, "M02": 6000, "M03": 5500, "M04": 6000, "M05": 4800, "M06": 4800}
MACHINE_BASE = {"M01": (62, 8), "M02": (74, 10), "M03": (55, 5), "M04": (68, 12), "M05": (41, 15), "M06": (36, 20)}
MACHINES = [  # Nr, Name, t, €/h, IH €/h, Prod %, Bedienfaktor
    ("M01", "Spritzgießmaschine 50 t", 50, 32, 3, 88, 0.25),
    ("M02", "Spritzgießmaschine 110 t", 110, 41, 4, 86, 0.3),
    ("M03", "Spritzgießmaschine 160 t 2K", 160, 58, 6, 82, 0.5),
    ("M04", "Spritzgießmaschine 250 t", 250, 66, 7, 85, 0.3),
    ("M05", "Spritzgießmaschine 420 t", 420, 89, 9, 84, 0.5),
    ("M06", "Spritzgießmaschine 650 t", 650, 118, 12, 83, 0.5),
]
MATERIALS = [  # Name, Familie, €/kg, Dichte
    ("PP Homopolymer natur", "PP", 1.65, 0.91), ("PP T20 schwarz", "PP", 2.10, 1.05),
    ("ABS schwarz", "ABS", 2.90, 1.05), ("PC/ABS schwarz", "PC/ABS", 3.80, 1.15),
    ("PA6 GF30 schwarz", "PA6", 3.40, 1.36), ("PA66 GF30 schwarz", "PA66", 4.20, 1.37),
    ("POM natur", "POM", 2.95, 1.41), ("PBT GF30 schwarz", "PBT", 3.70, 1.53), ("TPE 60 Shore A", "TPE", 4.90, 1.10),
]


def seed_calc(db):
    from .calc_engine import compute, normalize, post_calculate
    from .models import Calculation, CalculationVersion, Machine, Material, PostCalculation
    from .routers.calc import STATUS_PROBABILITY, default_inputs, get_settings, sync_opportunity

    if db.scalar(select(func.count()).select_from(Machine)):
        print("Kalkulations-Stammdaten existieren bereits – übersprungen.")
        return
    machines = [Machine(number=n, name=nm, clamping_force_t=t, hourly_rate=r, maintenance_rate=ih,
                        productivity_pct=p, operator_factor=bf, location="Werk 1", available_hours_year=MACHINE_HOURS.get(n, 6000),
                        base_load_pct=MACHINE_BASE[n][0], base_load_decline_pct=MACHINE_BASE[n][1])
                for n, nm, t, r, ih, p, bf in MACHINES]
    materials = [Material(name=nm, family=fam, price_per_kg=pr, density=d, supplier="Rahmenvertrag")
                 for nm, fam, pr, d in MATERIALS]
    db.add_all(machines + materials)
    db.flush()
    st = get_settings(db)
    accounts = db.scalars(select(Account).order_by(Account.id)).unique().all()
    users = db.scalars(select(User).where(User.role == "vertrieb")).all() or db.scalars(select(User)).all()
    nowt = datetime.now(timezone.utc)
    examples = [  # Artikel, Kd-Nr, Status, Grund, Maschine, Material, g, Anguss, Zyklus, Fach, Menge, Los, Werkzeug
        ("Abdeckkappe Steuergerät", "4711-220", "angeboten", None, 1, 4, 18, 3, 28, 4, 250000, 25000, 38000),
        ("Clip-Halter Kabelbaum", "KB-1180", "verhandlung", None, 0, 6, 2.4, 0, 14, 16, 1200000, 100000, 52000),
        ("Gehäuse Sensor 2K", "SN-778-01", "kalkulation", None, 2, 3, 46, 8, 42, 2, 80000, 8000, 96000),
        ("Blende Innenraum links", "7L0-858-415", "gewonnen", None, 4, 1, 310, 0, 55, 1, 60000, 5000, 145000),
        ("Griffschale Haushalt", "HH-2201", "verloren", "artikelpreis_zu_hoch", 1, 2, 64, 6, 35, 2, 150000, 15000, 42000),
        ("Lüftergitter", "LG-500", "verloren", "werkzeug_zu_teuer", 3, 7, 120, 12, 40, 1, 40000, 4000, 88000),
        ("Trägerplatte Batterie", "BT-9001", "verloren", "projekt_kunde_nicht_gewonnen", 5, 5, 780, 0, 75, 1, 30000, 3000, 210000),
        ("Frontend-Modulträger", "FM-2027-01", "verhandlung", None, 5, 1, 1450, 0, 68, 1, 180000, 6000, 640000),
        ("Gehäuseschale Wallbox", "WB-330", "angeboten", None, 4, 3, 520, 25, 52, 1, 220000, 10000, 185000),
        ("Halter Steuergerät", "4711-221", "kalkulation", None, 1, 4, 26, 4, 30, 2, 250000, 25000, 34000),
        ("Deckel Sicherungskasten", "4711-305", "kalkulation", None, 3, 3, 88, 9, 38, 2, 120000, 12000, 61000),
        ("Distanzscheibe M4", "DS-04", "kein_angebot", "mengen_zu_klein", 0, 0, 0.3, 0, 12, 32, 5000, 5000, 9000),
        ("Kühlergrill-Träger", "KG-900", "kein_angebot", "keine_maschine_kapazitaet", 5, 1, 2400, 0, 90, 1, 50000, 5000, 380000),
        ("Verpackungseinsatz", "PK-17", "verloren", "projekt_eingestellt", 3, 0, 95, 10, 30, 2, 200000, 20000, 35000),
        ("Dichtungsrahmen TPE", "DR-303", "anfrage", None, 1, 8, 12, 2, 32, 4, 90000, 10000, 30000),
    ]
    for idx, (art, kd, status, reason, mi, mati, g, spr, cyc, cav, vol, lot, tool) in enumerate(examples):
        acc = accounts[idx % len(accounts)] if accounts else None
        if accounts and art in ("Halter Steuergerät", "Deckel Sicherungskasten"):
            acc = accounts[0]  # mehrere Artikel desselben Kunden (Sammelangebot)
        m, mat = machines[mi], materials[mati]
        inp = default_inputs(db)
        inp.update(material_id=mat.id, material_name=mat.name, material_price_kg=mat.price_per_kg,
                   part_weight_g=g, sprue_weight_g=spr, machine_id=m.id, machine_name=m.name,
                   machine_rate_h=m.hourly_rate, maintenance_rate_h=m.maintenance_rate,
                   productivity_pct=m.productivity_pct, operator_factor=m.operator_factor,
                   cycle_time_s=cyc, cavities=cav, annual_volume=vol, lot_size=lot,
                   one_time=[{"label": "Spritzgießwerkzeug", "cost": tool, "price": tool},
                             {"label": "Erstbemusterung / EMPB", "cost": 1800, "price": 1800}],
                   extras=[{"label": "Verpackung KLT", "amount": round(max(2.0, g * 0.12), 2), "basis": "tausend", "category": "vertrieb"}])
        if art in ("Abdeckkappe Steuergerät", "Frontend-Modulträger", "Clip-Halter Kabelbaum"):
            inp["lot_tiers"] = [round(lot / 2), lot, lot * 3]
        if art.startswith("Frontend"):
            inp["project_years"] = 6
        if art.startswith("Gehäuse Sensor"):
            inp["assembly_time_s"] = 6
            inp["purchased_parts"] = 0.12
            inp["extras"].append({"label": "Bedrucken Tampondruck", "amount": 0.035, "basis": "stueck", "category": "fertigung"})
        inp = normalize(inp)
        owner = users[idx % len(users)]
        calc = Calculation(number=f"KA-{date.today().year}-{idx + 1:04d}", article_name=art, customer_article_no=kd,
                           own_article_no=f"FR-{30100 + idx}", account_id=acc.id if acc else None,
                           contact_id=acc.contacts[0].id if acc and acc.contacts else None,
                           status=status, probability=STATUS_PROBABILITY[status],
                           close_reason=reason if status == "verloren" else None,
                           no_bid_reason=reason if status == "kein_angebot" else None,
                           no_bid_note={"keine_maschine_kapazitaet": "Benötigt ca. 1.300 t, größte Maschine 650 t."}.get(reason),
                           feasibility={"anfrage": None, "kalkulation": "bedingt_herstellbar", "kein_angebot":
                                        ("nicht_herstellbar" if reason == "keine_maschine_kapazitaet" else "herstellbar")}.get(status, "herstellbar"),
                           sop_date=(date(date.today().year + 1, 1 + (idx * 2) % 12, 1) if status != "gewonnen"
                                     else date.today() - timedelta(days=60)),
                           owner_id=owner.id, inquiry_date=date.today() - timedelta(days=90 - idx * 8),
                           due_date=date.today() + timedelta(days=10 + idx * 3),
                           last_call_at=nowt - timedelta(days=3 + idx * 4),
                           remark={"verloren": "Wettbewerber aus Osteuropa günstiger."}.get(status))
        res1 = compute(inp)
        calc.versions.append(CalculationVersion(version_no=1, inputs=inp, results=res1, created_by_id=owner.id,
                                                change_note="Erstkalkulation"))
        final = (inp, res1)
        if status in ("verhandlung", "gewonnen", "angeboten"):
            inp2 = normalize({**inp, "cycle_time_s": cyc * 0.92, "profit_pct": 5.5})
            res2 = compute(inp2)
            calc.versions.append(CalculationVersion(version_no=2, inputs=inp2, results=res2, created_by_id=owner.id,
                                                    change_note="Zykluszeit nach Simulation reduziert, Gewinn auf 5,5 % (Kundengespräch)"))
            final = (inp2, res2)
        calc.current_version = len(calc.versions)
        r = final[1]
        calc.unit_price, calc.annual_volume, calc.annual_revenue = r["unit_price"], r["annual_volume"], r["annual_revenue"]
        calc.one_time_revenue, calc.margin_pct = r["one_time_price"], r["margin_pct"]
        db.add(calc)
        db.flush()
        if status == "gewonnen":
            for ref, actual in (("Auftrag 2026-0412 (Okt.)", {"cycle_time_s": cyc * 0.95, "scrap_pct": 2.5, "quantity": 5000}),
                                ("Auftrag 2026-0466 (Nov.)", {"cycle_time_s": cyc * 1.08, "scrap_pct": 6, "productivity_pct": 78,
                                                              "material_price_kg": 1.95, "quantity": 5000, "extra_costs": 600})):
                pres, light = post_calculate(final[0], r, actual, st)
                calc.post_calcs.append(PostCalculation(version_no=calc.current_version, reference=ref, actuals=actual,
                                                       results=pres, traffic_light=light, created_by_id=owner.id))
    db.commit()
    # Großprojekte mit Verkaufschance und Angebot verknüpfen (zeigt Hervorhebung in Pipeline/Angeboten)
    from .routers.calc import create_opportunity, create_quote
    for calc in db.scalars(select(Calculation).where(Calculation.article_name.in_(
            ["Frontend-Modulträger", "Gehäuseschale Wallbox"]))).unique().all():
        owner = db.get(User, calc.owner_id)
        create_opportunity(calc.id, db=db, user=owner)
        create_quote(calc.id, version_no=None, db=db, user=owner)
    print("Kalkulations-Stammdaten und Beispielkalkulationen angelegt.")


CALL_SCRIPT = {
    "anfrage": [("rueckruf_vereinbart", "Zeichnung und Stückzahlen angefragt, Rückruf nächste Woche.")],
    "kalkulation": [("neu_kalkulieren", "Kunde ändert Wandstärke auf 1,8 mm – Gewicht neu bewerten."),
                    ("rueckruf_vereinbart", "Neue Zeichnung kommt bis Freitag.")],
    "angeboten": [("nicht_erreicht", None), ("kunde_entscheidet_noch", "Vergleich mit 2 Wettbewerbern, Entscheidung Ende des Monats.")],
    "verhandlung": [("preis_nachverhandeln", "Zielpreis 27 €/1.000 – Zykluszeit prüfen."),
                    ("auftrag_in_aussicht", "Mit neuer Zykluszeit im Rahmen, Freigabe Einkauf steht aus.")],
    "gewonnen": [("auftrag_in_aussicht", "Technische Freigabe erteilt."), ("auftrag_erhalten", "Bestellung Werkzeug und Rahmenvertrag erhalten.")],
    "verloren": [("kunde_entscheidet_noch", "Angebot liegt vor, Rückmeldung offen."), ("absage", "Absage – Wettbewerber günstiger.")],
}


def seed_calls(db):
    from .models import Calculation, CalculationCall
    if db.scalar(select(func.count()).select_from(CalculationCall)):
        return
    for calc in db.scalars(select(Calculation)).unique().all():
        script = CALL_SCRIPT.get(calc.status, [])
        last = calc.last_call_at or datetime.now(timezone.utc) - timedelta(days=5)
        for n, (res, note) in enumerate(reversed(script)):
            calc.calls.append(CalculationCall(called_at=last - timedelta(days=9 * n), result=res, note=note,
                                              contact_id=calc.contact_id, user_id=calc.owner_id))
        if script:
            calc.last_call_at = last
    db.commit()
    print("Demo-Anrufe angelegt.")


if __name__ == "__main__":
    run()
