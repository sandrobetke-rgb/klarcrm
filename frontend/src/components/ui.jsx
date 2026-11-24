import { useEffect, useState } from 'react'
import { api, qs } from '../api'
import { contactName } from '../constants'
import NumInput from './NumInput'

export function Modal({ title, onClose, children, wide }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-label={title}>
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Schließen">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function Badge({ children, tone = 'neutral' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

export function Empty({ children }) {
  return <div className="empty">{children}</div>
}

export function ErrorBox({ error }) {
  if (!error) return null
  return <div className="error-box">{String(error.message || error)}</div>
}

export function useFetch(path, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tick, setTick] = useState(0)
  useEffect(() => {
    if (!path) return
    let alive = true
    setLoading(true)
    api.get(path)
      .then((d) => alive && (setData(d), setError(null)))
      .catch((e) => alive && setError(e))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, tick, ...deps])
  return { data, error, loading, reload: () => setTick((t) => t + 1) }
}

// Auswahllisten für Verknüpfungen
const REF = {
  account: { path: '/accounts', params: { sort: 'name', limit: 500 }, label: (r) => r.name },
  // Kunden/Interessenten ohne Lieferanten – für Angebote, Kalkulationen, Verkaufschancen (REV01-B04)
  customer: { path: '/accounts', params: { sort: 'name', limit: 500 }, label: (r) => r.name, rowFilter: (r) => r.type !== 'lieferant' },
  contact: { path: '/contacts', params: { sort: 'last_name', limit: 500 }, label: (r) => `${contactName(r)}${r.account ? ' · ' + r.account.name : ''}`, dep: 'account_id' },
  opportunity: { path: '/opportunities', params: { sort: 'name', limit: 500 }, label: (r) => `${r.number ? r.number + ' · ' : ''}${r.name}`, dep: 'account_id' },
  quote: { path: '/quotes', params: { sort: '-quote_date', limit: 500 }, label: (r) => `${r.number} · ${r.title}`, dep: 'account_id' },
  calculation: { path: '/calculations', params: { limit: 500 }, label: (r) => `${r.number} · ${r.article_name}${r.account ? ' · ' + r.account.name : ''}` },
}

export function RefSelect({ kind, value, onChange, filter, required, id }) {
  const cfg = REF[kind]
  const [rows, setRows] = useState([])
  useEffect(() => {
    if (kind === 'user') {
      api.get('/users').then((u) => setRows(u.filter((x) => x.active)))
      return
    }
    const params = { ...cfg.params }
    if (cfg.dep && filter) params[cfg.dep] = filter
    api.get(cfg.path + qs(params)).then((d) => setRows(cfg.rowFilter ? d.items.filter((r) => cfg.rowFilter(r) || r.id === value) : d.items))
  }, [kind, filter])
  const label = kind === 'user' ? (r) => r.name : cfg.label
  return (
    <select id={id} value={value ?? ''} required={required}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      <option value="">– keine Auswahl –</option>
      {rows.map((r) => <option key={r.id} value={r.id}>{label(r)}</option>)}
    </select>
  )
}

const toLocalInput = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  const off = d.getTimezoneOffset() * 60000
  return new Date(d - off).toISOString().slice(0, 16)
}

/**
 * Generisches Formular. fields: [{name, label, type, options, required, span, dependsOn}]
 */
