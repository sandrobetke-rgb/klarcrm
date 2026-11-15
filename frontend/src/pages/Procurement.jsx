import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import Attachments from '../components/Attachments'
import { LetterFooter, LetterHead } from '../components/Letterhead'
import { BarList } from '../components/charts'
import { Badge, confirmDelete, EntityForm, ErrorBox, Modal } from '../components/ui'
import { eur, num } from '../constants'

export const PROC_KINDS = [
  { value: 'werkzeug', label: 'Spritzgießwerkzeug' },
  { value: 'montagelinie', label: 'Montagelinie' },
  { value: 'vorrichtung', label: 'Vorrichtung' },
  { value: 'pruefmittel', label: 'Prüfmittel' },
  { value: 'sonstiges', label: 'Sonstiges' },
]
const kindLabel = (k) => PROC_KINDS.find((x) => x.value === k)?.label || k
const STATUS = {
  offen: ['offen', 'neutral'], angefragt: ['angefragt', 'info'], entschieden: ['entschieden', 'good'],
  bestellt: ['bestellt', 'good'], abgebrochen: ['abgebrochen', 'neutral'],
}
const OFFER_STATUS = {
  angefragt: ['angefragt', 'neutral'], angebot: ['Angebot liegt vor', 'info'], abgesagt: ['abgesagt', 'neutral'],
  gewaehlt: ['gewählt', 'good'], abgelehnt: ['nicht gewählt', 'neutral'],
}
const fmtD = (d) => (d ? new Date(d).toLocaleDateString('de-DE') : '–')

// Technische Eckdaten der Anfrage je Art
const SPEC_TOOL = [
  ['part_name', 'Artikel'], ['customer_part_no', 'Kunden-Art.-Nr.'], ['own_part_no', 'Eigene Art.-Nr.'],
  ['material', 'Werkstoff'], ['part_weight_g', 'Teilgewicht g', 'number'], ['cavities', 'Fachzahl', 'number'],
  ['tool_type', 'Werkzeugart'], ['hot_runner', 'Heißkanal / Kaltkanal'], ['hot_runner_nozzles', 'Anzahl Düsen', 'number'],
  ['hot_runner_make', 'Heißkanal-Fabrikat (Vorgabe)'], ['gate', 'Anspritzpunkt / Anschnitt'], ['cycle_time_s', 'Ziel-Zykluszeit s', 'number'],
  ['machine', 'Maschine'], ['clamping_force_t', 'Schließkraft t', 'number'], ['annual_volume', 'Jahresmenge Stk', 'number'],
  ['project_years', 'Laufzeit Jahre', 'number'], ['tool_life_shots', 'Werkzeugstandzeit Schuss', 'number'], ['steel', 'Werkzeugstahl'],
  ['mold_standard', 'Normalien'], ['slides', 'Schieber / Kernzüge'], ['cooling', 'Temperierung'], ['ejection', 'Entformung / Auswerfer'],
  ['surface', 'Oberfläche / Narbung'], ['sampling', 'Bemusterung'], ['documents', 'Unterlagen'], ['delivery', 'Lieferbedingung'], ['sop', 'Serienstart (SOP)'],
]
const SPEC_OTHER = [
  ['part_name', 'Artikel'], ['customer_part_no', 'Kunden-Art.-Nr.'], ['annual_volume', 'Jahresmenge Stk', 'number'],
  ['project_years', 'Laufzeit Jahre', 'number'], ['sop', 'Serienstart (SOP)'], ['scope', 'Leistungsumfang', 'textarea'],
  ['operations', 'Arbeitsgänge / Stationen'], ['cycle_time_s', 'Taktzeit s', 'number'], ['availability', 'Verfügbarkeit / OEE'],
  ['acceptance', 'Abnahme'], ['documents', 'Unterlagen'], ['delivery', 'Lieferbedingung'],
]
const specFields = (kind) => (kind === 'werkzeug' ? SPEC_TOOL : SPEC_OTHER)
const specText = (r) => specFields(r.kind).filter(([k]) => r.spec?.[k] !== undefined && r.spec?.[k] !== null && r.spec?.[k] !== '')
  .map(([k, l, t]) => `${l}: ${t === 'number' ? num(r.spec[k]) : r.spec[k]}`)

