import { api } from '../api'
import { useAuth } from '../auth'
import ListPage from '../components/ListPage'
import { ACTIVITY_TYPES, activityType, contactName, fmtDateTime } from '../constants'
import { activityFields } from '../forms'

export function DoneToggle({ row, onChange }) {
  const { canWrite } = useAuth()
  return (
    <input type="checkbox" aria-label="Erledigt" checked={row.done} disabled={!canWrite}
      onClick={(e) => e.stopPropagation()}
      onChange={async (e) => { await api.patch(`/activities/${row.id}`, { done: e.target.checked }); onChange() }} />
  )
}

export const isOverdue = (a) => !a.done && a.due_at && new Date(a.due_at) < new Date()

export default function Activities() {
  return (
    <ListPage
      title="Aktivitäten" subtitle="Anrufe, Termine, E-Mails und Aufgaben" path="/activities" entityLabel="Aktivität"
      fields={activityFields} defaultSort="due_at" newDefaults={{ type: 'aufgabe', done: false }}
      baseParams={{}}
      filters={[
        { name: 'done', label: 'Status', options: [{ value: 'false', label: 'Offen' }, { value: 'true', label: 'Erledigt' }] },
        { name: 'due', label: 'Fällig', options: [{ value: 'overdue', label: 'Überfällig' }, { value: 'today', label: 'Heute' }, { value: 'week', label: 'Nächste 7 Tage' }] },
        { name: 'type', label: 'Art', options: ACTIVITY_TYPES },
      ]}
      columns={[
        { key: 'done', label: '✓', render: (r, reload) => <DoneToggle row={r} onChange={reload} /> },
        { key: 'type', label: 'Art', sort: 'type', render: (r) => <span className="act-type">{activityType(r.type).icon} {activityType(r.type).label}</span> },
        { key: 'subject', label: 'Betreff', sort: 'subject', render: (r) => <span className={r.done ? 'line-through muted' : ''}>{r.subject}</span> },
        { key: 'due_at', label: 'Fällig', sort: 'due_at', render: (r) => <span className={isOverdue(r) ? 'text-critical' : ''}>{isOverdue(r) && '⚠ '}{fmtDateTime(r.due_at)}</span> },
        { key: 'account', label: 'Firma / Kontakt', render: (r) => <>{r.account?.name || '–'}{r.contact && <><br /><small className="muted">{contactName(r.contact)}</small></>}</> },
        { key: 'owner', label: 'Zuständig', render: (r) => r.owner?.name || '–' },
      ]}
    />
  )
}
