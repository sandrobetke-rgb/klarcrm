import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import NumInput from '../components/NumInput'
import { Badge, ErrorBox, Modal, useFetch } from '../components/ui'
import { eur, fmtDate, fmtDateTime, num, stageLabel } from '../constants'

// Monatsbericht Vertrieb für Geschäftsführung und Gesellschafter: Neuumsatz gegen Ziel, gewonnen/verloren, offen,
// Handlungsbedarf, Auslastung, Preisliste. Live-Stand oder gespeicherter (eingefrorener) Bericht, Druck als PDF.
const MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
const LIGHT = { gruen: ['good', 'im Plan'], gelb: ['warning', 'knapp unter Plan'], rot: ['critical', 'unter Plan'] }
const pct = (v) => (v == null ? '–' : `${num(v, 1)} %`)
const keur = (v) => (v == null ? '–' : Math.abs(v) >= 1e6 ? `${num(v / 1e6, 2)} Mio. €` : eur(v))

function prevMonth() {
  const d = new Date(); d.setDate(1); d.setMonth(d.getMonth() - 1)
  return { year: d.getFullYear(), month: d.getMonth() + 1 }
}

export default function MonthlyReport() {
  const { user, isAdmin, canWrite } = useAuth()
  const [sel, setSel] = useState(prevMonth)
  const [saved, setSaved] = useState(null)     // gespeicherter Bericht (mit data)
  const [live, setLive] = useState(null)
  const [comment, setComment] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [targets, setTargets] = useState(false)
  const { data: list, reload: reloadList } = useFetch('/monthly-reports')

  useEffect(() => {
    setLive(null); setErr(null)
    if (saved) return
    api.get(`/monthly-reports/live?year=${sel.year}&month=${sel.month}`).then(setLive).catch(setErr)
  }, [sel.year, sel.month, saved])

  const data = saved?.data || live
  const openSaved = async (id) => { setErr(null); try { const r = await api.get(`/monthly-reports/${id}`); setSaved(r); setComment(r.comment || ''); setSel({ year: r.year, month: r.month }) } catch (e) { setErr(e) } }
  async function freeze() {
    setBusy(true); setErr(null)
    try { const r = await api.post('/monthly-reports', { year: sel.year, month: sel.month, comment }); setSaved(r); reloadList() } catch (e) { setErr(e) } finally { setBusy(false) }
  }
  async function patch(body) {
    setErr(null)
    try { const r = await api.patch(`/monthly-reports/${saved.id}`, body); setSaved(r); reloadList() } catch (e) { setErr(e) }
  }
  const canRelease = isAdmin || user?.can_approve
  const years = [new Date().getFullYear() - 1, new Date().getFullYear()]

  return (
    <div className="page page-wide report-page">
      <div className="no-print">
        <header className="page-head">
          <div><h1>Monatsbericht Vertrieb</h1>
            <p className="muted">Neuumsatz gegen Ziel, gewonnen und verloren, offene Pipeline, Handlungsbedarf und Auslastung – als PDF für die Gesellschafter.</p></div>
          <div className="toolbar">
            {isAdmin && <button className="btn btn-ghost" onClick={() => setTargets(true)}>Vertriebsziele</button>}
            <button className="btn btn-ghost" onClick={() => window.print()} disabled={!data}>Drucken / PDF</button>
          </div>
        </header>
        <div className="filters">
          <select value={sel.month} onChange={(e) => { setSaved(null); setSel({ ...sel, month: Number(e.target.value) }) }}>{MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}</select>
          <select value={sel.year} onChange={(e) => { setSaved(null); setSel({ ...sel, year: Number(e.target.value) }) }}>{years.map((y) => <option key={y}>{y}</option>)}</select>
          {saved ? <Badge tone={saved.status === 'freigegeben' ? 'good' : 'info'}>gespeicherter Stand {fmtDateTime(saved.updated_at)} · {saved.status}</Badge>
            : <Badge tone="warning">Live-Stand (aktuelle Daten)</Badge>}
          {saved && <button className="btn btn-ghost btn-sm" onClick={() => setSaved(null)}>Live-Stand zeigen</button>}
          <span className="spacer" />
          <select value="" onChange={(e) => e.target.value && openSaved(Number(e.target.value))}>
            <option value="">Gespeicherte Berichte ({list?.length || 0})…</option>
            {(list || []).map((r) => <option key={r.id} value={r.id}>{r.label} · {r.status} · {fmtDate(r.updated_at)}</option>)}
          </select>
          {canWrite && (!saved || saved.status === 'entwurf') && <button className="btn btn-primary" disabled={busy || !data} onClick={freeze}>{saved ? 'Stand aktualisieren' : 'Stand speichern'}</button>}
          {saved && canRelease && saved.status === 'entwurf' && <button className="btn btn-primary" onClick={() => patch({ status: 'freigegeben', comment })}>Freigeben</button>}
          {saved && isAdmin && saved.status === 'freigegeben' && <button className="btn btn-ghost btn-sm" onClick={() => patch({ status: 'entwurf' })}>Freigabe zurücknehmen</button>}
        </div>
        <ErrorBox error={err} />
        <p className="small muted">Neuumsatz = Umsatz des stärksten Lieferjahres der gewonnenen Artikel (z. B. 0,5 / 1,0 / 1,5 Mio. € → 1,5 Mio. €). „Stand speichern“ friert die Zahlen ein,
          damit sich der Bericht nachträglich nicht mehr ändert; „Freigeben“ schließt ihn ab.</p>
      </div>
      {!data ? <div className="loading">Lade…</div> : <Report d={data} saved={saved} comment={comment} setComment={setComment}
        editable={canWrite && (!saved || saved.status === 'entwurf')} onSaveComment={saved ? () => patch({ comment }) : null} />}
      {targets && <TargetsDialog year={sel.year} onClose={() => { setTargets(false); if (!saved) setSel({ ...sel }) }} />}
    </div>
  )
}

