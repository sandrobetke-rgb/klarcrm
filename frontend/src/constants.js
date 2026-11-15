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
  { value: 'kein_angebot', label: 'Kein Angebot abgegeben', tone: 'neutral' },
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
  operator_factor: ['Bediener-Anteil (Faktor)', '× 100 = %'], handling_pct: ['Anteil Handling', '%'], handling_rate_h: ['Lohnsatz Handling', '€/h'],
  automation_pct: ['Anteil Automatisierung', '%'], automation_rate_h: ['Lohnsatz Automatisierung', '€/h'],
  setup_staff_min: ['Einrichter-Zeit je Rüstvorgang', 'min'], automation_setup_min: ['Automatisierer-Zeit je Rüstvorgang', 'min'], labor_rate_h: ['Lohnsatz Bediener', '€/h'],
  setup_time_h: ['Rüstzeit je Los', 'h'], setup_persons: ['Einrichter je Rüstvorgang', 'Pers.'], setup_rate_h: ['Lohnsatz Einrichter', '€/h'],
  startup_scrap_pcs: ['Anfahrausschuss je Los', 'Stk'],
  assembly_time_s: ['Montagezeit je Stück', 's'], assembly_persons: ['Montage-Personen', 'Pers.'], assembly_rate_h: ['Lohnsatz Montage', '€/h'],
  assembly_productivity_pct: ['Produktivität Montage', '%'],
  mgk_pct: ['Materialgemeinkosten', '%'], fgk_pct: ['Fertigungsgemeinkosten', '%'], scrap_pct: ['Ausschuss', '%'],
  vwgk_pct: ['Verwaltungsgemeinkosten', '%'], vtgk_pct: ['Vertriebsgemeinkosten', '%'], pm_pct: ['Projektmanagement', '%'],
  quality_pct: ['Qualität', '%'], quality_base: ['Basis Qualität', ''], toolshop_pct: ['Werkzeugbau', '%'], toolshop_base: ['Basis Werkzeugbau', ''],
  profit_pct: ['Gewinn', '%'], cash_discount_pct: ['Skonto', '%'], rebate_pct: ['Rabatt', '%'], price_override: ['Verkaufspreis manuell', '€/Stk'],
  lot_tiers: ['Staffel-Losgrößen', 'Stk'], volume_tiers: ['Staffel-Jahresmengen', 'Stk'],
  components: ['Weitere Komponenten', ''], operations: ['Weitere Arbeitsgänge', ''], purchased_items: ['Zukaufteile (Liste)', ''], purchased_mgk_pct: ['MGK Zukaufteile', '%'],
  price_reductions: ['Jahresabschläge Serienpreis', '% ab Jahr 2'], side_price_reductions: ['Jahresabschläge Zukaufteile NK', '% ab Jahr 2'],
  price_reductions_basis: ['Bezug Jahresabschläge', ''], price_reductions_preload: ['Abschläge vorab eingerechnet', ''], price_reductions_preload_mode: ['Vorab-Einrechnung', ''],
  preseries_qty: ['Vorserienmenge', 'Stk'], preseries_price_manual: ['Vorserienpreis fest', '€/Stk'],
  price_year1_mode: ['Preis Jahr 1', ''], energy_price_kwh: ['Strompreis', '€/kWh'], price_year1_manual: ['Preis Jahr 1 manuell', '€/Stk'], preseries_lot: ['Losgröße Vorserie', 'Stk'], preseries_setup_h: ['Rüstzeit Vorserie', 'h'],
  preseries_productivity_pct: ['Produktivität Vorserie', '%'], preseries_scrap_pct: ['Ausschuss Vorserie', '%'], preseries_surcharge_pct: ['Aufschlag Vorserie', '%'],
  side_mgk_pct: ['MGK Nebenkalkulation', '%'], side_quality_pct: ['Qualität Nebenkalkulation', '%'], side_scrap_pct: ['Ausschuss Nebenkalkulation', '%'], side_markup_pct: ['Aufschlag Nebenkalkulation', '%'], family_share_pct: ['Anteil Familienwerkzeug', '%'], family_group: ['Familienwerkzeug', ''],
  amort_quantity: ['Amortisation über', 'Stk'],
  pack_mode: ['Verpackung – Art der Eingabe', ''], pack_pct: ['Verpackung pauschal', '% auf HK'],
  pack_type: ['Verpackungsart', ''], pack_parts_per_unit: ['Teile je VE', 'Stk'], pack_cost_per_unit: ['Kosten je VE', '€'],
  pack_reusable: ['Mehrweg', ''], pack_time_s: ['Packzeit je VE', 's'], pack_units_per_pallet: ['VE je Palette', ''],
  co2_material_kg_kg: ['CO₂ Material', 'kg CO₂e/kg'], co2_masterbatch_kg_kg: ['CO₂ Masterbatch', 'kg CO₂e/kg'],
  machine_power_kw: ['Leistung Maschine', 'kW'], co2_grid_kg_kwh: ['Strom-Emissionsfaktor', 'kg CO₂e/kWh'],
  co2_scope1_kg_h: ['Werksemissionen', 'kg CO₂e/h'], co2_purchased_parts: ['CO₂ Zukaufteile', 'kg/Stk'],
  co2_pack_per_unit: ['CO₂ Verpackung je VE', 'kg'], transport_km: ['Transportentfernung', 'km'],
  co2_transport_kg_tkm: ['CO₂ Transport', 'kg/tkm'], co2_on_quote: ['CO₂ im Angebot', ''],
  incoterm: ['Lieferbedingung', ''], transport_mode: ['Transportkosten-Art', ''], transport_cost_per_pallet: ['Fracht je Palette', '€'],
  transport_cost_per_delivery: ['Kosten je Lieferung', '€'], transport_deliveries_per_year: ['Lieferungen p. a.', ''], transport_pct: ['Transport', '% auf HK'],
  extras: ['Zusatzpositionen', ''], one_time: ['Einmalkosten (Werkzeug …)', ''],
}
export const fix4 = (v) => n4.format(Number(v || 0))

