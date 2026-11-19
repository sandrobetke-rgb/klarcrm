import { useState } from 'react'
import { Modal } from './ui'
import { CLOSE_REASONS } from '../constants'

// REV01-P05: Wer etwas auf „Verloren“ setzt, muss einen Grund angeben – Vorauswahl, bei „Sonstiges“ Freitext Pflicht
export default function LostReasonDialog({ title = 'Warum verloren?', onCancel, onConfirm, reasons = CLOSE_REASONS, confirmLabel = 'Als verloren markieren' }) {
  const [reason, setReason] = useState('')
  const [note, setNote] = useState('')
  const ok = reason && (reason !== 'sonstiges' || note.trim())
  return (
    <Modal title={title} onClose={onCancel}>
      <div className="form">
        <div className="field"><label>Verlustgrund *</label>
          <div className="reason-list">{reasons.map((r) => (
            <label key={r.value} className="radio-row"><input type="radio" name="lost" checked={reason === r.value} onChange={() => setReason(r.value)} /> {r.label}</label>))}
          </div></div>
        <div className="field"><label>Begründung {reason === 'sonstiges' ? '*' : '(optional)'}</label>
          <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="z. B. Wettbewerber 12 % günstiger, Werkzeug in China" /></div>
        <div className="form-actions"><span className="spacer" />
          <button type="button" className="btn btn-ghost" onClick={onCancel}>Abbrechen</button>
          <button type="button" className="btn btn-primary" disabled={!ok}
            onClick={() => onConfirm({ reason, note: note.trim(), label: reasons.find((r) => r.value === reason)?.label.replace(' (Freitext)', '') })}>{confirmLabel}</button>
        </div>
      </div>
    </Modal>
  )
}
