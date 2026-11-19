from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now():
    return datetime.now(timezone.utc)


ROLES = ("admin", "vertrieb", "gesellschafter")
# Pipeline-Phasen (REV01-P01): Lead = Potenzial ohne Anfrage (manuell), Neue Anfrage = Anfrage vor der Entscheidung,
# Qualifiziert = zur Kalkulation freigegeben, Angebot = versendet, Verhandlung = Endrunde / technisches Gespräch,
# nicht_angeboten = Anfrage abgelehnt (zählt nicht als verloren)
STAGES = ("lead", "neue_anfrage", "qualifiziert", "angebot", "verhandlung", "gewonnen", "verloren", "nicht_angeboten")
CLOSED_STAGES = ("gewonnen", "verloren", "nicht_angeboten")
STAGE_PROBABILITY = {
    "lead": 10, "neue_anfrage": 15, "qualifiziert": 25, "angebot": 50,
    "verhandlung": 75, "gewonnen": 100, "verloren": 0, "nicht_angeboten": 0,
}
ACTIVITY_TYPES = ("anruf", "termin", "email", "aufgabe", "notiz")
QUOTE_STATUS = ("entwurf", "versendet", "angenommen", "abgelehnt", "ersetzt")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int | None] = mapped_column(Integer)                # Standard-Standort für neue Kalkulationen
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="vertrieb")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    can_approve: Mapped[bool | None] = mapped_column(Boolean, default=False)  # darf Kalkulationen freigeben
    calendar_token: Mapped[str | None] = mapped_column(String(64), index=True)  # Outlook-Kalenderabo


class Account(TimestampMixin, Base):
    """Firma / Kunde."""
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    type: Mapped[str] = mapped_column(String(30), default="interessent")  # interessent/kunde/partner/lieferant
    industry: Mapped[str | None] = mapped_column(String(100))
    website: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(200))
    street: Mapped[str | None] = mapped_column(String(200))
    zip: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100), default="Deutschland")
    notes: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    owner = relationship("User", lazy="joined")
    contacts = relationship("Contact", back_populates="account", cascade="all, delete-orphan")


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    salutation: Mapped[str | None] = mapped_column(String(20))
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    position: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    account = relationship("Account", back_populates="contacts", lazy="joined")
    owner = relationship("User", lazy="joined")


