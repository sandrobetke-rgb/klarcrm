import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { BarList } from '../components/charts'
import { ErrorBox, RefSelect } from '../components/ui'
import { calcStatus, eur, FEASIBILITY, noBidLabel, num, reasonLabel } from '../constants'

const FEAS = Object.fromEntries(FEASIBILITY.map((x) => [x.value, x.label]))

// Berichte: Schlüssel, Titel, Spaltenbezeichnung der Gruppe, Beschriftung des Schlüssels
const REPORTS = [
  ['machine_class', 'Maschinengröße (Schließkraft)', 'Größenklasse', (k) => k, 'In welchem Bereich kommen die meisten Anfragen, wo sagen wir ab oder verlieren?'],
  ['customer', 'Kunden', 'Kunde', (k) => k, 'Wer fragt am meisten an, welcher Anteil am angefragten Umsatz, wie oft gewinnen wir?'],
  ['no_bid_reasons', 'Absagen (kein Angebot abgegeben)', 'Grund', (k) => noBidLabel(k), 'Warum geben wir kein Angebot ab?'],
  ['lost_reasons', 'Verlorene Anfragen', 'Verlustgrund', (k) => reasonLabel(k), 'Warum verlieren wir angebotene Projekte?'],
  ['machine', 'Maschinen', 'Maschine', (k) => k, 'Für welche Maschine wird am meisten angefragt?'],
  ['material', 'Werkstoffe', 'Werkstoffgruppe', (k) => k, 'Welche Werkstoffe werden angefragt?'],
  ['owner', 'Vertrieb', 'Zuständig', (k) => k, 'Anfragen und Erfolgsquote je Vertriebsmitarbeiter.'],
  ['status', 'Status', 'Status', (k) => calcStatus(k).label, 'Wo stehen die Anfragen gerade?'],
  ['feasibility', 'Machbarkeit', 'Bewertung', (k) => FEAS[k] || k, 'Ergebnis der Machbarkeitsbewertung.'],
  ['month', 'Anfragen je Monat', 'Monat', (k) => (k.length === 7 ? new Date(`${k}-01`).toLocaleDateString('de-DE', { month: 'short', year: 'numeric' }) : k), 'Eingang nach Anfragedatum.'],
]
const pct = (v) => (v == null ? '–' : `${num(v, 1)} %`)

