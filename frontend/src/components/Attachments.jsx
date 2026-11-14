import { useRef, useState } from 'react'
import { api, downloadFile, qs } from '../api'
import { useAuth } from '../auth'
import { fmtDateTime } from '../constants'
import { Badge, ErrorBox, useFetch } from './ui'

const size = (b) => (b > 1048576 ? `${(b / 1048576).toLocaleString('de-DE', { maximumFractionDigits: 1 })} MB` : `${Math.max(1, Math.round(b / 1024))} KB`)

/** Dokumente zu einem Datensatz: hochladen (auch per Drag & Drop), herunterladen, ausblenden. */
export default function Attachments({ entity, entityId, title = 'Dokumente', compact }) {
  const { canWrite, user } = useAuth()
  const { data, reload } = useFetch(`/attachments${qs({ entity, entity_id: entityId })}`)
  const [meta, setMeta] = useState({ doc_type: 'zeichnung', revision: '', note: '' })
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const [drag, setDrag] = useState(false)
  const input = useRef()

  async function upload(files) {
    setErr(null); setBusy(true)
    try {
      for (const f of files) {
        const fd = new FormData()
        fd.append('entity', entity); fd.append('entity_id', entityId)
        Object.entries(meta).forEach(([k, v]) => fd.append(k, v))
        fd.append('file', f)
        await api.upload('/attachments', fd)
      }
      setMeta((m) => ({ ...m, revision: '', note: '' }))
      reload()
    } catch (e) { setErr(e) } finally { setBusy(false); if (input.current) input.current.value = '' }
  }
  const types = data?.doc_types || {}
  return (
    <div className="card">
      <div className="section-head"><h3>{title} {data && <span className="count">{data.items.length}</span>}</h3></div>
      {canWrite && (
        <div className={`dropzone ${drag ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); upload([...e.dataTransfer.files]) }}>
          <select value={meta.doc_type} onChange={(e) => setMeta({ ...meta, doc_type: e.target.value })}>
            {Object.entries(types).filter(([k]) => k !== 'logo').map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
          <input placeholder="Revision / Index" value={meta.revision} onChange={(e) => setMeta({ ...meta, revision: e.target.value })} />
          {!compact && <input placeholder="Notiz" value={meta.note} onChange={(e) => setMeta({ ...meta, note: e.target.value })} />}
          <input ref={input} type="file" multiple hidden onChange={(e) => upload([...e.target.files])} />
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => input.current.click()}>{busy ? 'Lädt hoch…' : 'Datei wählen'}</button>
          <span className="muted small">oder Dateien hierher ziehen</span>
        </div>
      )}
      <ErrorBox error={err} />
      {data?.items.length ? (
        <table className="table table-compact">
          <thead><tr><th>Datei</th><th>Art</th><th>Rev.</th><th>Hochgeladen</th><th className="num">Größe</th><th /></tr></thead>
          <tbody>{data.items.map((a) => (
            <tr key={a.id}>
              <td><button className="linklike" onClick={() => downloadFile(`/attachments/${a.id}/download`, a.filename).catch(setErr)}>{a.filename}</button>
                {a.note && <><br /><small className="muted">{a.note}</small></>}</td>
              <td><Badge>{a.doc_type_label}</Badge></td>
              <td>{a.revision || '–'}</td>
              <td className="small">{fmtDateTime(a.created_at)}<br /><span className="muted">{a.uploaded_by}</span></td>
              <td className="num small">{size(a.size)}</td>
              <td>{canWrite && (user.role === 'admin' || a.uploaded_by === user.name) &&
                <button className="icon-btn" title="Ausblenden (bleibt als Nachweis gespeichert)" onClick={async () => { await api.del(`/attachments/${a.id}`); reload() }}>×</button>}</td>
            </tr>
          ))}</tbody>
        </table>
      ) : <div className="empty small">Noch keine Dokumente.</div>}
    </div>
  )
}
