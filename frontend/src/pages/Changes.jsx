import { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import ListPage from '../components/ListPage'
import { Badge, ErrorBox, useFetch } from '../components/ui'

// Änderungsprotokoll (REV01-X01): Testrückmeldungen und Wünsche erfassen, abarbeiten und prüfen
export const CR_STATUS = [
  { value: 'eingereicht', label: 'Eingereicht – wartet auf Freigabe (Admin)', tone: 'neutral' },
  { value: 'freigegeben', label: 'Freigegeben zur Umsetzung', tone: 'info' },
  { value: 'offen', label: 'Offen', tone: 'neutral' },
  { value: 'in_arbeit', label: 'In Arbeit', tone: 'info' },
  { value: 'umgesetzt', label: 'Umgesetzt – bitte prüfen', tone: 'warning' },
  { value: 'geprueft', label: 'Geprüft ✓', tone: 'good' },
  { value: 'nachbessern', label: 'Nachbessern', tone: 'critical' },
  { value: 'zurueckgestellt', label: 'Zurückgestellt', tone: 'neutral' },
  { value: 'abgelehnt', label: 'Abgelehnt', tone: 'neutral' },
  { value: 'ueberholt', label: 'Überholt (ersetzt)', tone: 'neutral' },
]
const KIND = [{ value: 'fehler', label: 'Fehler' }, { value: 'wunsch', label: 'Wunsch' }, { value: 'doku', label: 'Dokumentation' }]
const kindLabel = (v) => KIND.find((k) => k.value === v)?.label || v || '–'
// Vorschläge – Art und Bereich sind frei eingebbar
const KIND_OPTIONS = ['Fehler', 'Wunsch', 'Dokumentation', 'Verbesserung', 'Frage', 'Schulung']
const AREAS = ['Allgemein', 'Dashboard', 'Pipeline', 'Anfrage', 'Artikelanalyse', 'Kalkulation', 'Zukaufteile', 'Material', 'Werkzeug',
  'Angebot', 'Angebotsdruck', 'Aktivitäten', 'Firmen', 'Kontakte', 'Beschaffung', 'Auslastung', 'Auswertungen', 'Stammdaten',
  'Standorte', 'Benutzer', 'Dokumentation']
const PRIO = [{ value: 'hoch', label: 'hoch' }, { value: 'mittel', label: 'mittel' }, { value: 'niedrig', label: 'niedrig' }]
const PHASES = [
  { value: '1', label: 'Phase 1 – Fehler & Sofortmaßnahmen' },
  { value: '2', label: 'Phase 2 – Anfrage → Angebot → Pipeline' },
  { value: '3', label: 'Phase 3 – Kalkulation erweitern (Blätter)' },
  { value: '4', label: 'Phase 4 – Beschaffung, Dashboard, Berichte' },
]
const st = (v) => CR_STATUS.find((s) => s.value === v) || CR_STATUS[0]

const fields = [
  { name: 'title', label: 'Titel', required: true, span: true },
  { name: 'kind', label: 'Art', type: 'combo', required: true, options: KIND_OPTIONS, hint: 'Auswahl oder eigene Eingabe' },
  { name: 'area', label: 'Bereich', type: 'combo', options: AREAS, hint: 'Auswahl oder eigene Eingabe' },
  { name: 'priority', label: 'Priorität', type: 'select', required: true, options: PRIO },
  { name: 'phase', label: 'Phase', type: 'select', options: PHASES },
  { name: 'description', label: 'Anforderung / Fehlerbeschreibung', type: 'textarea', rows: 4, span: true },
  { name: 'status', label: 'Status', type: 'select', required: true, options: CR_STATUS },
  { name: 'requested_by', label: 'Gemeldet von', hint: 'wird beim Anlegen automatisch mit dem angemeldeten Benutzer gefüllt' },
  { name: 'solution', label: 'Umsetzung (was wurde gelöst)', type: 'textarea', rows: 4, span: true },
  { name: 'test_steps', label: 'Prüfanweisung (Was tun)', type: 'textarea', rows: 3, span: true },
  { name: 'expected', label: 'Was herauskommen muss', type: 'textarea', rows: 3, span: true },
  { name: 'check_version', label: 'Prüfen mit Update', hint: 'z. B. 1.32 – erscheint dann auf der Seite „Prüfen“' },
  { name: 'check_link', label: 'Hinspringen (Seite im CRM)', hint: 'z. B. /pipeline' },
  { name: 'superseded_by', label: 'Überholt durch' },
  { name: 'test_result', label: 'Prüfergebnis / Anmerkung', type: 'textarea', rows: 3, span: true, hint: 'Bei Status „Nachbessern“ bitte beschreiben, was noch nicht passt' },
  { name: 'tested_by', label: 'Geprüft von', hint: 'wird beim Prüfergebnis automatisch gesetzt' },
  { name: 'tested_at', label: 'Geprüft am', type: 'date' },
  { name: 'req_ids', label: 'Lastenheft-ID(s)' },
  { name: 'version', label: 'Umgesetzt in Version' },
]

function Summary() {
  const { data } = useFetch('/changes?limit=500')
  if (!data) return null
  const items = data.items
  const count = (f) => items.filter(f).length
  const done = count((r) => ['geprueft', 'abgelehnt'].includes(r.status))
  const csv = () => {
    const cols = ['code', 'phase', 'kind', 'priority', 'area', 'title', 'status', 'description', 'solution', 'test_steps', 'test_result', 'tested_by', 'tested_at', 'req_ids', 'version']
    const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`
    const body = [cols.join(';'), ...items.map((r) => cols.map((c) => esc(c === 'status' ? st(r.status).label : r[c])).join(';'))].join('\r\n')
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob(['﻿' + body], { type: 'text/csv;charset=utf-8' }))
    a.download = `KlarCRM_Aenderungsprotokoll_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
  }
  return (
    <section>
      <div className="kpi-grid">
        <div className="kpi"><span className="kpi-label">Punkte gesamt</span><span className="kpi-value">{items.length}</span>
          <span className="kpi-sub">{count((r) => ['fehler', 'Fehler'].includes(r.kind))} Fehler · {count((r) => ['wunsch', 'Wunsch'].includes(r.kind))} Wünsche</span></div>
        {CR_STATUS.filter((s) => ['eingereicht', 'freigegeben', 'umgesetzt', 'geprueft', 'nachbessern'].includes(s.value)).map((s) => (
          <a key={s.value} className="kpi kpi-link" href={`/aenderungen?status=${s.value}`}><span className="kpi-label">{s.label}</span>
            <span className="kpi-value">{count((r) => r.status === s.value)}</span></a>))}
        <div className="kpi"><span className="kpi-label">Fortschritt</span><span className="kpi-value">{items.length ? Math.round(100 * done / items.length) : 0} %</span>
          <span className="kpi-sub">geprüft oder abgelehnt</span></div>
      </div>
      <div className="toolbar" style={{ margin: '8px 0 12px' }}>
        {PHASES.map((p) => <a key={p.value} className="btn btn-ghost btn-sm" href={`/aenderungen?phase=${p.value}`}>{p.label} ({count((r) => String(r.phase) === p.value)})</a>)}
        <span className="spacer" />
        <button className="btn btn-ghost btn-sm" onClick={csv}>Export CSV (Excel)</button>
      </div>
    </section>
  )
}

// WUN-0001: Prüfergebnis per Klick (bei „nicht in Ordnung“ Beschreibung Pflicht), Freigabe neuer Wünsche nur durch Admin
function QuickActions({ r, onDone }) {   // onDone = Liste neu laden, Filter bleiben stehen (REV03-06)
  const { isAdmin, canWrite } = useAuth()
  const [bad, setBad] = useState(false)
  const [text, setText] = useState('')
  const [err, setErr] = useState(null)
  const patch = async (body) => { setErr(null); try { await api.patch(`/changes/${r.id}`, body); setBad(false); setText(''); onDone() } catch (e) { setErr(e) } }
  const stop = (e) => e.stopPropagation()
  if (!canWrite) return null
  return (
    <div className="cr-actions" onClick={stop}>
      {r.status === 'eingereicht' && isAdmin && <>
        <button className="btn btn-primary btn-sm" onClick={() => patch({ status: 'freigegeben' })}>Freigeben</button>
        <button className="btn btn-ghost btn-sm" onClick={() => { const t = window.prompt('Begründung der Ablehnung'); if (t) patch({ status: 'abgelehnt', test_result: t }) }}>Ablehnen</button></>}
      {r.status === 'eingereicht' && !isAdmin && <small className="muted">wartet auf Admin</small>}
      {['umgesetzt', 'nachbessern'].includes(r.status) && !bad && <>
        <button className="btn btn-ghost btn-sm btn-ok" title="Geprüft – in Ordnung" onClick={() => patch({ status: 'geprueft', test_result: r.status === 'nachbessern' ? `${r.test_result || ''}\n→ nachgeprüft: in Ordnung`.trim() : 'in Ordnung' })}>✓ i. O.</button>
        <button className="btn btn-ghost btn-sm btn-danger-ghost" title="Nicht in Ordnung – bitte beschreiben" onClick={() => setBad(true)}>✗ n. i. O.</button></>}
      {bad && <div className="cr-bad">
        <textarea rows={2} autoFocus placeholder="Was passt nicht? (Pflicht)" value={text} onChange={(e) => setText(e.target.value)} />
        <button className="btn btn-primary btn-sm" disabled={!text.trim()} onClick={() => patch({ status: 'nachbessern', test_result: text })}>Speichern</button>
        <button className="btn btn-ghost btn-sm" onClick={() => setBad(false)}>×</button></div>}
      <ErrorBox error={err} />
    </div>
  )
}

export default function Changes() {
  return (
    <ListPage title="Änderungswünsche & Prüfprotokoll" subtitle="Testrückmeldungen (REV01 ff.) und neue Wünsche – erfassen, umsetzen, prüfen, abhaken"
      path="/changes" entityLabel="Änderungswunsch" fields={fields} defaultSort="code" limit={200}
      newDefaults={{ kind: 'Wunsch', priority: 'mittel', status: 'eingereicht' }}
      toForm={(r) => ({ ...r, kind: kindLabel(r.kind), phase: r.phase ? String(r.phase) : '' })}
      top={(n) => <><div className="info-box">Zum Prüfen eines Updates bitte die Seite <a href="/pruefen"><strong>Prüfen</strong></a> verwenden – dort stehen nur die Punkte des aktuellen Updates in der richtigen Reihenfolge.</div><Summary key={n} /></>}
      rowClass={(r) => (r.status === 'nachbessern' ? 'row-big' : '')}
      filters={[{ name: 'status', label: 'Status', options: CR_STATUS }, { name: 'phase', label: 'Phase', options: PHASES },
        { name: 'kind', label: 'Art', options: KIND }, { name: 'priority', label: 'Priorität', options: PRIO }]}
      columns={[
        { key: 'code', label: 'Nr.', sort: 'code', render: (r) => <strong>{r.code}</strong> },
        { key: 'title', label: 'Punkt', sort: 'title', render: (r) => <>{r.title}<br /><small className="muted">{r.area || '–'} · {kindLabel(r.kind)}</small></> },
        { key: 'priority', label: 'Prio', sort: 'priority', render: (r) => <Badge tone={r.priority === 'hoch' ? 'critical' : r.priority === 'mittel' ? 'warning' : 'neutral'}>{r.priority}</Badge> },
        { key: 'phase', label: 'Phase', sort: 'phase', className: 'num', render: (r) => r.phase || '–' },
        { key: 'status', label: 'Status', sort: 'status', render: (r) => <><Badge tone={st(r.status).tone}>{st(r.status).label}</Badge>{r.superseded_by && <><br /><small className="muted">→ {r.superseded_by}</small></>}</> },
        { key: 'solution', label: 'Umsetzung', render: (r) => <small className="clamp-3">{r.solution || '–'}</small> },
        { key: 'tested_at', label: 'Geprüft', render: (r) => (r.tested_at ? <small>{new Date(r.tested_at).toLocaleDateString('de-DE')}<br />{r.tested_by}</small> : '–') },
        { key: 'act', label: '', render: (r, reload) => <QuickActions r={r} onDone={reload} /> },
      ]} />
  )
}
