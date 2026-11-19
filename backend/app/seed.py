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
        seed_procurement(db)
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
            stage = random.choices(list(STAGE_PROBABILITY), weights=[3, 0, 3, 3, 2, 3, 1, 0])[0]
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
                qt = Quote(number=f"A{today:%y}-{o.id:04d}", title=o.name, account_id=acc.id,
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
    seed_procurement(db)
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
MATERIALS = [  # Name, Familie, €/kg, Dichte, kg CO₂e/kg (Richtwert)
    ("PP Homopolymer natur", "PP", 1.65, 0.91, 1.7), ("PP T20 schwarz", "PP", 2.10, 1.05, 1.9),
    ("ABS schwarz", "ABS", 2.90, 1.05, 3.5), ("PC/ABS schwarz", "PC/ABS", 3.80, 1.15, 4.0),
    ("PA6 GF30 schwarz", "PA6", 3.40, 1.36, 6.5), ("PA66 GF30 schwarz", "PA66", 4.20, 1.37, 7.0),
    ("POM natur", "POM", 2.95, 1.41, 2.8), ("PBT GF30 schwarz", "PBT", 3.70, 1.53, 4.3), ("TPE 60 Shore A", "TPE", 4.90, 1.10, 3.5),
]
# Weitere Anlagen (Arbeitsgänge): Nr, Name, Art, €/h, IH €/h, Prod %, Bedienfaktor, kW, h/Jahr, Grundlast %
EXTRA_MACHINES = [
    ("MON-01", "Montagelinie Gehäuse (3 Stationen)", "montage", 28, 2, 90, 2.0, 6, 4000, 45),
    ("US-01", "Ultraschall-Schweißanlage 20 kHz", "nachbearbeitung", 18, 1.5, 92, 0.5, 3, 4000, 30),
    ("TD-01", "Tampondruck 2-farbig", "nachbearbeitung", 15, 1, 90, 0.5, 1.5, 4000, 25),
    ("PR-01", "Dichtheitsprüfstand", "pruefung", 22, 1.5, 95, 0.25, 2, 4000, 20),
]
PURCHASED_PARTS = [  # Art.-Nr., Bezeichnung, Lieferant, Lief.-Nr., Preis, Preiseinheit, MOQ, Lieferzeit, kg CO₂e/Stk
    ("ZK-1001", "Gewindebuchse Messing M4 (Einlegeteil)", "Metallwaren Schulte", "GB-M4-6", 45.0, 1000, 10000, 21, 0.004),
    ("ZK-1002", "O-Ring 22×2 NBR", "Dichtungstechnik Lippe", "OR-22x2", 18.0, 1000, 5000, 14, 0.001),
    ("ZK-1003", "Federstahl-Clip verzinkt", "Stanztechnik Detmold", "FC-118", 0.032, 1, 20000, 28, 0.006),
    ("ZK-1004", "Schraube PT K30×8 Torx", "Verbindungselemente Weser", "PT30x8", 9.5, 1000, 10000, 10, 0.002),
    ("ZK-1005", "Typenschild-Etikett PET", "Etiketten Paderborn", "TS-40x20", 12.0, 1000, 5000, 7, 0.0005),
    ("ZK-2001", "Leiterplatte Sensor bestückt", "Elektronikfertigung Bielefeld", "LP-SN-778", 3.85, 1, 2000, 42, 0.45),
]
# Standorte der Gruppe – Abweichungen von den Gruppen-Parametern (Demo-Werte, durch echte Sätze ersetzen)
SITES = [
    ("DE1", "Stammwerk", "Deutschland", {}),
    ("DE2", "Werk 2", "Deutschland", {"labor_rate_h": 36.0, "setup_rate_h": 45.0, "fgk_pct": 14.0, "energy_price_kwh": 0.22}),
    ("CZ", "Werk Krupka", "Tschechien", {"labor_rate_h": 19.0, "setup_rate_h": 25.0, "assembly_rate_h": 17.0,
                                          "handling_rate_h": 17.0, "automation_rate_h": 31.0, "fgk_pct": 10.0, "vwgk_pct": 6.0,
                                          "energy_price_kwh": 0.17, "co2_grid_kg_kwh": 0.42, "co2_transport_kg_tkm": 0.09}),
]
# Maschinen an Werk 2 und Krupka: Nr, Name, t, €/h, IH €/h, Prod %, Bedienfaktor, kW, Standort-Code, Art
SITE_MACHINES = [
    ("W2-01", "Spritzgießmaschine 110 t", 110, 43, 4, 86, 0.3, 14, "DE2", "spritzguss"),
    ("W2-02", "Spritzgießmaschine 250 t", 250, 69, 7, 85, 0.3, 28, "DE2", "spritzguss"),
    ("W2-03", "Spritzgießmaschine 420 t", 420, 92, 9, 84, 0.5, 42, "DE2", "spritzguss"),
    ("KR-01", "Spritzgießmaschine 80 t", 80, 24, 3, 86, 0.3, 11, "CZ", "spritzguss"),
    ("KR-02", "Spritzgießmaschine 160 t 2K", 160, 41, 5, 82, 0.5, 22, "CZ", "spritzguss"),
    ("KR-03", "Spritzgießmaschine 300 t", 300, 52, 6, 84, 0.4, 32, "CZ", "spritzguss"),
    ("KR-04", "Spritzgießmaschine 500 t", 500, 71, 9, 83, 0.5, 48, "CZ", "spritzguss"),
    ("KR-M1", "Montagelinie (2 Stationen)", None, 19, 1.5, 88, 2.0, 5, "CZ", "montage"),
]
MACHINE_POWER = {"M01": 9, "M02": 14, "M03": 22, "M04": 28, "M05": 42, "M06": 60}
# Herleitung Stundensatz: Wiederbeschaffungswert, m², Instandhaltung €/Jahr, sonstige Fixkosten €/Jahr
MACHINE_COST = {"M01": (120000, 18, 18000, 2500), "M02": (190000, 24, 24000, 3500), "M03": (420000, 36, 33000, 6000),
                "M04": (330000, 34, 42000, 5000), "M05": (520000, 48, 43000, 7000), "M06": (800000, 70, 58000, 9000)}


def seed_calc(db):
    from .calc_engine import compute, normalize, post_calculate
    from .models import Calculation, CalculationVersion, Machine, Material, PostCalculation, PurchasedPart
    from .routers.calc import STATUS_PROBABILITY, default_inputs, get_settings, sync_opportunity

    if db.scalar(select(func.count()).select_from(Machine)):
        print("Kalkulations-Stammdaten existieren bereits – übersprungen.")
        return
    machines = [Machine(number=n, name=nm, clamping_force_t=t, hourly_rate=r, maintenance_rate=ih,
                        productivity_pct=p, operator_factor=bf, location="Werk 1", available_hours_year=MACHINE_HOURS.get(n, 6000),
                        base_load_pct=MACHINE_BASE[n][0], base_load_decline_pct=MACHINE_BASE[n][1],
                        power_kw=MACHINE_POWER.get(n), acquisition_value=MACHINE_COST[n][0], useful_life_years=10,
                        interest_pct=6, floor_space_m2=MACHINE_COST[n][1], maintenance_cost_year=MACHINE_COST[n][2],
                        other_fixed_cost_year=MACHINE_COST[n][3])
                for n, nm, t, r, ih, p, bf in MACHINES]
    materials = [Material(name=nm, family=fam, price_per_kg=pr, density=d, supplier="Rahmenvertrag", co2_kg_per_kg=c,
                          notes="CO₂-Faktor ist ein Richtwert – durch Lieferanten-PCF ersetzen")
                 for nm, fam, pr, d, c in MATERIALS]
    extra = [Machine(number=n, name=nm, kind=k, hourly_rate=r, maintenance_rate=ih, productivity_pct=p, operator_factor=bf,
                     power_kw=kw, available_hours_year=h, base_load_pct=bl, base_load_decline_pct=5, location="Werk 1",
                     useful_life_years=8, interest_pct=6)
             for n, nm, k, r, ih, p, bf, kw, h, bl in EXTRA_MACHINES]
    parts = [PurchasedPart(part_no=n, name=nm, supplier=sup, supplier_part_no=sn, price=pr, price_basis=pb, moq=moq,
                           lead_time_days=lt, co2_kg_per_piece=co2, price_valid_from=date(date.today().year, 1, 1),
                           notes="CO₂-Wert: Lieferantenangabe/Richtwert")
             for n, nm, sup, sn, pr, pb, moq, lt, co2 in PURCHASED_PARTS]
    from .models import Site
    sites = {}
    for n, (code, name, country, over) in enumerate(SITES):
        site = db.scalars(select(Site).where(Site.code == code)).first() or Site(code=code, name=name, country=country,
                                                                                 settings=over, sort=n)
        db.add(site)
        sites[code] = site
    db.flush()
    for m in machines + extra:
        m.site_id, m.location = sites["DE1"].id, sites["DE1"].name
    site_machines = [Machine(number=n, name=nm, kind=k, clamping_force_t=t, hourly_rate=r, maintenance_rate=ih,
                             productivity_pct=p, operator_factor=bf, power_kw=kw, site_id=sites[sc].id, location=sites[sc].name,
                             available_hours_year=6000 if k == "spritzguss" else 4000, base_load_pct=55, base_load_decline_pct=10,
                             useful_life_years=10, interest_pct=6, grid_factor=sites[sc].settings.get("co2_grid_kg_kwh"))
                     for n, nm, t, r, ih, p, bf, kw, sc, k in SITE_MACHINES]
    db.add_all(machines + materials + extra + parts + site_machines)
    db.flush()
    for m in machines:
        m.kind = "spritzguss"
    # Beispiel: große Maschinen mit Entnahmeroboter und Handling
    for m in machines[4:]:
        m.handling_pct, m.automation_pct = 25, 10
    # Umlage so ansetzen, dass der hergeleitete Satz nahe am eingetragenen liegt (Demo)
    from .calc_engine import DEFAULT_SETTINGS, machine_rate
    for m in machines:
        md = {c.name: getattr(m, c.name) for c in Machine.__table__.columns}
        base = machine_rate(md, DEFAULT_SETTINGS)["hourly_rate"]
        m.allocation_cost_year = round(max(0, (m.hourly_rate * 0.97 - base) * (m.available_hours_year or 6000)), -2)
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
        inp = default_inputs(db, sites["DE1"].id)
        inp.update(material_id=mat.id, material_name=mat.name, material_price_kg=mat.price_per_kg,
                   part_weight_g=g, sprue_weight_g=spr, machine_id=m.id, machine_name=m.name,
                   machine_rate_h=m.hourly_rate, maintenance_rate_h=m.maintenance_rate,
                   productivity_pct=m.productivity_pct, operator_factor=m.operator_factor,
                   handling_pct=m.handling_pct or 0, automation_pct=m.automation_pct or 0,
                   automation_setup_min=15 if m.automation_pct else 0,
                   cycle_time_s=cyc, cavities=cav, annual_volume=vol, lot_size=lot,
                   co2_material_kg_kg=mat.co2_kg_per_kg or 0, machine_power_kw=m.power_kw or 0,
                   co2_pack_per_unit=0.15 if g < 200 else 2.5, transport_km=0 if idx % 3 else 320,
                   one_time=[{"label": "Spritzgießwerkzeug", "cost": tool, "price": tool},
                             {"label": "Erstbemusterung / EMPB", "cost": 1800, "price": 1800}],
                   extras=[],
                   pack_type="KLT 6280 Mehrweg" if g < 200 else "Gitterbox mit Zwischenlagen",
                   pack_parts_per_unit=max(1, int((2500 if g < 200 else 120000) / max(g, 0.5))) if g < 200 else max(1, int(120000 / g)),
                   pack_cost_per_unit=1.20 if g < 200 else 9.50, pack_reusable=g < 200, pack_time_s=25 if g < 200 else 60,
                   pack_units_per_pallet=24 if g < 200 else 1,
                   incoterm="FCA Werk" if idx % 3 else "DAP Kunde",
                   transport_mode="keine" if idx % 3 else "palette", transport_cost_per_pallet=68.0)
        if art in ("Abdeckkappe Steuergerät", "Frontend-Modulträger", "Clip-Halter Kabelbaum"):
            inp["lot_tiers"] = [round(lot / 2), lot, lot * 3]
        if art.startswith("Frontend"):
            inp["project_years"] = 6
            inp["price_reductions"] = [2, 3, 3, 3, 3]  # Jahresabschläge Automotive, vorab eingerechnet
        if art.startswith("Gehäuse Sensor"):
            tpe = materials[8]
            inp["components"] = [{"label": "Dichtung TPE", "material_id": tpe.id, "material_name": tpe.name,
                                  "price_kg": tpe.price_per_kg, "co2_kg_kg": tpe.co2_kg_per_kg, "part_weight_g": 6,
                                  "sprue_weight_g": 2, "regrind_pct": 0}]
        if art in ("Halter Steuergerät", "Abdeckkappe Steuergerät"):
            inp["family_group"], inp["family_share_pct"] = "WZ-4711 Familie Steuergerät", 50
        if art == "Deckel Sicherungskasten":
            inp["one_time"][0]["amortize"] = True
        if art == "Clip-Halter Kabelbaum":
            inp["volume_tiers"] = [600000, 1200000, 2500000]
        if art.startswith("Gehäuse Sensor"):
            def op(mach, name, cyc, setup_h):
                return {"machine_id": mach.id, "name": name, "kind": mach.kind, "rate_h": mach.hourly_rate,
                        "maintenance_h": mach.maintenance_rate, "cycle_s": cyc, "parts_per_cycle": 1,
                        "productivity_pct": mach.productivity_pct, "operator_factor": mach.operator_factor,
                        "labor_rate_h": inp.get("labor_rate_h", 38), "setup_h": setup_h, "setup_persons": 1,
                        "power_kw": mach.power_kw or 0}
            inp["operations"] = [op(extra[0], "Montage Buchsen + Clip", 14, 0.5), op(extra[3], "Dichtheitsprüfung 100 %", 9, 0.25)]

            def pi(part, qty):
                return {"part_id": part.id, "part_no": part.part_no, "name": part.name, "qty": qty,
                        "price_per_piece": part.price / (part.price_basis or 1), "co2_kg_per_piece": part.co2_kg_per_piece or 0}
            inp["purchased_items"] = [pi(parts[0], 2), pi(parts[2], 1), pi(parts[4], 1), {**pi(parts[5], 1), "side": True}]
            # Jahr 1 manueller Anlaufpreis, ab Jahr 2 Serienpreis, danach Abschläge; Leiterplatte ohne Abschlag
            inp.update(price_year1_mode="manuell", price_year1_manual=6.60, price_reductions=[0, 2, 4, 6],
                       side_price_reductions=[0, 0, 0, 0])
            inp.update(preseries_qty=1000, preseries_lot=500, preseries_productivity_pct=65, preseries_scrap_pct=6,
                       preseries_surcharge_pct=5)
            inp["extras"].append({"label": "Bedrucken Tampondruck", "amount": 0.035, "basis": "stueck", "category": "fertigung"})
        inp = normalize(inp)
        owner = users[idx % len(users)]
        calc = Calculation(number=f"K{date.today():%y}-{idx + 1:04d}", article_name=art, customer_article_no=kd,
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
        calc.site_id = final[0].get("site_id")
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
    # Beispiel Standortwechsel: Wallbox-Schale (Kunde in Tschechien) nach Krupka verlagert
    from .routers.calc import site_inputs
    wb = db.scalars(select(Calculation).where(Calculation.article_name == "Gehäuseschale Wallbox")).first()
    if wb:
        ver = wb.versions[-1]
        inp_cz, _ = site_inputs(db, ver.inputs, sites["CZ"], sites["DE1"].id)
        res_cz = compute(normalize(inp_cz))
        no = ver.version_no + 1
        wb.versions.append(CalculationVersion(version_no=no, inputs=normalize(inp_cz), results=res_cz, created_by_id=wb.owner_id,
                                              change_note="Standort Werk Krupka (Standortvergleich: günstiger, Kunde in CZ)"))
        wb.current_version, wb.site_id = no, sites["CZ"].id
        wb.unit_price, wb.annual_revenue, wb.margin_pct = res_cz["unit_price"], res_cz["annual_revenue"], res_cz["margin_pct"]
    db.commit()
    # Preisgleitung demonstrieren: PA6 GF30 nach der Kalkulation teurer (Historie wird automatisch geschrieben)
    from .models import MaterialPrice
    pa6 = next(m for m in materials if m.name.startswith("PA6"))
    db.add(MaterialPrice(material_id=pa6.id, price_per_kg=3.10, valid_from=date.today() - timedelta(days=200),
                         note="Rahmenvertrag 1. Halbjahr"))
    pa6.price_index = "Marktbericht PA6 GF30 (Monatsmittel)"
    db.commit()
    pa6.price_per_kg = 3.65
    db.commit()
    # Großprojekte mit Verkaufschance und Angebot verknüpfen (zeigt Hervorhebung in Pipeline/Angeboten)
    from .routers.calc import create_opportunity, create_quote
    approver = db.scalar(select(User).where(User.email == "tim.kraus@firma.de"))
    if approver:
        approver.can_approve = True
    for calc in db.scalars(select(Calculation).where(Calculation.article_name.in_(
            ["Frontend-Modulträger", "Gehäuseschale Wallbox"]))).unique().all():
        owner = db.get(User, calc.owner_id)
        # Großprojekt: Freigabe (Vier-Augen) vor dem Angebot
        calc.approval_status, calc.approval_version = "freigegeben", calc.current_version
        calc.approval_requested_by_id = owner.id
        calc.approval_by_id = approver.id if approver and approver.id != owner.id else None
        calc.approval_at = calc.approval_requested_at = datetime.now(timezone.utc)
        calc.approval_comment = "Strategischer Kunde, Marge akzeptiert"
        calc.decision, calc.decision_note = "anbieten", "Beispiel"
        db.flush()
        create_opportunity(calc.id, db=db, user=owner)
        create_quote(calc.id, db=db, user=owner)
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




TOOLMAKERS = [  # Name, Ort, Ansprechpartner, E-Mail, Land
    ("Formenbau Ostwestfalen GmbH", "Bünde", "Herr Brandt", "angebote@formenbau-owl.example", "DE"),
    ("Werkzeugbau Lippe KG", "Lemgo", "Frau Sommer", "vertrieb@wzb-lippe.example", "DE"),
    ("Precision Moulds s.r.o.", "Most", "Herr Dvořák", "sales@precision-moulds.example", "CZ"),
    ("Sauerland Formtechnik GmbH", "Lüdenscheid", "Herr Kaiser", "info@sauerland-form.example", "DE"),
    ("Alpen Werkzeugbau AG", "Kufstein", "Frau Huber", "offers@alpen-wzb.example", "AT"),
    ("Mould Tech Portugal Lda.", "Marinha Grande", "Sr. Costa", "quotes@mouldtech.example", "PT"),
    ("Automation Weser GmbH", "Minden", "Herr Vogt", "projekte@automation-weser.example", "DE"),
    ("Anlagenbau Teutoburg GmbH", "Detmold", "Frau Lenz", "anfrage@ab-teutoburg.example", "DE"),
]


def seed_procurement(db):
    from .models import ProcurementOffer, ProcurementRequest
    from .routers.procurement import _num, _prefill

    if db.scalar(select(func.count()).select_from(ProcurementRequest)):
        return
    owner = db.scalars(select(User).where(User.role == "admin")).first() or db.scalars(select(User)).first()
    sup = {}
    for name, city, contact, email, country in TOOLMAKERS:
        acc = db.scalars(select(Account).where(Account.name == name)).first()
        if not acc:
            acc = Account(name=name, industry="Werkzeug- und Anlagenbau", city=city, type="lieferant", owner_id=owner.id)
            db.add(acc)
            db.flush()
            ln = contact.split(" ", 1)[1]
            db.add(Contact(account_id=acc.id, salutation=contact.split(" ")[0].replace("Sr.", "Herr"), first_name="",
                           last_name=ln, position="Vertrieb", email=email))
        sup[name] = (acc, email, country)
    db.flush()
    from .models import Calculation
    calcs = {c.article_name: c for c in db.scalars(select(Calculation)).unique()}
    today = date.today()

    def req(calc, kind, offers, decide=None, note=None):
        title, spec = _prefill(db, kind, calc)
        r = ProcurementRequest(number=_num(db), calculation_id=calc.id, kind=kind, title=title, spec=spec,
                               reply_by=today + timedelta(days=10), needed_by=today + timedelta(days=120),
                               owner_id=owner.id, status="angefragt")
        db.add(r)
        db.flush()
        for n, (name, price, weeks, cav, hr, steel, life, rating, loc) in enumerate(offers):
            acc, email, country = sup[name]
            r.offers.append(ProcurementOffer(
                account_id=acc.id, supplier_name=name, contact_email=email, requested_at=today - timedelta(days=21),
                status="angebot" if price else "angefragt", offer_no=f"A-{2600 + n * 7}" if price else None,
                offer_date=today - timedelta(days=7 - n) if price else None, price=price, lead_time_weeks=weeks,
                cavities=cav, hot_runner=hr, steel=steel, tool_life_shots=life, rating=rating,
                location=loc or country, payment_terms="30/40/30 (Bestellung/T0/Abnahme)" if price else None,
                warranty="1.000.000 Schuss / 24 Monate" if price else None))
        db.flush()
        if decide:
            o = next(x for x in r.offers if x.supplier_name == decide)
            r.decided_offer_id, r.decision_note, r.status = o.id, note, "entschieden"
            r.decided_by_id, r.decided_at = owner.id, datetime.now(timezone.utc)
            for x in r.offers:
                x.status = "gewaehlt" if x.id == o.id else ("abgelehnt" if x.price else x.status)

    sensor = calcs.get("Gehäuse Sensor 2K")
    if sensor:
        req(sensor, "werkzeug", [
            ("Formenbau Ostwestfalen GmbH", 98500, 14, 2, "HK 2-fach, Synventive", "1.2343 gehärtet", 1000000, 5, "DE"),
            ("Werkzeugbau Lippe KG", 104000, 12, 2, "HK 2-fach, Mold-Masters", "1.2343 / 1.2738", 1000000, 4, "DE"),
            ("Precision Moulds s.r.o.", 79800, 16, 2, "HK 2-fach, Yudo", "1.2343", 800000, 4, "CZ"),
            ("Sauerland Formtechnik GmbH", 112500, 11, 2, "HK 2-fach, Synventive", "1.2343 ESU", 1500000, 5, "DE"),
            ("Alpen Werkzeugbau AG", 121000, 13, 2, "HK 2-fach, Husky", "1.2343 ESU", 1500000, 5, "AT"),
            ("Mould Tech Portugal Lda.", 72400, 18, 2, "HK 2-fach, Yudo", "1.2311", 600000, 3, "PT"),
            ("Werkzeugbau Lippe KG", None, None, None, None, None, None, None, "DE"),
        ][:6], decide="Formenbau Ostwestfalen GmbH",
            note="Bestes Preis-Leistungs-Verhältnis bei 1 Mio. Schuss, kurze Wege für Änderungen, gute Erfahrung bei 2K.")
        req(sensor, "montagelinie", [
            ("Automation Weser GmbH", 186000, 20, None, None, None, None, 4, "DE"),
            ("Anlagenbau Teutoburg GmbH", 171500, 24, None, None, None, None, 4, "DE"),
            ("Precision Moulds s.r.o.", None, None, None, None, None, None, None, "CZ"),
        ])
    blende = calcs.get("Gehäuseschale Wallbox")
    if blende:
        req(blende, "werkzeug", [
            ("Formenbau Ostwestfalen GmbH", 176000, 16, 1, "HK 1-fach Nadelverschluss", "1.2738 / 1.2343", 1000000, 5, "DE"),
            ("Precision Moulds s.r.o.", 149000, 18, 1, "HK 1-fach Nadelverschluss", "1.2738", 800000, 4, "CZ"),
            ("Mould Tech Portugal Lda.", 138500, 20, 1, "HK 1-fach offen", "1.2311", 500000, 3, "PT"),
            ("Alpen Werkzeugbau AG", None, None, None, None, None, None, None, "AT"),
        ])
    db.commit()


def seed_pricelist():
    """Demo-Preisliste: einige VK-Artikel je Kunde mit Materialbasis (Platzhalterwerte)."""
    from datetime import date as _d  # noqa: PLC0415
    from .models import Account, Material, PriceArticle, PriceArticleHistory, PriceArticleMaterial, PriceArticlePart  # noqa: PLC0415
    db = SessionLocal()
    if db.query(PriceArticle).count():
        db.close()
        return
    mats = db.query(Material).order_by(Material.id).all()
    for i, m in enumerate(mats):
        m.number = m.number or f"RM{5930 + i:05d}"
    accs = [a for a in db.query(Account).filter(Account.type == "kunde").order_by(Account.id).all()][:3]
    demo = [  # Kunde-Index, Artikel-Nr., Kunden-Nr., Bezeichnung, Preis/100, Planmenge, Schussgewicht, Material-Index, Basis, Vertrag
        (0, "100-2001", "SN-778-01", "Gehäuse Sensor 2K Oberteil", 66.00, 80000, 14.2, 0, None, False, "Preisgleitklausel Material"),
        (0, "100-2002", "SN-778-02", "Gehäuse Sensor 2K Unterteil", 52.40, 80000, 11.6, 0, None, False, "Preisgleitklausel Material"),
        (0, "100-2005", "SN-901-11", "Abdeckkappe", 8.90, 250000, 3.1, 1, None, True, "Festpreis bis 31.12.2027"),
        (1, "200-1001", "EK-55-1200", "Steckergehäuse 12-polig", 31.75, 150000, 7.8, 0, None, False, ""),
        (1, "200-1002", "EK-55-1210", "Verriegelung", 6.20, 300000, 1.9, 1, None, True, "Rahmenvertrag 2027, Preisbindung"),
        (2, "300-0501", "HW-4471", "Griffschale", 24.10, 60000, 22.5, 2 if len(mats) > 2 else 0, None, False, ""),
    ]
    for ai, no, cno, desc, price, qty, shot, mi, basis, bound, note in demo:
        if ai >= len(accs) or not mats:
            continue
        m = mats[mi % len(mats)]
        a = PriceArticle(account_id=accs[ai].id, article_no=no, customer_part_no=cno, description=desc, location="DE",
                         price_unit=100, currency="EUR", price=price, price_valid_from=_d(_d.today().year, 1, 1), forecast_qty=qty,
                         shot_weight_g=shot, part_weight_g=round(shot * 0.92, 1), mgk_pct=8, contract_bound=bound,
                         contract_until=_d(_d.today().year + 1, 12, 31) if bound else None, contract_note=note or None)
        a.materials = [PriceArticleMaterial(position=1, material_id=m.id, weight_g=shot, price_basis=basis or m.price_per_kg)]
        if no == "100-2001":
            a.parts = [PriceArticlePart(position=1, name="Gewindebuchse M4", qty_per_part=4, price_basis=0.021, current_price=0.021)]
        db.add(a)
        db.flush()
        db.add(PriceArticleHistory(article_id=a.id, price=price, valid_from=a.price_valid_from, source="erstanlage", note="Beispiel"))
    db.commit()
    db.close()


def seed_inquiries():
    """Demo: Kalkulationen in Anfragen überführen (wie beim Update eines bestehenden Servers)."""
    from .inquiry import migrate  # noqa: PLC0415
    db = SessionLocal()
    print("Anfragen:", migrate(db))
    db.close()


if __name__ == "__main__":
    run()
    seed_inquiries()
    seed_pricelist()
