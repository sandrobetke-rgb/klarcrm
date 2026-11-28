import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api, qs } from '../api'
import { useAuth } from '../auth'
import { ErrorBox, useFetch } from '../components/ui'
import { fmtInstalled, useVersion } from '../components/Version'

// REV04-02 Prüfseite je Update: nur die Punkte des Updates, in Prüfreihenfolge, eins nach dem anderen
export const CHECK_KEY = 'crm_check'
export function setChecking(item) {
  try { item ? sessionStorage.setItem(CHECK_KEY, JSON.stringify({ id: item.id, code: item.code, title: item.title })) : sessionStorage.removeItem(CHECK_KEY) } catch { /* ohne Speicher */ }
}
export function getChecking() {
  try { return JSON.parse(sessionStorage.getItem(CHECK_KEY)) } catch { return null }
}

function CheckCard({ it, n, current, onSaved }) {
  const { canWrite } = useAuth()
  const nav = useNavigate()
  const [bad, setBad] = useState(false)
  const [text, setText] = useState('')
  const [err, setErr] = useState(null)
  const [open, setOpen] = useState(current)
  useEffect(() => { setOpen(current) }, [current])
  const done = it.status === 'geprueft'
  const failed = it.status === 'nachbessern'
  async function send(ok, note) {
    setErr(null)
    try { await api.post(`/checks/${it.id}`, { ok, note }); setBad(false); setText(''); setChecking(null); onSaved() } catch (e) { setErr(e) }
  }
  const jump = () => { setChecking(it); nav(it.check_link) }
  return (
    <article id={`chk-${it.id}`} className={`check-card ${current ? 'is-current' : ''} ${done ? 'is-done' : ''} ${failed ? 'is-failed' : ''}`}>
      <header className="check-head" onClick={() => setOpen(!open)}>
        <span className="check-no">{done ? '✓' : failed ? '✗' : n}</span>
        <div className="check-title"><strong>{it.title}</strong><small className="muted">{it.code} · {it.area || '–'}</small></div>
        <span className={`check-state ${done ? 'ok' : failed ? 'bad' : ''}`}>{done ? 'passt' : failed ? 'passt nicht' : current ? 'jetzt prüfen' : 'offen'}</span>
      </header>
      {open && <div className="check-body">
        {it.solution && <p className="check-what"><span className="check-label">Was geändert wurde</span>{it.solution}</p>}
        <div className="check-grid">
          <div><span className="check-label">Was tun</span><p>{it.test_steps || '–'}</p></div>
          <div><span className="check-label">Was herauskommen muss</span><p>{it.expected || '–'}</p></div>
        </div>
        {(done || failed) && it.test_result && <p className="check-note"><span className="check-label">Ergebnis</span>{it.test_result}
          <small className="muted"> – {it.tested_by}{it.tested_at ? `, ${new Date(it.tested_at).toLocaleDateString('de-DE')}` : ''}</small></p>}
        <div className="check-actions">
          {it.check_link && <button className="btn btn-ghost" onClick={jump}>↗ Hinspringen</button>}
          <span className="spacer" />
          {canWrite && !done && !bad && <>
            <button className="btn btn-lg btn-ok-solid" onClick={() => send(true, '')}>✓ passt</button>
            <button className="btn btn-lg btn-bad-solid" onClick={() => setBad(true)}>✗ passt nicht</button></>}
          {canWrite && (done || failed) && !bad && <button className="btn btn-ghost btn-sm" onClick={() => send(null)}>Ergebnis zurücksetzen</button>}
        </div>
        {bad && <div className="check-bad">
          <textarea rows={3} autoFocus placeholder="Was passt nicht? Was haben Sie gesehen? (Pflicht)" value={text} onChange={(e) => setText(e.target.value)} />
          <div className="toolbar"><button className="btn btn-primary" disabled={!text.trim()} onClick={() => send(false, text)}>Speichern</button>
            <button className="btn btn-ghost" onClick={() => setBad(false)}>Abbrechen</button></div>
        </div>}
        <ErrorBox error={err} />
      </div>}
    </article>
  )
}

const ST = { geprueft: 'passt', nachbessern: 'passt nicht', umgesetzt: 'offen' }
const dDE = (d) => (d ? new Date(d).toLocaleDateString('de-DE') : '')

