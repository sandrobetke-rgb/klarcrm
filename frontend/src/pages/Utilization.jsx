import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorBox, useFetch } from '../components/ui'
import { calcStatus, machineKindLabel, num } from '../constants'

const MODES = [
  ['pct_fixed', 'Fest', 'Bestand + gewonnene Kalkulationen'],
  ['pct_expected', 'Erwartet', 'Fest + offene Kalkulationen × Wahrscheinlichkeit'],
  ['pct_max', 'Maximal', 'Fest + alle offenen Kalkulationen zu 100 %'],
]
const tone = (p) => (p == null ? '' : p >= 100 ? 'ut-over' : p >= 85 ? 'ut-high' : p >= 60 ? 'ut-mid' : 'ut-low')

function Cell({ y, mode }) {
  const cap = y.capacity_h
  const p = y[mode]
  if (p == null) return <td className="num muted">–</td>
  const seg = (h) => `${Math.min(100, (h / (cap || 1)) * 100)}%`
  return (
    <td className={`ut-cell ${tone(p)}`} title={`Bestand ${num(y.base)} h · gewonnen ${num(y.fixed)} h · gewichtet ${num(y.weighted)} h · potenziell ${num(y.potential)} h`}>
      <div className="ut-val">{num(p, 0)} %{p >= 100 && ' ⚠'}</div>
      <div className="ut-bar">
        <span className="ut-base" style={{ width: seg(y.base) }} />
        <span className="ut-fixed" style={{ width: seg(y.fixed) }} />
        {mode !== 'pct_fixed' && <span className="ut-open" style={{ width: seg(mode === 'pct_max' ? y.potential : y.weighted) }} />}
      </div>
    </td>
  )
}

export default function Utilization() {
  const [years, setYears] = useState(5)
  const [mode, setMode] = useState('pct_expected')
  const [open, setOpen] = useState(null)
  const { data, error } = useFetch(`/calc/utilization?years=${years}`)
  if (error) return <ErrorBox error={error} />
  if (!data) return <div className="loading">Lade Auslastung…</div>
  const totalsRow = data.totals.map((t) => ({ ...t, capacity_h: t.capacity_h }))

  return (
    <div className="page page-wide">
      <header className="page-head">
        <div>
          <h1>Auslastung kommende Jahre</h1>
          <p className="muted">Maschinenstunden aus Bestand und Kalkulationen im Verhältnis zur verfügbaren Kapazität je Maschine</p>
        </div>
        <div className="toolbar">
          <div className="seg">{MODES.map(([k, l, d]) => <button key={k} title={d} className={mode === k ? 'on' : ''} onClick={() => setMode(k)}>{l}</button>)}</div>
          <select value={years} onChange={(e) => setYears(Number(e.target.value))}>
            {[3, 5, 7, 10].map((n) => <option key={n} value={n}>{n} Jahre</option>)}
          </select>
        </div>
      </header>
      <div className="card legend-card small">
        <span><span className="ut-swatch ut-base" /> Bestand (Grundauslastung)</span>
        <span><span className="ut-swatch ut-fixed" /> Gewonnene Kalkulationen</span>
        <span><span className="ut-swatch ut-open" /> Offene Kalkulationen ({mode === 'pct_max' ? '100 %' : 'gewichtet'})</span>
        <span className="spacer" />
        <span><span className="ut-chip ut-low">&lt; 60 %</span> <span className="ut-chip ut-mid">60–85 %</span> <span className="ut-chip ut-high">85–100 %</span> <span className="ut-chip ut-over">≥ 100 % ⚠</span></span>
      </div>
      <div className="card card-flush">
        <table className="table ut-table">
          <thead><tr><th>Maschine / Anlage</th><th className="num">Kapazität h/Jahr</th>{data.years.map((y) => <th key={y} className="num">{y}</th>)}</tr></thead>
          <tbody>
            {data.machines.map((m) => (
              <Fragment key={m.machine.id ?? 'none'}>
                <tr className="row-click" onClick={() => setOpen(open === m.machine.id ? undefined : m.machine.id)}>
                  <td><strong>{m.machine.number ? `${m.machine.number} · ` : ''}{m.machine.name}</strong>
                    <br /><small className="muted">{m.machine.kind && m.machine.kind !== 'spritzguss' ? `${machineKindLabel(m.machine.kind)} · ` : ''}{m.items.length} Kalkulation(en) {open === m.machine.id ? '▲' : '▼'}</small></td>
                  <td className="num">{m.capacity_h ? num(m.capacity_h) : '–'}</td>
                  {m.years.map((y) => <Cell key={y.year} y={{ ...y, capacity_h: m.capacity_h }} mode={mode} />)}
                </tr>
                {open === m.machine.id && m.items.map((it) => (
                  <tr key={`${it.id}-${it.operation || ''}`} className="ut-sub">
                    <td colSpan={2}>↳ <Link to={`/kalkulationen/${it.id}`}>{it.number} {it.article_name}</Link>{it.operation && <> · <em>{it.operation}</em></>}
                      <small className="muted"> · {calcStatus(it.status).label} · {it.probability} % · ab {new Date(it.start).toLocaleDateString('de-DE', { month: '2-digit', year: 'numeric' })} · {num(it.project_years, 1)} J.</small></td>
                    {data.years.map((y) => <td key={y} className="num small">{it.years[y] ? `${num(it.years[y])} h` : ''}</td>)}
                  </tr>
                ))}
              </Fragment>
            ))}
            <tr className="calc-row-summe">
              <td>Gesamt</td><td className="num">{num(totalsRow[0]?.capacity_h)}</td>
              {totalsRow.map((t) => <Cell key={t.year} y={t} mode={mode} />)}
            </tr>
          </tbody>
        </table>
      </div>
      <p className="muted small">
        Laufzeit je Kalkulation ab Serienstart (SOP), sonst ab heute (gewonnen) bzw. ab 1. Januar des Folgejahres (offen), über die Projektlaufzeit.
        Maschinenstunden inkl. Rüsten aus der aktuellen Kalkulationsversion. Kapazität, Grundauslastung und Auslauf je Maschine unter Stammdaten.
      </p>
    </div>
  )
}
