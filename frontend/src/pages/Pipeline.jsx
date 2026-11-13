import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, qs } from '../api'
import { useAuth } from '../auth'
import ListPage from '../components/ListPage'
import { confirmDelete, EntityForm, ErrorBox, Modal, RefSelect, SearchInput, useFetch } from '../components/ui'
import { eur, fmtDate, STAGES, stageLabel } from '../constants'
import { opportunityFields } from '../forms'

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
        title="Pipeline" subtitle="Alle Verkaufschancen" path="/opportunities" entityLabel="Verkaufschance"
        fields={opportunityFields} defaultSort="-amount" newDefaults={{ stage: 'lead' }} extraActions={toggle}
        filters={[{ name: 'stage', label: 'Phase', options: STAGES.map((s) => ({ value: s.key, label: s.label })) }]}
        columns={[
          { key: 'name', label: 'Chance', sort: 'name', render: (r) => <strong>{r.name}</strong> },
          { key: 'account', label: 'Firma', render: (r) => r.account?.name || '–' },
          { key: 'stage', label: 'Phase', sort: 'stage', render: (r) => stageLabel(r.stage) },
          { key: 'probability', label: 'Wahrsch.', sort: 'probability', className: 'num', render: (r) => `${r.probability} %` },
          { key: 'close_date', label: 'Abschluss', sort: 'close_date', render: (r) => fmtDate(r.close_date) },
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
  const [owner, setOwner] = useState(null)
  const [q, setQ] = useState('')
  const { data, error, reload } = useFetch('/opportunities' + qs({ limit: 500, sort: '-amount', owner_id: owner, q }))
  const [items, setItems] = useState(null)
  const [dragOver, setDragOver] = useState(null)
  const [editing, setEditing] = useState(null)
  const list = items && data && items.src === data ? items.list : data?.items || []

  async function move(id, stage) {
    const opp = list.find((o) => o.id === id)
    if (!opp || opp.stage === stage) return
    // optimistisch umsortieren
    setItems({ src: data, list: list.map((o) => (o.id === id ? { ...o, stage } : o)) })
    try {
      await api.patch(`/opportunities/${id}`, { stage })
    } finally {
      reload()
    }
  }
  async function save(values) {
    if (editing.id) await api.patch(`/opportunities/${editing.id}`, values)
    else await api.post('/opportunities', values)
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
      <header className="page-head">
        <div>
          <h1>Pipeline</h1>
          <p className="muted">{canWrite ? 'Karten per Drag & Drop in die nächste Phase ziehen' : 'Alle offenen und abgeschlossenen Verkaufschancen'}</p>
        </div>
        <div className="toolbar">
          {toggle}
          {canWrite && <button className="btn btn-primary" onClick={() => setEditing({ stage: 'lead' })}>+ Verkaufschance</button>}
        </div>
      </header>
      <div className="filters">
        <SearchInput value={q} onChange={setQ} />
        <label className="inline-label">Vertrieb <RefSelect kind="user" value={owner} onChange={setOwner} /></label>
      </div>
      <ErrorBox error={error} />
      <div className="board">
        {STAGES.map((st) => {
          const col = list.filter((o) => o.stage === st.key)
          const sum = col.reduce((s, o) => s + o.amount, 0)
          const weighted = col.reduce((s, o) => s + (o.amount * o.probability) / 100, 0)
          return (
            <div key={st.key} className={`board-col stage-${st.key} ${dragOver === st.key ? 'drag-over' : ''}`}
              onDragOver={(e) => { if (canWrite) { e.preventDefault(); setDragOver(st.key) } }}
              onDragLeave={() => setDragOver(null)}
              onDrop={(e) => { e.preventDefault(); setDragOver(null); move(Number(e.dataTransfer.getData('text/plain')), st.key) }}>
              <div className="board-col-head">
                <div><strong>{st.label}</strong> <span className="count">{col.length}</span></div>
                <div className="board-sum">{eur(sum)}{!['gewonnen', 'verloren'].includes(st.key) && <small> · gew. {eur(weighted)}</small>}</div>
              </div>
              <div className="board-cards">
                {col.map((o) => (
                  <div key={o.id} className="deal" draggable={canWrite}
                    onDragStart={(e) => e.dataTransfer.setData('text/plain', String(o.id))}
                    onClick={() => canWrite && setEditing(o)}>
                    <div className="deal-title">{o.name}</div>
                    <Link to={`/firmen/${o.account?.id}`} className="deal-acc" onClick={(e) => e.stopPropagation()}>{o.account?.name}</Link>
                    <div className="deal-foot">
                      <strong>{eur(o.amount)}</strong>
                      <span className={o.close_date && new Date(o.close_date) < new Date(new Date().toDateString()) && !['gewonnen', 'verloren'].includes(o.stage) ? 'text-critical' : 'muted'}>
                        {fmtDate(o.close_date)}
                      </span>
                    </div>
                    <div className="deal-owner muted">{o.owner?.name} · {o.probability} %</div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
      {editing && (
        <Modal title={editing.id ? 'Verkaufschance bearbeiten' : 'Verkaufschance anlegen'} onClose={() => setEditing(null)}>
          <EntityForm fields={opportunityFields} initial={editing} onSubmit={save} onCancel={() => setEditing(null)}
            onDelete={editing.id ? remove : undefined} />
        </Modal>
      )}
    </div>
  )
}
