import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { fmtDateTime } from '../constants'

/** Glocke mit Benachrichtigungen (Freigaben, fällige Aufgaben, ablaufende Angebote). */
export default function NotificationBell() {
  const nav = useNavigate()
  const [data, setData] = useState({ unread: 0, items: [] })
  const [open, setOpen] = useState(false)
  const ref = useRef()
  const load = () => api.get('/notifications').then(setData).catch(() => {})
  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t) }, [])
  useEffect(() => {
    const close = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false)
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])
  async function go(n) {
    if (typeof n.id === 'number' && !n.read) await api.post(`/notifications/${n.id}/read`)
    setOpen(false); load()
    if (n.link) nav(n.link)
  }
  return (
    <div className="bell-wrap" ref={ref}>
      <button className="bell" onClick={() => { setOpen(!open); if (!open) load() }} aria-label="Benachrichtigungen">
        🔔 Hinweise{data.unread > 0 && <span className="bell-count">{data.unread}</span>}
      </button>
      {open && (
        <div className="bell-panel">
          <div className="bell-head"><strong>Benachrichtigungen</strong>
            <button className="linklike small" onClick={async () => { await api.post('/notifications/read-all'); load() }}>alle gelesen</button></div>
          {data.items.length ? data.items.map((n) => (
            <button key={n.id} className={`bell-item ${n.read ? 'read' : ''} sev-${n.severity || 'info'}`} onClick={() => go(n)}>
              <span className="bell-title">{n.title}</span>
              {n.body && <span className="bell-body">{n.body}</span>}
              <span className="bell-time">{fmtDateTime(n.created_at)}</span>
            </button>
          )) : <div className="empty small">Keine Hinweise.</div>}
        </div>
      )}
    </div>
  )
}
