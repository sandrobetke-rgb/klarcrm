import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { ErrorBox } from '../components/ui'
import { ROLES } from '../constants'

export default function Profile() {
  const { user } = useAuth()
  const [oldPw, setOld] = useState('')
  const [newPw, setNew] = useState('')
  const [msg, setMsg] = useState(null)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/auth/password', { old_password: oldPw, new_password: newPw })
      setMsg('Passwort geändert.')
      setOld(''); setNew('')
    } catch (err) { setError(err) }
  }
  return (
    <div className="page page-narrow">
      <h1>Mein Profil</h1>
      <div className="card">
        <dl className="dl">
          <dt>Name</dt><dd>{user.name}</dd>
          <dt>E-Mail</dt><dd>{user.email}</dd>
          <dt>Rolle</dt><dd>{ROLES.find((r) => r.value === user.role)?.label}</dd>
        </dl>
      </div>
      <CalendarSub />
      <form className="card form" onSubmit={submit}>
        <h3>Passwort ändern</h3>
        <div className="field"><label>Aktuelles Passwort</label><input type="password" required value={oldPw} onChange={(e) => setOld(e.target.value)} /></div>
        <div className="field"><label>Neues Passwort (mind. 8 Zeichen)</label><input type="password" minLength={8} required value={newPw} onChange={(e) => setNew(e.target.value)} /></div>
        <ErrorBox error={error} />
        {msg && <div className="ok-box">{msg}</div>}
        <div className="form-actions"><span className="spacer" /><button className="btn btn-primary">Ändern</button></div>
      </form>
    </div>
  )
}


function CalendarSub() {
  const [t, setT] = useState(null)
  const [copied, setCopied] = useState(false)
  useEffect(() => { api.get('/calendar-token').then(setT) }, [])
  if (!t) return null
  const url = `${t.app_url || window.location.origin}${t.path}`
  return (
    <div className="card">
      <h3>Outlook-Kalender abonnieren</h3>
      <p className="small muted" style={{ marginTop: 0 }}>Termine, Anrufe und Aufgaben (Wiedervorlagen) erscheinen automatisch in Outlook.
        In Outlook: <b>Kalender hinzufügen → Aus dem Internet</b> und diese Adresse einfügen. Nicht weitergeben – sie ersetzt die Anmeldung.</p>
      <div className="calsub"><input readOnly value={url} onFocus={(e) => e.target.select()} />
        <button className="btn btn-ghost btn-sm" onClick={() => { navigator.clipboard?.writeText(url); setCopied(true) }}>{copied ? '✓ kopiert' : 'Kopieren'}</button>
        <button className="btn btn-ghost btn-sm" onClick={async () => { setT(await api.post('/calendar-token/renew')); setCopied(false) }}>Neue Adresse</button></div>
    </div>
  )
}