class Opportunity(TimestampMixin, Base):
    """Verkaufschance."""
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"))
    stage: Mapped[str] = mapped_column(String(30), default="lead", index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    probability: Mapped[int] = mapped_column(Integer, default=10)
    close_date: Mapped[date | None] = mapped_column(Date)
    closed_at: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    lost_reason: Mapped[str | None] = mapped_column(String(255))
    lost_code: Mapped[str | None] = mapped_column(String(40))          # Verlustgrund als Schlüssel (für Auswertung)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # Anfrage / Projekt (REV01 Phase 2): eine Pipeline-Karte je Kundenanfrage mit n Artikeln (Kalkulationen)
    number: Mapped[str | None] = mapped_column(String(30), unique=True, index=True)   # AF26-0001
    kind: Mapped[str | None] = mapped_column(String(20), default="anfrage")         # anfrage | lead
    inquiry_date: Mapped[date | None] = mapped_column(Date)                         # Eingang der Anfrage
    due_date: Mapped[date | None] = mapped_column(Date)                             # Angebotsabgabe bis
    offered_at: Mapped[date | None] = mapped_column(Date)                           # erstes Angebot versendet
    final_round: Mapped[bool | None] = mapped_column(Boolean, default=False)       # war in der Endrunde (Verhandlung)
    tech_talk: Mapped[bool | None] = mapped_column(Boolean, default=False)         # technisches Gespräch erforderlich

    account = relationship("Account", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    owner = relationship("User", lazy="joined")


class Activity(TimestampMixin, Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(20), default="aufgabe")
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"))
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    quote_id: Mapped[int | None] = mapped_column(ForeignKey("quotes.id", ondelete="SET NULL"), index=True)  # REV01-P07
    kind: Mapped[str | None] = mapped_column(String(30))        # angebotsverfolgung | technisches_gespraech | None
    attempts: Mapped[int | None] = mapped_column(Integer, default=0)   # „niemanden erreicht“-Zähler
    result: Mapped[str | None] = mapped_column(String(30))      # erreicht | nicht_erreicht | wieder_melden

    account = relationship("Account", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    opportunity = relationship("Opportunity", lazy="joined")
    owner = relationship("User", lazy="joined")
    quote = relationship("Quote", lazy="joined", foreign_keys=[quote_id])


class Quote(TimestampMixin, Base):
    """Angebot."""
    __tablename__ = "quotes"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"))
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(20), default="entwurf")
    quote_date: Mapped[date] = mapped_column(Date, default=date.today)
    valid_until: Mapped[date | None] = mapped_column(Date)
    tax_rate: Mapped[float] = mapped_column(Float, default=19.0)
    intro_text: Mapped[str | None] = mapped_column(Text)
    terms: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    calculation_ids: Mapped[list | None] = mapped_column(JSON)  # Herkunft: Kalkulationen (Sammelangebot)
    language: Mapped[str | None] = mapped_column(String(5), default="de")  # de | en
    sent_at: Mapped[date | None] = mapped_column(Date)                    # versendet am (Start Angebotsverfolgung)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # letzte Rückmeldung / Anruf
    last_contact_note: Mapped[str | None] = mapped_column(Text)
    tool_lead_time: Mapped[str | None] = mapped_column(String(80))       # Werkzeug: Lieferzeit FOT (Phase 3 je Artikel)

    account = relationship("Account", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    opportunity = relationship("Opportunity", lazy="joined")
    owner = relationship("User", lazy="joined")
    items = relationship(
        "QuoteItem", back_populates="quote", cascade="all, delete-orphan",
        order_by="QuoteItem.position", lazy="selectin",
    )

    @property
    def calculations(self) -> list[dict]:
        """Herkunfts-Kalkulationen (Nummer, Artikel) für die Anzeige."""
        from sqlalchemy.orm import object_session
        ids = self.calculation_ids or []
        sess = object_session(self)
        if not ids or sess is None:
            return []
        rows = sess.execute(select(Calculation.id, Calculation.number, Calculation.article_name)
                            .where(Calculation.id.in_(ids)).order_by(Calculation.number)).all()
        return [{"id": r[0], "number": r[1], "article_name": r[2]} for r in rows]

    @property
    def net_total(self) -> float:
        return round(sum(i.line_total for i in self.items), 2)

    @property
    def tax_total(self) -> float:
        return round(self.net_total * (self.tax_rate or 0) / 100, 2)

    @property
    def gross_total(self) -> float:
        return round(self.net_total + self.tax_total, 2)


class QuoteItem(Base):
    __tablename__ = "quote_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=1)
    pos_label: Mapped[str | None] = mapped_column(String(10))   # „1“, „1.1“ … (REV01-P08)
    kind: Mapped[str | None] = mapped_column(String(20))        # artikel | werkzeug | sonstiges | vorserie | co2 | text
    calculation_id: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Float, default=1)
    unit: Mapped[str] = mapped_column(String(20), default="Stk")
    unit_price: Mapped[float] = mapped_column(Numeric(14, 4), default=0)
    discount_pct: Mapped[float] = mapped_column(Float, default=0)

    quote = relationship("Quote", back_populates="items")

    @property
    def line_total(self) -> float:
        return round(
            float(self.quantity or 0) * float(self.unit_price or 0)
            * (1 - float(self.discount_pct or 0) / 100), 2
        )


# =====================================================================
# Kalkulation (Spritzguss)
# =====================================================================
from sqlalchemy import JSON  # noqa: E402

CALC_STATUS = ("anfrage", "kalkulation", "angeboten", "verhandlung", "gewonnen", "verloren", "kein_angebot", "zurueckgestellt")
FEASIBILITY = ("herstellbar", "bedingt_herstellbar", "anpassungen_erforderlich", "nicht_herstellbar")
NO_BID_REASONS = ("mengen_zu_klein", "artikel_zu_klein", "artikel_zu_gross", "keine_maschine_kapazitaet",
                  "nicht_herstellbar", "technologie_passt_nicht", "termin_nicht_machbar", "sonstiges")
CLOSE_REASONS = (
    "artikelpreis_zu_hoch", "werkzeug_zu_teuer", "investition_zu_teuer",
    "projekt_kunde_nicht_gewonnen", "projekt_eingestellt", "lieferzeit", "technik", "vorrichtung_zu_teuer", "sonstiges",
)


class Machine(TimestampMixin, Base):
    """Maschinen-Stammdaten mit Standard-Stundensätzen."""
    __tablename__ = "machines"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str | None] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str | None] = mapped_column(String(30), default="spritzguss")  # spritzguss | montage | nachbearbeitung | pruefung | sonstige
    status: Mapped[str | None] = mapped_column(String(20), default="bestand")  # bestand | geplant (nur für Kalkulation, REV01-M02)
    shifts: Mapped[int | None] = mapped_column(Integer)  # Schichtmodell 1/2/3 → verfügbare Std = Schichten × 8 h × 240 Tage
    delete_requested_by: Mapped[int | None] = mapped_column(Integer)   # Löschantrag (Vier-Augen, REV01-M03)
    delete_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clamping_force_t: Mapped[float | None] = mapped_column(Float)
    hourly_rate: Mapped[float] = mapped_column(Float, default=0)        # Maschinenstundensatz €/h (ohne Personal)
    maintenance_rate: Mapped[float] = mapped_column(Float, default=0)   # Instandhaltung €/h
    productivity_pct: Mapped[float] = mapped_column(Float, default=85)  # Nutzungsgrad / Produktivität
    operator_factor: Mapped[float] = mapped_column(Float, default=0.3)  # Personen je Maschine
    handling_pct: Mapped[float | None] = mapped_column(Float)     # Standard-Anteil Mitarbeiter Handling %
    automation_pct: Mapped[float | None] = mapped_column(Float)   # Standard-Anteil Mitarbeiter Automatisierung %
    location: Mapped[str | None] = mapped_column(String(80))
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id", ondelete="SET NULL"), index=True)
    available_hours_year: Mapped[float | None] = mapped_column(Float, default=6000)  # verfügbare Std/Jahr (Schichtmodell)
    base_load_pct: Mapped[float | None] = mapped_column(Float, default=0)          # Grundauslastung Bestandsaufträge %
    base_load_decline_pct: Mapped[float | None] = mapped_column(Float, default=0)  # Auslauf Bestand je Jahr %
    power_kw: Mapped[float | None] = mapped_column(Float)                          # mittl. Leistungsaufnahme inkl. Peripherie
    # Herleitung Maschinenstundensatz
    acquisition_value: Mapped[float | None] = mapped_column(Float)     # Wiederbeschaffungswert €
    useful_life_years: Mapped[float | None] = mapped_column(Float)     # Nutzungsdauer Jahre
    interest_pct: Mapped[float | None] = mapped_column(Float)          # kalkulatorischer Zins %
    floor_space_m2: Mapped[float | None] = mapped_column(Float)        # Platzbedarf m²
    maintenance_cost_year: Mapped[float | None] = mapped_column(Float)  # Instandhaltung €/Jahr
    other_fixed_cost_year: Mapped[float | None] = mapped_column(Float)  # Versicherung, Sonstiges €/Jahr
    allocation_cost_year: Mapped[float | None] = mapped_column(Float)  # Umlage Kostenstelle (Meister, Logistik, Peripherie …) €/Jahr
    grid_factor: Mapped[float | None] = mapped_column(Float)                       # Strom kg CO₂e/kWh (Standort), leer = Parameter
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Material(TimestampMixin, Base):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))          # z. B. PA6 GF30 schwarz
    number: Mapped[str | None] = mapped_column(String(40), index=True)  # F&R-Materialnummer (Preisliste „F&R Mat Number“)
    family: Mapped[str | None] = mapped_column(String(40))  # PA6, PP, ABS ...
    supplier: Mapped[str | None] = mapped_column(String(120))
    price_per_kg: Mapped[float] = mapped_column(Float, default=0)
    density: Mapped[float | None] = mapped_column(Float)
    co2_kg_per_kg: Mapped[float | None] = mapped_column(Float)  # Emissionsfaktor Cradle-to-Gate kg CO₂e/kg (Lieferanten-PCF)
    price_index: Mapped[str | None] = mapped_column(String(120))  # Bezugsindex Preisgleitung (z. B. Marktbericht)
    price_valid_from: Mapped[date | None] = mapped_column(Date)    # Stand des aktuellen Preises
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class CalcSettings(Base):
    """Standardwerte für neue Kalkulationen (eine Zeile, id=1)."""
    __tablename__ = "calc_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Calculation(TimestampMixin, Base):
    """Anfrage / Kalkulation mit Versionen."""
    __tablename__ = "calculations"
    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int | None] = mapped_column(Integer, index=True)   # Fertigungsstandort (aktuelle Version)
    number: Mapped[str] = mapped_column(String(30), unique=True, index=True)  # KA-2026-0001
    article_name: Mapped[str] = mapped_column(String(200))
    customer_article_no: Mapped[str | None] = mapped_column(String(80))
    own_article_no: Mapped[str | None] = mapped_column(String(80))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"))
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), default="anfrage", index=True)
    probability: Mapped[int] = mapped_column(Integer, default=25)
    close_reason: Mapped[str | None] = mapped_column(String(40))
    close_note: Mapped[str | None] = mapped_column(Text)  # Freitext zum Verlustgrund (Pflicht bei „Sonstiges“, REV01-P05)
    remark: Mapped[str | None] = mapped_column(Text)
    last_call_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inquiry_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)              # Angebotsabgabe bis
    sop_date: Mapped[date | None] = mapped_column(Date)              # Serienstart (SOP)
    sync_opportunity: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # Machbarkeit / kein Angebot / Artikelanalyse
    # Entscheidung je Artikel vor Kalkulationsstart (REV01-P02)
    decision: Mapped[str | None] = mapped_column(String(30))   # anbieten | nicht_anbieten | anderer_standort | sonstiges
    decision_note: Mapped[str | None] = mapped_column(Text)
    decision_by_id: Mapped[int | None] = mapped_column(Integer)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    feasibility: Mapped[str | None] = mapped_column(String(40))
    feasibility_note: Mapped[str | None] = mapped_column(Text)
    no_bid_reason: Mapped[str | None] = mapped_column(String(40))
    no_bid_note: Mapped[str | None] = mapped_column(Text)
    analysis: Mapped[dict | None] = mapped_column(JSON)
    analysis_results: Mapped[dict | None] = mapped_column(JSON)
    lifecycle: Mapped[dict | None] = mapped_column(JSON)  # Lebenswegbetrachtung (ISO 14001)
    # Freigabe (Vier-Augen-Prinzip)
    approval_status: Mapped[str | None] = mapped_column(String(20))  # angefragt | freigegeben | abgelehnt
    approval_version: Mapped[int | None] = mapped_column(Integer)
    approval_comment: Mapped[str | None] = mapped_column(Text)            # Begründung der Anfrage
    approval_decision_comment: Mapped[str | None] = mapped_column(Text)   # Kommentar der Entscheidung
    approval_requested_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approval_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approval_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Kennzahlen der aktuellen Version (für Listen/Sortierung)
    current_version: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    annual_volume: Mapped[float] = mapped_column(Float, default=0)
    annual_revenue: Mapped[float] = mapped_column(Float, default=0)
    one_time_revenue: Mapped[float] = mapped_column(Float, default=0)
    margin_pct: Mapped[float] = mapped_column(Float, default=0)

    account = relationship("Account", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    opportunity = relationship("Opportunity", lazy="joined")
    owner = relationship("User", lazy="joined", foreign_keys="Calculation.owner_id")
    approval_by = relationship("User", lazy="joined", foreign_keys="Calculation.approval_by_id")
    approval_requested_by = relationship("User", lazy="joined", foreign_keys="Calculation.approval_requested_by_id")
    versions = relationship("CalculationVersion", back_populates="calculation", cascade="all, delete-orphan",
                            order_by="CalculationVersion.version_no", lazy="selectin")
    post_calcs = relationship("PostCalculation", back_populates="calculation", cascade="all, delete-orphan",
                              order_by="PostCalculation.created_at", lazy="selectin")


class CalculationVersion(Base):
    __tablename__ = "calculation_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    calculation_id: Mapped[int] = mapped_column(ForeignKey("calculations.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    change_note: Mapped[str | None] = mapped_column(Text)
    inputs: Mapped[dict] = mapped_column(JSON)
    results: Mapped[dict] = mapped_column(JSON)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    calculation = relationship("Calculation", back_populates="versions")
    created_by = relationship("User", lazy="joined")


class PostCalculation(Base):
    """Nachkalkulation zu einer Kalkulationsversion (z. B. je Auftrag/Zeitraum)."""
    __tablename__ = "post_calculations"
    id: Mapped[int] = mapped_column(primary_key=True)
    calculation_id: Mapped[int] = mapped_column(ForeignKey("calculations.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    reference: Mapped[str | None] = mapped_column(String(120))  # Auftragsnummer / Zeitraum
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    actuals: Mapped[dict] = mapped_column(JSON)
    results: Mapped[dict] = mapped_column(JSON)
    traffic_light: Mapped[str] = mapped_column(String(10), default="gruen")  # gruen/gelb/rot
    remark: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    calculation = relationship("Calculation", back_populates="post_calcs")
    created_by = relationship("User", lazy="joined")


CALL_RESULTS = (
    "nicht_erreicht", "rueckruf_vereinbart", "kunde_entscheidet_noch", "preis_nachverhandeln",
    "neu_kalkulieren", "auftrag_in_aussicht", "auftrag_erhalten", "absage", "sonstiges",
)


class CalculationCall(Base):
    """Anruf zu einer Kalkulation mit Ergebnis."""
    __tablename__ = "calculation_calls"
    id: Mapped[int] = mapped_column(primary_key=True)
    calculation_id: Mapped[int] = mapped_column(ForeignKey("calculations.id", ondelete="CASCADE"), index=True)
    called_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    result: Mapped[str] = mapped_column(String(40), default="sonstiges")
    note: Mapped[str | None] = mapped_column(Text)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"))
    follow_up: Mapped[date | None] = mapped_column(Date)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    contact = relationship("Contact", lazy="joined")
    user = relationship("User", lazy="joined")


Calculation.calls = relationship("CalculationCall", cascade="all, delete-orphan",
                                 order_by="CalculationCall.called_at", lazy="selectin")


def _last_call(self):
    return self.calls[-1] if self.calls else None


Calculation.last_call = property(_last_call)


def _invest(self):
    """Invest = Einmalkosten (Werkzeug, Bemusterung …) der aktuellen Version."""
    v = next((x for x in reversed(self.versions) if x.version_no == self.current_version), None)
    return float((v.results or {}).get("one_time_cost", 0)) if v else 0.0


Calculation.invest = property(_invest)


def _last_light(self):
    return self.post_calcs[-1].traffic_light if self.post_calcs else None


Calculation.last_traffic_light = property(_last_light)


class MaterialPrice(Base):
    """Preishistorie je Material (Rohstoffpreis-Index für Preisgleitung)."""
    __tablename__ = "material_prices"
    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), index=True)
    price_per_kg: Mapped[float] = mapped_column(Float)
    valid_from: Mapped[date] = mapped_column(Date, default=date.today)
    note: Mapped[str | None] = mapped_column(String(255))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user = relationship("User", lazy="joined")
    material = relationship("Material")


class CalcTemplate(Base):
    """Kalkulationsvorlage (Eingaben einer Kalkulation zur Wiederverwendung)."""
    __tablename__ = "calc_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    inputs: Mapped[dict] = mapped_column(JSON)
    source_calc: Mapped[str | None] = mapped_column(String(30))
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_by = relationship("User", lazy="joined")



class AuditLog(Base):
    """Änderungsprotokoll (IATF 16949 / ISO 14001: Lenkung dokumentierter Information)."""
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    user_name: Mapped[str | None] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(10))           # anlegen | ändern | löschen
    entity: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    label: Mapped[str | None] = mapped_column(String(255))
    ref: Mapped[str | None] = mapped_column(String(60), index=True)  # übergeordneter Datensatz, z. B. calculations:12
    changes: Mapped[dict | None] = mapped_column(JSON)


