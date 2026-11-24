import { useState } from 'react'
import { api, auditUnlocked, setAuditToken } from '../api'
import { useAuth } from '../auth'
import { AUDIT_VIEW } from '../constants'
import { ErrorBox } from './ui'

// REV02-07: Protokoll nur für den SuperUser und erst nach erneuter Passworteingabe (30 Minuten freigeschaltet)
export default function AuditGate({ children }) {
  const { user } = useAuth()
  const [ok, setOk] = useState(auditUnlocked())
  const [pw, setPw] = useState('')
  const [err, setErr] = useState(null)
  if (!AUDIT_VIEW) return <div className="card"><p className="muted">Das Protokoll ist in dieser Version ausgeblendet.</p></div>
  if (!user?.is_superuser) return <div className="card"><p className="muted">🔒 Das Protokoll ist gesperrt und nur für den SuperUser zugänglich.</p></div>
  if (ok) return children
  async function unlock(e) {
    e.preventDefault(); setErr(null)
    try { const r = await api.post('/audit/unlock', { password: pw }); setAuditToken(r.token, r.minutes); setOk(true) } catch (x) { setErr(x) }
  }
  return (
    <form className="card audit-lock" onSubmit={unlock}>
      <h3>🔒 Protokoll gesperrt</h3>
      <p className="muted small">Zum Öffnen bitte dein Passwort erneut eingeben. Die Freischaltung gilt 30 Minuten in diesem Browser-Tab.</p>
      <ErrorBox error={err} />
      <div className="filters"><input type="password" autoComplete="current-password" autoFocus placeholder="Passwort" value={pw} onChange={(e) => setPw(e.target.value)} />
        <button className="btn btn-primary" disabled={!pw}>Entsperren</button></div>
    </form>
  )
}