function csv(title, label, rows, keyLabel) {
  const head = [keyLabel, 'Anfragen', 'Anteil Anfragen %', 'angeboten', 'gewonnen', 'verloren', 'kein Angebot', 'offen',
    'Umsatz p. a. angefragt €', 'Anteil Umsatz %', 'gewonnen € p. a.', 'Trefferquote %', 'Absage-/Verlustquote %']
  const lines = rows.map((r) => [label(r.key), r.count, r.share_count_pct, r.quoted, r.won, r.lost, r.no_bid, r.open,
    r.revenue, r.share_revenue_pct, r.won_revenue, r.hit_rate_pct ?? '', r.decline_rate_pct])
  const body = [head, ...lines].map((l) => l.map((v) => {
    const s = typeof v === 'number' ? String(v).replace('.', ',') : String(v ?? '')
    return /[;"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }).join(';')).join('\r\n')
  const blob = new Blob(['﻿' + body], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `Auswertung_${title.replace(/[^\wäöüÄÖÜß]+/g, '_')}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

function ReportTable({ title, keyLabel, label, rows, question }) {
  const [metric, setMetric] = useState('count')
  const bars = useMemo(() => rows.slice(0, 12).map((r) => ({
    label: label(r.key),
    value: metric === 'count' ? r.count : metric === 'revenue' ? r.revenue : (r.no_bid + r.lost),
    note: metric === 'count' ? ` · ${pct(r.share_count_pct)}` : metric === 'revenue' ? ` · ${pct(r.share_revenue_pct)}` : ` · ${pct(r.decline_rate_pct)}`,
    tone: metric === 'decline' ? 'bad' : undefined,
  })), [rows, metric, label])
  return (
    <div className="card report-card">
      <div className="section-head">
        <div><h3>{title}</h3><p className="report-q">{question}</p></div>
        <div className="toolbar">
          <div className="seg">
            {[['count', 'Anzahl'], ['revenue', 'Umsatz'], ['decline', 'Absagen + Verluste']].map(([k, l]) =>
              <button key={k} className={metric === k ? 'on' : ''} onClick={() => setMetric(k)}>{l}</button>)}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => csv(title, label, rows, keyLabel)} title="Als CSV für Excel exportieren">CSV</button>
        </div>
      </div>
      {rows.length ? <>
        <BarList data={bars} format={metric === 'revenue' ? eur : (v) => num(v)} />
        <div className="table-wrap">
          <table className="table report-table">
            <thead><tr><th>{keyLabel}</th><th className="num">Anfragen</th><th className="num">Anteil</th><th className="num">angeboten</th>
              <th className="num">gewonnen</th><th className="num">verloren</th><th className="num">kein Angebot</th><th className="num">offen</th>
              <th className="num">Umsatz p. a. angefragt</th><th className="num">Anteil Umsatz</th><th className="num">gewonnen p. a.</th>
              <th className="num">Trefferquote</th><th className="num">Absage-/Verlustquote</th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.key}>
                <td><strong>{label(r.key)}</strong></td><td className="num">{num(r.count)}</td><td className="num">{pct(r.share_count_pct)}</td>
                <td className="num">{num(r.quoted)}</td><td className="num">{num(r.won)}</td><td className="num">{num(r.lost)}</td>
                <td className="num">{num(r.no_bid)}</td><td className="num">{num(r.open)}</td>
                <td className="num">{eur(r.revenue)}</td><td className="num">{pct(r.share_revenue_pct)}</td><td className="num">{eur(r.won_revenue)}</td>
                <td className="num">{pct(r.hit_rate_pct)}</td><td className="num">{pct(r.decline_rate_pct)}</td>
              </tr>))}</tbody>
          </table>
        </div>
      </> : <div className="empty small">Keine Daten im gewählten Zeitraum</div>}
    </div>
  )
}

export default function Reports() {
  const [f, setF] = useState({ date_from: '', date_to: '', owner_id: null, account_id: null })
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [show, setShow] = useState('machine_class')
  useEffect(() => {
    const q = new URLSearchParams()
    Object.entries(f).forEach(([k, v]) => { if (v) q.set(k, v) })
    api.get(`/reports?${q}`).then(setData).catch(setError)
  }, [f])
  const year = new Date().getFullYear()
  const s = data?.summary
  return (
    <div className="page">
      <div className="page-head">
        <div><h1>Auswertungen</h1><p className="muted">Anfragen und Kalkulationen nach Maschinengröße, Kunde, Absagegründen, Werkstoff, Vertrieb und Zeit</p></div>
        <div className="toolbar"><button className="btn btn-ghost no-print" onClick={() => window.print()}>Drucken / PDF</button></div>
      </div>
      <div className="card filters report-filters no-print">
        <div className="field"><label>Anfrage von</label><input type="date" value={f.date_from} onChange={(e) => setF({ ...f, date_from: e.target.value })} /></div>
        <div className="field"><label>bis</label><input type="date" value={f.date_to} onChange={(e) => setF({ ...f, date_to: e.target.value })} /></div>
        <div className="field"><label>Zeitraum</label>
          <div className="seg">
            <button onClick={() => setF({ ...f, date_from: `${year}-01-01`, date_to: `${year}-12-31` })}>{year}</button>
            <button onClick={() => setF({ ...f, date_from: `${year - 1}-01-01`, date_to: `${year - 1}-12-31` })}>{year - 1}</button>
            <button onClick={() => { const d = new Date(); d.setMonth(d.getMonth() - 12); setF({ ...f, date_from: d.toISOString().slice(0, 10), date_to: '' }) }}>12 Monate</button>
            <button onClick={() => setF({ ...f, date_from: '', date_to: '' })}>alle</button>
          </div></div>
        <div className="field"><label>Vertrieb</label><RefSelect kind="user" value={f.owner_id} onChange={(v) => setF({ ...f, owner_id: v })} /></div>
        <div className="field"><label>Kunde</label><RefSelect kind="account" value={f.account_id} onChange={(v) => setF({ ...f, account_id: v })} /></div>
      </div>
      <ErrorBox error={error} />
      {s && <div className="kpi-grid">
        <div className="kpi"><span className="kpi-label">Anfragen</span><span className="kpi-value">{num(s.count)}</span><span className="kpi-sub">{num(s.open)} offen</span></div>
        <div className="kpi"><span className="kpi-label">Angebotsquote</span><span className="kpi-value">{pct(s.quote_rate_pct)}</span><span className="kpi-sub">{num(s.quoted)} angeboten</span></div>
        <div className="kpi"><span className="kpi-label">Trefferquote</span><span className="kpi-value">{pct(s.hit_rate_pct)}</span><span className="kpi-sub">{num(s.won)} gewonnen / {num(s.lost)} verloren</span></div>
        <div className="kpi"><span className="kpi-label">Absagequote</span><span className="kpi-value">{pct(s.no_bid_rate_pct)}</span><span className="kpi-sub">{num(s.no_bid)} kein Angebot</span></div>
        <div className="kpi"><span className="kpi-label">Umsatz p. a. angefragt</span><span className="kpi-value">{eur(s.revenue)}</span><span className="kpi-sub">gewonnen {eur(s.won_revenue)}</span></div>
      </div>}
      {data && <>
        <div className="seg report-tabs no-print">
          {REPORTS.map(([k, t]) => <button key={k} className={show === k ? 'on' : ''} onClick={() => setShow(k)}>{t}</button>)}
          <button className={show === 'all' ? 'on' : ''} onClick={() => setShow('all')}>Alle Berichte</button>
        </div>
        {REPORTS.filter(([k]) => show === 'all' || show === k).map(([k, t, kl, lbl, q]) =>
          <ReportTable key={k} title={t} keyLabel={kl} label={lbl} rows={data[k] || []} question={q} />)}
        <p className="muted small">Grundlage: alle Kalkulationen (Anfragen) im Zeitraum nach Anfragedatum (sonst Anlagedatum); Umsatz = Jahresumsatz der aktuellen Version.
          Trefferquote = gewonnen / (gewonnen + verloren). Absage-/Verlustquote = (kein Angebot + verloren) / Anfragen. Maschinengröße nach Schließkraft der in der Kalkulation gewählten Maschine.</p>
      </>}
    </div>
  )
}