function Report({ d, saved, comment, setComment, editable, onSaveComment }) {
  const k = d.kpi
  const t = d.target
  return (
    <article className="report">
      <header className="report-head">
        <div><h1>Monatsbericht Vertrieb · {d.label}</h1>
          <p className="muted">Stand {fmtDateTime(d.generated_at)}{saved?.status === 'freigegeben' ? ` · freigegeben ${fmtDate(saved.released_at)} ${saved.released_by || ''}` : saved ? ' · Entwurf' : ' · Live-Stand'}</p></div>
      </header>

      {/* 1 Zielerreichung */}
      <section className="report-sec">
        <h2>1 · Vertriebsziel {d.year}: Neuumsatz</h2>
        {t ? <>
          <div className="goal">
            <div className="goal-main">
              <div className="goal-num">{keur(t.achieved)} <span className="muted">von {keur(t.target)}</span></div>
              <div className="goal-sub"><strong>{pct(t.pct)}</strong> des Jahresziels erreicht · Soll bis Ende {MONTHS[d.month - 1]}: {keur(t.expected)} · es fehlen noch <strong>{keur(Math.max(t.gap, 0))}</strong>
                {t.light && <> <Badge tone={LIGHT[t.light][0]}>● {LIGHT[t.light][1]}</Badge></>}</div>
              <Progress value={t.achieved} max={t.target} mark={t.expected} />
              {t.summed && <small className="muted">Jahresziel = Summe der Ziele je Vertriebler (kein eigenes Gesamtziel hinterlegt)</small>}
            </div>
            {t.one_time_target ? <div className="goal-side">
              <div className="small muted">Werkzeug- und Einmalumsatz</div>
              <div><strong>{keur(t.one_time_achieved)}</strong> von {keur(t.one_time_target)} ({pct(t.one_time_pct)})</div>
              <Progress value={t.one_time_achieved} max={t.one_time_target} mark={t.one_time_target * d.month / 12} small />
            </div> : null}
          </div>
          {d.by_owner.length > 0 && <table className="rtable">
            <thead><tr><th>Vertrieb</th><th className="num">Neuumsatz {MONTHS[d.month - 1]}</th><th className="num">seit Jahresbeginn</th><th className="num">Ziel</th><th className="num">erreicht</th><th>Plan</th><th className="num">Werkzeug/Einmal</th></tr></thead>
            <tbody>{d.by_owner.map((o) => <tr key={o.user_id}><td>{o.name}</td><td className="num">{eur(o.month)}</td><td className="num"><strong>{eur(o.annual)}</strong></td>
              <td className="num">{o.target ? eur(o.target.target) : '–'}</td><td className="num">{o.target ? pct(o.target.pct) : '–'}</td>
              <td>{o.target?.light && <Badge tone={LIGHT[o.target.light][0]}>●</Badge>}</td><td className="num">{eur(o.one_time)}</td></tr>)}</tbody>
          </table>}
        </> : <p className="muted">Für {d.year} ist noch kein Vertriebsziel hinterlegt (Administrator: „Vertriebsziele“).</p>}
        <CumChart series={d.series} year={d.year} month={d.month} />
      </section>

      {/* 2 Kennzahlen */}
      <section className="report-sec">
        <h2>2 · Kennzahlen</h2>
        <div className="rkpis">
          <RK l={`Neuumsatz gewonnen im ${MONTHS[d.month - 1]}`} v={keur(k.won_month.annual)} s={`${k.won_month.count} Artikel`} />
          <RK l={`Neuumsatz gewonnen seit 1.1.${d.year}`} v={keur(k.won_ytd.annual)} s={`${k.won_ytd.count} Artikel${d.target ? ` · ${pct(d.target.pct)} vom Jahresziel` : ''}`} />
          <RK l="Werkzeug/Einmal seit Jahresbeginn" v={keur(k.won_ytd.one_time)} s={`im Monat ${keur(k.won_month.one_time)}`} />
          <RK l="Gewinnquote (lfd. Jahr)" v={pct(k.win_rate_ytd)} s={`Endrunde: ${k.final_round_ytd.won} gewonnen / ${k.final_round_ytd.lost} verloren`} />
          <RK l="Verloren im Monat" v={keur(k.lost_month.annual)} s={`${k.lost_month.count} Artikel · nicht angeboten ${k.nobid_month.count}`} />
          <RK l="Neue Anfragen" v={k.new_inquiries.count} s={`Volumen ${keur(k.new_inquiries.amount)}`} />
          <RK l="Angebote versendet" v={k.quotes_sent.count} s={`netto ${keur(k.quotes_sent.amount)}`} />
          <RK l="Durchlaufzeit Anfrage → Angebot" v={k.lead_time.avg != null ? `${num(k.lead_time.avg, 1)} AT` : '–'} s={`Ziel ${num(k.lead_time.target)} AT · ${k.lead_time.within}/${k.lead_time.count} im Ziel`} />
          <RK l="Kalkulierte Artikel" v={k.articles_calculated} s="mit neuer Version im Monat" />
          <RK l="Offene Pipeline" v={keur(k.open_pipeline.amount)} s={`${k.open_pipeline.count} Anfragen / Leads`} />
        </div>
      </section>

      {/* 3 Gewonnen */}
      <section className="report-sec">
        <h2>3 · Gewonnen im {MONTHS[d.month - 1]}</h2>
        {d.won.length ? <table className="rtable">
          <thead><tr><th>Artikel</th><th>Kunde</th><th>Vertrieb</th><th>Maschine</th><th>SOP</th><th className="num">Neuumsatz (Spitzenjahr)</th><th className="num">Jahr 1</th><th className="num">Werkzeug/Einmal</th></tr></thead>
          <tbody>{d.won.map((w) => <tr key={w.type + w.id}><td><strong>{w.number}</strong> {w.name}</td><td>{w.account}</td><td>{w.owner}</td><td>{w.machine || '–'}</td><td>{fmtDate(w.sop)}</td>
            <td className="num"><strong>{eur(w.annual)}</strong></td><td className="num">{eur(w.first_year)}</td><td className="num">{eur(w.one_time)}</td></tr>)}</tbody>
        </table> : <p className="muted">Kein Auftrag im Monat gewonnen.</p>}
        {d.won_ytd_list.length > 0 && <>
          <h3>Gewonnen seit 1.1.{d.year} ({k.won_ytd.count} Artikel · {keur(k.won_ytd.annual)} Neuumsatz)</h3>
          <table className="rtable"><thead><tr><th>gewonnen am</th><th>Artikel</th><th>Kunde</th><th>Vertrieb</th><th className="num">Neuumsatz</th><th className="num">Werkzeug/Einmal</th></tr></thead>
            <tbody>{d.won_ytd_list.map((w) => <tr key={w.type + w.id}><td>{fmtDate(w.date)}</td><td><strong>{w.number}</strong> {w.name}</td><td>{w.account}</td><td>{w.owner}</td>
              <td className="num">{eur(w.annual)}</td><td className="num">{eur(w.one_time)}</td></tr>)}</tbody></table></>}
      </section>

      {/* 4 Verloren */}
      <section className="report-sec">
        <h2>4 · Verloren und nicht angeboten</h2>
        {d.lost.length || d.nobid.length || d.variants?.length ? <>
          {d.reasons.length > 0 && <p>Verlustgründe: {d.reasons.map((r) => `${r.reason} (${r.count}× · ${keur(r.annual)})`).join(' · ')}</p>}
          <table className="rtable"><thead><tr><th>Artikel</th><th>Kunde</th><th>Grund</th><th>Endrunde</th><th className="num">Neuumsatz</th></tr></thead>
            <tbody>{d.lost.map((l) => <tr key={l.id}><td><strong>{l.number}</strong> {l.name}</td><td>{l.account}</td><td>{l.reason}</td><td>{l.final_round ? 'ja' : ''}</td><td className="num">{eur(l.annual)}</td></tr>)}
              {(d.variants || []).map((l) => <tr key={`v${l.id}`} className="muted"><td><strong>{l.number}</strong> {l.name}</td><td>{l.account}</td><td>{l.reason} (kein Verlust)</td><td /><td className="num">{eur(l.annual)}</td></tr>)}
              {d.nobid.map((l) => <tr key={`n${l.id}`} className="muted"><td><strong>{l.number}</strong> {l.name}</td><td>{l.account}</td><td>nicht angeboten: {l.reason}</td><td /><td className="num">{eur(l.annual)}</td></tr>)}</tbody></table>
        </> : <p className="muted">Im Monat nichts verloren.</p>}
      </section>

      {/* 5 Offen */}
      <section className="report-sec">
        <h2>5 · Offene Pipeline</h2>
        <div className="pipe-strip">{d.pipeline.map((p) => <div key={p.stage}><span>{stageLabel(p.stage)}</span><strong>{p.count}</strong><small>{keur(p.amount)}</small></div>)}</div>
        <h3>Größte offene Anfragen</h3>
        <table className="rtable"><thead><tr><th>Anfrage</th><th>Kunde</th><th>Phase</th><th>Vertrieb</th><th>Entscheidung</th><th className="num">Wahrsch.</th><th className="num">Volumen</th></tr></thead>
          <tbody>{d.top_open.map((o) => <tr key={o.id}><td>{o.big && '★ '}<strong>{o.number}</strong> {o.name}</td><td>{o.account}</td><td>{stageLabel(o.stage)}</td><td>{o.owner}</td><td>{fmtDate(o.close_date)}</td><td className="num">{o.probability} %</td><td className="num">{eur(o.amount)}</td></tr>)}</tbody></table>
        {d.due_next.length > 0 && <p><strong>Entscheidung im Folgemonat erwartet:</strong> {d.due_next.map((o) => `${o.number} ${o.name} (${keur(o.amount)})`).join(' · ')}</p>}
      </section>

      {/* 6 Handlungsbedarf */}
      <section className="report-sec">
        <h2>6 · Wo fehlt etwas? (Stand heute)</h2>
        <ul className="actions-list">
          <Act n={d.actions.followups_red.length} l="Angebotsverfolgung überfällig (rot)" items={d.actions.followups_red.map((a) => `${a.quote} ${a.account || ''} – fällig ${fmtDate(a.due)}${a.attempts ? `, ${a.attempts}× nicht erreicht` : ''} (${a.owner || '–'})`)} />
          <Act n={d.actions.undecided.length} l="Anfragen ohne Entscheidung (anbieten / nicht anbieten)" items={d.actions.undecided.map((a) => `${a.number} ${a.name} – ${a.account || ''}`)} />
          <Act n={d.actions.overdue_due.length} l="Abgabetermin überschritten, noch kein Angebot" items={d.actions.overdue_due.map((o) => `${o.number} ${o.name} – Abgabe ${fmtDate(o.close_date)}`)} />
          <Act n={d.actions.approvals.length} l="Freigaben offen" items={d.actions.approvals.map((a) => `${a.number} ${a.name}: ${a.reasons.join(', ')}`)} />
          <Act n={d.actions.analysis_missing.length} l="Artikelanalyse unvollständig" items={d.actions.analysis_missing.map((a) => `${a.number} ${a.name}`)} />
        </ul>
      </section>

      {/* 7 Auslastung */}
      <section className="report-sec">
        <h2>7 · Auslastung {d.utilization.year} aus Bestand und gewonnenen Projekten</h2>
        <p className="small muted">Gesamt {pct(d.utilization.pct_fixed)} fest belegt. Spalte „mit Großprojekten“: falls die offenen Großprojekte zusätzlich gewonnen werden. Ampel: ab 85 % knapp, ab 100 % überlastet.</p>
        <table className="rtable"><thead><tr><th>Maschine</th><th className="num">Kapazität h</th><th className="num">fest belegt</th><th className="num">mit Großprojekten</th><th>gewonnene Projekte</th></tr></thead>
          <tbody>{d.utilization.machines.map((m, i) => <tr key={`${m.number}-${m.machine}-${i}`}><td>{m.number ? `${m.number} · ` : ''}{m.machine}</td><td className="num">{num(m.capacity_h)}</td>
            <td className="num"><UtilBar v={m.pct_fixed} /></td><td className="num">{m.pct_with_big !== m.pct_fixed ? <UtilBar v={m.pct_with_big} /> : <span className="muted">–</span>}</td>
            <td className="small">{m.won_projects.join(', ')}</td></tr>)}</tbody></table>
      </section>

      {/* 8 Preisliste */}
      <section className="report-sec">
        <h2>8 · Preisliste / Materialpreise</h2>
        {d.pricelist.changes ? <p>{d.pricelist.changes} Preisänderung(en) mit {d.pricelist.articles} betroffenen Artikeln, Jahreseffekt {keur(d.pricelist.effect)} –
          davon an Kunden weitergegeben {keur(d.pricelist.passed)}, vertraglich gebunden {keur(d.pricelist.contract)}, noch offen {d.pricelist.open} Artikel.</p>
          : <p className="muted">Keine Material- oder VK-Preisänderung im Monat.</p>}
      </section>

      {/* 9 Kommentar */}
      <section className="report-sec">
        <h2>9 · Kommentar der Geschäftsführung</h2>
        {editable ? <div className="no-print">
          <textarea rows={5} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Einordnung des Monats, Schwerpunkte, Risiken, nächste Schritte …" />
          {onSaveComment && <button className="btn btn-ghost btn-sm" onClick={onSaveComment}>Kommentar speichern</button>}
          {!onSaveComment && <small className="hint">Wird mit „Stand speichern“ übernommen.</small>}
        </div> : null}
        <div className={editable ? 'print-only pre' : 'pre'}>{comment || (editable ? '' : '–')}</div>
      </section>
      <footer className="report-foot">KlarCRM · Monatsbericht {d.label} · vertraulich – nur für Geschäftsführung und Gesellschafter</footer>
    </article>
  )
}