def _approval_reasons(self):
    """Gründe, warum die aktuelle Version freigegeben werden muss (Vier-Augen-Prinzip)."""
    from sqlalchemy.orm import object_session
    from .calc_engine import DEFAULT_SETTINGS
    sess = object_session(self)
    row = sess.get(CalcSettings, 1) if sess else None
    st = {**DEFAULT_SETTINGS, **((row.data or {}) if row else {})}
    r = []
    if (self.annual_revenue or 0) >= st["big_revenue_threshold"]:
        r.append("Jahresumsatz ≥ Großprojekt-Schwelle")
    if (self.invest or 0) >= st["big_invest_threshold"]:
        r.append("Invest ≥ Großprojekt-Schwelle")
    if self.current_version and (self.margin_pct or 0) < st["approval_min_margin_pct"]:
        r.append(f"Marge unter {st['approval_min_margin_pct']:g} %".replace(".", ","))
    if not self.analysis_complete and self.decision_note != "übernommen aus Altdaten":
        r.append("Artikelanalyse unvollständig")   # REV01-P03: Angebot nur nach Freigabe durch Vorgesetzten
    return r


def _analysis_complete(self) -> bool:
    """Artikelanalyse vollständig: gespeichert, alle Prüfpunkte bewertet, Machbarkeit eingetragen."""
    res = self.analysis_results or {}
    return bool(self.analysis and res and res.get("open_checks", 1) == 0 and self.feasibility)


