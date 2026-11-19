import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, qs } from '../api'
import { useAuth } from '../auth'
import ListPage from '../components/ListPage'
import { Badge, confirmDelete, EntityForm, ErrorBox, Modal, RefSelect, SearchInput, useFetch } from '../components/ui'
import { eur, fmtDate, STAGES, stageLabel } from '../constants'
import { opportunityFields } from '../forms'
import { bigReasons, useThresholds } from '../components/BigProject'
import LostReasonDialog from '../components/LostReasonDialog'
import { LightBadge } from '../components/Followup'
import { NO_BID_REASONS } from '../constants'

export default function Pipeline() {
  const [view, setView] = useState('board')
  const toggle = (
    <div className="seg">
      <button className={view === 'board' ? 'on' : ''} onClick={() => setView('board')}>Board</button>
      <button className={view === 'list' ? 'on' : ''} onClick={() => setView('list')}>Liste</button>
    </div>
  )
  if (view === 'list') {
    return (
      <ListPage
        title="Pipeline" subtitle="Alle Anfragen, Projekte und Leads" path="/opportunities" entityLabel="Anfrage / Lead"
        fields={opportunityFields} defaultSort="-amount" newDefaults={{ stage: 'lead', kind: 'lead' }} extraActions={toggle}
        filters={[{ name: 'stage', label: 'Phase', options: STAGES.map((s) => ({ value: s.key, label: s.label })) }]}
        columns={[
          { key: 'number', label: 'Nr.', sort: 'number', render: (r) => <Link to={`/anfragen/${r.id}`}><strong>{r.number}</strong></Link> },
          { key: 'name', label: 'Projekt', sort: 'name', render: (r) => <strong>{r.name}</strong> },
          { key: 'account', label: 'Firma', render: (r) => r.account?.name || '–' },
          { key: 'stage', label: 'Phase', sort: 'stage', render: (r) => stageLabel(r.stage) },
          { key: 'probability', label: 'Wahrsch. Auftrag', sort: 'probability', className: 'num', render: (r) => `${r.probability} %` },
          { key: 'final_round', label: 'Endrunde', render: (r) => (r.final_round ? '✓' : '') },
          { key: 'close_date', label: 'Entscheidung', sort: 'close_date', render: (r) => fmtDate(r.close_date) },
          { key: 'owner', label: 'Verantwortlich', render: (r) => r.owner?.name || '–' },
          { key: 'amount', label: 'Volumen', sort: 'amount', className: 'num', render: (r) => eur(r.amount) },
        ]}
      />
    )
  }
  return <Board toggle={toggle} />
}

