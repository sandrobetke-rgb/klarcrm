import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { ErrorBox } from '../components/ui'

export default function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/" replace />

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      await login(email, password)
      nav('/')
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }
  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <div className="brand brand-lg"><span className="logo">K</span> KlarCRM</div>
        <p className="muted">Bitte melde dich mit deinem Konto an.</p>
        <div className="field">
          <label htmlFor="email">E-Mail</label>
          <input id="email" type="email" autoFocus required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="pw">Passwort</label>
          <input id="pw" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <ErrorBox error={error} />
        <button className="btn btn-primary btn-block" disabled={busy}>{busy ? 'Anmelden…' : 'Anmelden'}</button>
      </form>
    </div>
  )
}