// v1.33 REV05-03: Prüfbericht als CSV (Excel) und zum Drucken / „Als PDF speichern“
function csvDownload(data) {
  const esc = (v) => `"${String(v ?? '').replace(/"/g, '""').replace(/\r?\n/g, ' ')}"`
  const head = ['Nr', 'Punkt', 'Bereich', 'Titel', 'Was tun', 'Was herauskommen muss', 'Ergebnis', 'Status', 'Prüfer', 'Datum']
  const lines = data.items.map((it, n) => [n + 1, it.code, it.area, it.title, it.test_steps, it.expected, it.test_result, ST[it.status] || it.status, it.tested_by, dDE(it.tested_at)])
  const meta = [[`Prüfbericht KlarCRM v${data.version}`], [`${data.done} von ${data.total} geprüft`, data.accepted ? `abgenommen von ${data.accepted.by} am ${fmtInstalled(data.accepted.at)}` : 'noch nicht abgenommen'], []]
  const txt = '\ufeff' + [...meta, head, ...lines].map((r) => r.map(esc).join(';')).join('\r\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([txt], { type: 'text/csv;charset=utf-8' }))
  a.download = `KlarCRM_Pruefbericht_v${data.version}.csv`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

function Report({ data }) {
  const v = useVersion()
  const inst = v?.releases?.find((r) => r.version === data.version)?.installed_at
  return (
    <div className="check-report">
      <h1>Prüfbericht KlarCRM v{data.version}</h1>
      <p>Eingespielt am {fmtInstalled(inst) || '–'} · {data.done} von {data.total} Punkten „passt“{data.failed ? ` · ${data.failed} „passt nicht“` : ''} ·
        {' '}{data.accepted ? <>abgenommen von <b>{data.accepted.by}</b> am <b>{fmtInstalled(data.accepted.at)}</b></> : 'noch nicht abgenommen'} · Stand {new Date().toLocaleString('de-DE')}</p>
      <table>
        <thead><tr><th>Nr</th><th>Punkt</th><th>Titel</th><th>Was herauskommen muss</th><th>Ergebnis</th><th>Status</th><th>Prüfer / Datum</th></tr></thead>
        <tbody>{data.items.map((it, n) => (
          <tr key={it.id}><td>{n + 1}</td><td>{it.code}</td><td>{it.title}</td><td>{it.expected}</td><td>{it.test_result}</td>
            <td><b>{ST[it.status] || it.status}</b></td><td>{it.tested_by}<br />{dDE(it.tested_at)}</td></tr>))}</tbody>
      </table>
      <p className="report-sign">Nachweis der Abnahme eines Software-Updates (IATF 16949 / ISO 14001) · KlarCRM · © SB/Thinkworks</p>
    </div>
  )
}

export default function Pruefen() {
  const { isAdmin } = useAuth()
  const [sp, setSp] = useSearchParams()
  const { data, error, reload } = useFetch('/checks' + qs({ version: sp.get('version') }))
  const [err, setErr] = useState(null)
  useEffect(() => {   // zurück vom Hinspringen: zur Karte scrollen
    const c = getChecking()
    if (data && c) document.getElementById(`chk-${c.id}`)?.scrollIntoView({ block: 'center' })
  }, [data])
  if (error) return <ErrorBox error={error} />
  if (!data) return <div className="loading">Lade…</div>
  const cur = data.items.find((i) => !['geprueft', 'nachbessern'].includes(i.status))
  const pct = data.total ? Math.round(100 * data.done / data.total) : 0
  const allOk = data.total > 0 && data.done === data.total
  async function accept() {
    setErr(null)
    try { await api.post('/checks/accept', { version: data.version }); reload() } catch (e) { setErr(e) }
  }
  return (
    <div className="page page-narrow">
      <Report data={data} />
      <div className="pruefen-screen">
      <header className="page-head">
        <div><h1>Prüfen · Update v{data.version}</h1>
          <p className="muted">Punkte von oben nach unten abarbeiten: „Was tun“ lesen, „Hinspringen“, ansehen, dann „✓ passt“ oder „✗ passt nicht“.</p></div>
        <div className="toolbar no-print">
          <button className="btn btn-ghost" onClick={() => window.print()} title="Im Druckdialog „Als PDF speichern“ wählen">🖨 Prüfbericht drucken / PDF</button>
          <button className="btn btn-ghost" onClick={() => csvDownload(data)}>⬇ Prüfbericht CSV</button>
        </div>
        {data.versions.length > 1 && <div className="toolbar"><label className="inline-label">Update
          <select value={data.version} onChange={(e) => setSp({ version: e.target.value })}>
            {data.versions.map((v) => <option key={v} value={v}>v{v}{v === data.current ? ' (aktuell)' : ''}</option>)}</select></label></div>}
      </header>

      <section className="check-progress card">
        <div className="check-count"><strong>{data.done} von {data.total}</strong> geprüft
          {data.failed > 0 && <span className="text-critical"> · {data.failed} passt nicht</span>}</div>
        <div className="check-bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${pct}%` }} /></div>
      </section>

      {data.accepted && <div className="ok-box">✓ Update v{data.version} abgenommen von {data.accepted.by} am {fmtInstalled(data.accepted.at)}.</div>}
      {!data.total && <div className="warn-box">Für dieses Update sind keine Prüfpunkte hinterlegt.</div>}

      {data.items.map((it, i) => <CheckCard key={it.id} it={it} n={i + 1} current={cur?.id === it.id} onSaved={reload} />)}

      {data.total > 0 && !data.accepted && <section className="card check-final">
        {allOk
          ? (isAdmin ? <><p>Alle Punkte passen. Damit ist das Update abgenommen und der nächste Themenblock kann starten.</p>
              <button className="btn btn-lg btn-ok-solid" onClick={accept}>v{data.version} abgenommen</button></>
            : <p>Alle Punkte passen – die Abnahme erklärt ein Administrator.</p>)
          : <p className="muted">Abnahme „v{data.version} abgenommen“ ist möglich, sobald alle Punkte mit „✓ passt“ geprüft sind
            {data.failed > 0 && ' – Punkte mit „passt nicht“ werden nachgebessert und kommen mit dem nächsten Update wieder auf diese Seite'}.</p>}
        <ErrorBox error={err} />
      </section>}

      {data.older_open > 0 && <p className="muted small">Hinweis: {data.older_open} Punkt(e) aus früheren Updates sind noch nicht geprüft –
        siehe <a href="/aenderungen?status=umgesetzt">Änderungswünsche</a>.</p>}
      </div>
    </div>
  )
}