function Board({ toggle }) {
  const { canWrite } = useAuth()
  const t = useThresholds()
  const [owner, setOwner] = useState(null)
  const [q, setQ] = useState('')
  const nav = useNavigate()
  const { data, error, reload } = useFetch('/inquiries' + qs({ limit: 500, owner_id: owner, q }))
  const [items, setItems] = useState(null)
  const [dragOver, setDragOver] = useState(null)
  const [editing, setEditing] = useState(null)
  const list = items && data && items.src === data ? items.list : data?.items || []

  const [lostAsk, setLostAsk] = useState(null)
  const [moveErr, setMoveErr] = useState(null)
  async function move(id, stage, extra = {}) {
    const opp = list.find((o) => o.id === id)
    if (!opp || opp.stage === stage) return
    if (['verloren', 'nicht_angeboten'].includes(stage) && !extra.lost_reason) { setLostAsk({ id, stage }); return }  // Grund ist Pflicht
    // optimistisch umsortieren
    setItems({ src: data, list: list.map((o) => (o.id === id ? { ...o, stage } : o)) })
    setMoveErr(null)
    try {
      await api.patch(`/opportunities/${id}`, { stage, ...extra })
    } catch (e) { setMoveErr(e) } finally {
      reload()
    }
  }
  async function save(values) {
    if (editing.id) await api.patch(`/opportunities/${editing.id}`, values)
    else {
      const r = await api.post('/opportunities', values)
      if (values.kind === 'anfrage') { nav(`/anfragen/${r.id}`); return }   // Anfrage → gleich Artikel erfassen
    }
    setEditing(null)
    reload()
  }
  async function remove() {
    if (await confirmDelete('Verkaufschance', () => api.del(`/opportunities/${editing.id}`))) {
      setEditing(null)
      reload()
    }
  }

  return (
    <div className="page page-wide">
      {lostAsk && <LostReasonDialog onCancel={() => setLostAsk(null)}
        title={lostAsk.stage === 'verloren' ? 'Warum verloren?' : 'Warum nicht angeboten?'}
        reasons={lostAsk.stage === 'verloren' ? undefined : NO_BID_REASONS}
        confirmLabel={lostAsk.stage === 'verloren' ? 'Als verloren markieren' : 'Nicht anbieten'}
        onConfirm={({ reason, label, note }) => { const { id, stage } = lostAsk; setLostAsk(null); move(id, stage, { lost_code: reason, lost_reason: note ? `${label}: ${note}` : label }) }} />}
      <ErrorBox error={moveErr} />
      <header className="page-head">
        <div>
          <h1>Pipeline</h1>
          <p className="muted">Eine Karte je Anfrage / Projekt. Neue Anfrage → Qualifiziert → Angebot laufen automatisch (Entscheidung, Versand); Verhandlung, Gewonnen und Verloren per Drag &amp; Drop. Karte anklicken öffnet die Anfrage.</p>
        </div>
        <div className="toolbar">
          {toggle}
          {canWrite && <button className="btn btn-ghost" onClick={() => setEditing({ stage: 'lead', kind: 'lead' })}>+ Lead</button>}
          {canWrite && <button className="btn btn-primary" onClick={() => setEditing({ stage: 'neue_anfrage', kind: 'anfrage', inquiry_date: new Date().toISOString().slice(0, 10) })}>+ Neue Anfrage</button>}
        </div>
      </header>
      <div className="filters">
        <SearchInput value={q} onChange={setQ} />
        <label className="inline-label">Vertrieb <RefSelect kind="user" value={owner} onChange={setOwner} /></label>
      </div>
      <ErrorBox error={error} />
      <div className="board">
        {STAGES.filter((st) => st.board).map((st) => {
          const col = list.filter((o) => o.stage === st.key)
          const sum = col.reduce((s, o) => s + o.amount, 0)
          return (
            <div key={st.key} className={`board-col stage-${st.key} ${dragOver === st.key ? 'drag-over' : ''}`}
              onDragOver={(e) => { if (canWrite) { e.preventDefault(); setDragOver(st.key) } }}
              onDragLeave={() => setDragOver(null)}
              onDrop={(e) => { e.preventDefault(); setDragOver(null); move(Number(e.dataTransfer.getData('text/plain')), st.key) }}>
              <div className="board-col-head">
                <div title={st.hint}><strong>{st.label}</strong> <span className="count">{col.length}</span></div>
                <div className="board-sum">{eur(sum)}</div>
              </div>
              <div className="board-cards">
                {col.map((o) => (
                  <div key={o.id} className={`deal ${bigReasons(t, o.amount, 0).length ? 'deal-big' : ''}`} draggable={canWrite}
                    onDragStart={(e) => e.dataTransfer.setData('text/plain', String(o.id))}
                    onClick={() => (o.kind === 'lead' && !o.articles ? canWrite && setEditing(o) : nav(`/anfragen/${o.id}`))}>
                    <div className="deal-title">{bigReasons(t, o.amount, 0).length > 0 && <span className="big-star" title="Großprojekt">★ </span>}<small className="muted">{o.number}</small> {o.name}</div>
                    <Link to={`/firmen/${o.account?.id}`} className="deal-acc" onClick={(e) => e.stopPropagation()}>{o.account?.name}</Link>
                    <div className="deal-foot">
                      <strong>{eur(o.amount)}</strong>
                      <span className={o.close_date && new Date(o.close_date) < new Date(new Date().toDateString()) && !['gewonnen', 'verloren'].includes(o.stage) ? 'text-critical' : 'muted'}>
                        {fmtDate(o.close_date)}
                      </span>
                    </div>
                    <div className="deal-owner muted">{o.owner?.name} · {o.probability} %{o.articles ? ` · ${o.articles} Art.` : ''}</div>
                    <div className="deal-meta">
                      {o.undecided > 0 && <Badge tone="warning">⚠ {o.undecided} Entscheidung offen</Badge>}
                      {o.quote && <Badge tone="info">{o.quote.number}</Badge>}
                      {o.quote?.followup && <LightBadge light={o.quote.followup.light} />}
                      {o.tech_talk && <Badge tone="warning">⚙ techn. Gespräch</Badge>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
      {editing && (
        <Modal title={editing.id ? 'Lead / Anfrage bearbeiten' : editing.kind === 'lead' ? 'Lead anlegen' : 'Neue Anfrage anlegen'} onClose={() => setEditing(null)}>
          <EntityForm fields={opportunityFields} initial={editing} onSubmit={save} onCancel={() => setEditing(null)}
            onDelete={editing.id ? remove : undefined} />
        </Modal>
      )}
    </div>
  )
}