const offerFields = [
  { name: 'supplier_name', label: 'Lieferant', required: true },
  { name: 'contact_email', label: 'E-Mail Ansprechpartner', type: 'email' },
  { name: 'status', label: 'Status', type: 'select', required: true, options: Object.entries(OFFER_STATUS).map(([value, [label]]) => ({ value, label })) },
  { name: 'requested_at', label: 'Angefragt am', type: 'date' },
  { name: 'offer_no', label: 'Angebots-Nr.' },
  { name: 'offer_date', label: 'Angebotsdatum', type: 'date' },
  { name: 'price', label: 'Preis netto €', type: 'number', step: 'any' },
  { name: 'lead_time_weeks', label: 'Lieferzeit bis T0 / Abnahme (Wochen)', type: 'number', step: 'any' },
  { name: 'cavities', label: 'Fachzahl', type: 'number', step: '1' },
  { name: 'hot_runner', label: 'Heißkanal (Fabrikat, Düsen)' },
  { name: 'steel', label: 'Werkzeugstahl' },
  { name: 'tool_life_shots', label: 'Standzeit / Garantie Schuss', type: 'number', step: 'any' },
  { name: 'warranty', label: 'Gewährleistung' },
  { name: 'payment_terms', label: 'Zahlungsbedingungen' },
  { name: 'location', label: 'Fertigungsort / Land' },
  { name: 'rating', label: 'Technische Bewertung (1 – 5)', type: 'number', step: '1', min: 1, max: 5 },
  { name: 'note', label: 'Bemerkung', type: 'textarea', span: true },
]

export default function ProcurementList() {
  const [kind, setKind] = useState('')
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [creating, setCreating] = useState(false)
  const { canWrite } = useAuth()
  useEffect(() => {
    const p = new URLSearchParams()
    if (kind) p.set('kind', kind)
    if (status) p.set('status', status)
    if (q) p.set('q', q)
    api.get(`/procurement?${p}`).then(setData).catch(setError)
  }, [kind, status, q])
  return (
    <div className="page">
      <div className="page-head">
        <div><h1>Beschaffung</h1><p className="muted">Werkzeuge, Montagelinien, Vorrichtungen und Prüfmittel: Lieferanten anfragen, Angebote vergleichen, entscheiden</p></div>
        {canWrite && <button className="btn btn-primary" onClick={() => setCreating(true)}>+ Beschaffung anlegen</button>}
      </div>
      <div className="filters">
        <input placeholder="Suchen …" value={q} onChange={(e) => setQ(e.target.value)} style={{ maxWidth: 260 }} />
        <select value={kind} onChange={(e) => setKind(e.target.value)}><option value="">Alle Arten</option>{PROC_KINDS.map((k) => <option key={k.value} value={k.value}>{k.label}</option>)}</select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Alle Status</option>{Object.entries(STATUS).map(([k, [l]]) => <option key={k} value={k}>{l}</option>)}</select>
      </div>
      <ErrorBox error={error} />
      <ProcTable items={data?.items} />
      {creating && <NewProcurement onClose={() => setCreating(false)} />}
    </div>
  )
}

export function ProcTable({ items, showCalc = true }) {
  const nav = useNavigate()
  if (!items) return null
  if (!items.length) return <div className="card"><div className="empty small">Noch keine Beschaffungsvorgänge</div></div>
  return (
    <div className="card card-flush">
      <table className="table">
        <thead><tr><th>Nr.</th><th>Vorgang</th>{showCalc && <th>Kalkulation / Artikel</th>}<th>Status</th><th className="num">Angebote</th>
          <th className="num">günstigstes</th><th>Entscheidung</th><th className="num">Preis gewählt</th></tr></thead>
        <tbody>{items.map((r) => (
          <tr key={r.id} className="row-click" onClick={() => nav(`/beschaffung/${r.id}`)}>
            <td>{r.number}</td>
            <td><strong>{r.title}</strong><br /><small className="muted">{kindLabel(r.kind)}</small></td>
            {showCalc && <td>{r.calculation ? <>{r.calculation.number}<br /><small className="muted">{r.calculation.account || ''}</small></> : '–'}</td>}
            <td><Badge tone={STATUS[r.status]?.[1]}>{STATUS[r.status]?.[0] || r.status}</Badge></td>
            <td className="num">{r.offers_priced} / {r.offers_count}</td>
            <td className="num">{r.best_price != null ? eur(r.best_price) : '–'}</td>
            <td>{r.chosen ? r.chosen.supplier_name : '–'}</td>
            <td className="num">{r.chosen?.price != null ? eur(r.chosen.price) : '–'}</td>
          </tr>))}</tbody>
      </table>
    </div>
  )
}

