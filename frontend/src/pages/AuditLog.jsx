import { useState } from 'react'
import AuditTable from '../components/AuditTable'
import { ErrorBox, Pager, RefSelect, SearchInput, useFetch } from '../components/ui'
import { qs } from '../api'

export default function AuditLog() {
  const [f, setF] = useState({ entity: '', user_id: null, q: '', date_from: '', date_to: '' })
  const [offset, setOffset] = useState(0)
  const { data, error } = useFetch('/audit' + qs({ ...f, limit: 100, offset }))
  const set = (k, v) => { setF((s) => ({ ...s, [k]: v })); setOffset(0) }
  return (
    <div className="page page-wide">
      <header className="page-head">
        <div><h1>Änderungsprotokoll</h1>
          <p className="muted">Wer hat wann was geändert – alle Datensätze, mit altem und neuem Wert. Einträge sind nicht änderbar.</p></div>
      </header>
      <div className="filters">
        <SearchInput value={f.q} onChange={(v) => set('q', v)} placeholder="Datensatz suchen (z. B. K26-0012)…" />
        <select value={f.entity} onChange={(e) => set('entity', e.target.value)}>
          <option value="">Bereich: alle</option>
          {data && Object.entries(data.entities).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
        <label className="inline-label">Benutzer <RefSelect kind="user" value={f.user_id} onChange={(v) => set('user_id', v)} /></label>
        <label className="inline-label">von <input type="date" value={f.date_from} onChange={(e) => set('date_from', e.target.value)} /></label>
        <label className="inline-label">bis <input type="date" value={f.date_to} onChange={(e) => set('date_to', e.target.value)} /></label>
      </div>
      <ErrorBox error={error} />
      <div className="card card-flush">{data && <AuditTable rows={data.items} />}</div>
      {data && <Pager total={data.total} limit={100} offset={offset} onChange={setOffset} />}
    </div>
  )
}
