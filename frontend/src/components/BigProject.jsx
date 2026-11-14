import { useEffect, useState } from 'react'
import { api } from '../api'
import { eurShort } from '../constants'

let cache = null
let pending = null

/** Schwellen für Großprojekte aus den Kalkulations-Parametern (einmal geladen, dann gecacht). */
export function useThresholds() {
  const [t, setT] = useState(cache)
  useEffect(() => {
    if (cache) return
    pending = pending || api.get('/calc/settings').then((s) => {
      cache = { revenue: Number(s.big_revenue_threshold || 500000), invest: Number(s.big_invest_threshold || 500000) }
      return cache
    })
    pending.then(setT)
  }, [])
  return t
}
export const resetThresholds = () => { cache = null; pending = null }

export function bigReasons(t, revenue, invest) {
  if (!t) return []
  const r = []
  if (Number(revenue || 0) >= t.revenue) r.push(`Umsatz ≥ ${eurShort(t.revenue)}`)
  if (Number(invest || 0) >= t.invest) r.push(`Invest ≥ ${eurShort(t.invest)}`)
  return r
}

/** Hervorhebung „Großprojekt“ mit Begründung. */
export function BigBadge({ revenue, invest, withReasons = true }) {
  const t = useThresholds()
  const reasons = bigReasons(t, revenue, invest)
  if (!reasons.length) return null
  return (
    <span className="big-badge" title={`Großprojekt: ${reasons.join(' · ')}`}>
      ★ Großprojekt{withReasons && <small>{reasons.join(' · ')}</small>}
    </span>
  )
}

/** Invest und Serienumsatz aus Angebotspositionen (Einheit „psch“ = Einmalkosten). */
export function quoteSplit(q) {
  const invest = (q.items || []).filter((i) => i.unit === 'psch').reduce((s, i) => s + i.line_total, 0)
  return { invest, revenue: (q.net_total || 0) - invest }
}
