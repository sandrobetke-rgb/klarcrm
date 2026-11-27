import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Modal } from './ui'

// REV04-01 Softwarestand: „KlarCRM v1.32 · eingespielt am …“ – Klick zeigt die Auslieferungen
let cache = null
let pending = null
function load() {
  if (cache) return Promise.resolve(cache)
  if (!pending) pending = fetch('/api/version').then((r) => (r.ok ? r.json() : null)).then((d) => (cache = d)).catch(() => null)
  return pending
}
export const fmtInstalled = (iso) => (iso ? new Date(iso).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : null)

export function useVersion() {
  const [v, setV] = useState(cache)
  useEffect(() => { let alive = true; load().then((d) => alive && setV(d)); return () => { alive = false } }, [])
  return v
}

export function Releases({ v }) {
  return (
    <table className="table table-compact">
      <thead><tr><th>Version</th><th>Stand</th><th>Inhalt</th><th>Eingespielt</th></tr></thead>
      <tbody>{v.releases.map((r) => (
        <tr key={r.version} className={r.version === v.version ? 'row-current' : ''}>
          <td><strong>v{r.version}</strong></td><td>{r.date}</td><td>{r.content}</td>
          <td>{fmtInstalled(r.installed_at) || <span className="muted">–</span>}</td></tr>))}
      </tbody>
    </table>
  )
}

export default function Version({ className = '' }) {
  const v = useVersion()
  const [open, setOpen] = useState(false)
  if (!v) return null
  const when = fmtInstalled(v.installed_at)
  return (
    <>
      <button type="button" className={`version-chip ${className}`} onClick={() => setOpen(true)} title="Softwarestand – Auslieferungen anzeigen">
        KlarCRM v{v.version}{when && <> · eingespielt am {when}</>}
      </button>
      {open && createPortal(<div className="version-modal"><Modal title={`Softwarestand KlarCRM v${v.version}`} onClose={() => setOpen(false)} wide>
        <div className="version-body"><p className="muted">Eingespielt am {when || '–'} (erster Start dieser Version auf dem Server). Frühere Stände ohne Datum wurden vor der Anzeige des Softwarestands eingespielt.</p>
        <Releases v={v} /></div>
      </Modal></div>, document.body)}
    </>
  )
}
