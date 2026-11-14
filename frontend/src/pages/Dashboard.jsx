import { useState } from 'react'
import { Link } from 'react-router-dom'
import { qs } from '../api'
import { useAuth } from '../auth'
import { BarList, ColumnChart } from '../components/charts'
import { ErrorBox, RefSelect, useFetch } from '../components/ui'
import { eur, fmtDate, stageLabel } from '../constants'

const MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

function Kpi({ label, value, sub, to }) {
  const body = (
    <>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      {sub && <span className="kpi-sub">{sub}</span>}
    </>
  )
  return to ? <Link to={to} className="kpi kpi-link">{body}</Link> : <div className="kpi">{body}</div>
}

export default function Dashboard() {
  const { user } = useAuth()
  const [owner, setOwner] = useState(null)
  const { data, error } = useFetch('/dashboard' + qs({ owner_id: owner }))
  const cs = useFetch('/calculations/stats' + qs({ owner_id: owner }))
  if (error) return <ErrorBox error={error} />
  if (!data) return <div className="loading">Lade Dashboard…</div>
  const k = data.kpis

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Guten Tag, {user.name.split(' ')[0]}</h1>
          <p className="muted">Vertriebsübersicht · Stand {new Date().toLocaleDateString('de-DE')}</p>
        </div>
        <div className="toolbar">
          <label className="inline-label">Vertrieb
            <RefSelect kind="user" value={owner} onChange={setOwner} />
          </label>
        </div>
      </header>

      <section className="kpi-grid">
        <Kpi label="Offene Pipeline" value={eur(k.open_pipeline.amount)} sub={`${k.open_pipeline.count} Chancen · gewichtet ${eur(k.open_pipeline.weighted)}`} to="/pipeline" />
        <Kpi label={`Forecast ${k.quarter}`} value={eur(k.forecast_quarter.weighted)} sub={`gewichtet · bereits gewonnen ${eur(k.won_quarter.amount)}`} />
        <Kpi label="Gewonnen (lfd. Jahr)" value={eur(k.won_ytd.amount)} sub={`${k.won_ytd.count} Abschlüsse · Ø ${eur(k.avg_deal_won)}`} />
        <Kpi label="Gewinnquote" value={k.win_rate != null ? `${k.win_rate.toLocaleString('de-DE')} %` : '–'} sub={`${k.won_ytd.count} gewonnen / ${k.lost_ytd.count} verloren`} />
        <Kpi label="Offene Angebote" value={eur(k.open_quotes.amount)} sub={`${k.open_quotes.count} versendet`} to="/angebote" />
        <Kpi label="Aufgaben" value={k.activities_overdue} sub={`überfällig · ${k.activities_today} heute fällig`} to="/aktivitaeten" />
      </section>

      {cs.data && (
        <section className="kpi-grid">
          <Kpi label="Anfragen / Kalkulationen offen" value={cs.data.count_open} sub={`${cs.data.overdue_calls} seit > 14 Tagen ohne Anruf`} to="/kalkulationen" />
          <Kpi label="Potenzial Jahresumsatz" value={eur(cs.data.open_revenue)} sub={`gewichtet ${eur(cs.data.open_weighted)}`} to="/kalkulationen" />
          <Kpi label="★ Großprojekte offen" value={cs.data.big_open_count} sub={`${eur(cs.data.big_open_revenue)} p. a. · Invest ${eur(cs.data.big_open_invest)}`} to="/kalkulationen" />
          <Kpi label="Werkzeuge offen" value={eur(cs.data.open_tooling)} sub="Einmalumsatz in offenen Kalkulationen" />
          <Kpi label="Trefferquote Kalkulationen" value={cs.data.hit_rate != null ? `${cs.data.hit_rate.toLocaleString('de-DE')} %` : '–'} sub={`${cs.data.won_count} gewonnen / ${cs.data.lost_count} verloren`} />
          <Kpi label="Nachkalkulation" value={`${cs.data.traffic_lights.gruen} / ${cs.data.traffic_lights.gelb} / ${cs.data.traffic_lights.rot}`} sub="grün / gelb / rot" to="/kalkulationen" />
        </section>
      )}

      <section className="grid-2">
        <div className="card">
          <h3>Gewonnener Umsatz je Monat</h3>
          <p className="card-sub">Letzte 12 Monate, netto</p>
          <ColumnChart ariaLabel="Gewonnener Umsatz je Monat"
            data={data.monthly_won.map((m) => {
              const [y, mo] = m.month.split('-')
              return { label: MONTHS[Number(mo) - 1], sub: `${MONTHS[Number(mo) - 1]} ${y}`, value: m.amount }
            })} />
        </div>
        <div className="card">
          <h3>Pipeline nach Phase</h3>
          <p className="card-sub">Volumen netto · Anzahl Chancen</p>
          <BarList data={data.by_stage.map((s) => ({
            label: stageLabel(s.stage), value: s.amount, note: `${s.count}×`,
            tone: s.stage === 'gewonnen' ? 'good' : s.stage === 'verloren' ? 'muted' : undefined,
          }))} />
        </div>
      </section>

      <section className="grid-2">
        <div className="card">
          <h3>Vertrieb im Vergleich</h3>
          <table className="table table-compact">
            <thead><tr><th>Mitarbeiter</th><th className="num">Offen</th><th className="num">Gewichtet</th><th className="num">Gewonnen lfd. J.</th></tr></thead>
            <tbody>
              {data.by_owner.map((o) => (
                <tr key={o.user.id}>
                  <td>{o.user.name}</td>
                  <td className="num">{eur(o.open_amount)} <small className="muted">({o.open_count})</small></td>
                  <td className="num">{eur(o.weighted)}</td>
                  <td className="num">{eur(o.won_ytd)}</td>
                </tr>
              ))}
              {!data.by_owner.length && <tr><td colSpan={4} className="muted">Keine Daten</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h3>Abschluss in den nächsten 30 Tagen</h3>
          <table className="table table-compact">
            <thead><tr><th>Chance</th><th>Phase</th><th>Datum</th><th className="num">Volumen</th></tr></thead>
            <tbody>
              {data.closing_soon.map((o) => (
                <tr key={o.id}>
                  <td><Link to={`/firmen/${o.account?.id}`}>{o.name}</Link><br /><small className="muted">{o.account?.name}</small></td>
                  <td>{stageLabel(o.stage)}</td>
                  <td className={new Date(o.close_date) < new Date(new Date().toDateString()) ? 'text-critical' : ''}>{fmtDate(o.close_date)}</td>
                  <td className="num">{eur(o.amount)}</td>
                </tr>
              ))}
              {!data.closing_soon.length && <tr><td colSpan={4} className="muted">Nichts fällig</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h3>Größte offene Chancen</h3>
        <table className="table table-compact">
          <thead><tr><th>Chance</th><th>Firma</th><th>Phase</th><th className="num">Wahrsch.</th><th>Verantwortlich</th><th className="num">Volumen</th></tr></thead>
          <tbody>
            {data.top_open.map((o) => (
              <tr key={o.id}>
                <td>{o.name}</td>
                <td><Link to={`/firmen/${o.account?.id}`}>{o.account?.name}</Link></td>
                <td>{stageLabel(o.stage)}</td>
                <td className="num">{o.probability} %</td>
                <td>{o.owner?.name}</td>
                <td className="num">{eur(o.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
