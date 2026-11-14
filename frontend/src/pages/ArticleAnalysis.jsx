import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { Badge, ErrorBox } from '../components/ui'
import { feasibility, FEASIBILITY, num, num2 } from '../constants'

const STATUS = [
  { value: 'offen', label: 'offen' }, { value: 'ok', label: 'ok' },
  { value: 'kritisch', label: 'kritisch' }, { value: 'na', label: 'n. a.' },
]
const FIELDS = [
  ['length_mm', 'Länge', 'mm'], ['width_mm', 'Breite', 'mm'], ['height_mm', 'Höhe', 'mm'],
  ['projected_area_cm2', 'Projizierte Fläche je Kavität (inkl. Anguss)', 'cm²'],
  ['wall_min_mm', 'Wandstärke min.', 'mm'], ['wall_max_mm', 'Wandstärke max.', 'mm'],
  ['flow_length_mm', 'Längster Fließweg', 'mm'], ['safety_factor', 'Sicherheitsfaktor Schließkraft', ''],
  ['handling_time_s', 'Nebenzeit (Öffnen, Entformen)', 's'],
]
const PARAMS = [
  ['pressure_bar', 'Werkzeuginnendruck', 'bar'], ['flow_ratio_max', 'Max. Fließweg/Wandstärke', ''],
  ['a', 'Temperaturleitfähigkeit', 'mm²/s'], ['t_melt', 'Massetemperatur', '°C'],
  ['t_mold', 'Werkzeugtemperatur', '°C'], ['t_eject', 'Entformungstemperatur', '°C'],
]