Calculation.analysis_complete = property(_analysis_complete)


def _is_approved(self):
    return self.approval_status == "freigegeben" and self.approval_version == self.current_version


Calculation.approval_reasons = property(_approval_reasons)


def _activity_light(self):
    if self.kind != "angebotsverfolgung":
        return None
    from .inquiry import followup_light  # noqa: PLC0415
    return followup_light(self.due_at, self.done)


def _quote_followup(self):
    """Offene Angebotsverfolgung des Angebots: Fälligkeit, Ampel, Versuche."""
    from sqlalchemy.orm import object_session
    sess = object_session(self)
    if not sess or not self.id:
        return None
    t = sess.query(Activity).filter(Activity.quote_id == self.id, Activity.kind == "angebotsverfolgung",
                                    Activity.done.is_(False)).order_by(Activity.due_at).first()
    if not t:
        return None
    return {"id": t.id, "due_at": t.due_at.isoformat() if t.due_at else None, "light": t.light, "attempts": t.attempts or 0,
            "owner": t.owner.name if t.owner else None}


Activity.light = property(_activity_light)
Quote.followup = property(_quote_followup)
Calculation.is_approved = property(_is_approved)


class Notification(Base):
    """Benachrichtigung je Benutzer (Freigaben, Hinweise)."""
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(255))
    read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Attachment(Base):
    """Dokument zu einem Datensatz (Zeichnung, 3D-Daten, Anfrage, Lastenheft …)."""
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity: Mapped[str] = mapped_column(String(40), index=True)   # calculations | accounts | quotes | opportunities | app
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(120))
    size: Mapped[int] = mapped_column(Integer, default=0)
    doc_type: Mapped[str | None] = mapped_column(String(40))      # zeichnung | 3d | anfrage | lastenheft | pruefplan | sonstiges | logo
    revision: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(String(255))
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # nur ausgeblendet (Nachweis bleibt)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    uploaded_by = relationship("User", lazy="joined")


