import { useState } from 'react'
import { api } from '../api'
import { Badge, ErrorBox, Modal } from './ui'
import { LIGHT } from '../constants'

// Angebotsverfolgung (REV01-P06): Ampel + Ergebnis der Rücksprache
export function LightBadge({ light, due }) {
  if (!light) return null
  const l = LIGHT[light]
  return <Badge tone={l.tone}>● {l.label}{due ? ` · ${new Date(due).toLocaleDateString('de-DE')}` : ''}</Badge>
}

export default function FollowupDialog({ task, onClose, onDone }) {
  const [result, setResult] = useState('erreicht')
  const [note, setNote] = useState('')
  const [next, setNext] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  async function submit() {
    setBusy(true); setErr(null)
    try {
      await api.post(`/followups/${task.id}`, { result, note: note || null, next_date: next || null })
      onDone?.()
    } catch (e) { setErr(e) } finally { setBusy(false) }
  }
  const opts = [
    ['erreicht', 'Kunde erreicht – Rückmeldung erhalten', 'Aufgabe erledigt; optional neue Wiedervorlage'],
    ['nicht_erreicht', 'Niemanden erreicht', 'Aufgabe kommt am nächsten Arbeitstag wieder (oder am gewählten Datum)'],
    ['wieder_melden', 'Kunde meldet sich wieder am …', 'Wiedervorlage zum gewählten Datum'],
  ]
  return (
    <Modal title={`Rücksprache: ${task.subject}`} onClose={onClose}>
      <ErrorBox error={err} />
      <div className="form">
        {task.attempts > 0 && <p className="muted small">Bisher {task.attempts}× niemanden erreicht.</p>}
        <div className="field"><label>Ergebnis</label>
          {opts.map(([v, l, h]) => (
            <label key={v} className="radio-row"><input type="radio" name="fu" checked={result === v} onChange={() => setResult(v)} />
              <span>{l}<br /><small className="muted">{h}</small></span></label>))}
        </div>
        <div className="field"><label>Notiz zum Gespräch</label>
          <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="z. B. Entscheidung Ende KW 49, Preis im Rahmen, Werkzeug wird verglichen" /></div>
        <div className="field"><label>{result === 'wieder_melden' ? 'Wieder melden am *' : result === 'erreicht' ? 'Neue Wiedervorlage am (optional)' : 'Erneut anrufen am (leer = nächster Arbeitstag)'}</label>
          <input type="date" value={next} onChange={(e) => setNext(e.target.value)} /></div>
        <div className="form-actions"><span className="spacer" />
          <button className="btn btn-ghost" onClick={onClose}>Abbrechen</button>
          <button className="btn btn-primary" disabled={busy || (result === 'wieder_melden' && !next)} onClick={submit}>Speichern</button>
        </div>
      </div>
    </Modal>
  )
}
