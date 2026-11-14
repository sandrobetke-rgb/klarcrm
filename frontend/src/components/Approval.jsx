import { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { fmtDateTime } from '../constants'
import { Badge, ErrorBox } from './ui'

/** Freigabe-Leiste (Vier-Augen-Prinzip) im Kopf einer Kalkulation. */
export default function ApprovalBar({ calc, setCalc }) {
  const { user, canWrite } = useAuth()
  const [comment, setComment] = useState('')
  const [err, setErr] = useState(null)
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
  else if (st === 'angefragt' && forCurrent) state = <Badge tone="warning">⏳ Freigabe angefragt V{calc.approval_version} von {calc.approval_requested_by?.name}</Badge>
  else if (st === 'abgelehnt' && forCurrent) state = <Badge tone="critical">✖ Abgelehnt von {calc.approval_by?.name}</Badge>
  else state = <Badge tone="warning">Freigabe erforderlich{st && !forCurrent ? ` (Freigabe galt für V${calc.approval_version})` : ''}</Badge>

  return (
    <div className={`approval-bar ${calc.is_approved ? 'ok' : ''}`}>
      <div className="approval-info">
        <strong>Freigabe (Vier-Augen-Prinzip)</strong> {state}
        {needed && <span className="muted small">Grund: {calc.approval_reasons.join(' · ')}</span>}
        {calc.approval_comment && <span className="small">Anfrage: „{calc.approval_comment}“</span>}
        {calc.approval_decision_comment && <span className="small">Entscheidung: „{calc.approval_decision_comment}“</span>}
      </div>
      <div className="approval-actions no-print">
        {(st === 'angefragt' && forCurrent && isApprover && calc.approval_requested_by?.id !== user.id) ? <>
          <input placeholder="Kommentar (bei Ablehnung Pflicht)" value={comment} onChange={(e) => setComment(e.target.value)} />
          <button className="btn btn-ghost btn-sm btn-danger-ghost" onClick={() => act('decide', { decision: 'abgelehnt', comment })}>Ablehnen</button>
          <button className="btn btn-primary btn-sm" onClick={() => act('decide', { decision: 'freigegeben', comment })}>Freigeben V{calc.current_version}</button>
        </> : (!calc.is_approved && !(st === 'angefragt' && forCurrent) && canWrite) ? <>
          <input placeholder="Begründung für die Freigabe" value={comment} onChange={(e) => setComment(e.target.value)} />
          <button className="btn btn-primary btn-sm" onClick={() => act('request', { comment })}>Freigabe anfordern</button>
        </> : (st === 'angefragt' && forCurrent && calc.approval_requested_by?.id === user.id) ?
          <span className="muted small">Wartet auf Freigabe durch eine andere Person.</span> : null}
      </div>
      <ErrorBox error={err} />
    </div>
  )
}
