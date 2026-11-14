from datetime import date, datetime, timezone

from sqlalchemy import (
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now():
    return datetime.now(timezone.utc)


ROLES = ("admin", "vertrieb", "gesellschafter")
STAGES = ("lead", "qualifiziert", "angebot", "verhandlung", "gewonnen", "verloren")
STAGE_PROBABILITY = {
    "lead": 10, "qualifiziert": 25, "angebot": 50,
    "verhandlung": 75, "gewonnen": 100, "verloren": 0,
}
ACTIVITY_TYPES = ("anruf", "termin", "email", "aufgabe", "notiz")
QUOTE_STATUS = ("entwurf", "versendet", "angenommen", "abgelehnt")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="vertrieb")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


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
    first_name: Mapped[str] = mapped_column(String(100))
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
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

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

    account = relationship("Account", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    opportunity = relationship("Opportunity", lazy="joined")
    owner = relationship("User", lazy="joined")


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

    account = relationship("Account", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    opportunity = relationship("Opportunity", lazy="joined")
    owner = relationship("User", lazy="joined")
    items = relationship(
        "QuoteItem", back_populates="quote", cascade="all, delete-orphan",
        order_by="QuoteItem.position", lazy="selectin",
    )

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
    description: Mapped[str] = mapped_column(String(500))
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
    "projekt_kunde_nicht_gewonnen", "projekt_eingestellt", "lieferzeit", "technik", "sonstiges",
)


class Machine(TimestampMixin, Base):
    """Maschinen-Stammdaten mit Standard-Stundensätzen."""
    __tablename__ = "machines"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str | None] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    clamping_force_t: Mapped[float | None] = mapped_column(Float)
    hourly_rate: Mapped[float] = mapped_column(Float, default=0)        # Maschinenstundensatz €/h (ohne Personal)
    maintenance_rate: Mapped[float] = mapped_column(Float, default=0)   # Instandhaltung €/h
    productivity_pct: Mapped[float] = mapped_column(Float, default=85)  # Nutzungsgrad / Produktivität
    operator_factor: Mapped[float] = mapped_column(Float, default=0.3)  # Personen je Maschine
    location: Mapped[str | None] = mapped_column(String(80))
    available_hours_year: Mapped[float | None] = mapped_column(Float, default=6000)  # verfügbare Std/Jahr (Schichtmodell)
    base_load_pct: Mapped[float | None] = mapped_column(Float, default=0)          # Grundauslastung Bestandsaufträge %
    base_load_decline_pct: Mapped[float | None] = mapped_column(Float, default=0)  # Auslauf Bestand je Jahr %
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Material(TimestampMixin, Base):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))          # z. B. PA6 GF30 schwarz
    family: Mapped[str | None] = mapped_column(String(40))  # PA6, PP, ABS ...
    supplier: Mapped[str | None] = mapped_column(String(120))
    price_per_kg: Mapped[float] = mapped_column(Float, default=0)
    density: Mapped[float | None] = mapped_column(Float)
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
    remark: Mapped[str | None] = mapped_column(Text)
    last_call_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inquiry_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)              # Angebotsabgabe bis
    sop_date: Mapped[date | None] = mapped_column(Date)              # Serienstart (SOP)
    sync_opportunity: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # Machbarkeit / kein Angebot / Artikelanalyse
    feasibility: Mapped[str | None] = mapped_column(String(40))
    feasibility_note: Mapped[str | None] = mapped_column(Text)
    no_bid_reason: Mapped[str | None] = mapped_column(String(40))
    no_bid_note: Mapped[str | None] = mapped_column(Text)
    analysis: Mapped[dict | None] = mapped_column(JSON)
    analysis_results: Mapped[dict | None] = mapped_column(JSON)
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
    owner = relationship("User", lazy="joined")
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
