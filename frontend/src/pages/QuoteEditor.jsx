import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Badge, confirmDelete, ErrorBox, RefSelect } from '../components/ui'
import { contactName, eur, fmtDate, QUOTE_STATUS } from '../constants'
import { quoteTone } from './Quotes'
import { BigBadge } from '../components/BigProject'

const emptyItem = () => ({ description: '', quantity: 1, unit: 'Stk', unit_price: 0, discount_pct: 0 })
const greeting = (c) => {
  if (c?.salutation === 'Frau') return `Sehr geehrte Frau ${c.last_name},`
  if (c?.salutation === 'Herr') return `Sehr geehrter Herr ${c.last_name},`
  return 'Sehr geehrte Damen und Herren,'
}
const lineTotal = (i) => Number(i.quantity || 0) * Number(i.unit_price || 0) * (1 - Number(i.discount_pct || 0) / 100)

export default function QuoteEditor() {
  const { id } = useParams()
  const [search] = useSearchParams()
  const nav = useNavigate()
  const { canWrite } = useAuth()
  const isNew = id === 'neu'
  const [q, setQ] = useState(null)
  const [account, setAccount] = useState(null)
  const [cfg, setCfg] = useState({ company_name: '', default_tax_rate: 19 })
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.get('/quotes/settings').then(setCfg)
    if (isNew) {
      const accId = search.get('account_id')
      setQ({
        title: '', status: 'entwurf', account_id: accId ? Number(accId) : null, contact_id: null, opportunity_id: null,
        tax_rate: null, intro_text: 'vielen Dank für Ihre Anfrage. Gerne unterbreiten wir Ihnen folgendes Angebot:',
        terms: 'Zahlungsbedingungen: 30 Tage netto. Lieferung ab Werk. Preise zzgl. gesetzl. MwSt.',
        items: [emptyItem()],
      })
    } else {
      api.get(`/quotes/${id}`).then(setQ).catch(setError)
    }
  }, [id])

  useEffect(() => {
    if (q?.account_id) api.get(`/accounts/${q.account_id}`).then(setAccount)
    else setAccount(null)
  }, [q?.account_id])

  if (error && !q) return <ErrorBox error={error} />
  if (!q) return <div className="loading">Lade…</div>
  const ro = !canWrite
  const set = (k, v) => { setQ((s) => ({ ...s, [k]: v })); setSaved(false) }
  const setItem = (idx, k, v) => set('items', q.items.map((it, i) => (i === idx ? { ...it, [k]: v } : it)))
  const move = (idx, dir) => {
    const items = [...q.items]
    const j = idx + dir
    if (j < 0 || j >= items.length) return
    ;[items[idx], items[j]] = [items[j], items[idx]]
    set('items', items)
  }
  const tax = q.tax_rate ?? cfg.default_tax_rate
  const net = q.items.reduce((s, i) => s + lineTotal(i), 0)
  const taxSum = (net * tax) / 100

  async function save() {
    setError(null)
    const body = {
      title: q.title, status: q.status, account_id: q.account_id, contact_id: q.contact_id,
      opportunity_id: q.opportunity_id, valid_until: q.valid_until || null, quote_date: q.quote_date || null,
      tax_rate: q.tax_rate === '' ? null : q.tax_rate, intro_text: q.intro_text, terms: q.terms,
      items: q.items.filter((i) => i.description.trim()).map((i) => ({
        description: i.description, unit: i.unit || 'Stk', quantity: Number(i.quantity || 0),
        unit_price: Number(i.unit_price || 0), discount_pct: Number(i.discount_pct || 0),
      })),
    }
    try {
      const res = isNew ? await api.post('/quotes', body) : await api.patch(`/quotes/${id}`, body)
      setQ(res)
      setSaved(true)
      if (isNew) nav(`/angebote/${res.id}`, { replace: true })
    } catch (e) { setError(e) }
  }
  async function duplicate() {
    const res = await api.post(`/quotes/${id}/duplicate`)
    nav(`/angebote/${res.id}`)
  }
  async function remove() {
    if (await confirmDelete('Angebot', () => api.del(`/quotes/${id}`))) nav('/angebote')
  }

  return (
    <div className="page">
      <div className="no-print quote-screen">
        <Link to="/angebote" className="back">‹ Alle Angebote</Link>
        <header className="page-head">
          <div>
            <h1>{isNew ? 'Neues Angebot' : q.number} {!isNew && <Badge tone={quoteTone[q.status]}>{QUOTE_STATUS.find((s) => s.value === q.status)?.label}</Badge>}
              <BigBadge revenue={net - q.items.filter((i) => i.unit === 'psch').reduce((s, i) => s + lineTotal(i), 0)}
                invest={q.items.filter((i) => i.unit === 'psch').reduce((s, i) => s + lineTotal(i), 0)} /></h1>
            <p className="muted">{isNew ? 'Nummer wird beim Speichern vergeben' : `Erstellt ${fmtDate(q.quote_date)} von ${q.owner?.name || '–'}`}
              {q.calculation_ids?.length > 0 && <> · aus Kalkulation{q.calculation_ids.length > 1 ? 'en' : ''}{' '}
                {(q.calculations || q.calculation_ids.map((id) => ({ id, number: `#${id}` }))).map((c, i) => (
                  <span key={c.id}>{i > 0 && ', '}<Link to={`/kalkulationen/${c.id}`} title={c.article_name}>{c.number}</Link></span>))}</>}
            </p>
          </div>
          <div className="toolbar">
            {!isNew && <button className="btn btn-ghost" onClick={() => window.print()}>Drucken / PDF</button>}
            {!isNew && canWrite && <button className="btn btn-ghost" onClick={duplicate}>Duplizieren</button>}
            {!isNew && canWrite && <button className="btn btn-danger-ghost" onClick={remove}>Löschen</button>}
            {canWrite && <button className="btn btn-primary" onClick={save}>{saved ? '✓ Gespeichert' : 'Speichern'}</button>}
          </div>
        </header>
        <ErrorBox error={error} />

        <div className="card">
          <div className="form-grid form-grid-3">
            <div className="field span-2"><label>Titel *</label><input disabled={ro} value={q.title} onChange={(e) => set('title', e.target.value)} placeholder="z. B. Gehäuse 2K-Bauteil Serie" /></div>
            <div className="field"><label>Status</label>
              <select disabled={ro} value={q.status} onChange={(e) => set('status', e.target.value)}>
                {QUOTE_STATUS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select></div>
            <div className="field"><label>Firma *</label><RefSelect kind="account" value={q.account_id} onChange={(v) => { set('account_id', v) }} /></div>
            <div className="field"><label>Ansprechpartner</label><RefSelect kind="contact" filter={q.account_id} value={q.contact_id} onChange={(v) => set('contact_id', v)} /></div>
            <div className="field"><label>Verkaufschance</label><RefSelect kind="opportunity" filter={q.account_id} value={q.opportunity_id} onChange={(v) => set('opportunity_id', v)} /></div>
            <div className="field"><label>Angebotsdatum</label><input disabled={ro} type="date" value={q.quote_date || ''} onChange={(e) => set('quote_date', e.target.value)} /></div>
            <div className="field"><label>Gültig bis</label><input disabled={ro} type="date" value={q.valid_until || ''} onChange={(e) => set('valid_until', e.target.value)} /><small className="hint">Leer = 30 Tage</small></div>
            <div className="field"><label>MwSt. %</label><input disabled={ro} type="number" step="0.1" value={q.tax_rate ?? ''} placeholder={String(cfg.default_tax_rate)} onChange={(e) => set('tax_rate', e.target.value === '' ? null : Number(e.target.value))} /></div>
            <div className="field span-3"><label>Einleitungstext</label><textarea disabled={ro} rows={2} value={q.intro_text || ''} onChange={(e) => set('intro_text', e.target.value)} /></div>
          </div>
        </div>

        <div className="card card-flush">
          <table className="table items-table">
            <thead><tr><th style={{ width: 36 }}>Pos</th><th>Beschreibung</th><th className="num" style={{ width: 120 }}>Menge</th><th style={{ width: 80 }}>Einheit</th><th className="num" style={{ width: 130 }}>Einzelpreis €</th><th className="num" style={{ width: 80 }}>Rabatt %</th><th className="num" style={{ width: 130 }}>Gesamt</th><th style={{ width: 90 }} /></tr></thead>
            <tbody>
              {q.items.map((it, idx) => (
                <tr key={idx}>
                  <td>{idx + 1}</td>
                  <td><textarea rows={Math.min(8, Math.max(1, (it.description || '').split('\n').reduce((n, l) => n + Math.max(1, Math.ceil(l.length / 75)), 0)))} disabled={ro} value={it.description} onChange={(e) => setItem(idx, 'description', e.target.value)} placeholder="Artikel / Leistung" /></td>
                  <td><input disabled={ro} type="number" step="any" className="num" value={it.quantity} onChange={(e) => setItem(idx, 'quantity', e.target.value)} /></td>
                  <td><input disabled={ro} value={it.unit} onChange={(e) => setItem(idx, 'unit', e.target.value)} /></td>
                  <td><input disabled={ro} type="number" step="any" className="num" value={it.unit_price} onChange={(e) => setItem(idx, 'unit_price', e.target.value)} /></td>
                  <td><input disabled={ro} type="number" step="any" min="0" max="100" className="num" value={it.discount_pct} onChange={(e) => setItem(idx, 'discount_pct', e.target.value)} /></td>
                  <td className="num"><strong>{eur(lineTotal(it), true)}</strong></td>
                  <td className="row-actions">
                    {!ro && <>
                      <button className="icon-btn" title="Nach oben" onClick={() => move(idx, -1)}>↑</button>
                      <button className="icon-btn" title="Nach unten" onClick={() => move(idx, 1)}>↓</button>
                      <button className="icon-btn" title="Entfernen" onClick={() => set('items', q.items.filter((_, i) => i !== idx))}>×</button>
                    </>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="items-foot">
            {!ro ? <button className="btn btn-ghost btn-sm" onClick={() => set('items', [...q.items, emptyItem()])}>+ Position</button> : <span />}
            <dl className="totals">
              <dt>Netto</dt><dd>{eur(net, true)}</dd>
              <dt>MwSt. {tax} %</dt><dd>{eur(taxSum, true)}</dd>
              <dt className="grand">Gesamt brutto</dt><dd className="grand">{eur(net + taxSum, true)}</dd>
            </dl>
          </div>
        </div>
        <div className="card">
          <div className="field"><label>Bedingungen / Schlusstext</label><textarea disabled={ro} rows={3} value={q.terms || ''} onChange={(e) => set('terms', e.target.value)} /></div>
        </div>
      </div>

      {/* Druckansicht */}
      <div className="print-only print-doc">
        <div className="print-sender">{cfg.company_name}</div>
        <div className="print-head">
          <div className="print-address">
            <strong>{account?.name}</strong><br />
            {q.contact && <>{contactName(q.contact)}<br /></>}
            {account?.street && <>{account.street}<br /></>}
            {[account?.zip, account?.city].filter(Boolean).join(' ')}<br />
            {account?.country !== 'Deutschland' && account?.country}
          </div>
          <dl className="print-meta">
            <dt>Angebot Nr.</dt><dd>{q.number}</dd>
            <dt>Datum</dt><dd>{fmtDate(q.quote_date)}</dd>
            <dt>Gültig bis</dt><dd>{fmtDate(q.valid_until)}</dd>
            <dt>Ansprechpartner</dt><dd>{q.owner?.name}</dd>
          </dl>
        </div>
        <h2>Angebot: {q.title}</h2>
        <p>{greeting(q.contact)}</p>
        <p className="pre">{q.intro_text}</p>
        <table className="print-table">
          <thead><tr><th>Pos</th><th>Beschreibung</th><th className="num">Menge</th><th className="num">Einzelpreis</th><th className="num">Rabatt</th><th className="num">Gesamt</th></tr></thead>
          <tbody>
            {q.items.map((it, i) => (
              <tr key={i}><td>{i + 1}</td><td className="pre">{it.description}</td>
                <td className="num">{Number(it.quantity).toLocaleString('de-DE')} {it.unit}</td>
                <td className="num">{eur(it.unit_price, true)}</td>
                <td className="num">{Number(it.discount_pct) ? `${it.discount_pct} %` : ''}</td>
                <td className="num">{eur(lineTotal(it), true)}</td></tr>
            ))}
          </tbody>
        </table>
        <dl className="totals print-totals">
          <dt>Summe netto</dt><dd>{eur(net, true)}</dd>
          <dt>zzgl. MwSt. {tax} %</dt><dd>{eur(taxSum, true)}</dd>
          <dt className="grand">Gesamtbetrag</dt><dd className="grand">{eur(net + taxSum, true)}</dd>
        </dl>
        <p className="pre">{q.terms}</p>
        <p>Mit freundlichen Grüßen<br />{q.owner?.name}<br />{cfg.company_name}</p>
      </div>
    </div>
  )
}
