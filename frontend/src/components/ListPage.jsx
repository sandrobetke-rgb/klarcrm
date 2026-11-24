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
  newDefaults = {}, onRowClick, toForm = (r) => r, extraActions, limit = 50, top, rowClass, bulkBar, customDelete,
}) {
  const { canWrite } = useAuth()
  const [q, setQ] = useState('')
  const [sort, setSort] = useState(defaultSort)
  const [offset, setOffset] = useState(0)
  // Filter aus der Adresszeile übernehmen (z. B. Dashboard-Kachel → /kalkulationen?big=true)
  const [filterVals, setFilterVals] = useState(() => {
    const p = new URLSearchParams(window.location.search)
    return Object.fromEntries(filters.filter((f) => p.get(f.name)).map((f) => [f.name, p.get(f.name)]))
  })
  const [editing, setEditing] = useState(null)
  const [selected, setSelected] = useState({})
  const selRows = Object.values(selected)
  const toggle = (r) => setSelected((s) => { const n = { ...s }; if (n[r.id]) delete n[r.id]; else n[r.id] = r; return n })
  const params = { ...baseParams, ...filterVals, q, sort, limit, offset }
  const { data, error, loading, reload } = useFetch(path + qs(params))

  const [notice, setNotice] = useState(null)
  const [saved, setSaved] = useState(0)
  async function save(values) {
    const isNew = !editing.id
    const r = isNew ? await api.post(path, values) : await api.patch(`${path}/${editing.id}`, values)
    setEditing(null)
    setSaved((n) => n + 1)
    // Rückmeldung nach dem Speichern – auch wenn ein aktiver Filter den Datensatz ausblendet
    const name = r?.code || r?.number || r?.name || r?.title || ''
    setNotice({ text: `${entityLabel} ${name} ${isNew ? 'angelegt' : 'gespeichert'}`.replace(/\s+/g, ' '),
      hidden: isNew && Object.values(filterVals).some(Boolean) })
    reload()
  }
  async function remove() {
    if (customDelete) { if (await customDelete(editing)) { setEditing(null); reload() } return }
    if (await confirmDelete(entityLabel, () => api.del(`${path}/${editing.id}`))) {
      setEditing(null)
      reload()
    }
  }
  const toggleSort = (key) => setSort((s) => (s === key ? `-${key}` : key))

  return (
    <div className="page page-wide">
      {notice && <div className="notice-ok no-print">✓ {notice.text}
        {notice.hidden && <> – der aktive Filter blendet ihn evtl. aus. <button className="btn btn-ghost btn-sm" onClick={() => { setFilterVals({}); window.history.replaceState(null, '', window.location.pathname); setNotice(null) }}>Filter zurücksetzen</button></>}
        <button className="btn-x" onClick={() => setNotice(null)} aria-label="schließen">×</button></div>}
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
      {typeof top === 'function' ? top(saved) : top}
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
      {bulkBar && selRows.length > 0 && <div className="bulk-bar">{bulkBar(selRows, () => setSelected({}))}</div>}
      <div className="card card-flush">
        <table className="table">
          <thead>
            <tr>
              {bulkBar && (
                <th className="sel-col">
                  <input type="checkbox" aria-label="Alle auf dieser Seite auswählen"
                    checked={!!data?.items.length && data.items.every((r) => selected[r.id])}
                    onChange={(e) => setSelected((s) => {
                      const n = { ...s }
                      data?.items.forEach((r) => { if (e.target.checked) n[r.id] = r; else delete n[r.id] })
                      return n
                    })} />
                </th>
              )}
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
                {bulkBar && (
                  <td className="sel-col" onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" aria-label="Auswählen" checked={!!selected[r.id]} onChange={() => toggle(r)} />
                  </td>
                )}
                {columns.map((c) => <td key={c.key} className={c.className}>{c.render ? c.render(r, reload) : r[c.key] ?? '–'}</td>)}
              </tr>
            ))}
            {data && !data.items.length && (
              <tr><td colSpan={columns.length + (bulkBar ? 1 : 0)} className="empty">Keine Einträge gefunden.</td></tr>
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