export function NewProcurement({ onClose, calculationId }) {
  const nav = useNavigate()
  const [error, setError] = useState(null)
  return (
    <Modal title="Beschaffung anlegen" onClose={onClose}>
      <EntityForm
        fields={[
          { name: 'kind', label: 'Art', type: 'select', required: true, options: PROC_KINDS },
          ...(calculationId ? [] : [{ name: 'calculation_id', label: 'Kalkulations-ID (optional)', type: 'number', step: '1', hint: 'Eckdaten werden aus der Kalkulation vorbelegt' }]),
          { name: 'title', label: 'Bezeichnung', hint: 'leer = automatisch, z. B. „Spritzgießwerkzeug Gehäuse …“' },
          { name: 'reply_by', label: 'Angebotsabgabe bis', type: 'date' },
          { name: 'needed_by', label: 'Benötigt bis (z. B. T0 / Abnahme)', type: 'date' },
        ]}
        initial={{ kind: 'werkzeug' }}
        submitLabel="Anlegen"
        onCancel={onClose}
        onSubmit={async (v) => {
          try {
            const r = await api.post('/procurement', { ...v, calculation_id: calculationId || v.calculation_id || null })
            nav(`/beschaffung/${r.id}`)
          } catch (e) { setError(e) }
        }} />
      <ErrorBox error={error} />
    </Modal>
  )
}

export function ProcurementTab({ calc }) {
  const [data, setData] = useState(null)
  const [creating, setCreating] = useState(false)
  const { canWrite } = useAuth()
  useEffect(() => { api.get(`/procurement?calculation_id=${calc.id}`).then(setData) }, [calc.id])
  return (
    <div className="stack" style={{ maxWidth: 1200 }}>
      <div className="section-head">
        <p className="muted" style={{ margin: 0 }}>Werkzeug, Montagelinie, Vorrichtungen und Prüfmittel zu diesem Artikel anfragen und vergeben. Das gewählte Angebot lässt sich als Einmalkosten in die Kalkulation übernehmen.</p>
        {canWrite && <button className="btn btn-primary" onClick={() => setCreating(true)}>+ Werkzeug / Anlage anfragen</button>}
      </div>
      <ProcTable items={data?.items} showCalc={false} />
      {creating && <NewProcurement calculationId={calc.id} onClose={() => setCreating(false)} />}
    </div>
  )
}

