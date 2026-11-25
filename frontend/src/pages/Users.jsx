import { siteOptions, useSites } from '../components/useSites'
import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Badge, EntityForm, ErrorBox, Modal, useFetch } from '../components/ui'
import { fmtDate, ROLES } from '../constants'

const fields = (isNew, sites = []) => [
  { name: 'name', label: 'Name', required: true },
  { name: 'email', label: 'E-Mail (Login)', type: 'email', required: true },
  { name: 'role', label: 'Rolle', type: 'select', options: ROLES, required: true },
  { name: 'password', label: isNew ? 'Passwort' : 'Neues Passwort', type: 'password', required: isNew, hint: isNew ? 'Mind. 8 Zeichen' : 'Leer lassen = unverändert' },
  ...(sites.length ? [{ name: 'site_id', label: 'Standard-Standort (für neue Kalkulationen)', type: 'select', options: siteOptions(sites) }] : []),
  { name: 'can_approve', label: 'Darf Kalkulationen freigeben (Vier-Augen-Prinzip)', type: 'checkbox' },
  { name: 'active', label: 'Aktiv', type: 'checkbox' },
]

export default function Users() {
  const { isAdmin, user: me } = useAuth()
  const { data, error, reload } = useFetch('/users')
  const [editing, setEditing] = useState(null)
  const sites = useSites()
  if (!isAdmin) return <Navigate to="/" />

  async function save(values) {
    if (!values.password) delete values.password
    if (!me?.is_superuser || !!values.is_superuser === !!editing.is_superuser) delete values.is_superuser
    if (editing.id) await api.patch(`/users/${editing.id}`, values)
    else await api.post('/users', values)
    setEditing(null)
    reload()
  }
  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Benutzer</h1>
          <p className="muted">Admin: alles · Vertrieb: Daten pflegen · Gesellschafter: alles sehen, nichts ändern</p>
        </div>
        <button className="btn btn-primary" onClick={() => setEditing({ role: 'vertrieb', active: true })}>+ Benutzer anlegen</button>
      </header>
      <ErrorBox error={error} />
      <div className="card card-flush">
        <table className="table">
          <thead><tr><th>Name</th><th>E-Mail</th><th>Rolle</th><th>Status</th><th>Angelegt</th></tr></thead>
          <tbody>
            {data?.map((u) => (
              <tr key={u.id} className="row-click" onClick={() => setEditing(u)}>
                <td><strong>{u.name}</strong>{u.id === me.id && <small className="muted"> (du)</small>}</td>
                <td>{u.email}</td>
                <td>{ROLES.find((r) => r.value === u.role)?.label}{(u.can_approve || u.role === 'admin') && <><br /><small className="muted">✓ Freigabe</small></>}{u.is_superuser && <><br /><small className="muted">🔒 SuperUser</small></>}</td>
                <td>{u.active ? <Badge tone="good">aktiv</Badge> : <Badge>deaktiviert</Badge>}</td>
                <td>{fmtDate(u.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing && (
        <Modal title={editing.id ? 'Benutzer bearbeiten' : 'Benutzer anlegen'} onClose={() => setEditing(null)}>
          <EntityForm fields={fields(!editing.id, sites).filter((f) => !f.superOnly || me?.is_superuser)} initial={editing} onSubmit={save} onCancel={() => setEditing(null)} />
        </Modal>
      )}
    </div>
  )
}