const RK = ({ l, v, s }) => <div className="rk"><span>{l}</span><strong>{v}</strong>{s && <small>{s}</small>}</div>

function Act({ n, l, items }) {
  return (
    <li className={n ? 'has' : 'ok'}><strong>{n ? `${n} × ` : '✓ '}{l}</strong>
      {n > 0 && <ul>{items.slice(0, 8).map((x, i) => <li key={i}>{x}</li>)}{n > 8 && <li>… und {n - 8} weitere</li>}</ul>}</li>
  )
}

function Progress({ value, max, mark, small }) {
  const p = max ? Math.min(100, (value / max) * 100) : 0
  const m = max ? Math.min(100, (mark / max) * 100) : null
  return (
    <div className={`progress ${small ? 'small' : ''}`}>
      <div className="progress-fill" style={{ width: `${p}%` }} />
      {m != null && <div className="progress-mark" style={{ left: `${m}%` }} title="Soll zum Stichtag" />}
    </div>
  )
}

function UtilBar({ v }) {
  const tone = v >= 100 ? 'crit' : v >= 85 ? 'warn' : v >= 60 ? 'good' : 'low'
  return <span className="ubar"><span className="ubar-track"><span className={`ubar-fill ${tone}`} style={{ width: `${Math.min(v || 0, 100)}%` }} /></span><span className="ubar-v">{pct(v)}</span></span>
}