class AppSettings(Base):
    """Firmendaten und Angebotslayout (eine Zeile, id=1)."""
    __tablename__ = "app_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class PurchasedPart(TimestampMixin, Base):
    """Zukaufteil (Einlegeteile, Buchsen, Dichtungen, Schrauben, Etiketten …)."""
    __tablename__ = "purchased_parts"
    id: Mapped[int] = mapped_column(primary_key=True)
    part_no: Mapped[str | None] = mapped_column(String(60), index=True)
    name: Mapped[str] = mapped_column(String(200))
    supplier: Mapped[str | None] = mapped_column(String(150))
    supplier_part_no: Mapped[str | None] = mapped_column(String(80))
    price: Mapped[float] = mapped_column(Float, default=0)          # Preis je Preiseinheit
    price_basis: Mapped[int] = mapped_column(Integer, default=1)    # Preiseinheit: 1 oder 1000 Stück
    unit: Mapped[str | None] = mapped_column(String(20), default="Stk")
    moq: Mapped[float | None] = mapped_column(Float)                # Mindestbestellmenge
    lead_time_days: Mapped[int | None] = mapped_column(Integer)
    co2_kg_per_piece: Mapped[float | None] = mapped_column(Float)   # kg CO₂e je Stück (Lieferantenangabe)
    price_valid_from: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProcurementRequest(TimestampMixin, Base):
    """Beschaffungsvorgang für Werkzeug, Montagelinie, Vorrichtung, Prüfmittel … mit Lieferantenangeboten."""
    __tablename__ = "procurement_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str | None] = mapped_column(String(30), index=True)       # BA-2026-0001
    calculation_id: Mapped[int | None] = mapped_column(ForeignKey("calculations.id", ondelete="SET NULL"), index=True)
    kind: Mapped[str] = mapped_column(String(30), default="werkzeug")       # werkzeug | montagelinie | vorrichtung | pruefmittel | sonstiges
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="offen")        # offen | angefragt | entschieden | bestellt | abgebrochen
    spec: Mapped[dict | None] = mapped_column(JSON)                         # technische Eckdaten der Anfrage
    reply_by: Mapped[date | None] = mapped_column(Date)                     # Angebotsabgabe bis
    needed_by: Mapped[date | None] = mapped_column(Date)                    # benötigt bis (z. B. Bemusterung)
    note: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    decided_offer_id: Mapped[int | None] = mapped_column(Integer)
    decision_note: Mapped[str | None] = mapped_column(Text)
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_version: Mapped[int | None] = mapped_column(Integer)            # in Kalkulationsversion übernommen
    offers: Mapped[list["ProcurementOffer"]] = relationship(back_populates="request", cascade="all, delete-orphan",
                                                            order_by="ProcurementOffer.id", lazy="selectin")
    calculation: Mapped["Calculation | None"] = relationship(lazy="joined")


