import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { confirmDelete, ErrorBox } from '../components/ui'
import { eur, eur4, fix4, fmtDate, INPUT_LABELS, LIGHTS, num } from '../constants'
import { Light } from './Calculations'
import NumInput from '../components/NumInput'

const ACTUAL_FIELDS = [
  'cycle_time_s', 'cavities', 'productivity_pct', 'scrap_pct', 'material_price_kg', 'part_weight_g', 'sprue_weight_g',
  'setup_time_h', 'lot_size', 'assembly_time_s', 'labor_rate_h', 'operator_factor', 'machine_rate_h', 'maintenance_rate_h', 'purchased_parts',
  'pack_cost_per_unit', 'pack_parts_per_unit', 'transport_cost_per_pallet', 'transport_cost_per_delivery', 'transport_deliveries_per_year',
]
const COMPARE = ['mek_material', 'machine', 'maintenance', 'labor', 'setup', 'assembly', 'quality_f', 'toolshop_f', 'scrap', 'hk', 'quality_h', 'toolshop_h', 'packaging', 'transport', 'sk', 'profit']

export default function PostCalcTab({ calc, setCalc }) {
  const { canWrite } = useAuth()
  const [versionNo, setVersionNo] = useState(calc.current_version)
  const ver = calc.versions.find((v) => v.version_no === versionNo)
  const [form, setForm] = useState({ reference: '', period_from: '', period_to: '', remark: '' })
  const [act, setAct] = useState({})
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(calc.post_calcs.length ? calc.post_calcs[calc.post_calcs.length - 1].id : null)
  const t = useRef()
  const body = () => ({ version_no: versionNo, ...form, period_from: form.period_from || null, period_to: form.period_to || null,
    actuals: Object.fromEntries(Object.entries(act).filter(([, v]) => v !== '' && v != null)) })

  useEffect(() => {
    clearTimeout(t.current)
    t.current = setTimeout(() => api.post(`/calculations/${calc.id}/postcalcs/preview`, body()).then(setPreview).catch(setError), 300)
    return () => clearTimeout(t.current)
  }, [act, versionNo])

  async function save() {
    setError(null)
    try {
      const c = await api.post(`/calculations/${calc.id}/postcalcs`, body())
      setCalc(c); setAct({}); setForm({ reference: '', period_from: '', period_to: '', remark: '' })
      setSelected(c.post_calcs[c.post_calcs.length - 1].id)
    } catch (e) { setError(e) }
  }
  const shown = calc.post_calcs.find((p) => p.id === selected)

  return (
    <div className="stack">
      <div className="card">
        <h3>Ampel-Regel</h3>
        <p className="muted small" style={{ margin: 0 }}>
          Vergleich der Ist-Selbstkosten je Stück mit der Plan-Kalkulation. <Light value="gruen" withText /> bis zur Grün-Schwelle Abweichung ·{' '}
          <Light value="gelb" withText /> bis zur Rot-Schwelle · <Light value="rot" withText /> darüber oder wenn der Preis die Ist-Kosten nicht deckt.
          Schwellen unter Stammdaten → Parameter (Standard +3 % / +10 %).
        </p>
      </div>

      {calc.post_calcs.length > 0 && (
        <div className="card card-flush">
          <table className="table">
            <thead><tr><th>Ampel</th><th>Referenz / Auftrag</th><th>Zeitraum</th><th>Basis</th><th className="num">Menge</th><th className="num">SK Plan</th><th className="num">SK Ist</th><th className="num">Abw.</th><th className="num">Marge Ist</th><th className="num">Ergebnis</th><th /></tr></thead>
            <tbody>
              {[...calc.post_calcs].reverse().map((p) => (
                <tr key={p.id} className={`row-click ${selected === p.id ? 'row-selected' : ''}`} onClick={() => setSelected(p.id)}>
                  <td><Light value={p.traffic_light} withText /></td>
                  <td>{p.reference || '–'}{p.remark && <><br /><small className="muted">{p.remark}</small></>}</td>
                  <td>{p.period_from ? `${fmtDate(p.period_from)} – ${fmtDate(p.period_to)}` : fmtDate(p.created_at)}</td>
                  <td>V{p.version_no}</td>
                  <td className="num">{num(p.results.quantity)}</td>
                  <td className="num">{eur4(p.results.plan_self_cost)}</td>
                  <td className="num">{eur4(p.results.self_cost)}</td>
                  <td className={`num ${p.results.deviation_sk_pct > 0 ? 'delta-up' : 'delta-down'}`}>{p.results.deviation_sk_pct > 0 ? '+' : ''}{num(p.results.deviation_sk_pct, 1)} %</td>
                  <td className="num">{num(p.results.margin_pct, 1)} %</td>
                  <td className="num">{p.results.result_total != null ? eur(p.results.result_total) : '–'}</td>
                  <td>{canWrite && <button className="icon-btn" title="Löschen" onClick={async (e) => {
                    e.stopPropagation()
                    if (await confirmDelete('Nachkalkulation', () => api.del(`/calculations/${calc.id}/postcalcs/${p.id}`))) setCalc(await api.get(`/calculations/${calc.id}`))
                  }}>×</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {shown && <Compare plan={calc.versions.find((v) => v.version_no === shown.version_no)?.results} ist={shown.results} title={`Plan / Ist – ${shown.reference || 'Nachkalkulation'}`} />}

      {canWrite && (
        <div className="card">
          <div className="section-head"><h3>Neue Nachkalkulation</h3>
            <label className="inline-label">gegen Version
              <select value={versionNo} onChange={(e) => setVersionNo(Number(e.target.value))}>
                {calc.versions.map((v) => <option key={v.version_no} value={v.version_no}>V{v.version_no}</option>)}
              </select></label></div>
          <p className="card-sub">Nur Ist-Werte eintragen, die abweichen. Leere Felder = Planwert (grau).</p>
          <div className="form-grid form-grid-4">
            <div className="field span-2"><label>Referenz (Auftrag, Zeitraum)</label><input value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} placeholder="z. B. FA 2026-0412" /></div>
            <div className="field"><label>Von</label><input type="date" value={form.period_from} onChange={(e) => setForm({ ...form, period_from: e.target.value })} /></div>
            <div className="field"><label>Bis</label><input type="date" value={form.period_to} onChange={(e) => setForm({ ...form, period_to: e.target.value })} /></div>
            <ActField k="quantity" label="Produzierte Menge" unit="Stk" act={act} setAct={setAct} />
            <ActField k="extra_costs" label="Zusätzliche Ist-Kosten gesamt" unit="€" act={act} setAct={setAct} hint="Sonderfahrten, Nacharbeit …" />
            <ActField k="actual_price" label="Erzielter Preis" unit="€/Stk" act={act} setAct={setAct} plan={ver?.results.unit_price} />
            {ACTUAL_FIELDS.map((k) => <ActField key={k} k={k} label={INPUT_LABELS[k][0]} unit={INPUT_LABELS[k][1]} act={act} setAct={setAct} plan={ver?.inputs[k]} />)}
            <div className="field span-4"><label>Bemerkung</label><input value={form.remark} onChange={(e) => setForm({ ...form, remark: e.target.value })} /></div>
          </div>
          <ErrorBox error={error} />
          {preview && (
            <div className={`postcalc-preview ${LIGHTS[preview.traffic_light].cls}-bg`}>
              <Light value={preview.traffic_light} withText />
              <span>SK Ist {eur4(preview.self_cost)} vs. Plan {eur4(preview.plan_self_cost)} ({preview.deviation_sk_pct > 0 ? '+' : ''}{num(preview.deviation_sk_pct, 1)} %)</span>
              <span>Marge Ist {num(preview.margin_pct, 1)} % (Plan {num(preview.plan_margin_pct, 1)} %)</span>
              <span className="spacer" />
              <button className="btn btn-primary" onClick={save}>Nachkalkulation speichern</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ActField({ k, label, unit, act, setAct, plan, hint }) {
  return (
    <div className={`field ${act[k] !== undefined && act[k] !== '' ? 'field-changed' : ''}`}>
      <label>{label} <span className="unit">{unit}</span></label>
      <NumInput type="number" step="any" className="num" placeholder={plan != null ? num(plan, 4) : ''} value={act[k] ?? ''}
        onChange={(e) => setAct({ ...act, [k]: e.target.value === '' ? '' : Number(e.target.value) })} />
      {hint && <small className="hint">{hint}</small>}
    </div>
  )
}

function Compare({ plan, ist, title }) {
  if (!plan) return null
  const lab = Object.fromEntries(ist.lines.map((l) => [l.key, l.label]))
  return (
    <div className="card">
      <h3>{title}</h3>
      <table className="table table-compact">
        <thead><tr><th>Position</th><th className="num">Plan €/Stk</th><th className="num">Ist €/Stk</th><th className="num">Δ €/Stk</th><th className="num">Δ %</th></tr></thead>
        <tbody>{COMPARE.map((k) => {
          const p = plan.values?.[k] ?? 0, i = ist.values?.[k] ?? 0
          if (!p && !i) return null
          const d = i - p
          const bad = k === 'profit' ? d < 0 : d > 0
          return (
            <tr key={k} className={['hk', 'sk'].includes(k) ? 'calc-row-summe' : ''}>
              <td>{lab[k]?.replace(/ \d+(,\d+)? %$/, '') || k}</td><td className="num">{fix4(p)}</td><td className="num">{fix4(i)}</td>
              <td className={`num ${Math.abs(d) < 1e-6 ? 'muted' : bad ? 'delta-up' : 'delta-down'}`}>{d > 0 ? '+' : ''}{fix4(d)}</td>
              <td className="num">{p ? `${d > 0 ? '+' : ''}${num((d / Math.abs(p)) * 100, 1)} %` : '–'}</td>
            </tr>
          )
        })}
          <tr><td>Stück/h</td><td className="num">{num(plan.pieces_per_hour)}</td><td className="num">{num(ist.pieces_per_hour)}</td><td /><td /></tr>
        </tbody>
      </table>
    </div>
  )
}