// Kumulierter Neuumsatz: Ist laufendes Jahr gegen Ziellinie – eine Achse
function CumChart({ series, year, month }) {
  const W = 760, H = 220, L = 64, R = 14, T = 14, B = 28
  const max = Math.max(1, ...series.map((s) => Math.max(s.cum || 0, s.cum_target || 0))) * 1.08
  const x = (i) => L + (i * (W - L - R)) / 11
  const y = (v) => T + (H - T - B) * (1 - v / max)
  const path = (key, upto = 12) => series.slice(0, upto).filter((s) => s[key] != null).map((s, i) => `${i ? 'L' : 'M'}${x(s.month - 1)},${y(s[key])}`).join(' ')
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * max)
  const hasTarget = series.some((s) => s.cum_target)
  return (
    <figure className="cumchart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Kumulierter Neuumsatz ${year}`}>
        {ticks.map((v) => <g key={v}><line x1={L} x2={W - R} y1={y(v)} y2={y(v)} className="grid" /><text x={L - 6} y={y(v) + 4} textAnchor="end" className="tick">{v >= 1e6 ? `${num(v / 1e6, 1)} Mio` : `${num(v / 1000, 0)} T`}</text></g>)}
        {series.map((s) => <text key={s.month} x={x(s.month - 1)} y={H - 8} textAnchor="middle" className="tick">{s.label}</text>)}
        {hasTarget && <path d={path('cum_target')} className="l-target" />}
        <path d={path('cum', month)} className="l-cur" />
        {series.slice(0, month).map((s) => <circle key={s.month} cx={x(s.month - 1)} cy={y(s.cum || 0)} r="3.5" className="p-cur"><title>{`${s.label}: ${eur(s.cum)}`}</title></circle>)}
      </svg>
      <figcaption><span className="lg cur" /> Neuumsatz {year} kumuliert {hasTarget && <><span className="lg target" /> Ziel (linear)</>}</figcaption>
    </figure>
  )
}