class ProcurementOffer(TimestampMixin, Base):
    """Angefragter Lieferant und sein Angebot."""
    __tablename__ = "procurement_offers"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("procurement_requests.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"))
    supplier_name: Mapped[str] = mapped_column(String(200))
    contact_email: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="angefragt")    # angefragt | angebot | abgesagt | gewaehlt | abgelehnt
    requested_at: Mapped[date | None] = mapped_column(Date)
    offer_no: Mapped[str | None] = mapped_column(String(60))
    offer_date: Mapped[date | None] = mapped_column(Date)
    price: Mapped[float | None] = mapped_column(Float)                      # Angebotspreis netto €
    lead_time_weeks: Mapped[float | None] = mapped_column(Float)            # Lieferzeit bis T0/Abnahme
    cavities: Mapped[int | None] = mapped_column(Integer)
    hot_runner: Mapped[str | None] = mapped_column(String(120))             # z. B. „HK 4-fach, Synventive“
    steel: Mapped[str | None] = mapped_column(String(120))
    tool_life_shots: Mapped[float | None] = mapped_column(Float)
    warranty: Mapped[str | None] = mapped_column(String(120))
    payment_terms: Mapped[str | None] = mapped_column(String(120))
    location: Mapped[str | None] = mapped_column(String(120))               # Fertigungsort / Land
    rating: Mapped[int | None] = mapped_column(Integer)                     # technische Bewertung 1 … 5
    note: Mapped[str | None] = mapped_column(Text)
    request: Mapped["ProcurementRequest"] = relationship(back_populates="offers")



