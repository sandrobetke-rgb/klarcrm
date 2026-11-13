import { useState } from 'react'
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