export function ProcurementDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { canWrite } = useAuth()
  const [r, setR] = useState(null)
  const [app, setApp] = useState({})
  const [error, setError] = useState(null)
  const [msg, setMsg] = useState(null)
  const [edit, setEdit] = useState(null)          // Angebot bearbeiten/neu
  const [suppliers, setSuppliers] = useState([])
  const [pick, setPick] = useState('')
  const [specEdit, setSpecEdit] = useState(false)
  const [printFor, setPrintFor] = useState(null)  // Angebot, für das die Anfrage gedruckt wird
  const [decideNote, setDecideNote] = useState('')
  useEffect(() => { api.get(`/procurement/${id}`).then((x) => { setR(x); setDecideNote(x.decision_note || '') }).catch(setError) }, [id])
  useEffect(() => {
    api.get('/app-settings').then(setApp).catch(() => {})
    api.get('/accounts?type=lieferant&limit=500&sort=name').then((x) => setSuppliers(x.items)).catch(() => {})
  }, [])
  useEffect(() => {
    if (!printFor) return undefined
    const t = setTimeout(() => { window.print(); setPrintFor(null) }, 150)
    return () => clearTimeout(t)
  }, [printFor])

  const priced = useMemo(() => (r?.offers || []).filter((o) => o.price && o.status !== 'abgesagt'), [r])
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!r) return <div className="page"><div className="muted">Lädt …</div></div>
  const run = async (fn, ok) => { setError(null); try { const x = await fn(); setR(x); if (ok) setMsg(ok) } catch (e) { setError(e) } }
  const best = r.best_price
  const fields = specFields(r.kind)

  const mailto = (o) => {
    const subject = `Anfrage ${kindLabel(r.kind)} ${r.number} – ${r.title}`
    const body = [`Sehr geehrte Damen und Herren,`, '',
      `wir bitten um Ihr Angebot für folgendes ${kindLabel(r.kind)}:`, '', ...specText(r), '',
      r.reply_by ? `Bitte senden Sie uns Ihr Angebot bis zum ${fmtD(r.reply_by)}.` : 'Bitte senden Sie uns Ihr Angebot.',
      r.needed_by ? `Benötigt bis: ${fmtD(r.needed_by)}.` : '', 'Zeichnung und 3D-Daten erhalten Sie in der Anlage.', '',
      'Mit freundlichen Grüßen', app.company_name || ''].filter((x) => x !== null).join('\n')
    return `mailto:${o.contact_email || ''}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  }
  const open = suppliers.filter((s) => !r.offers.some((o) => o.account_id === s.id))
  const addSuppliers = async (ids) => {
    for (const sid of ids) {
      const s = suppliers.find((x) => x.id === Number(sid))
      // eslint-disable-next-line no-await-in-loop
      await run(() => api.post(`/procurement/${r.id}/offers`, { account_id: s.id, supplier_name: s.name }))
    }
    setPick('')
  }

  return (
    <>
      <div className="page no-print">
        <div className="page-head">
          <div>
            <p className="muted small" style={{ margin: 0 }}><Link to="/beschaffung">Beschaffung</Link> / {r.number}</p>
            <h1>{r.title}</h1>
            <p className="muted">{kindLabel(r.kind)}{r.calculation && <> · Kalkulation <Link to={`/kalkulationen/${r.calculation.id}`}>{r.calculation.number} {r.calculation.article_name}</Link>{r.calculation.account ? ` · ${r.calculation.account}` : ''}</>}</p>
          </div>
          <div className="toolbar">
            <Badge tone={STATUS[r.status]?.[1]}>{STATUS[r.status]?.[0]}</Badge>
            {canWrite && <select value={r.status} onChange={(e) => run(() => api.put(`/procurement/${r.id}`, { status: e.target.value }))} title="Status ändern">
              {Object.entries(STATUS).map(([k, [l]]) => <option key={k} value={k}>{l}</option>)}</select>}
            {canWrite && <button className="btn btn-ghost" onClick={() => confirmDelete(`Beschaffung ${r.number}`, async () => { await api.del(`/procurement/${r.id}`); nav('/beschaffung') })}>Löschen</button>}
          </div>
        </div>
        <ErrorBox error={error} />
        {msg && <div className="ok-box">{msg}</div>}

        <div className="kpi-grid">
          <div className="kpi"><span className="kpi-label">Angefragt</span><span className="kpi-value">{r.offers_count}</span><span className="kpi-sub">{r.offers_priced} Angebote mit Preis</span></div>
          <div className="kpi"><span className="kpi-label">Günstigstes Angebot</span><span className="kpi-value">{best != null ? eur(best) : '–'}</span><span className="kpi-sub">{r.max_price != null && best != null ? `Spanne ${eur(r.max_price - best)}` : ''}</span></div>
          <div className="kpi"><span className="kpi-label">Gewählt</span><span className="kpi-value">{r.chosen ? eur(r.chosen.price) : '–'}</span><span className="kpi-sub">{r.chosen?.supplier_name || 'noch offen'}</span></div>
          <div className="kpi"><span className="kpi-label">Angebotsabgabe bis</span><span className="kpi-value">{fmtD(r.reply_by)}</span><span className="kpi-sub">benötigt bis {fmtD(r.needed_by)}</span></div>
        </div>

        <div className="card">
          <div className="section-head"><h3>Angebotsvergleich</h3>
            {canWrite && <div className="toolbar">
              <select className="supplier-pick" value={pick} onChange={(e) => setPick(e.target.value)} title="Lieferanten aus „Firmen“ mit Typ Lieferant">
                <option value="">Lieferant wählen …</option>
                {open.map((s) => <option key={s.id} value={s.id}>{s.name}{s.city ? ` · ${s.city}` : ''}</option>)}
              </select>
              <button className="btn btn-ghost btn-sm" disabled={!pick} onClick={() => addSuppliers([pick])}>Anfragen</button>
              {open.length > 0 && <button className="btn btn-ghost btn-sm" onClick={() => addSuppliers(open.map((s) => s.id))} title="Alle Lieferanten aus den Firmen hinzufügen">alle ({open.length})</button>}
              <button className="btn btn-ghost btn-sm" onClick={() => setEdit({ status: 'angefragt', requested_at: new Date().toISOString().slice(0, 10) })}>+ anderer Lieferant</button>
            </div>}
          </div>
          {priced.length > 0 && <BarList data={[...priced].sort((a, b) => a.price - b.price).map((o) => ({
            label: o.supplier_name, value: o.price, tone: o.id === r.decided_offer_id ? 'good' : undefined,
            note: o.price === best ? ' · günstigstes' : best ? ` · +${num((o.price / best - 1) * 100, 1)} %` : '',
          }))} />}
          {r.offers.length ? (
            <div className="table-wrap">
              <table className="table offer-table">
                <thead><tr><th>Lieferant</th><th>Status</th><th>Angebot</th><th className="num">Preis netto</th><th className="num">Δ zum günstigsten</th>
                  <th className="num">Lieferzeit</th><th className="num">Fachzahl</th><th>Heißkanal</th><th>Stahl</th><th className="num">Standzeit</th><th>Ort</th><th>Bewertung</th></tr></thead>
                <tbody>{r.offers.map((o) => (
                  <tr key={o.id} className={o.id === r.decided_offer_id ? 'row-chosen' : ''}>
                    <td><strong>{o.supplier_name}</strong>{o.contact_email && <><br /><small className="muted">{o.contact_email}</small></>}
                    <div className="offer-actions">
                      <button className="btn btn-ghost btn-sm" onClick={() => setPrintFor(o)} title="Werkzeuganfrage für diesen Lieferanten drucken / als PDF speichern">Anfrage</button>
                      <a className="btn btn-ghost btn-sm" href={mailto(o)} title="E-Mail-Entwurf mit den Eckdaten öffnen">E-Mail</a>
                      {canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setEdit(o)}>Erfassen</button>}
                      {canWrite && o.price && o.id !== r.decided_offer_id && <button className="btn btn-primary btn-sm" onClick={() => run(() => api.post(`/procurement/${r.id}/decide`, { offer_id: o.id, note: decideNote }), `${o.supplier_name} ausgewählt.`)}>Wählen</button>}
                    </div></td>
                    <td><Badge tone={OFFER_STATUS[o.status]?.[1]}>{OFFER_STATUS[o.status]?.[0] || o.status}</Badge><br /><small className="muted">angefragt {fmtD(o.requested_at)}</small></td>
                    <td>{o.offer_no || '–'}<br /><small className="muted">{o.offer_date ? fmtD(o.offer_date) : ''}</small></td>
                    <td className={`num ${o.price && o.price === best ? 'best-price' : ''}`}><b>{o.price != null ? eur(o.price) : '–'}</b></td>
                    <td className="num">{o.price && best ? (o.price === best ? '–' : `+${num((o.price / best - 1) * 100, 1)} %`) : ''}</td>
                    <td className="num">{o.lead_time_weeks ? `${num(o.lead_time_weeks)} Wo.` : '–'}</td>
                    <td className="num">{o.cavities ?? '–'}</td>
                    <td>{o.hot_runner || '–'}</td><td>{o.steel || '–'}</td>
                    <td className="num">{o.tool_life_shots ? num(o.tool_life_shots) : '–'}</td>
                    <td>{o.location || '–'}</td>
                    <td className="stars">{o.rating ? '★'.repeat(o.rating) + '☆'.repeat(5 - o.rating) : '–'}</td>

                  </tr>))}</tbody>
              </table>
            </div>
          ) : <div className="empty small">Noch keine Lieferanten angefragt – oben Lieferanten hinzufügen.</div>}
        </div>

        <div className="grid-2">
          <div className="card">
            <h3>Entscheidung</h3>
            {r.chosen ? <p><b>{r.chosen.supplier_name}</b> · {eur(r.chosen.price)}{r.chosen.offer_no ? ` · Angebot ${r.chosen.offer_no}` : ''}<br />
              <small className="muted">entschieden am {fmtD(r.decided_at)}{best && r.chosen.price > best ? ` · ${eur(r.chosen.price - best)} über dem günstigsten Angebot` : ''}</small></p>
              : <p className="muted">Noch nicht entschieden – im Vergleich „Wählen“ klicken.</p>}
            <div className="field"><label>Begründung der Vergabe</label>
              <textarea rows={3} value={decideNote} disabled={!canWrite} onChange={(e) => setDecideNote(e.target.value)}
                placeholder="z. B. Preis, Lieferzeit, Erfahrung, Standzeit, Nähe für Änderungen" /></div>
            {canWrite && <div className="toolbar">
              {r.chosen && <button className="btn btn-ghost btn-sm" onClick={() => run(() => api.post(`/procurement/${r.id}/decide`, { offer_id: r.decided_offer_id, note: decideNote }), 'Begründung gespeichert.')}>Begründung speichern</button>}
              {r.chosen && <button className="btn btn-ghost btn-sm" onClick={() => run(() => api.post(`/procurement/${r.id}/decide`, { offer_id: null }), 'Entscheidung zurückgenommen.')}>Entscheidung zurücknehmen</button>}
              {r.chosen && r.calculation && <button className="btn btn-primary btn-sm" onClick={() => run(async () => {
                const x = await api.post(`/procurement/${r.id}/apply`, {}); setMsg(`Neue Kalkulationsversion V${x.version_no}: ${x.change_note}`); return x
              })}>In Kalkulation übernehmen</button>}
            </div>}
            {r.applied_version && <small className="hint">In Kalkulationsversion V{r.applied_version} übernommen (Einmalkosten).</small>}
          </div>
          <div className="card">
            <div className="section-head"><h3>Eckdaten der Anfrage</h3>
              {canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setSpecEdit(true)}>Bearbeiten</button>}</div>
            <dl className="spec-list">{fields.map(([k, l, t]) => (r.spec?.[k] !== undefined && r.spec?.[k] !== '' && r.spec?.[k] !== null) && (
              <div key={k}><dt>{l}</dt><dd>{t === 'number' ? num(r.spec[k]) : r.spec[k]}</dd></div>))}</dl>
            {r.note && <p className="pre small">{r.note}</p>}
          </div>
        </div>
        <Attachments entity="procurement" entityId={r.id} title="Dokumente (Zeichnung, 3D-Daten, Angebote der Lieferanten, Bestellung …)" />
      </div>

      {printFor && <PrintRfq r={r} o={printFor} app={app} />}

      {edit && <Modal title={edit.id ? `Angebot ${edit.supplier_name}` : 'Lieferant / Angebot erfassen'} onClose={() => setEdit(null)} wide>
        <EntityForm fields={offerFields} initial={edit} onCancel={() => setEdit(null)}
          onDelete={edit.id ? () => confirmDelete(`Angebot ${edit.supplier_name}`, async () => { setR(await api.del(`/procurement/offers/${edit.id}`)); setEdit(null) }) : undefined}
          onSubmit={async (v) => {
            setR(edit.id ? await api.put(`/procurement/offers/${edit.id}`, v) : await api.post(`/procurement/${r.id}/offers`, v))
            setEdit(null)
          }} />
      </Modal>}
      {specEdit && <Modal title="Eckdaten der Anfrage" onClose={() => setSpecEdit(false)} wide>
        <EntityForm
          fields={[{ name: 'title', label: 'Bezeichnung', required: true, span: true },
            { name: 'reply_by', label: 'Angebotsabgabe bis', type: 'date' }, { name: 'needed_by', label: 'Benötigt bis', type: 'date' },
            ...fields.map(([k, l, t]) => ({ name: `spec.${k}`, label: l, type: t === 'textarea' ? 'textarea' : (t || 'text'), step: 'any', span: t === 'textarea' })),
            { name: 'note', label: 'Weitere Anforderungen / Hinweise', type: 'textarea', span: true }]}
          initial={{ title: r.title, reply_by: r.reply_by, needed_by: r.needed_by, note: r.note,
            ...Object.fromEntries(fields.map(([k]) => [`spec.${k}`, r.spec?.[k] ?? ''])) }}
          onCancel={() => setSpecEdit(false)}
          onSubmit={async (v) => {
            const spec = { ...(r.spec || {}) }
            Object.entries(v).forEach(([k, val]) => { if (k.startsWith('spec.')) spec[k.slice(5)] = val })
            setR(await api.put(`/procurement/${r.id}`, { title: v.title, reply_by: v.reply_by, needed_by: v.needed_by, note: v.note, spec }))
            setSpecEdit(false)
          }} />
      </Modal>}
    </>
  )
}

function PrintRfq({ r, o, app }) {
  const a = app || {}
  return (
    <div className="print-only print-doc" style={{ '--accent': a.accent_color || '#1f4b99' }}>
      <LetterHead a={a} />
      <div className="pq-addr-meta">
        <div className="pq-address"><strong>{o.supplier_name}</strong>{o.location && <><br />{o.location}</>}{o.contact_email && <><br />{o.contact_email}</>}</div>
        <dl className="pq-meta">
          <dt>Anfrage-Nr.</dt><dd>{r.number}</dd>
          <dt>Datum</dt><dd>{new Date().toLocaleDateString('de-DE')}</dd>
          <dt>Angebot bis</dt><dd>{fmtD(r.reply_by)}</dd>
          {a.phone && <><dt>Tel.</dt><dd>{a.phone}</dd></>}
          {a.email && <><dt>E-Mail</dt><dd>{a.email}</dd></>}
        </dl>
      </div>
      <h2 className="pq-title">Anfrage {kindLabel(r.kind)}: {r.title}</h2>
      <p>Sehr geehrte Damen und Herren,</p>
      <p>wir bitten um Ihr verbindliches Angebot für das folgende {kindLabel(r.kind)} auf Basis der beigefügten Zeichnung und 3D-Daten.</p>
      <table className="pq-table">
        <tbody>{specFields(r.kind).filter(([k]) => r.spec?.[k] !== undefined && r.spec?.[k] !== '' && r.spec?.[k] !== null).map(([k, l, t]) => (
          <tr key={k}><td style={{ width: '38%' }}><b>{l}</b></td><td className="pre">{t === 'number' ? num(r.spec[k]) : r.spec[k]}</td></tr>))}</tbody>
      </table>
      {r.note && <p className="pre">{r.note}</p>}
      <p>Bitte geben Sie in Ihrem Angebot an: Preis netto, Lieferzeit bis T0 bzw. Abnahme, Fachzahl, Heißkanal (Fabrikat, Düsen),
        Werkzeugstahl, garantierte Standzeit, Gewährleistung, Zahlungsbedingungen und Fertigungsort.
        {r.needed_by ? ` Benötigt wird das ${kindLabel(r.kind)} bis zum ${fmtD(r.needed_by)}.` : ''}</p>
      <p>Bitte senden Sie Ihr Angebot bis zum <b>{fmtD(r.reply_by)}</b>{a.email ? ` an ${a.email}` : ''}.</p>
      <p>Mit freundlichen Grüßen<br />{a.company_name}</p>
      <LetterFooter a={a} />
    </div>
  )
}
