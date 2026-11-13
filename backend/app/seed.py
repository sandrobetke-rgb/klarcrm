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
        print("Es existieren bereits Daten – Seed übersprungen.")
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
    print("Demo-Daten angelegt. Logins: anna.berg@firma.de / demo1234, gesellschafter@firma.de / demo1234")


if __name__ == "__main__":
    run()
