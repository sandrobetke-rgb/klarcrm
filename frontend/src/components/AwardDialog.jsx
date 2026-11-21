import { useEffect, useState } from 'react'
import { api } from '../api'
import { CLOSE_REASONS, eur } from '../constants'
import { ErrorBox, Modal } from './ui'

// MB-30 … MB-35: „Auftrag erhalten“ – je Artikel des Angebots beauftragt / verloren (Grund) / andere Variante / noch offen.
// Beispiel: 10 Artikel angeboten, 2 werden Auftrag → die 2 anhaken, für den Rest einmal den Grund wählen.
const OUT = [
  ['gewonnen', 'beauftragt'],
  ['verloren', 'verloren'],
  ['andere_variante', 'andere Variante beauftragt'],
  ['offen', 'noch offen'],
]

export default function AwardDialog({ quote, onCancel, onDone, beforeSave }) {
  const [rows, setRows] = useState(null)
  const [rest, setRest] = useState({ outcome: 'verloren', reason: '', note: '' })
  const [note, setNote] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.get(`/quotes/${quote.id}/award`).then((r) => setRows(r.map((x) => ({ ...x, custom: x.outcome !== 'offen' && x.outcome !== 'gewonnen' }))))
      .catch(setErr)
  }, [quote.id])

  if (!rows) return <Modal title="Auftrag erhalten" onClose={onCancel}>{err ? <ErrorBox error={err} /> : <div className="loading">Lade Artikel…</div>}</Modal>

  // Artikel ohne eigene Auswahl übernehmen die Vorgabe „für alle nicht beauftragten“
  const eff = (r) => (r.outcome === 'gewonnen' || r.custom ? r : { ...r, outcome: rest.outcome, reason: rest.reason, note: rest.note })
  const lines = rows.map(eff)
  const won = lines.filter((l) => l.outcome === 'gewonnen')
  const missingReason = lines.find((l) => l.outcome === 'verloren' && (!l.reason || (l.reason === 'sonstiges' && !(l.note || '').trim())))
  const ok = rows.length === 0 || (won.length > 0 && !missingReason)
  const upd = (i, patch) => setRows(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)))

  async function confirm() {
    setBusy(true); setErr(null)
    try {
      if (beforeSave) await beforeSave()
      const res = await api.post(`/quotes/${quote.id}/award`, {
        note: note || null,
        lines: lines.map((l) => ({ calculation_id: l.calculation_id, outcome: l.outcome, reason: l.reason || null, note: l.note || null })),
      })
      onDone(res)
    } catch (e) { setErr(e); setBusy(false) }
  }

  return (
    <Modal title={`Auftrag erhalten – ${quote.number}`} onClose={onCancel} wide>
      <ErrorBox error={err} />
      {rows.length === 0 ? <p>Dieses Angebot enthält keine Artikel aus Kalkulationen – es wird als „angenommen“ gespeichert.</p> : <>
        <p className="small muted">Beauftragte Artikel anhaken. Für alle anderen gilt die Vorgabe unten; einzelne Artikel lassen sich abweichend setzen
          (z. B. „andere Variante beauftragt“ – zählt <strong>nicht</strong> als Verlust, oder „noch offen“ – bleibt in der Pipeline).</p>
        <table className="table table-compact">
          <thead><tr><th>Auftrag</th><th>Artikel</th><th className="num">Neuumsatz</th><th className="num">Werkzeug/Einmal</th><th>Ergebnis</th></tr></thead>
          <tbody>{rows.map((r, i) => {
            const e = eff(r)
            return (
              <tr key={r.calculation_id} className={e.outcome === 'gewonnen' ? 'row-won' : ''}>
                <td><input type="checkbox" checked={r.outcome === 'gewonnen'} aria-label={`${r.number} beauftragt`}
                  onChange={(ev) => upd(i, ev.target.checked ? { outcome: 'gewonnen', custom: false } : { outcome: 'offen', custom: false })} /></td>
                <td><strong>{r.number}</strong> {r.name}</td>
                <td className="num">{eur(r.peak_revenue)}</td><td className="num">{eur(r.one_time_revenue)}</td>
                <td>{r.outcome === 'gewonnen' ? <strong className="txt-good">beauftragt</strong> : <div className="award-cell">
                  <select value={r.custom ? e.outcome : ''} onChange={(ev) => upd(i, ev.target.value ? { custom: true, outcome: ev.target.value, reason: r.reason || rest.reason, note: r.note || '' } : { custom: false, outcome: 'offen' })}>
                    <option value="">wie Vorgabe ({OUT.find((o) => o[0] === rest.outcome)[1]})</option>
                    {OUT.filter((o) => o[0] !== 'gewonnen').map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                  {r.custom && e.outcome === 'verloren' && <select value={r.reason || ''} onChange={(ev) => upd(i, { reason: ev.target.value })}>
                    <option value="">Grund wählen…</option>{CLOSE_REASONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}</select>}
                  {r.custom && (e.outcome === 'verloren' || e.outcome === 'andere_variante') &&
                    <input value={r.note || ''} placeholder={e.outcome === 'andere_variante' ? 'welche Variante?' : 'Begründung'} onChange={(ev) => upd(i, { note: ev.target.value })} />}
                </div>}</td>
              </tr>)
          })}</tbody>
        </table>
        <div className="card award-rest">
          <strong>Vorgabe für alle nicht beauftragten Artikel</strong>
          <div className="form-grid form-grid-3">
            <div className="field"><label>Ergebnis</label><select value={rest.outcome} onChange={(e) => setRest({ ...rest, outcome: e.target.value })}>
              {OUT.filter((o) => o[0] !== 'gewonnen').map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></div>
            {rest.outcome === 'verloren' && <div className="field"><label>Verlustgrund *</label><select value={rest.reason} onChange={(e) => setRest({ ...rest, reason: e.target.value })}>
              <option value="">Grund wählen…</option>{CLOSE_REASONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}</select></div>}
            {rest.outcome !== 'offen' && <div className="field"><label>Begründung {rest.outcome === 'verloren' && rest.reason === 'sonstiges' ? '*' : ''}</label>
              <input value={rest.note} onChange={(e) => setRest({ ...rest, note: e.target.value })} placeholder="z. B. an Wettbewerber vergeben" /></div>}
          </div>
        </div>
        <div className="field"><label>Notiz zum Auftrag (optional)</label><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="z. B. Bestellung Nr. 4711 vom 20.11." /></div>
        <p className="award-sum"><strong>{won.length} von {rows.length}</strong> Artikeln beauftragt · Neuumsatz {eur(won.reduce((s, l) => s + l.peak_revenue, 0))}
          {' · '}Angebot wird {won.length === rows.length ? <strong>angenommen</strong> : <strong>teilweise beauftragt</strong>}
          {won.length === 0 && <span className="txt-crit"> – mindestens ein Artikel muss beauftragt sein (sonst Angebot „abgelehnt“)</span>}
          {missingReason && won.length > 0 && <span className="txt-crit"> – Verlustgrund fehlt ({missingReason.number})</span>}</p>
      </>}
      <div className="form-actions"><span className="spacer" />
        <button className="btn btn-ghost" onClick={onCancel}>Abbrechen</button>
        <button className="btn btn-primary" disabled={!ok || busy} onClick={confirm}>Auftrag speichern</button></div>
    </Modal>
  )
}
