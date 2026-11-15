import { useState } from 'react'
import { api, downloadFile } from '../api'
import { useAuth } from '../auth'
import { Badge, ErrorBox, Modal } from './ui'

const TONE = { neu: 'good', aktualisieren: 'info', 'unverändert': 'neutral', fehler: 'critical' }

/** Import aus CSV/Excel: Vorlage → Datei → Spaltenzuordnung und Vorschau → Übernahme. */
export default function ImportButton({ entity, label, adminOnly = false, onDone }) {
  const { canWrite, isAdmin } = useAuth()
  const [open, setOpen] = useState(false)
  if (!canWrite || (adminOnly && !isAdmin)) return null
  return <>
    <button className="btn btn-ghost" onClick={() => setOpen(true)}>Importieren</button>
    {open && <ImportDialog entity={entity} label={label} onClose={() => setOpen(false)} onDone={onDone} />}
  </>
}

function ImportDialog({ entity, label, onClose: close, onDone }) {
  const [file, setFile] = useState(null)
  const [fields, setFields] = useState([])
  const [prev, setPrev] = useState(null)
  const [mapping, setMapping] = useState(null)
  const [update, setUpdate] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(null)
  // Liste erst beim Schließen neu laden – sonst schließt das Neuladen den Dialog vor der Erfolgsmeldung
  const onClose = () => { close(); if (done && (done.created || done.updated)) onDone?.() }

  async function preview(f, mp) {
    setBusy(true); setError(null)
    try {
      if (!fields.length) setFields((await api.get(`/import/${entity}/fields`)).fields)
      const fd = new FormData()
      fd.append('file', f)
      if (mp) fd.append('mapping', JSON.stringify(mp))
      const x = await api.post(`/import/${entity}/preview`, fd)
      setPrev(x); setMapping(x.mapping)
    } catch (e) { setError(e) } finally { setBusy(false) }
  }
  async function commit() {
    setBusy(true); setError(null)
    try {
      const fd = new FormData()
      fd.append('file', file); fd.append('mapping', JSON.stringify(mapping)); fd.append('update_existing', update ? 'true' : 'false')
      const x = await api.post(`/import/${entity}/commit`, fd)
      setDone(x)
    } catch (e) { setError(e) } finally { setBusy(false) }
  }
  const setCol = (col, key) => {
    const mp = { ...mapping }
    Object.keys(mp).forEach((c) => { if (key && mp[c] === key) delete mp[c] })
    if (key) mp[col] = key; else delete mp[col]
    setMapping(mp); preview(file, mp)
  }
  const missing = fields.filter((f) => f.required && !Object.values(mapping || {}).includes(f.key))
  const c = prev?.counts || {}
  const importable = (c.neu || 0) + (update ? (c.aktualisieren || 0) : 0)

  return (
    <Modal title={`${label} importieren`} onClose={onClose} wide>
      {done ? (
        <div className="stack">
          <div className="ok-box">Import abgeschlossen: {done.created} neu angelegt, {done.updated} aktualisiert{done.skipped ? `, ${done.skipped} Zeilen mit Fehlern übersprungen` : ''}. Alle Änderungen stehen im Änderungsprotokoll.</div>
          {done.errors.length > 0 && <ul className="small">{done.errors.map((e) => <li key={e.row}>Zeile {e.row}: {e.errors.join('; ')}</li>)}</ul>}
          <div className="toolbar"><button className="btn btn-primary" onClick={onClose}>Schließen</button></div>
        </div>
      ) : <>
        <ol className="import-steps small">
          <li><button className="btn btn-ghost btn-sm" onClick={() => downloadFile(`/import/${entity}/template`, `Vorlage_${label}.csv`)}>Vorlage herunterladen</button>
            {' '}– oder eine vorhandene Excel-/CSV-Liste nehmen; erste Zeile = Spaltenüberschriften.</li>
          <li><input type="file" accept=".csv,.txt,.xlsx" onChange={(e) => { const f = e.target.files[0]; setFile(f); setPrev(null); if (f) preview(f) }} />
            <span className="muted"> CSV (Semikolon/Komma) oder Excel .xlsx, max. 5.000 Zeilen</span></li>
          <li>Spaltenzuordnung und Vorschau prüfen – gespeichert wird erst mit „Importieren“.</li>
        </ol>
        <ErrorBox error={error} />
        {busy && <div className="muted small">Prüfe Datei …</div>}
        {prev && <>
          <div className="import-summary">
            {Object.entries(c).map(([k, v]) => <Badge key={k} tone={TONE[k]}>{v} {k}</Badge>)}
            <span className="muted small">{prev.total} Zeilen</span>
            {missing.length > 0 && <span className="text-critical small">Pflichtfeld nicht zugeordnet: {missing.map((f) => f.label).join(', ')}</span>}
          </div>
          <div className="table-wrap import-table">
            <table className="table table-compact">
              <thead>
                <tr><th>Zeile</th><th>Status</th>{prev.headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
                <tr className="map-row"><th /><th className="muted small">→ Feld</th>{prev.headers.map((h, i) => (
                  <th key={i}><select value={mapping[String(i)] || ''} onChange={(e) => setCol(String(i), e.target.value)}>
                    <option value="">– nicht importieren –</option>
                    {fields.map((f) => <option key={f.key} value={f.key}>{f.label}{f.required ? ' *' : ''}</option>)}
                  </select></th>))}</tr>
              </thead>
              <tbody>{prev.rows.slice(0, 200).map((r) => (
                <tr key={r.row} className={r.status === 'fehler' ? 'row-error' : ''}>
                  <td>{r.row}</td>
                  <td><Badge tone={TONE[r.status]}>{r.status}</Badge>
                    {r.errors.length > 0 && <div className="text-critical small">{r.errors.join('; ')}</div>}
                    {r.changes && Object.keys(r.changes).length > 0 && <div className="muted small">ändert: {Object.keys(r.changes).join(', ')}</div>}</td>
                  {r.raw.map((v, i) => <td key={i} className={mapping[String(i)] ? '' : 'muted'}>{v}</td>)}
                </tr>))}</tbody>
            </table>
          </div>
          {prev.total > 200 && <small className="hint">Vorschau zeigt die ersten 200 Zeilen; importiert werden alle {prev.total}.</small>}
          <div className="toolbar import-actions">
            <label className="inline-label"><input type="checkbox" checked={update} onChange={(e) => setUpdate(e.target.checked)} /> vorhandene Datensätze aktualisieren</label>
            <button className="btn btn-ghost" onClick={onClose}>Abbrechen</button>
            <button className="btn btn-primary" disabled={busy || missing.length > 0 || !importable} onClick={commit}>
              {importable} Datensätze importieren{c.fehler ? ` (${c.fehler} mit Fehlern überspringen)` : ''}</button>
          </div>
        </>}
      </>}
    </Modal>
  )
}
