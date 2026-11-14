import { fmtDateTime, INPUT_LABELS } from '../constants'

const FIELD_LABELS = {
  status: 'Status', probability: 'Wahrscheinlichkeit %', close_reason: 'Verlustgrund', no_bid_reason: 'Grund kein Angebot',
  no_bid_note: 'Erläuterung kein Angebot', feasibility: 'Machbarkeit', feasibility_note: 'Anmerkung Machbarkeit', remark: 'Bemerkung',
  article_name: 'Artikel', customer_article_no: 'Art.-Nr. Kunde', own_article_no: 'Eigene Art.-Nr.', account_id: 'Kunde (ID)',
  contact_id: 'Ansprechpartner (ID)', opportunity_id: 'Verkaufschance (ID)', owner_id: 'Verantwortlich (ID)', last_call_at: 'Zuletzt angerufen',
  current_version: 'Aktuelle Version', unit_price: 'Stückpreis €', annual_revenue: 'Umsatz p. a. €', annual_volume: 'Jahresmenge',
  one_time_revenue: 'Einmalumsatz €', margin_pct: 'Marge %', approval_status: 'Freigabestatus', approval_version: 'Freigabe für Version',
  approval_comment: 'Begründung Freigabeanfrage', approval_decision_comment: 'Kommentar Freigabe', approval_by_id: 'Freigegeben von (ID)',
  approval_at: 'Freigabezeitpunkt', approval_requested_by_id: 'Angefragt von (ID)', approval_requested_at: 'Anfragezeitpunkt',
  version_no: 'Version', change_note: 'Änderungsnotiz', inputs: 'Eingaben', results: 'Ergebnisse', created_by_id: 'Erstellt von (ID)',
  calculation_id: 'Kalkulation (ID)', called_at: 'Angerufen am', result: 'Ergebnis', note: 'Notiz', follow_up: 'Wiedervorlage', user_id: 'Benutzer (ID)',
  price_per_kg: 'Preis €/kg', valid_from: 'gültig ab', hourly_rate: 'Maschinenstundensatz €/h', maintenance_rate: 'Instandhaltung €/h',
  name: 'Name', email: 'E-Mail', role: 'Rolle', active: 'aktiv', can_approve: 'Freigabeberechtigung', password_hash: 'Passwort',
  number: 'Nummer', title: 'Titel', amount: 'Volumen €', stage: 'Phase', lifecycle: 'Lebensweg', analysis: 'Artikelanalyse',
  traffic_light: 'Ampel', reference: 'Referenz', data: 'Parameter', description: 'Beschreibung', quantity: 'Menge', unit: 'Einheit',
  discount_pct: 'Rabatt %', position: 'Position', quote_id: 'Angebot (ID)', valid_until: 'gültig bis', quote_date: 'Angebotsdatum',
}
const fieldLabel = (k) => FIELD_LABELS[k] || INPUT_LABELS[k]?.[0] || k

const fmt = (v) => {
  if (v === null || v === undefined || v === '') return '–'
  if (typeof v === 'boolean') return v ? 'ja' : 'nein'
  if (typeof v === 'number') return v.toLocaleString('de-DE', { maximumFractionDigits: 4 })
  if (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(v)) return fmtDateTime(v)
  return String(v)
}
const tone = { anlegen: 'good', ändern: 'info', löschen: 'critical' }

export default function AuditTable({ rows, showEntity = true }) {
  if (!rows?.length) return <div className="empty">Keine Einträge.</div>
  return (
    <table className="table audit-table">
      <thead><tr><th>Zeitpunkt</th><th>Benutzer</th><th>Aktion</th>{showEntity && <th>Datensatz</th>}<th>Änderungen (alt → neu)</th></tr></thead>
      <tbody>{rows.map((a) => (
        <tr key={a.id}>
          <td className="nowrap">{fmtDateTime(a.ts)}</td>
          <td>{a.user}</td>
          <td><span className={`badge badge-${tone[a.action] || 'neutral'}`}>{a.action}</span></td>
          {showEntity && <td>{a.entity_label}<br /><small className="muted">{a.label}</small></td>}
          <td className="audit-changes">{Object.entries(a.changes).slice(0, 12).map(([k, [o, n]]) => (
            <div key={k}><code title={k}>{fieldLabel(k)}</code>: {a.action === 'anlegen' ? fmt(n) : <>{fmt(o)} → <b>{fmt(n)}</b></>}</div>
          ))}{Object.keys(a.changes).length > 12 && <div className="muted">… {Object.keys(a.changes).length - 12} weitere</div>}</td>
        </tr>
      ))}</tbody>
    </table>
  )
}
