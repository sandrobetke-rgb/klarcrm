export const STAGES = [
  { key: 'lead', label: 'Lead' },
  { key: 'qualifiziert', label: 'Qualifiziert' },
  { key: 'angebot', label: 'Angebot' },
  { key: 'verhandlung', label: 'Verhandlung' },
  { key: 'gewonnen', label: 'Gewonnen' },
  { key: 'verloren', label: 'Verloren' },
]
export const stageLabel = (k) => STAGES.find((s) => s.key === k)?.label || k

export const ACCOUNT_TYPES = [
  { value: 'interessent', label: 'Interessent' },
  { value: 'kunde', label: 'Kunde' },
  { value: 'partner', label: 'Partner' },
  { value: 'lieferant', label: 'Lieferant' },
]

export const ACTIVITY_TYPES = [
  { value: 'anruf', label: 'Anruf', icon: '☎' },
  { value: 'termin', label: 'Termin', icon: '◷' },
  { value: 'email', label: 'E-Mail', icon: '✉' },
  { value: 'aufgabe', label: 'Aufgabe', icon: '✓' },
  { value: 'notiz', label: 'Notiz', icon: '✎' },
]
export const activityType = (v) => ACTIVITY_TYPES.find((t) => t.value === v) || { label: v, icon: '•' }

export const QUOTE_STATUS = [
  { value: 'entwurf', label: 'Entwurf' },
  { value: 'versendet', label: 'Versendet' },
  { value: 'angenommen', label: 'Angenommen' },
  { value: 'abgelehnt', label: 'Abgelehnt' },
]

export const ROLES = [
  { value: 'admin', label: 'Administrator' },
  { value: 'vertrieb', label: 'Vertrieb' },
  { value: 'gesellschafter', label: 'Gesellschafter (nur lesen)' },
]

const eurFmt = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
const eurFmt2 = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' })
export const eur = (v, exact = false) => (exact ? eurFmt2 : eurFmt).format(Number(v || 0))
export const eurShort = (v) => {
  const n = Number(v || 0)
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toLocaleString('de-DE', { maximumFractionDigits: 1 })} Mio €`
  if (Math.abs(n) >= 1e3) return `${(n / 1e3).toLocaleString('de-DE', { maximumFractionDigits: 0 })} T€`
  return eur(n)
}
export const fmtDate = (d) => (d ? new Date(d).toLocaleDateString('de-DE') : '–')
export const fmtDateTime = (d) =>
  d ? new Date(d).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }) : '–'
export const contactName = (c) => (c ? `${c.first_name} ${c.last_name}` : '')

// ---------- Kalkulation ----------
export const CALC_STATUS = [
  { value: 'anfrage', label: 'Anfrage', tone: 'neutral' },
  { value: 'kalkulation', label: 'In Kalkulation', tone: 'info' },
  { value: 'angeboten', label: 'Angeboten', tone: 'info' },
  { value: 'verhandlung', label: 'Verhandlung', tone: 'info' },
  { value: 'gewonnen', label: 'Gewonnen', tone: 'good' },
  { value: 'verloren', label: 'Verloren', tone: 'critical' },
  { value: 'zurueckgestellt', label: 'Zurückgestellt', tone: 'neutral' },
]
export const calcStatus = (v) => CALC_STATUS.find((s) => s.value === v) || { label: v, tone: 'neutral' }

export const CLOSE_REASONS = [
  { value: 'artikelpreis_zu_hoch', label: 'Artikelpreis zu hoch' },
  { value: 'werkzeug_zu_teuer', label: 'Werkzeug zu teuer' },
  { value: 'investition_zu_teuer', label: 'Investition zu teuer' },
  { value: 'projekt_kunde_nicht_gewonnen', label: 'Kunde hat Projekt nicht gewonnen' },
  { value: 'projekt_eingestellt', label: 'Projekt beim Kunden eingestellt' },
  { value: 'lieferzeit', label: 'Lieferzeit / Kapazität' },
  { value: 'technik', label: 'Technisch nicht machbar' },
  { value: 'sonstiges', label: 'Sonstiges' },
]
export const reasonLabel = (v) => CLOSE_REASONS.find((r) => r.value === v)?.label || v || ''

const n4 = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
const n2 = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
export const eur4 = (v) => `${n4.format(Number(v || 0))} €`
export const num2 = (v) => n2.format(Number(v || 0))
export const num = (v, d = 0) => Number(v || 0).toLocaleString('de-DE', { maximumFractionDigits: d })

export const LIGHTS = {
  gruen: { label: 'Grün', cls: 'light-green', text: 'im Plan' },
  gelb: { label: 'Gelb', cls: 'light-yellow', text: 'leicht über Plan' },
  rot: { label: 'Rot', cls: 'light-red', text: 'deutlich über Plan / Verlust' },
}

// Beschriftung aller Kalkulations-Eingaben (für Versionsvergleich und Nachkalkulation)
export const INPUT_LABELS = {
  annual_volume: ['Jahresmenge', 'Stk'], lot_size: ['Losgröße', 'Stk'], project_years: ['Projektlaufzeit', 'Jahre'],
  material_name: ['Material', ''], material_price_kg: ['Materialpreis', '€/kg'], part_weight_g: ['Teilgewicht', 'g'],
  sprue_weight_g: ['Angussgewicht je Schuss', 'g'], regrind_pct: ['Mahlgutanteil Anguss', '%'],
  masterbatch_pct: ['Masterbatch-Anteil', '%'], masterbatch_price_kg: ['Masterbatch-Preis', '€/kg'],
  purchased_parts: ['Zukaufteile je Stück', '€'],
  machine_name: ['Maschine', ''], machine_rate_h: ['Maschinenstundensatz', '€/h'], maintenance_rate_h: ['Instandhaltung', '€/h'],
  cycle_time_s: ['Zykluszeit', 's'], cavities: ['Fachzahl', ''], productivity_pct: ['Produktivität / Nutzungsgrad', '%'],
  operator_factor: ['Bedienfaktor', 'Pers./Masch.'], labor_rate_h: ['Lohnsatz Bediener', '€/h'],
  setup_time_h: ['Rüstzeit je Los', 'h'], setup_persons: ['Einrichter je Rüstvorgang', 'Pers.'], setup_rate_h: ['Lohnsatz Einrichter', '€/h'],
  startup_scrap_pcs: ['Anfahrausschuss je Los', 'Stk'],
  assembly_time_s: ['Montagezeit je Stück', 's'], assembly_persons: ['Montage-Personen', 'Pers.'], assembly_rate_h: ['Lohnsatz Montage', '€/h'],
  assembly_productivity_pct: ['Produktivität Montage', '%'],
  mgk_pct: ['Materialgemeinkosten', '%'], fgk_pct: ['Fertigungsgemeinkosten', '%'], scrap_pct: ['Ausschuss', '%'],
  vwgk_pct: ['Verwaltungsgemeinkosten', '%'], vtgk_pct: ['Vertriebsgemeinkosten', '%'], pm_pct: ['Projektmanagement', '%'],
  profit_pct: ['Gewinn', '%'], cash_discount_pct: ['Skonto', '%'], rebate_pct: ['Rabatt', '%'], price_override: ['Verkaufspreis manuell', '€/Stk'],
  extras: ['Zusatzpositionen', ''], one_time: ['Einmalkosten (Werkzeug …)', ''],
}
export const fix4 = (v) => n4.format(Number(v || 0))
