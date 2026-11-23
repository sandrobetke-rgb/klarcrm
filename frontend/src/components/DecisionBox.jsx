import { useState } from 'react'
import { api } from '../api'
import { Badge, ErrorBox } from './ui'
import { DECISIONS, decisionLabel } from '../constants'
import { useSites } from './useSites'

// Entscheidung je Artikel vor Kalkulationsstart (REV01-P02)
export default function DecisionBox({ calc, onDone, compact = false, canWrite = true }) {
  const sites = useSites()
  const [open, setOpen] = useState(false)
  const [d, setD] = useState(calc.decision || 'anbieten')
  const [note, setNote] = useState(calc.decision_note || '')
  const [site, setSite] = useState('')
  const [err, setErr] = useState(null)
  const needNote = d === 'nicht_anbieten' || d === 'sonstiges'
  async function save() {
    setErr(null)
    try {
      await api.post(`/calculations/${calc.id}/decision`, { decision: d, note: note || null, site_id: site ? Number(site) : null })
      setOpen(false); onDone?.()
    } catch (e) { setErr(e) }
  }
  const tone = DECISIONS.find((x) => x.value === calc.decision)?.tone || 'warning'
  if (!open) {
    return (
      <span className="decision-inline">
        <Badge tone={calc.decision ? tone : 'warning'}>{calc.decision ? decisionLabel(calc.decision) : '⚠ Entscheidung offen'}</Badge>
        {calc.decision_note && !compact && <small className="muted"> {calc.decision_note}</small>}
        {canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setOpen(true)}>{calc.decision ? 'ändern' : 'entscheiden'}</button>}
      </span>
    )
  }
  return (
    <div className="decision-box card">
      <ErrorBox error={err} />
      <strong>Entscheidung für {calc.number} {calc.article_name}</strong>
      <div className="reason-list">{DECISIONS.map((x) => (
        <label key={x.value} className="radio-row"><input type="radio" name={`dec-${calc.id}`} checked={d === x.value} onChange={() => setD(x.value)} /> {x.label}</label>))}
      </div>
      {d === 'anderer_standort' && <div className="field"><label>Standort, der anbietet *</label>
        <select value={site} onChange={(e) => setSite(e.target.value)}><option value="">– wählen –</option>
          {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
        <small className="hint">Kalkulation wird mit den Sätzen dieses Standorts als neue Version angelegt</small></div>}
      <div className="field"><label>Begründung {needNote ? '*' : '(optional)'}</label>
        <input value={note} onChange={(e) => setNote(e.target.value)} placeholder={d === 'nicht_anbieten' ? 'z. B. Mengen zu klein, keine Maschine, Technologie passt nicht' : ''} /></div>
      <small className="hint">Pflichtangaben: Entscheidung · bei „nicht anbieten“ und „Sonstiges“ eine Begründung · bei „anderer Standort“ der Standort.
        Die Entscheidung wird spätestens beim Erstellen des Angebots gebraucht.</small>
      <div className="form-actions"><span className="spacer" />
        <button className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>Abbrechen</button>
        <button className="btn btn-primary btn-sm" disabled={(needNote && !note.trim()) || (d === 'anderer_standort' && !site)} onClick={save}>Entscheidung speichern</button>
      </div>
    </div>
  )
}
