import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, qs } from '../api'
import { useAuth } from '../auth'
import { Badge, confirmDelete, EntityForm, ErrorBox, Modal, useFetch } from '../components/ui'
import { ACCOUNT_TYPES, activityType, calcStatus, contactName, eur, eur4, fmtDate, fmtDateTime, QUOTE_STATUS, reasonLabel, stageLabel } from '../constants'
import { accountFields, activityFields, contactFields, opportunityFields } from '../forms'
import { DoneToggle, isOverdue } from './Activities'
import { typeTone } from './Accounts'

export default function AccountDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { canWrite } = useAuth()
  const acc = useFetch(`/accounts/${id}`)
  const contacts = useFetch(`/contacts${qs({ account_id: id, limit: 200 })}`)
  const opps = useFetch(`/opportunities${qs({ account_id: id, limit: 200 })}`)
  const acts = useFetch(`/activities${qs({ account_id: id, limit: 200, sort: '-due_at' })}`)
  const quotes = useFetch(`/quotes${qs({ account_id: id, limit: 200 })}`)
  const calcs = useFetch(`/calculations${qs({ account_id: id, limit: 200 })}`)
  const [modal, setModal] = useState(null) // {kind, values}

  const cfg = {
    account: { path: '/accounts', fields: accountFields, label: 'Firma', reload: acc.reload },
    contact: { path: '/contacts', fields: contactFields, label: 'Kontakt', reload: contacts.reload },
    opportunity: { path: '/opportunities', fields: opportunityFields, label: 'Verkaufschance', reload: opps.reload },
    activity: { path: '/activities', fields: activityFields, label: 'Aktivität', reload: acts.reload },
  }

  if (acc.error) return <ErrorBox error={acc.error} />
  if (!acc.data) return <div className="loading">Lade…</div>
  const a = acc.data
  const open = (kind, values = {}) => canWrite && setModal({ kind, values: { account_id: a.id, ...values } })

  async function save(values) {
    const c = cfg[modal.kind]
    if (modal.values.id) await api.patch(`${c.path}/${modal.values.id}`, values)
    else await api.post(c.path, values)
    setModal(null)
    c.reload()
    if (modal.kind !== 'account') acts.reload()
  }
  async function remove() {
    const c = cfg[modal.kind]
    if (await confirmDelete(c.label, () => api.del(`${c.path}/${modal.values.id}`))) {
      setModal(null)
      if (modal.kind === 'account') nav('/firmen')
      else c.reload()
    }
  }

  const openSum = (opps.data?.items || []).filter((o) => !['gewonnen', 'verloren'].includes(o.stage)).reduce((s, o) => s + o.amount, 0)
  const wonSum = (opps.data?.items || []).filter((o) => o.stage === 'gewonnen').reduce((s, o) => s + o.amount, 0)

  return (
    <div className="page">
      <Link to="/firmen" className="back">‹ Alle Firmen</Link>
      <header className="page-head">
        <div>
          <h1>{a.name} <Badge tone={typeTone[a.type]}>{ACCOUNT_TYPES.find((t) => t.value === a.type)?.label}</Badge></h1>
          <p className="muted">{[a.industry, a.city, a.country].filter(Boolean).join(' · ')}</p>
        </div>
        {canWrite && <div className="toolbar">
          <button className="btn btn-ghost" onClick={() => open('activity', { type: 'notiz', done: true, due_at: new Date().toISOString() })}>✎ Notiz</button>
          <button className="btn btn-ghost" onClick={() => setModal({ kind: 'account', values: a })}>Bearbeiten</button>
          <button className="btn btn-primary" onClick={() => nav(`/angebote/neu?account_id=${a.id}`)}>+ Angebot</button>
        </div>}
      </header>

      <div className="detail-grid">
        <div className="card">
          <h3>Stammdaten</h3>
          <dl className="dl">
            <dt>Telefon</dt><dd>{a.phone ? <a href={`tel:${a.phone}`}>{a.phone}</a> : '–'}</dd>
            <dt>E-Mail</dt><dd>{a.email ? <a href={`mailto:${a.email}`}>{a.email}</a> : '–'}</dd>
            <dt>Website</dt><dd>{a.website ? <a href={a.website.startsWith('http') ? a.website : `https://${a.website}`} target="_blank" rel="noreferrer">{a.website}</a> : '–'}</dd>
            <dt>Adresse</dt><dd>{[a.street, [a.zip, a.city].filter(Boolean).join(' '), a.country].filter(Boolean).join(', ') || '–'}</dd>
            <dt>Verantwortlich</dt><dd>{a.owner?.name || '–'}</dd>
            <dt>Angelegt</dt><dd>{fmtDate(a.created_at)}</dd>
          </dl>
          {a.notes && <p className="notes">{a.notes}</p>}
          <div className="mini-kpis">
            <div><span>Offene Pipeline</span><strong>{eur(openSum)}</strong></div>
            <div><span>Gewonnen gesamt</span><strong>{eur(wonSum)}</strong></div>
          </div>
        </div>

        <div className="stack">
          <Section title="Kontakte" count={contacts.data?.total} onAdd={canWrite && (() => open('contact'))}>
            {contacts.data?.items.map((c) => (
              <div key={c.id} className="list-row" onClick={() => open('contact', c)}>
                <div><strong>{contactName(c)}</strong><small className="muted"> {c.position}</small></div>
                <div className="muted small">{c.email && <a href={`mailto:${c.email}`} onClick={(e) => e.stopPropagation()}>{c.email}</a>} {c.phone}</div>
              </div>
            ))}
          </Section>

          <Section title="Verkaufschancen" count={opps.data?.total} onAdd={canWrite && (() => open('opportunity', { stage: 'lead' }))}>
            {opps.data?.items.map((o) => (
              <div key={o.id} className="list-row" onClick={() => open('opportunity', o)}>
                <div><strong>{o.name}</strong><br /><small className="muted">{stageLabel(o.stage)} · {o.probability} % · Abschluss {fmtDate(o.close_date)}</small></div>
                <div className="num"><strong>{eur(o.amount)}</strong></div>
              </div>
            ))}
          </Section>

          <Section title="Kalkulationen" count={calcs.data?.total} onAdd={canWrite && (() => nav('/kalkulationen/neu'))}>
            {calcs.data?.items.map((c) => (
              <Link key={c.id} to={`/kalkulationen/${c.id}`} className="list-row">
                <div><strong>{c.number}</strong> {c.article_name}<br /><small className="muted">{calcStatus(c.status).label}{c.close_reason ? ` · ${reasonLabel(c.close_reason)}` : ''} · V{c.current_version} · {c.probability} %</small></div>
                <div className="num">{eur4(c.unit_price)}<br /><small className="muted">{eur(c.annual_revenue)} p. a.</small></div>
              </Link>
            ))}
          </Section>

          <Section title="Angebote" count={quotes.data?.total}>
            {quotes.data?.items.map((q) => (
              <Link key={q.id} to={`/angebote/${q.id}`} className="list-row">
                <div><strong>{q.number}</strong> {q.title}<br /><small className="muted">{fmtDate(q.quote_date)} · {QUOTE_STATUS.find((s) => s.value === q.status)?.label}</small></div>
                <div className="num">{eur(q.net_total)}</div>
              </Link>
            ))}
          </Section>

          <Section title="Aktivitäten & Verlauf" count={acts.data?.total} onAdd={canWrite && (() => open('activity', { type: 'aufgabe', done: false }))}>
            {acts.data?.items.map((t) => (
              <div key={t.id} className="list-row timeline-row" onClick={() => open('activity', t)}>
                <div className="tl-left">
                  {t.type !== 'notiz' && <DoneToggle row={t} onChange={acts.reload} />}
                  <span className="act-type">{activityType(t.type).icon}</span>
                  <div>
                    <span className={t.done && t.type !== 'notiz' ? 'line-through muted' : ''}>{t.subject}</span>
                    {t.description && <div className="small muted pre">{t.description}</div>}
                  </div>
                </div>
                <div className={`small ${isOverdue(t) ? 'text-critical' : 'muted'}`}>{fmtDateTime(t.due_at)}<br />{t.owner?.name}</div>
              </div>
            ))}
          </Section>
        </div>
      </div>

      {modal && (
        <Modal title={`${cfg[modal.kind].label} ${modal.values.id ? 'bearbeiten' : 'anlegen'}`} onClose={() => setModal(null)}>
          <EntityForm fields={cfg[modal.kind].fields} initial={modal.values} onSubmit={save}
            onCancel={() => setModal(null)} onDelete={modal.values.id ? remove : undefined} />
        </Modal>
      )}
    </div>
  )
}

function Section({ title, count, onAdd, children }) {
  const empty = !children || (Array.isArray(children) && !children.length)
  return (
    <div className="card">
      <div className="section-head">
        <h3>{title} {count != null && <span className="count">{count}</span>}</h3>
        {onAdd && <button className="btn btn-ghost btn-sm" onClick={onAdd}>+ Neu</button>}
      </div>
      {empty ? <div className="empty small">Noch keine Einträge.</div> : <div className="list">{children}</div>}
    </div>
  )
}
