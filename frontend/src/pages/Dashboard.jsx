import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { qs } from '../api'
import { useAuth } from '../auth'
import { BarList, ColumnChart } from '../components/charts'
import { ErrorBox, RefSelect, useFetch } from '../components/ui'
import { eur, fmtDate, num, probLabel, stageLabel } from '../constants'
import FollowupDialog, { LightBadge } from '../components/Followup'

const MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

function Kpi({ label, value, sub, to }) {
  const body = (
    <>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      {sub && <span className="kpi-sub">{sub}</span>}
    </>
  )
  if (to?.startsWith('#')) return <a href={to} className="kpi kpi-link">{body}</a>
  return to ? <Link to={to} className="kpi kpi-link">{body}</Link> : <div className="kpi">{body}</div>
}

// REV04-04: Vertriebsziel groß oben – Erfüllungsgrad auf einen Blick, Soll-Marke = wo wir heute stehen müssten
const LIGHT = { gruen: ['im Plan', 'good'], gelb: ['knapp hinter Plan', 'warning'], rot: ['deutlich hinter Plan', 'critical'] }
function GoalBlock({ g }) {
  const nav = useNavigate()
  const { isAdmin } = useAuth()
  const yr = new Date().getFullYear()
  if (!g) return (
    <section className="card goal-block goal-empty">
      <h2>Vertriebsziel {yr}</h2>
      <p className="muted">Für {yr} ist noch kein Vertriebsziel hinterlegt.{isAdmin ? ' Eintragen unter ' : ' Das Ziel trägt ein Administrator ein unter '}
        <Link to="/monatsbericht">Monatsbericht → Vertriebsziele</Link></p>
    </section>)
  const [lt, tone] = LIGHT[g.light] || ['–', 'neutral']
  const pctW = Math.min(100, g.pct)
  return (
    <section className="card goal-block" role="link" tabIndex={0} onClick={() => nav('/monatsbericht')} onKeyDown={(e) => e.key === 'Enter' && nav('/monatsbericht')}
      title="Monatsbericht öffnen">
      <div className="goal-top">
        <div>
          <h2>Vertriebsziel {g.year} · Neuumsatz</h2>
          <p className="muted">gewonnen seit 1.1. (Umsatz im stärksten Lieferjahr){g.summed ? ' · Ziel = Summe der Ziele je Vertriebler' : ''}</p>
        </div>
        <span className={`goal-light goal-${tone}`}><span aria-hidden>●</span> {lt}</span>
      </div>
      <div className="goal-main">
        <div className="goal-pct">{g.pct.toLocaleString('de-DE', { maximumFractionDigits: 1 })} %</div>
        <div className="goal-figs">
          <div><span className="goal-k">Gewonnen</span><strong>{eur(g.achieved)}</strong><small className="muted">{g.count} Abschlüsse</small></div>
          <div><span className="goal-k">Jahresziel</span><strong>{eur(g.target)}</strong></div>
          <div><span className="goal-k">Soll heute</span><strong>{eur(g.expected)}</strong><small className="muted">{g.expected_pct.toLocaleString('de-DE')} % des Jahres</small></div>
          <div><span className="goal-k">Noch bis zum Ziel</span><strong>{eur(g.gap)}</strong></div>
        </div>
      </div>
      <div className="goal-bar" aria-label={`Erfüllungsgrad ${g.pct} %, Soll heute ${g.expected_pct} %`}>
        <span className="goal-fill" style={{ width: `${pctW}%` }} />
        <span className="goal-soll" style={{ left: `${Math.min(100, g.expected_pct)}%` }} title={`Soll heute: ${g.expected_pct} %`}><em>Soll heute</em></span>
      </div>
      <div className="goal-scale"><span>0 %</span><span>100 % = {eur(g.target)}</span></div>
      {g.owners?.length > 0 && <table className="table table-compact goal-owners">
        <thead><tr><th>Vertrieb</th><th className="num">Gewonnen</th><th className="num">Eigenes Ziel</th><th className="num">Erfüllt</th><th>Stand</th></tr></thead>
        <tbody>{g.owners.map((o) => <tr key={o.user_id}>
          <td>{o.name}</td><td className="num">{eur(o.achieved)}</td><td className="num">{o.target ? eur(o.target) : '–'}</td>
          <td className="num">{o.pct != null ? `${o.pct.toLocaleString('de-DE')} %` : '–'}</td>
          <td>{o.light ? <span className={`goal-light-sm goal-${LIGHT[o.light][1]}`}>● {LIGHT[o.light][0]}</span> : <small className="muted">ohne eigenes Ziel</small>}</td></tr>)}</tbody>
      </table>}
      <p className="goal-more">Details im Monatsbericht ›</p>
    </section>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [owner, setOwner] = useState(null)
  const { data, error } = useFetch('/dashboard' + qs({ owner_id: owner }))
  const cs = useFetch('/calculations/stats' + qs({ owner_id: owner }))
  const ut = useFetch('/calc/utilization?years=3')
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

      <GoalBlock g={k.sales_goal} />

      <section className="kpi-grid">
        <Kpi label="Offene Pipeline" value={eur(k.open_pipeline.amount)} sub={`${k.open_pipeline.count} Anfragen · davon ≥ 50 % Wahrsch. ${eur(k.open_pipeline.likely)}`} to="/pipeline" />
        <Kpi label={`Entscheidung ${k.quarter}`} value={eur(k.forecast_quarter.amount)} sub={`${k.forecast_quarter.count} Anfragen · bereits gewonnen ${eur(k.won_quarter.amount)}`} to="/anfragen" />
        <Kpi label="Gewonnen (lfd. Jahr)" value={eur(k.won_ytd.amount)} sub={`${k.won_ytd.count} Abschlüsse · Ø ${eur(k.avg_deal_won)}`} />
        <Kpi label="Gewinnquote" value={k.win_rate != null ? `${k.win_rate.toLocaleString('de-DE')} %` : '–'} sub={`${k.won_ytd.count} gewonnen / ${k.lost_ytd.count} verloren · Übersicht ›`} to="/auswertungen" />
        <Kpi label="Offene Angebote" value={eur(k.open_quotes.amount)} sub={`${k.open_quotes.count} versendet`} to="/angebote" />
        <Kpi label="Aufgaben" value={k.activities_overdue} sub={`überfällig · ${k.activities_today} heute fällig`} to="/aktivitaeten" />
        <Kpi label="Angebotsverfolgung" value={<span className="lights"><span className="l-rot">● {k.followups.rot}</span> <span className="l-gelb">● {k.followups.gelb}</span> <span className="l-gruen">● {k.followups.gruen}</span></span>}
          sub="überfällig · fällig · im Plan" to="#verfolgung" />
        <Kpi label="Endrunde (lfd. Jahr)" value={`${k.final_round.gewonnen} / ${k.final_round.verloren}`} sub="gewonnen / verloren nach Verhandlung" to="/pipeline" />
      </section>

      <MyApprovals />
      <Followups />

      {cs.data && (
        <section className="kpi-grid">
          <Kpi label="Anfragen in Bearbeitung" value={cs.data.count_inquiries} sub="noch ohne Angebot (Anfrage / Kalkulation)" to="/kalkulationen?status=kalkulation" />
          <Kpi label="Angebote beim Kunden" value={cs.data.count_offered} sub={`${eur(cs.data.offered_revenue)} p. a. · ${cs.data.overdue_calls} seit > 14 Tagen ohne Anruf`} to="/kalkulationen?status=angeboten" />
          <Kpi label="Potenzial Jahresumsatz" value={eur(cs.data.open_revenue)} sub="alle offenen Artikel, ungewichtet" to="/kalkulationen" />
          <Kpi label="★ Großprojekte offen" value={cs.data.big_open_count} sub={`${eur(cs.data.big_open_revenue)} p. a. · Invest ${eur(cs.data.big_open_invest)}`} to="/kalkulationen?big=true" />
          {ut.data && <Kpi label={`Auslastung ${ut.data.totals[1]?.year} (erwartet)`} value={`${num(ut.data.totals[1]?.pct_expected, 0)} %`}
            sub={`fest ${num(ut.data.totals[1]?.pct_fixed, 0)} % · max. ${num(ut.data.totals[1]?.pct_max, 0)} %`} to="/auslastung" />}
          <Kpi label="Werkzeuge offen" value={eur(cs.data.open_tooling)} sub="Einmalumsatz in offenen Kalkulationen" />
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
            <thead><tr><th>Mitarbeiter</th><th className="num">Offen</th><th className="num">Gewonnen lfd. J.</th></tr></thead>
            <tbody>
              {data.by_owner.map((o) => (
                <tr key={o.user.id}>
                  <td>{o.user.name}</td>
                  <td className="num">{eur(o.open_amount)} <small className="muted">({o.open_count})</small></td>
                  <td className="num">{eur(o.won_ytd)}</td>
                </tr>
              ))}
              {!data.by_owner.length && <tr><td colSpan={3} className="muted">Keine Daten</td></tr>}
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
                  <td><Link to={`/anfragen/${o.id}`}>{o.number} {o.name}</Link><br /><small className="muted">{o.account?.name}</small></td>
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
                <td><Link to={`/anfragen/${o.id}`}>{o.number} {o.name}</Link></td>
                <td><Link to={`/firmen/${o.account?.id}`}>{o.account?.name}</Link></td>
                <td>{stageLabel(o.stage)}</td>
                <td className="num">{probLabel(o)}</td>
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

// REV02-02: Freigaben, die auf mich warten (Vier-Augen-Prinzip)
function MyApprovals() {
  const { data } = useFetch('/calc/approvals/mine')
  if (!data || !data.length) return null
  return (
    <section className="card card-attn" id="freigaben">
      <h3>Freigaben für mich ({data.length})</h3>
      <p className="card-sub">Kalkulationen über der Freigabeschwelle – bitte prüfen und in der Kalkulation freigeben oder ablehnen</p>
      <table className="table table-compact">
        <thead><tr><th>Kalkulation</th><th>Kunde</th><th>Grund</th><th>angefragt von</th><th>seit</th><th>an</th><th>Begründung</th></tr></thead>
        <tbody>{data.map((a) => (
          <tr key={a.id}><td><Link to={`/kalkulationen/${a.id}`}><strong>{a.number}</strong></Link> V{a.version}<br /><small className="muted">{a.name}</small></td>
            <td>{a.account || '–'}</td><td><small>{a.reasons.join(' · ') || '–'}</small></td><td>{a.requested_by}</td><td>{fmtDate(a.requested_at)}</td>
            <td><small>{a.to}</small></td><td><small>{a.comment || '–'}</small></td></tr>))}</tbody>
      </table>
    </section>
  )
}

// Angebotsverfolgung für alle sichtbar (auch Gesellschafter) – rot = Rücksprache überfällig (REV01-P06)
function Followups() {
  const { canWrite } = useAuth()
  const { data, reload } = useFetch('/followups')
  const [fu, setFu] = useState(null)
  if (!data || !data.items.length) return null
  return (
    <section className="card" id="verfolgung">
      <h3>Angebotsverfolgung</h3>
      <p className="card-sub">Rücksprache mit dem Kunden spätestens 5 Arbeitstage nach Versand · „niemanden erreicht“ legt die Aufgabe auf den nächsten Arbeitstag</p>
      <table className="table table-compact">
        <thead><tr><th>Ampel</th><th>Angebot</th><th>Kunde</th><th>Versendet</th><th>Zuständig</th><th>Letzte Rückmeldung</th><th className="num">Netto</th><th /></tr></thead>
        <tbody>{data.items.map((a) => (
          <tr key={a.id} className={a.light === 'rot' ? 'row-big' : ''}>
            <td><LightBadge light={a.light} due={a.due_at} />{a.attempts > 0 && <><br /><small className="muted">{a.attempts}× nicht erreicht</small></>}</td>
            <td><Link to={`/angebote/${a.quote?.id}`}>{a.quote_number}</Link><br /><small className="muted">{a.quote?.title}</small></td>
            <td>{a.account?.name || '–'}</td>
            <td>{fmtDate(a.sent_at)}</td>
            <td>{a.owner?.name || '–'}</td>
            <td><small>{a.last_contact_note || '–'}</small></td>
            <td className="num">{eur(a.quote_total)}</td>
            <td>{canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setFu(a)}>Rücksprache</button>}</td>
          </tr>))}
        </tbody>
      </table>
      {fu && <FollowupDialog task={fu} onClose={() => setFu(null)} onDone={() => { setFu(null); reload() }} />}
    </section>
  )
}
