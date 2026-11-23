import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { fmtDateTime } from '../constants'
import { Badge, ErrorBox } from './ui'

/** Freigabe-Leiste (Vier-Augen-Prinzip) im Kopf einer Kalkulation. */
export default function ApprovalBar({ calc, setCalc }) {
  const { user, canWrite } = useAuth()
  const [comment, setComment] = useState('')
  const [err, setErr] = useState(null)
  const [approvers, setApprovers] = useState(null)
  const [to, setTo] = useState('')
  useEffect(() => { api.get('/calc/approvers').then((a) => { setApprovers(a); if (a.length) setTo(String(a[0].id)) }).catch(() => setApprovers([])) }, [])
  const needed = calc.approval_reasons?.length > 0
  const isApprover = user.role === 'admin' || user.can_approve
  const st = calc.approval_status
  const forCurrent = calc.approval_version === calc.current_version
  if (!needed && !st) return null
  const act = async (path, body) => {
    setErr(null)
    try { setCalc(await api.post(`/calculations/${calc.id}/approval/${path}`, body)); setComment('') } catch (e) { setErr(e) }
  }
  let state
  if (calc.is_approved) state = <Badge tone="good">✓ Freigegeben V{calc.approval_version} von {calc.approval_by?.name} · {fmtDateTime(calc.approval_at)}</Badge>
  else if (st === 'angefragt' && forCurrent) state = <Badge tone="warning">⏳ liegt bei {calc.approval_to?.name || 'allen Freigabeberechtigten'} · angefragt von {calc.approval_requested_by?.name} am {fmtDateTime(calc.approval_requested_at)}</Badge>
  else if (st === 'abgelehnt' && forCurrent) state = <Badge tone="critical">✖ Abgelehnt von {calc.approval_by?.name}</Badge>
  else state = <Badge tone="warning">Freigabe erforderlich{st && !forCurrent ? ` (Freigabe galt für V${calc.approval_version})` : ''}</Badge>

  return (
    <div className={`approval-bar ${calc.is_approved ? 'ok' : ''}`}>
      <div className="approval-info">
        <strong>Freigabe (Vier-Augen-Prinzip)</strong> {state}
        {needed && <span className="muted small">Grund: {calc.approval_reasons.join(' · ')}</span>}
        {approvers && !approvers.length && !calc.is_approved && <span className="small txt-crit">Keine andere Person mit Freigaberecht – in der Benutzerverwaltung „Freigaberecht“ vergeben.</span>}
        {calc.approval_comment && <span className="small">Anfrage: „{calc.approval_comment}“</span>}
        {calc.approval_decision_comment && <span className="small">Entscheidung: „{calc.approval_decision_comment}“</span>}
      </div>
      <div className="approval-actions no-print">
        {(st === 'angefragt' && forCurrent && isApprover && calc.approval_requested_by?.id !== user.id) ? <>
          <input placeholder="Kommentar (bei Ablehnung Pflicht)" value={comment} onChange={(e) => setComment(e.target.value)} />
          <button className="btn btn-ghost btn-sm btn-danger-ghost" onClick={() => act('decide', { decision: 'abgelehnt', comment })}>Ablehnen</button>
          <button className="btn btn-primary btn-sm" onClick={() => act('decide', { decision: 'freigegeben', comment })}>Freigeben V{calc.current_version}</button>
        </> : (!calc.is_approved && !(st === 'angefragt' && forCurrent) && canWrite) ? <>
          <label className="inline-label small">an
            <select value={to} onChange={(e) => setTo(e.target.value)} title="Wer die Freigabe erteilen soll – bekommt Benachrichtigung und Aufgabe">
              {(approvers || []).map((a) => <option key={a.id} value={a.id}>{a.name}{a.role === 'admin' ? ' (Admin)' : ''}</option>)}
              {approvers?.length > 1 && <option value="">alle Freigabeberechtigten</option>}
            </select></label>
          <input placeholder="Begründung für die Freigabe" value={comment} onChange={(e) => setComment(e.target.value)} />
          <button className="btn btn-primary btn-sm" disabled={approvers && !approvers.length} onClick={() => act('request', { comment, approver_id: to ? Number(to) : null })}>Freigabe anfordern</button>
        </> : (st === 'angefragt' && forCurrent && calc.approval_requested_by?.id === user.id) ?
          <span className="muted small">Die Person hat eine Benachrichtigung und die Aufgabe „Freigabe prüfen“ erhalten (auch auf ihrer Startseite).</span> : null}
      </div>
      <ErrorBox error={err} />
    </div>
  )
}
