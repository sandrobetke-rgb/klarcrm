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