class Site(TimestampMixin, Base):
    """Standort der Gruppe mit eigenen Sätzen (Abweichungen von den Gruppen-Parametern)."""
    __tablename__ = "sites"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(60))
    address: Mapped[str | None] = mapped_column(String(200))
    settings: Mapped[dict | None] = mapped_column(JSON)     # nur abweichende Parameter, z. B. {"labor_rate_h": 19}
    sort: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ChangeRequest(TimestampMixin, Base):
    """Änderungsprotokoll: Änderungswünsche und Fehlermeldungen aus Tests (z. B. REV01) – nachverfolgbar bis zur Prüfung."""
    __tablename__ = "change_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(30), unique=True, index=True)   # REV01-B01, WUN-0001
    revision: Mapped[str | None] = mapped_column(String(20), index=True)    # REV01
    area: Mapped[str | None] = mapped_column(String(60))                    # Bereich, z. B. Kalkulation
    kind: Mapped[str] = mapped_column(String(40), default="wunsch")          # fehler | wunsch | doku | Freitext
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)                   # Wortlaut der Anforderung
    priority: Mapped[str] = mapped_column(String(10), default="mittel")      # hoch | mittel | niedrig
    phase: Mapped[int | None] = mapped_column(Integer)                      # Umsetzungsphase 1–4
    status: Mapped[str] = mapped_column(String(20), default="offen")        # offen | in_arbeit | umgesetzt | geprueft | nachbessern | abgelehnt | zurueckgestellt
    solution: Mapped[str | None] = mapped_column(Text)                      # Umsetzung (was wurde wie gelöst)
    req_ids: Mapped[str | None] = mapped_column(String(200))                # Lastenheft-IDs
    version: Mapped[str | None] = mapped_column(String(20))                 # umgesetzt in Lastenheft-Version
    test_steps: Mapped[str | None] = mapped_column(Text)                    # Prüfanweisung
    test_result: Mapped[str | None] = mapped_column(Text)                   # Prüfergebnis / Anmerkung Prüfer
    tested_by: Mapped[str | None] = mapped_column(String(120))
    tested_at: Mapped[date | None] = mapped_column(Date)
    requested_by: Mapped[str | None] = mapped_column(String(120))



# ====================================================================== Preisliste (lebende VK-Preisliste)
class PriceArticle(TimestampMixin, Base):
    """Verkaufsartikel je Kunde mit aktuellem Preis je Preiseinheit, Materialien und Zukaufteilen."""
    __tablename__ = "price_articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), index=True)
    article_no: Mapped[str | None] = mapped_column(String(60), index=True)        # F&R-Artikelnummer
    customer_part_no: Mapped[str | None] = mapped_column(String(80), index=True)  # Part Number of Contract Product
    description: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(80))                      # Fertigungsort / Land
    site_id: Mapped[int | None] = mapped_column(Integer)
    price_unit: Mapped[int] = mapped_column(Integer, default=100)                 # Preis je n Stück
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    price: Mapped[float] = mapped_column(Float, default=0)                        # aktueller Preis je Preiseinheit
    price_valid_from: Mapped[date | None] = mapped_column(Date)
    forecast_qty: Mapped[float | None] = mapped_column(Float)                     # Planmenge (Stk/Jahr)
    qty_last_year: Mapped[float | None] = mapped_column(Float)
    revenue_last_year: Mapped[float | None] = mapped_column(Float)
    moq: Mapped[float | None] = mapped_column(Float)
    shot_weight_g: Mapped[float | None] = mapped_column(Float)                    # Schussgewicht je Teil (inkl. Anguss)
    part_weight_g: Mapped[float | None] = mapped_column(Float)                    # Teilgewicht netto
    mgk_pct: Mapped[float | None] = mapped_column(Float, default=8)               # MGK auf Materialdifferenz
    surcharge_pct: Mapped[float | None] = mapped_column(Float, default=0)         # Nachkalkulations-Zuschlag (NK) %
    ratio_per_unit: Mapped[float | None] = mapped_column(Float, default=0)        # Rationalisierung je Preiseinheit (negativ = Nachlass)
    contract_bound: Mapped[bool | None] = mapped_column(Boolean, default=False)   # Preisbindung laut Vertrag
    contract_until: Mapped[date | None] = mapped_column(Date)
    contract_note: Mapped[str | None] = mapped_column(String(255))                # „Vertrag“ (z. B. Preisgleitklausel, Festpreis bis …)
    calculation_id: Mapped[int | None] = mapped_column(Integer)                   # Herkunft Kalkulation
    comment: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    account = relationship("Account", lazy="joined")
    materials = relationship("PriceArticleMaterial", cascade="all, delete-orphan", lazy="selectin",
                             order_by="PriceArticleMaterial.position")
    parts = relationship("PriceArticlePart", cascade="all, delete-orphan", lazy="selectin", order_by="PriceArticlePart.position")


