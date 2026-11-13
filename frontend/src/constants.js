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
