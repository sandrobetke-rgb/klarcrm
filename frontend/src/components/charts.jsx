import { useState } from 'react'
import { eur, eurShort } from '../constants'

/** Säulendiagramm, eine Serie, mit Hover-Tooltip. data: [{label, value, sub}] */
export function ColumnChart({ data, height = 200, ariaLabel }) {
  const [hover, setHover] = useState(null)
  const max = Math.max(1, ...data.map((d) => d.value))
  const ticks = niceTicks(max)
  const top = ticks[ticks.length - 1]
  return (
    <div className="colchart" role="img" aria-label={ariaLabel}>
      <div className="colchart-plot" style={{ height }}>
        {ticks.map((t) => (
          <div key={t} className="gridline" style={{ bottom: `${(t / top) * 100}%` }}>
            <span>{eurShort(t)}</span>
          </div>
        ))}
        <div className="cols">
          {data.map((d, i) => (
            <div key={d.label} className="col-hit" onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              <div className={`col ${hover === i ? 'col-hover' : ''}`} style={{ height: `${(d.value / top) * 100}%` }} />
              {hover === i && (
                <div className="tooltip" style={{ bottom: `calc(${(d.value / top) * 100}% + 8px)` }}>
                  <strong>{d.sub || d.label}</strong>
                  <span>{eur(d.value)}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="cols-labels">
        {data.map((d) => <span key={d.label}>{d.label}</span>)}
      </div>
    </div>
  )
}

/** Horizontale Balken mit direkter Beschriftung. data: [{label, value, note}] */
export function BarList({ data, format = eur }) {
  const [hover, setHover] = useState(null)
  const max = Math.max(1, ...data.map((d) => d.value))
  return (
    <div className="barlist">
      {data.map((d, i) => (
        <div key={d.label} className="barlist-row" onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
          <span className="barlist-label">{d.label}</span>
          <span className="barlist-track">
            <span className={`barlist-bar ${d.tone ? 'tone-' + d.tone : ''} ${hover === i ? 'col-hover' : ''}`}
              style={{ width: `${Math.max(d.value ? 1.5 : 0, (d.value / max) * 100)}%` }} />
          </span>
          <span className="barlist-value">{format(d.value)}{d.note && <small>{d.note}</small>}</span>
        </div>
      ))}
    </div>
  )
}

function niceTicks(max) {
  const raw = max / 4
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw)
  const out = []
  for (let v = 0; v <= max + step * 0.001; v += step) out.push(v)
  if (out[out.length - 1] < max) out.push(out[out.length - 1] + step)
  return out
}
