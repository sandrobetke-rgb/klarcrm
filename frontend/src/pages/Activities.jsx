import { useState } from 'react'
import { Link } from 'react-router-dom'
import FollowupDialog, { LightBadge } from '../components/Followup'
import { api, downloadFile } from '../api'
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
        { key: 'subject', label: 'Betreff', sort: 'subject', render: (r, reload) => <>
          <span className={r.done ? 'line-through muted' : ''}>{r.subject}</span> {r.light && <LightBadge light={r.light} />}
          {(r.opportunity || r.quote) && <><br /><small className="muted">
            {r.opportunity && <Link to={`/anfragen/${r.opportunity.id}`} onClick={(e) => e.stopPropagation()}>{r.opportunity.number || r.opportunity.name}</Link>}
            {r.quote && <> · <Link to={`/angebote/${r.quote.id}`} onClick={(e) => e.stopPropagation()}>{r.quote.number}</Link></>}</small></>}
          {r.kind === 'angebotsverfolgung' && !r.done && <FollowupButton row={r} onDone={reload} />}</> },
        { key: 'due_at', label: 'Fällig', sort: 'due_at', render: (r) => <span className={isOverdue(r) ? 'text-critical' : ''}>{isOverdue(r) && '⚠ '}{fmtDateTime(r.due_at)}</span> },
        { key: 'account', label: 'Firma / Kontakt', render: (r) => <>{r.account?.name || '–'}{r.contact && <><br /><small className="muted">{contactName(r.contact)}</small></>}</> },
        { key: 'owner', label: 'Zuständig', render: (r) => r.owner?.name || '–' },
        { key: 'ics', label: '', render: (r) => r.due_at && r.type !== 'notiz' ? (
          <button className="icon-btn" title="In Outlook übernehmen (.ics)" onClick={(e) => { e.stopPropagation(); downloadFile(`/activities/${r.id}/ics`, `termin-${r.id}.ics`) }}>📅</button>) : null },
      ]}
    />
  )
}

function FollowupButton({ row, onDone }) {
  const [open, setOpen] = useState(false)
  return <>
    <button className="btn btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); setOpen(true) }}>Rücksprache erfassen</button>
    {open && <span onClick={(e) => e.stopPropagation()}><FollowupDialog task={row} onClose={() => setOpen(false)} onDone={() => { setOpen(false); onDone() }} /></span>}
  </>
}
