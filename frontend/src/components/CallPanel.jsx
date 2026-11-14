import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { CALL_RESULTS, callResult, contactName, fmtDate, fmtDateTime } from '../constants'
import { Badge, ErrorBox, RefSelect } from './ui'

const nowLocal = () => {
  const d = new Date()
  return new Date(d - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

/** Anrufhistorie einer Kalkulation mit Ergebnis + Formular „Anruf dokumentieren“. */
export default function CallPanel({ calc, onChange, compact }) {
  const { canWrite } = useAuth()
  const [form, setForm] = useState({ result: 'kunde_entscheidet_noch', note: '', called_at: nowLocal(), contact_id: calc.contact_id, follow_up: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState(!compact)
  useEffect(() => setForm((f) => ({ ...f, contact_id: calc.contact_id })), [calc.id])
  const calls = [...(calc.calls || [])].reverse()

  async function save(e) {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const c = await api.post(`/calculations/${calc.id}/call`, {
        ...form, called_at: new Date(form.called_at).toISOString(), follow_up: form.follow_up || null,
      })
      onChange(c)
      setForm({ result: 'kunde_entscheidet_noch', note: '', called_at: nowLocal(), contact_id: calc.contact_id, follow_up: '' })
      if (compact) setOpen(false)
    } catch (err) { setError(err) } finally { setBusy(false) }
  }
  async function remove(id) {
    onChange(await api.del(`/calculations/${calc.id}/calls/${id}`))
  }

  return (
    <div className="stack">
      {canWrite && (open ? (
        <form className="card form call-form" onSubmit={save}>
          <h3>Anruf dokumentieren</h3>
          <div className="form-grid form-grid-3">
            <div className="field"><label>Datum / Uhrzeit</label>
              <input type="datetime-local" required value={form.called_at} onChange={(e) => setForm({ ...form, called_at: e.target.value })} /></div>
            <div className="field"><label>Gesprächspartner</label>
              <RefSelect kind="contact" filter={calc.account_id || calc.account?.id} value={form.contact_id} onChange={(v) => setForm({ ...form, contact_id: v })} /></div>
            <div className="field"><label>Ergebnis *</label>
              <select required value={form.result} onChange={(e) => setForm({ ...form, result: e.target.value })}>
                {CALL_RESULTS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select></div>
            <div className="field span-2"><label>Gesprächsnotiz / Resultat</label>
              <textarea rows={3} value={form.note} placeholder="Was wurde besprochen? Nächste Schritte?" onChange={(e) => setForm({ ...form, note: e.target.value })} /></div>
            <div className="field"><label>Wiedervorlage am</label>
              <input type="date" value={form.follow_up} onChange={(e) => setForm({ ...form, follow_up: e.target.value })} />
              <small className="hint">Legt eine Aufgabe für den Verantwortlichen an</small></div>
          </div>
          <ErrorBox error={error} />
          <div className="form-actions"><span className="spacer" />
            {compact && <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>Abbrechen</button>}
            <button className="btn btn-primary" disabled={busy}>{busy ? 'Speichert…' : 'Anruf speichern'}</button>
          </div>
        </form>
      ) : <button className="btn btn-primary" onClick={() => setOpen(true)}>☎ Neuen Anruf dokumentieren</button>)}

      <div className="card card-flush">
        <table className="table">
          <thead><tr><th>Angerufen am</th><th>Ergebnis</th><th>Gesprächsnotiz / Resultat</th><th>Gesprächspartner</th><th>Wiedervorlage</th><th>Von</th>{canWrite && <th />}</tr></thead>
          <tbody>
            {calls.map((c, i) => (
              <tr key={c.id} className={i === 0 ? 'row-latest' : ''}>
                <td className="nowrap"><strong>{fmtDateTime(c.called_at)}</strong>{i === 0 && <><br /><small className="muted">zuletzt</small></>}</td>
                <td><Badge tone={callResult(c.result).tone}>{callResult(c.result).label}</Badge></td>
                <td className="pre">{c.note || <span className="muted">–</span>}</td>
                <td>{c.contact ? contactName(c.contact) : '–'}</td>
                <td>{c.follow_up ? fmtDate(c.follow_up) : '–'}</td>
                <td>{c.user?.name || '–'}</td>
                {canWrite && <td><button className="icon-btn" title="Eintrag löschen" onClick={() => remove(c.id)}>×</button></td>}
              </tr>
            ))}
            {!calls.length && <tr><td colSpan={7} className="empty">Noch keine Anrufe dokumentiert.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/** Kurzanzeige letzter Anruf (für Kopfzeile / Liste). */
export function LastCall({ call, date, onClick, warnDays = 14, open = true }) {
  const d = call?.called_at || date
  const old = open && (!d || (Date.now() - new Date(d)) / 86400000 > warnDays)
  return (
    <button type="button" className="lastcall" onClick={onClick} title="Anrufhistorie öffnen">
      <span className={old ? 'text-critical' : ''}>{d ? fmtDate(d) : 'noch nie'}</span>
      {call && <Badge tone={callResult(call.result).tone}>{callResult(call.result).label}</Badge>}
    </button>
  )
}