function TargetsDialog({ year, onClose }) {
  const { data: users } = useFetch('/users?limit=200')
  const [y, setY] = useState(year)
  const { data, reload } = useFetch(`/sales-targets?year=${y}`)
  const [f, setF] = useState({ user_id: '', revenue_target: '', one_time_target: '', note: '' })
  const [err, setErr] = useState(null)
  async function save() {
    setErr(null)
    try {
      await api.post('/sales-targets', { year: y, user_id: f.user_id ? Number(f.user_id) : null, revenue_target: Number(f.revenue_target || 0),
        one_time_target: f.one_time_target === '' ? null : Number(f.one_time_target), note: f.note || null })
      setF({ user_id: '', revenue_target: '', one_time_target: '', note: '' }); reload()
    } catch (e) { setErr(e) }
  }
  const list = users?.items || users || []
  return (
    <Modal title="Vertriebsziele (Neuumsatz)" onClose={onClose}>
      <ErrorBox error={err} />
      <p className="small muted">Neuumsatz = Umsatz des stärksten Lieferjahres der gewonnenen Artikel. Ziel gesamt und optional je Vertriebsmitarbeiter; dazu optional ein Ziel für Werkzeug- und Einmalumsatz.</p>
      <div className="filters"><label className="inline-label">Jahr <select value={y} onChange={(e) => setY(Number(e.target.value))}>{[year - 1, year, year + 1].map((v) => <option key={v}>{v}</option>)}</select></label></div>
      <table className="table table-compact"><thead><tr><th>für</th><th className="num">Neuumsatz</th><th className="num">Werkzeug/Einmal</th><th>Notiz</th><th /></tr></thead>
        <tbody>{(data || []).map((t) => <tr key={t.id}><td>{t.user}</td><td className="num">{eur(t.revenue_target)}</td><td className="num">{t.one_time_target != null ? eur(t.one_time_target) : '–'}</td><td className="small">{t.note}</td>
          <td><button className="btn btn-ghost btn-sm" onClick={() => setF({ user_id: t.user_id || '', revenue_target: t.revenue_target, one_time_target: t.one_time_target ?? '', note: t.note || '' })}>ändern</button>
            <button className="btn-x" onClick={async () => { await api.del(`/sales-targets/${t.id}`); reload() }}>×</button></td></tr>)}
          {data && !data.length && <tr><td colSpan={5} className="muted">Noch kein Ziel für {y}.</td></tr>}</tbody></table>
      <div className="form-grid form-grid-3">
        <div className="field"><label>für</label><select value={f.user_id} onChange={(e) => setF({ ...f, user_id: e.target.value })}><option value="">Gesamt (Vertrieb)</option>
          {list.filter((u) => u.active !== false).map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}</select></div>
        <div className="field"><label>Neuumsatz-Ziel €</label><NumInput type="number" value={f.revenue_target} onChange={(e) => setF({ ...f, revenue_target: e.target.value })} /></div>
        <div className="field"><label>Werkzeug/Einmal-Ziel €</label><NumInput type="number" value={f.one_time_target} onChange={(e) => setF({ ...f, one_time_target: e.target.value })} /></div>
        <div className="field span-3"><label>Notiz</label><input value={f.note} onChange={(e) => setF({ ...f, note: e.target.value })} /></div>
      </div>
      <div className="form-actions"><span className="spacer" /><button className="btn btn-ghost" onClick={onClose}>Schließen</button>
        <button className="btn btn-primary" disabled={!f.revenue_target} onClick={save}>Ziel speichern</button></div>
    </Modal>
  )
}

