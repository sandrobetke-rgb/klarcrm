import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, qs } from '../api'
import { useAuth } from '../auth'
import DecisionBox from '../components/DecisionBox'
import FollowupDialog, { LightBadge } from '../components/Followup'
import LostReasonDialog from '../components/LostReasonDialog'
import { Badge, EntityForm, ErrorBox, Modal, RefSelect, SearchInput, useFetch } from '../components/ui'
import {
  activityType, calcStatus, CLOSED_STAGES, contactName, eur, eur4, fmtDate, fmtDateTime, NO_BID_REASONS, num,
  QUOTE_STATUS, STAGES, stageLabel,
} from '../constants'
import { activityFields, opportunityFields } from '../forms'

const stageTone = (s) => ({ gewonnen: 'good', verloren: 'critical', nicht_angeboten: 'neutral', angebot: 'info', verhandlung: 'warning' }[s] || 'neutral')
const quoteStatus = (v) => QUOTE_STATUS.find((x) => x.value === v)?.label || v

// ------------------------------------------------------------------ Liste
export default function Inquiries() {
  const nav = useNavigate()
  const { canWrite } = useAuth()
  const [q, setQ] = useState('')
  const [stage, setStage] = useState(() => new URLSearchParams(window.location.search).get('stage') || 'offen')
  const [owner, setOwner] = useState(null)
  const [creating, setCreating] = useState(null)
  const params = { q, owner_id: owner, limit: 500, ...(stage === 'offen' ? { open_only: true } : stage ? { stage } : {}) }
  const { data, error, reload } = useFetch('/inquiries' + qs(params))
  async function create(values) {
    const r = await api.post('/opportunities', values)
    setCreating(null)
    nav(`/anfragen/${r.id}`)
  }
  return (
    <div className="page page-wide">
      <header className="page-head">
        <div><h1>Anfragen &amp; Projekte</h1>
          <p className="muted">Eine Anfrage je Kunde und Projekt – darunter alle Artikel (Kalkulationen) und genau ein Angebot</p></div>
        {canWrite && <div className="toolbar">
          <button className="btn btn-ghost" onClick={() => setCreating({ kind: 'lead', stage: 'lead' })}>+ Lead (ohne Anfrage)</button>
          <button className="btn btn-primary" onClick={() => setCreating({ kind: 'anfrage', stage: 'neue_anfrage', inquiry_date: new Date().toISOString().slice(0, 10) })}>+ Neue Anfrage</button>
        </div>}
      </header>
      <div className="filters">
        <SearchInput value={q} onChange={setQ} placeholder="Nr., Projekt, Notiz…" />
        <select value={stage} onChange={(e) => setStage(e.target.value)}>
          <option value="offen">alle offenen</option><option value="">alle</option>
          {STAGES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
        <label className="inline-label">Vertrieb <RefSelect kind="user" value={owner} onChange={setOwner} /></label>
      </div>
      <ErrorBox error={error} />
      <div className="card table-wrap">
        <table className="table">
          <thead><tr><th>Nr.</th><th>Projekt / Kunde</th><th>Phase</th><th className="num">Artikel</th><th>Entscheidung</th>
            <th>Angebot</th><th>Verfolgung</th><th>Abgabe bis</th><th className="num">Volumen</th><th className="num">Wahrsch.</th></tr></thead>
          <tbody>
            {(data?.items || []).map((o) => (
              <tr key={o.id} className="clickable" onClick={() => nav(`/anfragen/${o.id}`)}>
                <td><strong>{o.number}</strong>{o.kind === 'lead' && <><br /><small className="muted">Lead</small></>}</td>
                <td>{o.name}<br /><small className="muted">{o.account?.name || '–'}{o.owner ? ` · ${o.owner.name}` : ''}</small></td>
                <td><Badge tone={stageTone(o.stage)}>{stageLabel(o.stage)}</Badge>{o.tech_talk && <><br /><small>⚙ techn. Gespräch</small></>}</td>
                <td className="num">{o.articles || '–'}</td>
                <td>{o.undecided ? <Badge tone="warning">⚠ {o.undecided} offen</Badge> : o.articles ? <small className="muted">{o.released} angeboten</small> : '–'}</td>
                <td>{o.quote ? <>{o.quote.number}<br /><small className="muted">{quoteStatus(o.quote.status)}</small></> : '–'}</td>
                <td>{o.quote?.followup ? <LightBadge light={o.quote.followup.light} due={o.quote.followup.due_at} /> :
                  o.quote?.last_contact_at ? <small className="muted">{fmtDate(o.quote.last_contact_at)}</small> : '–'}</td>
                <td className={o.due_date && new Date(o.due_date) < new Date() && !o.quote ? 'text-critical' : ''}>{fmtDate(o.due_date)}</td>
                <td className="num">{eur(o.amount)}</td>
                <td className="num">{o.probability} %</td>
              </tr>
            ))}
            {data && !data.items.length && <tr><td colSpan={10} className="muted">Keine Anfragen gefunden.</td></tr>}
          </tbody>
        </table>
      </div>
      {creating && <Modal title={creating.kind === 'lead' ? 'Lead anlegen' : 'Neue Anfrage anlegen'} onClose={() => setCreating(null)}>
        <EntityForm fields={opportunityFields.filter((f) => !['stage', 'amount', 'lost_reason'].includes(f.name))} initial={creating}
          onSubmit={create} onCancel={() => setCreating(null)} submitLabel="Anlegen" />
      </Modal>}
    </div>
  )
}

// ------------------------------------------------------------------ Schrittleiste
function Steps({ o }) {
  const calcs = o.calculations || []
  const live = calcs.filter((c) => !['kein_angebot'].includes(c.status))
  const q = o.quote
  const steps = [
    ['Anfrage', true],
    ['Entscheidung', calcs.length > 0 && o.undecided === 0],
    ['Artikelanalyse', live.length > 0 && live.every((c) => c.analysis_complete || c.decision === 'nicht_anbieten')],
    ['Kalkulation', live.length > 0 && live.every((c) => c.current_version > 1 || c.decision === 'nicht_anbieten')],
    ['Freigabe', live.length > 0 && live.every((c) => !c.approval_reasons.length || c.is_approved)],
    ['Angebot', !!q],
    ['Versendet', q && q.status !== 'entwurf'],
    ['Abschluss', CLOSED_STAGES.includes(o.stage)],
  ]
  const cur = steps.findIndex(([, d]) => !d)
  return (
    <ol className="stepper">
      {steps.map(([l, d], i) => <li key={l} className={d ? 'done' : i === cur ? 'current' : ''}><span>{d ? '✓' : i + 1}</span>{l}</li>)}
    </ol>
  )
}

// ------------------------------------------------------------------ Detail
export function InquiryDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { canWrite } = useAuth()
  const { data: o, error, reload } = useFetch(`/inquiries/${id}`)
  const [err, setErr] = useState(null)
  const [edit, setEdit] = useState(false)
  const [newArt, setNewArt] = useState(null)
  const [ask, setAsk] = useState(null)          // verloren | nicht_angeboten
  const [fu, setFu] = useState(null)
  const [act, setAct] = useState(null)
  const [msg, setMsg] = useState(null)
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!o) return <div className="page"><div className="loading">Lade…</div></div>
  const run = async (fn) => { setErr(null); setMsg(null); try { await fn(); reload() } catch (e) { setErr(e) } }
  const q = o.quote
  const closed = CLOSED_STAGES.includes(o.stage)
  async function makeQuote() {
    await run(async () => {
      const r = await api.post(`/inquiries/${o.id}/quote`)
      setMsg(r.action === 'neu' ? `Angebot ${r.number} angelegt` : r.action === 'revision' ? `Revision ${r.number} angelegt – das versendete Angebot ist jetzt „ersetzt“` : `Angebot ${r.number} aktualisiert`)
    })
  }
  const setStage = (stage, extra = {}) => run(() => api.patch(`/opportunities/${o.id}`, { stage, ...extra }))
  return (
    <div className="page page-wide">
      <header className="page-head">
        <div>
          <Link to="/anfragen" className="muted small">← Anfragen</Link>
          <h1>{o.number} · {o.name}</h1>
          <p className="muted">
            {o.account ? <Link to={`/firmen/${o.account.id}`}>{o.account.name}</Link> : 'kein Kunde'}
            {o.contact && ` · ${contactName(o.contact)}`}{o.owner && ` · verantwortlich ${o.owner.name}`}
            {' · '}Eingang {fmtDate(o.inquiry_date)} · Abgabe bis {fmtDate(o.due_date)}
            {o.lead_time_workdays != null && ` · Durchlaufzeit ${o.lead_time_workdays} AT`}
          </p>
        </div>
        <div className="toolbar">
          <Badge tone={stageTone(o.stage)}>{stageLabel(o.stage)}</Badge>
          {o.final_round && <Badge tone="warning">Endrunde</Badge>}
          {canWrite && <button className="btn btn-ghost" onClick={() => setEdit(true)}>Bearbeiten</button>}
        </div>
      </header>
      <ErrorBox error={err} />
      {msg && <div className="notice-ok">✓ {msg}</div>}
      {o.kind !== 'lead' && <Steps o={o} />}
      {o.lost_reason && <div className="warn-box">Grund: {o.lost_reason}</div>}
      {o.tech_talk && <div className="warn-box">⚙ Laut Artikelanalyse ist ein <strong>technisches Gespräch</strong> mit dem Kunden erforderlich – Aufgabe ist angelegt.</div>}

      <section className="card">
        <div className="section-head"><h3>Artikel ({o.calculations.length})</h3>
          {canWrite && !closed && <div className="toolbar">
            {o.undecided > 0 && <button className="btn btn-ghost btn-sm" onClick={() => run(() => api.post(`/inquiries/${o.id}/decision`, { decision: 'anbieten' }))}>Alle offenen anbieten</button>}
            <button className="btn btn-primary btn-sm" onClick={() => setNewArt({ article_name: '' })}>+ Artikel / Kalkulation</button>
          </div>}
        </div>
        {o.calculations.length === 0 ? <p className="muted">Noch keine Artikel. „+ Artikel / Kalkulation“ legt den ersten an.</p> : (
          <table className="table table-compact">
            <thead><tr><th>Kalkulation</th><th>Artikel</th><th>Entscheidung</th><th>Artikelanalyse</th><th>Status</th>
              <th className="num">Preis/Stk</th><th className="num">Menge p. a.</th><th className="num">Umsatz p. a.</th><th className="num">Einmalig</th><th>Freigabe</th></tr></thead>
            <tbody>{o.calculations.map((c) => (
              <tr key={c.id}>
                <td><Link to={`/kalkulationen/${c.id}`}><strong>{c.number}</strong></Link><br /><small className="muted">V{c.current_version}</small></td>
                <td>{c.article_name}{c.customer_article_no && <><br /><small className="muted">{c.customer_article_no}</small></>}</td>
                <td><DecisionBox calc={c} onDone={reload} compact canWrite={canWrite && !closed} /></td>
                <td>{c.analysis_complete ? <Badge tone="good">✓ vollständig</Badge> : <Link to={`/kalkulationen/${c.id}?tab=analyse`}><Badge tone="warning">offen</Badge></Link>}
                  {c.suggested_size_t && <><br /><small className="muted">Maschine ≈ {num(c.suggested_size_t)} t</small></>}
                  {c.tech_talk && <><br /><small>⚙ techn. Gespräch</small></>}</td>
                <td><Badge tone={calcStatus(c.status).tone}>{calcStatus(c.status).label}</Badge></td>
                <td className="num">{c.unit_price ? eur4(c.unit_price) : '–'}</td>
                <td className="num">{num(c.annual_volume)}</td>
                <td className="num">{eur(c.annual_revenue)}</td>
                <td className="num">{eur(c.one_time_revenue)}</td>
                <td>{!c.approval_reasons.length ? <small className="muted">nicht nötig</small> : c.is_approved ? <Badge tone="good">freigegeben</Badge>
                  : <Link to={`/kalkulationen/${c.id}`}><Badge tone={c.approval_status === 'angefragt' ? 'info' : 'warning'}>{c.approval_status === 'angefragt' ? 'angefragt' : 'nötig'}</Badge></Link>}
                  {!c.is_approved && c.approval_reasons.length > 0 && <><br /><small className="muted">{c.approval_reasons.join(', ')}</small></>}</td>
              </tr>))}
            </tbody>
          </table>)}
      </section>

      <div className="grid-2">
        <section className="card">
          <div className="section-head"><h3>Angebot</h3>
            {canWrite && o.calculations.length > 0 && !closed && <button className="btn btn-primary btn-sm" onClick={makeQuote}>
              {q ? (q.status === 'entwurf' ? 'Angebot aktualisieren' : 'Neue Revision erstellen') : 'Angebot erstellen'}</button>}
          </div>
          {!q ? <p className="muted">Noch kein Angebot. Voraussetzung: alle Artikel entschieden, Artikelanalyse vollständig oder freigegeben.</p> : (
            <dl className="kv">
              <dt>Angebot</dt><dd><Link to={`/angebote/${q.id}`}><strong>{q.number}</strong></Link> · {quoteStatus(q.status)} · {eur(q.net_total)} netto</dd>
              <dt>Versendet</dt><dd>{q.sent_at ? fmtDate(q.sent_at) : 'noch nicht – im Angebot Status „versendet“ setzen, dann startet die Verfolgung'}</dd>
              <dt>Verfolgung</dt><dd>{q.followup ? <><LightBadge light={q.followup.light} due={q.followup.due_at} /> {q.followup.owner && <small className="muted">{q.followup.owner}</small>}
                {canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setFu({ id: q.followup.id, subject: `Angebot ${q.number}`, attempts: q.followup.attempts })}>Rücksprache erfassen</button>}</> : '–'}</dd>
              <dt>Letzte Rückmeldung</dt><dd>{q.last_contact_at ? <>{fmtDate(q.last_contact_at)} · {q.last_contact_note}</> : '–'}</dd>
              {o.quotes.length > 1 && <><dt>Frühere Fassungen</dt><dd>{o.quotes.slice(1).map((x) => <Link key={x.id} to={`/angebote/${x.id}`} className="muted">{x.number} ({quoteStatus(x.status)}) </Link>)}</dd></>}
            </dl>)}
          {canWrite && !closed && o.kind !== 'lead' && <div className="toolbar" style={{ marginTop: 12 }}>
            {o.stage !== 'verhandlung' && q && <button className="btn btn-ghost btn-sm" onClick={() => setStage('verhandlung')}>→ Verhandlung / techn. Gespräch</button>}
            <button className="btn btn-ghost btn-sm" onClick={() => setStage('gewonnen')}>✓ Gewonnen</button>
            <button className="btn btn-ghost btn-sm" onClick={() => setAsk('verloren')}>Verloren …</button>
            {!q && <button className="btn btn-ghost btn-sm" onClick={() => setAsk('nicht_angeboten')}>Nicht anbieten …</button>}
          </div>}
          {closed && canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setStage(o.kind === 'lead' ? 'lead' : 'qualifiziert')}>Wieder öffnen</button>}
        </section>

        <section className="card">
          <div className="section-head"><h3>Aktivitäten</h3>
            {canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setAct({ type: 'anruf', account_id: o.account?.id, contact_id: o.contact?.id, opportunity_id: o.id, quote_id: q?.id })}>+ Aktivität</button>}</div>
          {o.activities.length === 0 ? <p className="muted">Keine Aktivitäten.</p> : (
            <ul className="timeline">{o.activities.map((a) => (
              <li key={a.id} className={a.done ? 'done' : ''}>
                <span className="tl-icon">{activityType(a.type).icon}</span>
                <div><strong>{a.subject}</strong> {a.light && <LightBadge light={a.light} />}
                  <br /><small className="muted">{fmtDateTime(a.due_at)}{a.owner ? ` · ${a.owner.name}` : ''}{a.quote ? ` · ${a.quote.number}` : ''}{a.done ? ' · erledigt' : ''}</small>
                  {a.description && <div className="small">{a.description}</div>}
                  {a.kind === 'angebotsverfolgung' && !a.done && canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setFu(a)}>Rücksprache erfassen</button>}
                </div>
              </li>))}
            </ul>)}
        </section>
      </div>

      {edit && <Modal title="Anfrage bearbeiten" onClose={() => setEdit(false)}>
        <EntityForm fields={opportunityFields} initial={{ ...o, account_id: o.account?.id, contact_id: o.contact?.id, owner_id: o.owner?.id }}
          onSubmit={async (v) => { await api.patch(`/opportunities/${o.id}`, v); setEdit(false); reload() }} onCancel={() => setEdit(false)} />
      </Modal>}
      {newArt && <Modal title="Artikel zur Anfrage hinzufügen" onClose={() => setNewArt(null)}>
        <EntityForm fields={[{ name: 'article_name', label: 'Artikelbezeichnung', required: true, span: true },
          { name: 'customer_article_no', label: 'Artikel-Nr. Kunde' }, { name: 'own_article_no', label: 'Eigene Artikel-Nr.' },
          { name: 'copy_from', label: 'Werte übernehmen von', type: 'select', options: o.calculations.map((c) => ({ value: String(c.id), label: `${c.number} ${c.article_name}` })), hint: 'optional: Kalkulation als Vorlage' }]}
        initial={newArt} submitLabel="Anlegen" onCancel={() => setNewArt(null)}
        onSubmit={async (v) => { const r = await api.post(`/inquiries/${o.id}/articles`, { ...v, copy_from: v.copy_from ? Number(v.copy_from) : null }); setNewArt(null); nav(`/kalkulationen/${r.id}`) }} />
      </Modal>}
      {ask && <LostReasonDialog title={ask === 'verloren' ? 'Warum verloren?' : 'Warum nicht anbieten?'}
        reasons={ask === 'verloren' ? undefined : NO_BID_REASONS} confirmLabel={ask === 'verloren' ? 'Als verloren markieren' : 'Nicht anbieten'}
        onCancel={() => setAsk(null)}
        onConfirm={({ reason, label, note }) => { const st = ask; setAsk(null); setStage(st, { lost_code: reason, lost_reason: note ? `${label}: ${note}` : label }) }} />}
      {fu && <FollowupDialog task={fu} onClose={() => setFu(null)} onDone={() => { setFu(null); reload() }} />}
      {act && <Modal title="Aktivität anlegen" onClose={() => setAct(null)}>
        <EntityForm fields={activityFields} initial={act} onCancel={() => setAct(null)}
          onSubmit={async (v) => { await api.post('/activities', v); setAct(null); reload() }} />
      </Modal>}
    </div>
  )
}
