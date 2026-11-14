import { useState } from 'react'
import { api, qs } from '../api'
import { useAuth } from '../auth'
import { confirmDelete, EntityForm, ErrorBox, Modal, Pager, SearchInput, useFetch } from './ui'

/**
 * Generische Listen-Seite mit Suche, Filtern, Sortierung, Paging, Anlegen/Bearbeiten im Dialog.
 * columns: [{key, label, render(row), sort, className}]
 * filters: [{name, label, options:[{value,label}]}]
 */
export default function ListPage({
  title, subtitle, path, columns, fields, entityLabel, defaultSort, filters = [], baseParams = {},
  newDefaults = {}, onRowClick, toForm = (r) => r, extraActions, limit = 50, top, rowClass,
}) {
  const { canWrite } = useAuth()
  const [q, setQ] = useState('')
  const [sort, setSort] = useState(defaultSort)
  const [offset, setOffset] = useState(0)
  const [filterVals, setFilterVals] = useState({})
  const [editing, setEditing] = useState(null)
  const params = { ...baseParams, ...filterVals, q, sort, limit, offset }
  const { data, error, loading, reload } = useFetch(path + qs(params))

  async function save(values) {
    if (editing.id) await api.patch(`${path}/${editing.id}`, values)
    else await api.post(path, values)
    setEditing(null)
    reload()
  }
  async function remove() {
    if (await confirmDelete(entityLabel, () => api.del(`${path}/${editing.id}`))) {
      setEditing(null)
      reload()
    }
  }
  const toggleSort = (key) => setSort((s) => (s === key ? `-${key}` : key))

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>{title}</h1>
          {subtitle && <p className="muted">{subtitle}</p>}
        </div>
        <div className="toolbar">
          {extraActions}
          {canWrite && fields && (
            <button className="btn btn-primary" onClick={() => setEditing({ ...newDefaults })}>+ {entityLabel} anlegen</button>
          )}
        </div>
      </header>
      {top}
      <div className="filters">
        <SearchInput value={q} onChange={(v) => { setQ(v); setOffset(0) }} />
        {filters.map((f) => (
          <select key={f.name} value={filterVals[f.name] || ''} aria-label={f.label}
            onChange={(e) => { setFilterVals((s) => ({ ...s, [f.name]: e.target.value })); setOffset(0) }}>
            <option value="">{f.label}: alle</option>
            {f.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        ))}
      </div>
      <ErrorBox error={error} />
      <div className="card card-flush">
        <table className="table">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} className={c.className}>
                  {c.sort ? (
                    <button className="th-sort" onClick={() => toggleSort(c.sort)}>
                      {c.label}{sort === c.sort ? ' ↑' : sort === `-${c.sort}` ? ' ↓' : ''}
                    </button>
                  ) : c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data?.items.map((r) => (
              <tr key={r.id} className={`row-click ${rowClass ? rowClass(r) : ''}`}
                onClick={() => (onRowClick ? onRowClick(r) : canWrite && fields && setEditing(toForm(r)))}>
                {columns.map((c) => <td key={c.key} className={c.className}>{c.render ? c.render(r, reload) : r[c.key] ?? '–'}</td>)}
              </tr>
            ))}
            {data && !data.items.length && (
              <tr><td colSpan={columns.length} className="empty">Keine Einträge gefunden.</td></tr>
            )}
            {loading && !data && <tr><td colSpan={columns.length} className="empty">Lade…</td></tr>}
          </tbody>
        </table>
      </div>
      {data && <Pager total={data.total} limit={limit} offset={offset} onChange={setOffset} />}
      {editing && (
        <Modal title={editing.id ? `${entityLabel} bearbeiten` : `${entityLabel} anlegen`} onClose={() => setEditing(null)}>
          <EntityForm fields={fields} initial={editing} onSubmit={save} onCancel={() => setEditing(null)}
            onDelete={editing.id ? remove : undefined} />
        </Modal>
      )}
    </div>
  )
}