export default function ArticleAnalysis({ calc, setCalc }) {
  const { canWrite } = useAuth()
  const ver = calc.versions.find((v) => v.version_no === calc.current_version)
  const [a, setA] = useState(() => ({ safety_factor: 1.2, handling_time_s: 4, checklist: {}, ...(calc.analysis || {}) }))
  const [feas, setFeas] = useState(calc.feasibility || '')
  const [feasNote, setFeasNote] = useState(calc.feasibility_note || '')
  const [res, setRes] = useState(calc.analysis_results)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)
  const t = useRef()

  useEffect(() => {
    clearTimeout(t.current)
    t.current = setTimeout(() => api.post('/calc/analyze', { analysis: a, inputs: ver.inputs }).then(setRes).catch(setError), 250)
    return () => clearTimeout(t.current)
  }, [a])

  const set = (k, v) => { setSaved(false); setA((s) => ({ ...s, [k]: v })) }
  const setCheck = (k, field, v) => set('checklist', { ...a.checklist, [k]: { ...(a.checklist[k] || {}), [field]: v } })
  async function save() {
    setError(null)
    try {
      setCalc(await api.put(`/calculations/${calc.id}/analysis`, { analysis: a, feasibility: feas || null, feasibility_note: feasNote }))
      setSaved(true)
    } catch (e) { setError(e) }
  }
  const sug = res && feasibility(res.suggestion)
  const numIn = (k, label, unit, src = a, onCh = (v) => set(k, v), placeholder) => (
    <div className="field" key={k}><label>{label} <span className="unit">{unit}</span></label>
      <input type="number" step="any" className="num" value={src[k] ?? ''} placeholder={placeholder}
        onChange={(e) => onCh(e.target.value === '' ? '' : Number(e.target.value))} /></div>
  )

  return (
    <div className="calc-layout">
      <fieldset disabled={!canWrite} className="calc-fieldset">
        <div className="card">
          <h3>Artikeldaten</h3>
          <div className="form-grid form-grid-3">
            <div className="field"><label>Werkstoffgruppe</label>
              <select value={a.material_family || ''} onChange={(e) => set('material_family', e.target.value)}>
                <option value="">– wählen –</option>
                {(res?.families || []).map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
              <small className="hint">Kalkuliertes Material: {ver.inputs.material_name || '–'}</small></div>
            <div className="field"><label>Fachzahl (aus Kalkulation)</label><input disabled value={ver.inputs.cavities} className="num" /></div>
            <div className="field"><label>Zykluszeit (aus Kalkulation)</label><input disabled value={`${num(ver.inputs.cycle_time_s, 1)} s`} className="num" /></div>
            {FIELDS.map(([k, l, u]) => numIn(k, l, u))}
          </div>
        </div>

        <div className="card">
          <h3>Werkstoffkennwerte <span className="muted small">(Richtwerte, überschreibbar)</span></h3>
          <div className="form-grid form-grid-3">
            {PARAMS.map(([k, l, u]) => numIn(k, l, u, a, (v) => set(k, v), res?.material_params?.[k] != null ? String(res.material_params[k]) : ''))}
          </div>
        </div>

        <div className="card">
          <h3>Checkliste Machbarkeit</h3>
          <table className="table table-compact checklist">
            <thead><tr><th>Punkt</th><th>Bewertung</th><th>Anmerkung</th></tr></thead>
            <tbody>{(res?.checklist_items || []).map((c) => {
              const v = a.checklist?.[c.key] || {}
              return (
                <tr key={c.key} className={v.status === 'kritisch' ? 'row-critical' : ''}>
                  <td>{c.label}</td>
                  <td><div className="seg seg-sm">{STATUS.map((st) => (
                    <button type="button" key={st.value} className={(v.status || 'offen') === st.value ? `on st-${st.value}` : ''}
                      onClick={() => setCheck(c.key, 'status', st.value)}>{st.label}</button>))}</div></td>
                  <td><input value={v.note || ''} onChange={(e) => setCheck(c.key, 'note', e.target.value)} /></td>
                </tr>
              )
            })}</tbody>
          </table>
        </div>
      </fieldset>

      <aside className="calc-results">
        <div className="stack">
          <div className="card result-card">
            <span className="muted small">Ergebnis Artikelanalyse</span>
            <div className="result-kpis">
              <div><span>Schließkraft benötigt</span><b>{res ? `${num(res.clamping_force_t)} t` : '–'}</b></div>
              <div><span>Fließweg / Wandstärke</span><b className={res && res.flow_ratio > res.flow_ratio_max ? 'text-critical' : ''}>{res?.flow_ratio ? `${num(res.flow_ratio)} : 1` : '–'}</b></div>
              <div><span>Grenze Werkstoff</span><b>{res ? `${num(res.flow_ratio_max)} : 1` : '–'}</b></div>
              <div><span>Kühlzeit (Richtwert)</span><b>{res?.cooling_time_s ? `${num(res.cooling_time_s, 1)} s` : '–'}</b></div>
              <div><span>Zyklus (Richtwert)</span><b>{res?.cycle_estimate_s ? `${num(res.cycle_estimate_s, 1)} s` : '–'}</b></div>
              <div><span>Zyklus kalkuliert</span><b>{num(ver.inputs.cycle_time_s, 1)} s</b></div>
            </div>
            {res?.issues.map((i) => <div key={i} className="error-box small">✖ {i}</div>)}
            {res?.hints.map((i) => <div key={i} className="warn-box">⚠ {i}</div>)}
            {res && <div className="muted small">Checkliste: {res.critical_checks} kritisch · {res.open_checks} offen</div>}
          </div>

          <div className="card">
            <h3>Passende Maschinen</h3>
            {res?.suitable_machines?.length ? (
              <table className="table table-compact">
                <thead><tr><th>Maschine</th><th className="num">Schließkraft</th><th className="num">€/h</th></tr></thead>
                <tbody>{res.suitable_machines.map((m, i) => (
                  <tr key={m.id} className={m.id === ver.inputs.machine_id ? 'row-latest' : ''}>
                    <td>{m.number} · {m.name}{i === 0 && <> <Badge tone="good">kleinste passende</Badge></>}{m.id === ver.inputs.machine_id && <> <Badge tone="info">kalkuliert</Badge></>}</td>
                    <td className="num">{num(m.clamping_force_t)} t</td><td className="num">{num2(m.hourly_rate)}</td>
                  </tr>))}</tbody>
              </table>
            ) : <div className="empty small">{res?.clamping_force_t ? 'Keine passende Maschine vorhanden.' : 'Projizierte Fläche eingeben.'}</div>}
          </div>

          <div className="card">
            <h3>Machbarkeit</h3>
            {sug && <p className="small" style={{ marginTop: 0 }}>Vorschlag aus der Analyse: <Badge tone={sug.tone}>{sug.label}</Badge>{' '}
              {canWrite && feas !== res.suggestion && <button className="btn btn-ghost btn-sm" onClick={() => setFeas(res.suggestion)}>übernehmen</button>}</p>}
            <div className="feas-pick">
              {FEASIBILITY.map((f) => (
                <button key={f.value} type="button" disabled={!canWrite} className={`feas-btn tone-${f.tone} ${feas === f.value ? 'on' : ''}`}
                  onClick={() => { setSaved(false); setFeas(f.value) }}>{f.label}</button>
              ))}
            </div>
            <div className="field" style={{ marginTop: 10 }}><label>Anmerkung / erforderliche Anpassungen</label>
              <textarea rows={3} disabled={!canWrite} value={feasNote} onChange={(e) => { setSaved(false); setFeasNote(e.target.value) }} /></div>
            <ErrorBox error={error} />
            {canWrite && <div className="form-actions" style={{ marginTop: 10 }}><span className="spacer" />
              <button className="btn btn-primary" onClick={save}>{saved ? '✓ Gespeichert' : 'Analyse speichern'}</button></div>}
            <p className="hint" style={{ marginBottom: 0 }}>Richtwerte nach Kühlzeit-Näherung und Innendruck – ersetzen keine Füllsimulation.</p>
          </div>
        </div>
      </aside>
    </div>
  )
}