class PriceArticleMaterial(Base):
    """Material im Artikel. price_basis = Materialpreis (€/kg), der im aktuellen Artikelpreis steckt."""
    __tablename__ = "price_article_materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("price_articles.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=1)
    material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id", ondelete="SET NULL"), index=True)
    name: Mapped[str | None] = mapped_column(String(160))           # Freitext, falls nicht in den Stammdaten
    weight_g: Mapped[float | None] = mapped_column(Float)           # Einsatzgewicht je Teil (g), bei Material 1 meist Schussgewicht
    price_basis: Mapped[float | None] = mapped_column(Float)        # €/kg im aktuellen Preis
    material = relationship("Material", lazy="joined")


class PriceArticlePart(Base):
    """Zukaufteil im Artikel; price_basis = Stückpreis, der im aktuellen Artikelpreis steckt."""
    __tablename__ = "price_article_parts"
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("price_articles.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(160))
    qty_per_part: Mapped[float] = mapped_column(Float, default=1)
    price_basis: Mapped[float | None] = mapped_column(Float)        # €/Stk im aktuellen Preis
    current_price: Mapped[float | None] = mapped_column(Float)      # aktueller Einkaufspreis €/Stk
    supplier: Mapped[str | None] = mapped_column(String(120))


class PriceArticleHistory(Base):
    """Preishistorie je Artikel (jede Preisänderung, Import, Erstanlage)."""
    __tablename__ = "price_article_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("price_articles.id", ondelete="CASCADE"), index=True)
    price: Mapped[float] = mapped_column(Float)
    old_price: Mapped[float | None] = mapped_column(Float)
    price_unit: Mapped[int] = mapped_column(Integer, default=100)
    valid_from: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(20))                 # erstanlage | import | preisaenderung | manuell
    note: Mapped[str | None] = mapped_column(Text)
    change_id: Mapped[int | None] = mapped_column(Integer, index=True)
    created_by_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MaterialPriceHistory(Base):
    """Preishistorie je Material (€/kg)."""
    __tablename__ = "material_price_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), index=True)
    price_per_kg: Mapped[float] = mapped_column(Float)
    old_price: Mapped[float | None] = mapped_column(Float)
    valid_from: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(20))                 # manuell | import | stammdaten | preisliste
    note: Mapped[str | None] = mapped_column(Text)
    change_id: Mapped[int | None] = mapped_column(Integer, index=True)
    created_by_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PriceChange(TimestampMixin, Base):
    """Preisänderungsvorgang: neuer Materialpreis (manuell/Import) oder Import VK-Preise – mit betroffenen Artikeln."""
    __tablename__ = "price_changes"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True)   # PA26-0001
    kind: Mapped[str] = mapped_column(String(20))                   # material | material_import | vk_import | manuell
    title: Mapped[str] = mapped_column(String(200))
    valid_from: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    details: Mapped[list | None] = mapped_column(JSON)             # z. B. geänderte Materialien [{id, name, old, new}]
    created_by_id: Mapped[int | None] = mapped_column(Integer)
    impacts = relationship("PriceImpact", cascade="all, delete-orphan", lazy="selectin", order_by="PriceImpact.id")


class PriceImpact(Base):
    """Betroffener Artikel in einem Preisänderungsvorgang mit Kennzeichnung, ob an den Kunden weitergegeben."""
    __tablename__ = "price_impacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    change_id: Mapped[int] = mapped_column(ForeignKey("price_changes.id", ondelete="CASCADE"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("price_articles.id", ondelete="CASCADE"), index=True)
    old_price: Mapped[float | None] = mapped_column(Float)          # Preis je PE vor der Änderung
    delta: Mapped[float] = mapped_column(Float, default=0)          # Δ je Preiseinheit (berechnet bzw. aus Import)
    new_price: Mapped[float | None] = mapped_column(Float)          # Vorschlag bzw. importierter Preis
    annual_effect: Mapped[float | None] = mapped_column(Float)      # Δ × Planmenge
    detail: Mapped[list | None] = mapped_column(JSON)               # Aufschlüsselung je Material / Zukaufteil
    status: Mapped[str] = mapped_column(String(30), default="offen")  # offen | weitergegeben | vertraglich_gebunden | sonstiges
    note: Mapped[str | None] = mapped_column(Text)
    passed_price: Mapped[float | None] = mapped_column(Float)       # tatsächlich an Kunden weitergegebener Preis je PE
    effective_date: Mapped[date | None] = mapped_column(Date)
    decided_by_id: Mapped[int | None] = mapped_column(Integer)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    article = relationship("PriceArticle", lazy="joined")
