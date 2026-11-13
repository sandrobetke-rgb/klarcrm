import { ACCOUNT_TYPES, ACTIVITY_TYPES, QUOTE_STATUS, STAGES } from './constants'

export const accountFields = [
  { name: 'name', label: 'Firmenname', required: true, span: true },
  { name: 'type', label: 'Typ', type: 'select', options: ACCOUNT_TYPES, required: true },
  { name: 'industry', label: 'Branche' },
  { name: 'phone', label: 'Telefon' },
  { name: 'email', label: 'E-Mail', type: 'email' },
  { name: 'website', label: 'Website', span: true },
  { name: 'street', label: 'Straße', span: true },
  { name: 'zip', label: 'PLZ' },
  { name: 'city', label: 'Ort' },
  { name: 'country', label: 'Land' },
  { name: 'owner_id', label: 'Verantwortlich', type: 'user' },
  { name: 'notes', label: 'Notizen', type: 'textarea', span: true },
]

export const contactFields = [
  { name: 'salutation', label: 'Anrede', type: 'select', options: [
    { value: 'Herr', label: 'Herr' }, { value: 'Frau', label: 'Frau' }, { value: 'Divers', label: 'Divers' }] },
  { name: 'account_id', label: 'Firma', type: 'account' },
  { name: 'first_name', label: 'Vorname', required: true },
  { name: 'last_name', label: 'Nachname', required: true },
  { name: 'position', label: 'Position' },
  { name: 'email', label: 'E-Mail', type: 'email' },
  { name: 'phone', label: 'Telefon' },
  { name: 'mobile', label: 'Mobil' },
  { name: 'owner_id', label: 'Verantwortlich', type: 'user' },
  { name: 'notes', label: 'Notizen', type: 'textarea', span: true },
]

export const opportunityFields = [
  { name: 'name', label: 'Bezeichnung', required: true, span: true },
  { name: 'account_id', label: 'Firma', type: 'account', required: true },
  { name: 'contact_id', label: 'Ansprechpartner', type: 'contact', dependsOn: 'account_id' },
  { name: 'stage', label: 'Phase', type: 'select', required: true, options: STAGES.map((s) => ({ value: s.key, label: s.label })) },
  { name: 'amount', label: 'Volumen (€ netto)', type: 'number', step: '0.01', min: 0 },
  { name: 'probability', label: 'Wahrscheinlichkeit %', type: 'number', min: 0, max: 100, hint: 'Leer lassen = automatisch je Phase' },
  { name: 'close_date', label: 'Erw. Abschluss', type: 'date' },
  { name: 'source', label: 'Quelle', hint: 'z. B. Messe, Website, Empfehlung' },
  { name: 'owner_id', label: 'Verantwortlich', type: 'user' },
  { name: 'lost_reason', label: 'Verlustgrund (falls verloren)', span: true },
  { name: 'description', label: 'Beschreibung', type: 'textarea', span: true },
]

export const activityFields = [
  { name: 'type', label: 'Art', type: 'select', required: true, options: ACTIVITY_TYPES },
  { name: 'due_at', label: 'Fällig am', type: 'datetime' },
  { name: 'subject', label: 'Betreff', required: true, span: true },
  { name: 'account_id', label: 'Firma', type: 'account' },
  { name: 'contact_id', label: 'Kontakt', type: 'contact', dependsOn: 'account_id' },
  { name: 'opportunity_id', label: 'Verkaufschance', type: 'opportunity', dependsOn: 'account_id' },
  { name: 'owner_id', label: 'Zuständig', type: 'user' },
  { name: 'description', label: 'Beschreibung / Ergebnis', type: 'textarea', span: true },
  { name: 'done', label: 'Erledigt', type: 'checkbox' },
]

export const quoteHeadFields = [
  { name: 'title', label: 'Titel', required: true, span: true },
  { name: 'account_id', label: 'Firma', type: 'account', required: true },
  { name: 'contact_id', label: 'Ansprechpartner', type: 'contact', dependsOn: 'account_id' },
  { name: 'opportunity_id', label: 'Verkaufschance', type: 'opportunity', dependsOn: 'account_id' },
  { name: 'status', label: 'Status', type: 'select', required: true, options: QUOTE_STATUS },
]