export function EntityForm({ fields, initial, onSubmit, onCancel, onDelete, submitLabel = 'Speichern' }) {
  // Felder mit scale (z. B. Faktor 0,3 als 30 %) werden skaliert angezeigt und zurückgerechnet gespeichert
  const [values, setValues] = useState(() => {
    const v = { ...initial }
    fields.forEach((f) => { if (f.scale && v[f.name] != null && v[f.name] !== '') v[f.name] = Math.round(Number(v[f.name]) * f.scale * 1e6) / 1e6 })
    return v
  })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  // Feld mit onSet(wert, werte) kann abhängige Felder sofort mitsetzen (z. B. Schichtmodell → verfügbare Stunden)
  const set = (name, v) => setValues((s) => {
    const f = fields.find((x) => x.name === name)
    return { ...s, [name]: v, ...(f?.onSet ? f.onSet(v, s) || {} : {}) }
  })

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    const out = {}
    fields.forEach((f) => {
      let v = values[f.name]
      if (v === '' || v === undefined) v = null
      if (f.type === 'number' && v !== null) v = Number(v)
      if (f.scale && v !== null) v = v / f.scale
      if (f.type === 'datetime' && v) v = new Date(v).toISOString()
      if (f.type === 'checkbox') v = !!v
      out[f.name] = v
    })
    try {
      await onSubmit(out)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="form" autoComplete="off">
      <div className="form-grid">
        {fields.map((f) => {
          const id = `f-${f.name}`
          const v = values[f.name]
          let input
          if (['account', 'customer', 'contact', 'user', 'opportunity', 'quote', 'calculation'].includes(f.type)) {
            input = <RefSelect id={id} kind={f.type} value={v} required={f.required}
              filter={f.dependsOn ? values[f.dependsOn] : undefined} onChange={(x) => set(f.name, x)} />
          } else if (f.type === 'select') {
            input = (
              <select id={id} value={v ?? ''} required={f.required} onChange={(e) => set(f.name, e.target.value)}>
                {!f.required && <option value="">–</option>}
                {f.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            )
          } else if (f.type === 'combo') {
            // Vorauswahl mit freier Eingabe (z. B. Branche)
            input = <><input id={id} list={`${id}-list`} value={v ?? ''} required={f.required} autoComplete="off"
              onChange={(e) => set(f.name, e.target.value)} placeholder="auswählen oder eingeben" />
              <datalist id={`${id}-list`}>{f.options.map((o) => <option key={o} value={o} />)}</datalist></>
          } else if (f.type === 'textarea') {
            input = <textarea id={id} rows={f.rows || 3} value={v ?? ''} onChange={(e) => set(f.name, e.target.value)} />
          } else if (f.type === 'checkbox') {
            input = <input id={id} type="checkbox" checked={!!v} onChange={(e) => set(f.name, e.target.checked)} />
          } else if (f.type === 'datetime') {
            input = <input id={id} type="datetime-local" value={toLocalInput(v)} required={f.required}
              onChange={(e) => set(f.name, e.target.value ? new Date(e.target.value).toISOString() : null)} />
          } else {
            input = <NumInput id={id} type={f.type || 'text'} step={f.step} min={f.min} max={f.max}
              value={v ?? ''} required={f.required} onChange={(e) => set(f.name, e.target.value)} />
          }
          return (
            <div key={f.name} className={`field ${f.span ? 'span-2' : ''} ${f.type === 'checkbox' ? 'field-check' : ''}`}>
              <label htmlFor={id}>{f.label}{f.required && ' *'}</label>
              {input}
              {f.hint && <small className="hint">{f.hint}</small>}
            </div>
          )
        })}
      </div>
      <ErrorBox error={error} />
      <div className="form-actions">
        {onDelete && <button type="button" className="btn btn-danger-ghost" onClick={onDelete}>Löschen</button>}
        <span className="spacer" />
        <button type="button" className="btn btn-ghost" onClick={onCancel}>Abbrechen</button>
        <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Speichert…' : submitLabel}</button>
      </div>
    </form>
  )
}

export function SearchInput({ value, onChange, placeholder = 'Suchen…' }) {
  const [v, setV] = useState(value || '')
  useEffect(() => {
    const t = setTimeout(() => onChange(v), 250)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [v])
  return <input className="search" type="search" placeholder={placeholder} value={v} onChange={(e) => setV(e.target.value)} />
}

export function Pager({ total, limit, offset, onChange }) {
  if (total <= limit) return <div className="pager muted">{total} Einträge</div>
  return (
    <div className="pager">
      <span className="muted">{offset + 1}–{Math.min(offset + limit, total)} von {total}</span>
      <button className="btn btn-ghost btn-sm" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>‹ Zurück</button>
      <button className="btn btn-ghost btn-sm" disabled={offset + limit >= total} onClick={() => onChange(offset + limit)}>Weiter ›</button>
    </div>
  )
}

export async function confirmDelete(what, fn) {
  if (window.confirm(`${what} wirklich löschen? Das kann nicht rückgängig gemacht werden.`)) {
    await fn()
    return true
  }
  return false
}