export const CALL_RESULTS = [
  { value: 'nicht_erreicht', label: 'Nicht erreicht', tone: 'neutral' },
  { value: 'rueckruf_vereinbart', label: 'Rückruf vereinbart', tone: 'info' },
  { value: 'kunde_entscheidet_noch', label: 'Kunde entscheidet noch', tone: 'info' },
  { value: 'preis_nachverhandeln', label: 'Preis nachverhandeln', tone: 'warning' },
  { value: 'neu_kalkulieren', label: 'Neu kalkulieren / Änderung', tone: 'warning' },
  { value: 'auftrag_in_aussicht', label: 'Auftrag in Aussicht', tone: 'good' },
  { value: 'auftrag_erhalten', label: 'Auftrag erhalten', tone: 'good' },
  { value: 'absage', label: 'Absage', tone: 'critical' },
  { value: 'sonstiges', label: 'Sonstiges', tone: 'neutral' },
]
export const callResult = (v) => CALL_RESULTS.find((r) => r.value === v) || { label: v, tone: 'neutral' }

export const BRAND = { name: 'SB Thinkworks', claim: 'built with clarity', year: new Date().getFullYear() }

export const FEASIBILITY = [
  { value: 'herstellbar', label: 'Herstellbar', tone: 'good' },
  { value: 'bedingt_herstellbar', label: 'Bedingt herstellbar', tone: 'info' },
  { value: 'anpassungen_erforderlich', label: 'Anpassungen erforderlich', tone: 'warning' },
  { value: 'nicht_herstellbar', label: 'Nicht herstellbar', tone: 'critical' },
]
export const feasibility = (v) => FEASIBILITY.find((f) => f.value === v)

export const NO_BID_REASONS = [
  { value: 'mengen_zu_klein', label: 'Mengen zu klein' },
  { value: 'artikel_zu_klein', label: 'Artikel zu klein' },
  { value: 'artikel_zu_gross', label: 'Artikel zu groß' },
  { value: 'keine_maschine_kapazitaet', label: 'Keine Maschine / Kapazität' },
  { value: 'nicht_herstellbar', label: 'Nicht herstellbar' },
  { value: 'technologie_passt_nicht', label: 'Technologie passt nicht' },
  { value: 'termin_nicht_machbar', label: 'Termin nicht machbar' },
  { value: 'sonstiges', label: 'Sonstiges (Freitext)' },
]
export const noBidLabel = (v) => NO_BID_REASONS.find((r) => r.value === v)?.label || v || ''
export const CLOSED_STATUS = ['gewonnen', 'verloren', 'kein_angebot', 'zurueckgestellt']

export const MACHINE_KINDS = [
  { value: 'spritzguss', label: 'Spritzgießmaschine' },
  { value: 'montage', label: 'Montagelinie / Montageplatz' },
  { value: 'nachbearbeitung', label: 'Nachbearbeitung (Schweißen, Drucken, Entgraten …)' },
  { value: 'pruefung', label: 'Prüfstation' },
  { value: 'sonstige', label: 'Sonstige Anlage' },
]
export const machineKindLabel = (k) => (MACHINE_KINDS.find((x) => x.value === k)?.label || 'Spritzgießmaschine').split(' (')[0]
