from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "vertrieb", "gesellschafter"]
Stage = Literal["lead", "qualifiziert", "angebot", "verhandlung", "gewonnen", "verloren"]
ActivityType = Literal["anruf", "termin", "email", "aufgabe", "notiz"]
QuoteStatus = Literal["entwurf", "versendet", "angenommen", "abgelehnt"]
AccountType = Literal["interessent", "kunde", "partner", "lieferant"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Referenzen (für Listen) ----------
class UserRef(ORM):
    id: int
    name: str


class AccountRef(ORM):
    id: int
    name: str


class ContactRef(ORM):
    id: int
    salutation: str | None = None
    first_name: str
    last_name: str


class OpportunityRef(ORM):
    id: int
    name: str


# ---------- Auth / Benutzer ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    role: Role = "vertrieb"
    active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    role: Role | None = None
    active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class UserOut(ORM, UserBase):
    id: int
    created_at: datetime


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


# ---------- Firmen ----------
class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: AccountType = "interessent"
    industry: str | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    street: str | None = None
    zip: str | None = None
    city: str | None = None
    country: str | None = "Deutschland"
    notes: str | None = None
    owner_id: int | None = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(AccountBase):
    name: str | None = None
    type: AccountType | None = None


class AccountOut(ORM, AccountBase):
    id: int
    owner: UserRef | None = None
    created_at: datetime
    updated_at: datetime


# ---------- Kontakte ----------
class ContactBase(BaseModel):
    account_id: int | None = None
    salutation: str | None = None
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    notes: str | None = None
    owner_id: int | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    first_name: str | None = None
    last_name: str | None = None


class ContactOut(ORM, ContactBase):
    id: int
    account: AccountRef | None = None
    owner: UserRef | None = None
    created_at: datetime


# ---------- Verkaufschancen ----------
class OpportunityBase(BaseModel):
    name: str = Field(min_length=1)
    account_id: int | None = None
    contact_id: int | None = None
    stage: Stage = "lead"
    amount: float = 0
    probability: int | None = Field(default=None, ge=0, le=100)
    close_date: date | None = None
    source: str | None = None
    description: str | None = None
    lost_reason: str | None = None
    owner_id: int | None = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(OpportunityBase):
    name: str | None = None
    stage: Stage | None = None
    amount: float | None = None


class OpportunityOut(ORM, OpportunityBase):
    id: int
    probability: int
    closed_at: date | None = None
    account: AccountRef | None = None
    contact: ContactRef | None = None
    owner: UserRef | None = None
    created_at: datetime
    updated_at: datetime


# ---------- Aktivitäten ----------
class ActivityBase(BaseModel):
    type: ActivityType = "aufgabe"
    subject: str = Field(min_length=1)
    description: str | None = None
    due_at: datetime | None = None
    done: bool = False
    account_id: int | None = None
    contact_id: int | None = None
    opportunity_id: int | None = None
    owner_id: int | None = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(ActivityBase):
    type: ActivityType | None = None
    subject: str | None = None
    done: bool | None = None


class ActivityOut(ORM, ActivityBase):
    id: int
    account: AccountRef | None = None
    contact: ContactRef | None = None
    opportunity: OpportunityRef | None = None
    owner: UserRef | None = None
    created_at: datetime


# ---------- Angebote ----------
class QuoteItemIn(BaseModel):
    description: str = Field(min_length=1)
    quantity: float = 1
    unit: str = "Stk"
    unit_price: float = 0
    discount_pct: float = Field(default=0, ge=0, le=100)


class QuoteItemOut(ORM, QuoteItemIn):
    id: int
    position: int
    line_total: float


class QuoteBase(BaseModel):
    title: str = Field(min_length=1)
    account_id: int | None = None
    contact_id: int | None = None
    opportunity_id: int | None = None
    status: QuoteStatus = "entwurf"
    quote_date: date | None = None
    valid_until: date | None = None
    tax_rate: float | None = None
    intro_text: str | None = None
    terms: str | None = None
    owner_id: int | None = None


class QuoteCreate(QuoteBase):
    items: list[QuoteItemIn] = []


class QuoteUpdate(QuoteBase):
    title: str | None = None
    status: QuoteStatus | None = None
    items: list[QuoteItemIn] | None = None


class QuoteOut(ORM, QuoteBase):
    id: int
    number: str
    quote_date: date
    tax_rate: float
    items: list[QuoteItemOut]
    net_total: float
    tax_total: float
    gross_total: float
    account: AccountRef | None = None
    contact: ContactRef | None = None
    opportunity: OpportunityRef | None = None
    owner: UserRef | None = None
    created_at: datetime


class Page(BaseModel):
    total: int
    items: list


Token.model_rebuild()


# ---------- Kalkulation ----------
CalcStatus = Literal["anfrage", "kalkulation", "angeboten", "verhandlung", "gewonnen", "verloren", "zurueckgestellt"]
CloseReason = Literal["artikelpreis_zu_hoch", "werkzeug_zu_teuer", "investition_zu_teuer",
                      "projekt_kunde_nicht_gewonnen", "projekt_eingestellt", "lieferzeit", "technik", "sonstiges"]


class MachineBase(BaseModel):
    number: str | None = None
    name: str = Field(min_length=1)
    clamping_force_t: float | None = None
    hourly_rate: float = 0
    maintenance_rate: float = 0
    productivity_pct: float = 85
    operator_factor: float = 0.3
    location: str | None = None
    notes: str | None = None
    active: bool = True


class MachineUpdate(MachineBase):
    name: str | None = None


class MachineOut(ORM, MachineBase):
    id: int


class MaterialBase(BaseModel):
    name: str = Field(min_length=1)
    family: str | None = None
    supplier: str | None = None
    price_per_kg: float = 0
    density: float | None = None
    notes: str | None = None
    active: bool = True


class MaterialUpdate(MaterialBase):
    name: str | None = None


class MaterialOut(ORM, MaterialBase):
    id: int


class CalcMeta(BaseModel):
    article_name: str | None = None
    customer_article_no: str | None = None
    own_article_no: str | None = None
    account_id: int | None = None
    contact_id: int | None = None
    opportunity_id: int | None = None
    status: CalcStatus | None = None
    probability: int | None = Field(default=None, ge=0, le=100)
    close_reason: CloseReason | None = None
    remark: str | None = None
    last_call_at: datetime | None = None
    inquiry_date: date | None = None
    due_date: date | None = None
    sop_date: date | None = None
    sync_opportunity: bool | None = None
    owner_id: int | None = None


class CalcCreate(CalcMeta):
    article_name: str = Field(min_length=1)
    inputs: dict | None = None


class CalcVersionIn(BaseModel):
    inputs: dict
    change_note: str | None = None


class CalcVersionOut(ORM):
    id: int
    version_no: int
    change_note: str | None
    inputs: dict
    results: dict
    created_by: UserRef | None = None
    created_at: datetime


class PostCalcIn(BaseModel):
    version_no: int | None = None
    reference: str | None = None
    period_from: date | None = None
    period_to: date | None = None
    actuals: dict
    remark: str | None = None


class PostCalcOut(ORM):
    id: int
    version_no: int
    reference: str | None
    period_from: date | None
    period_to: date | None
    actuals: dict
    results: dict
    traffic_light: str
    remark: str | None
    created_by: UserRef | None = None
    created_at: datetime


class CallIn(BaseModel):
    result: Literal["nicht_erreicht", "rueckruf_vereinbart", "kunde_entscheidet_noch", "preis_nachverhandeln",
                    "neu_kalkulieren", "auftrag_in_aussicht", "auftrag_erhalten", "absage", "sonstiges"] = "sonstiges"
    note: str | None = None
    called_at: datetime | None = None
    contact_id: int | None = None
    follow_up: date | None = None


class CallOut(ORM):
    id: int
    called_at: datetime
    result: str
    note: str | None
    follow_up: date | None
    contact: ContactRef | None = None
    user: UserRef | None = None


class CalcOut(ORM, CalcMeta):
    id: int
    number: str
    article_name: str
    status: str
    probability: int
    sync_opportunity: bool
    current_version: int
    unit_price: float
    annual_volume: float
    annual_revenue: float
    one_time_revenue: float
    invest: float = 0
    margin_pct: float
    last_traffic_light: str | None = None
    last_call: CallOut | None = None
    account: AccountRef | None = None
    contact: ContactRef | None = None
    opportunity: OpportunityRef | None = None
    owner: UserRef | None = None
    created_at: datetime
    updated_at: datetime


class CalcDetail(CalcOut):
    calls: list[CallOut]
    versions: list[CalcVersionOut]
    post_calcs: list[PostCalcOut]
