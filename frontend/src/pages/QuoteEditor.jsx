import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Badge, confirmDelete, ErrorBox, RefSelect } from '../components/ui'
import { contactName, eur, fmtDate, QUOTE_STATUS } from '../constants'
import { quoteTone } from './Quotes'
import { BigBadge } from '../components/BigProject'
import Attachments from '../components/Attachments'

const emptyItem = () => ({ description: '', quantity: 1, unit: 'Stk', unit_price: 0, discount_pct: 0 })
const greeting = (c, lang = 'de') => {
  if (lang === 'en') {
    if (c?.salutation === 'Frau') return `Dear Ms ${c.last_name},`
    if (c?.salutation === 'Herr') return `Dear Mr ${c.last_name},`
    return 'Dear Sir or Madam,'
  }
  if (c?.salutation === 'Frau') return `Sehr geehrte Frau ${c.last_name},`
  if (c?.salutation === 'Herr') return `Sehr geehrter Herr ${c.last_name},`
  return 'Sehr geehrte Damen und Herren,'
}

const T = {
  de: { quote: 'Angebot', no: 'Angebots-Nr.', date: 'Datum', valid: 'Gültig bis', contact: 'Ihr Ansprechpartner', pos: 'Pos.',
    desc: 'Beschreibung', qty: 'Menge', price: 'Einzelpreis', disc: 'Rabatt', total: 'Gesamt', net: 'Summe netto', vat: 'zzgl. MwSt.',
    gross: 'Gesamtbetrag', page: 'Seite', cust: 'Kunden-Nr.', yourRef: 'Ihr Zeichen' },
  en: { quote: 'Quotation', no: 'Quotation no.', date: 'Date', valid: 'Valid until', contact: 'Your contact', pos: 'Item',
    desc: 'Description', qty: 'Quantity', price: 'Unit price', disc: 'Discount', total: 'Total', net: 'Net total', vat: 'plus VAT',
    gross: 'Total amount', page: 'Page', cust: 'Customer no.', yourRef: 'Your reference' },
}
const fmtD = (d, lang) => (d ? new Date(d).toLocaleDateString(lang === 'en' ? 'en-GB' : 'de-DE') : '–')
const money = (v, lang) => new Intl.NumberFormat(lang === 'en' ? 'en-GB' : 'de-DE', { style: 'currency', currency: 'EUR', minimumFractionDigits: 2, maximumFractionDigits: 4 }).format(Number(v || 0))

function mailto(q, account, app) {
  const en = q.language === 'en'
  const to = q.contact?.email || account?.email || ''
  const subj = `${en ? 'Quotation' : 'Angebot'} ${q.number} – ${q.title}`
  const body = `${greeting(q.contact, q.language)}\n\n${en ? 'please find attached our quotation' : 'anbei erhalten Sie unser Angebot'} ${q.number} (${q.title}).\n\n${(en ? app?.closing_en : app?.closing_de) || ''}\n${q.owner?.name || ''}\n${app?.company_name || ''}`
  return `mailto:${to}?subject=${encodeURIComponent(subj)}&body=${encodeURIComponent(body)}`
}

function PrintQuote({ q, account, app, net, taxSum, tax }) {
  const lang = q.language === 'en' ? 'en' : 'de'
  const t = T[lang]
  const a = app || {}
  const accent = a.accent_color || '#1f4b99'
  return (
    <div className="print-only print-doc" style={{ '--accent': accent }}>
      <div className="pq-head">
        <div className="pq-company"><strong>{a.company_name}</strong><br />{a.street}<br />{a.zip_city}{a.country && a.country !== 'Deutschland' ? `, ${a.country}` : ''}</div>
        {a.logo_attachment_id && <img className="pq-logo" src="/api/public/logo" alt="" />}
      </div>
      <div className="pq-sender">{[a.company_name, a.street, a.zip_city].filter(Boolean).join(' · ')}</div>
      <div className="pq-addr-meta">
        <div className="pq-address">
          <strong>{account?.name}</strong><br />
          {q.contact && <>{q.contact.salutation ? `${q.contact.salutation} ` : ''}{q.contact.first_name} {q.contact.last_name}<br /></>}
          {account?.street && <>{account.street}<br /></>}
          {[account?.zip, account?.city].filter(Boolean).join(' ')}{account?.country && account.country !== 'Deutschland' && <><br />{account.country}</>}
        </div>
        <dl className="pq-meta">
          <dt>{t.no}</dt><dd>{q.number}</dd>
          <dt>{t.date}</dt><dd>{fmtD(q.quote_date, lang)}</dd>
          <dt>{t.valid}</dt><dd>{fmtD(q.valid_until, lang)}</dd>
          <dt>{t.contact}</dt><dd>{q.owner?.name}</dd>
          {a.phone && <><dt>Tel.</dt><dd>{a.phone}</dd></>}
          {a.email && <><dt>E-Mail</dt><dd>{a.email}</dd></>}
        </dl>
      </div>
      <h2 className="pq-title">{t.quote} {q.number}: {q.title}</h2>
      <p>{greeting(q.contact, lang)}</p>
      <p className="pre">{q.intro_text || (lang === 'en' ? a.intro_en : a.intro_de)}</p>
      <table className="pq-table">
        <thead><tr><th>{t.pos}</th><th>{t.desc}</th><th className="num">{t.qty}</th><th className="num">{t.price}</th><th className="num">{t.disc}</th><th className="num">{t.total}</th></tr></thead>
        <tbody>{q.items.map((it, i) => (
          <tr key={i}><td>{i + 1}</td><td className="pre">{it.description}</td>
            <td className="num">{Number(it.quantity).toLocaleString(lang === 'en' ? 'en-GB' : 'de-DE')} {it.unit}</td>
            <td className="num">{money(it.unit_price, lang)}</td>
            <td className="num">{Number(it.discount_pct) ? `${it.discount_pct} %` : ''}</td>
            <td className="num">{money(lineTotal(it), lang)}</td></tr>
        ))}</tbody>
      </table>
      <dl className="pq-totals">
        <dt>{t.net}</dt><dd>{money(net, lang)}</dd>
        <dt>{t.vat} {tax} %</dt><dd>{money(taxSum, lang)}</dd>
        <dt className="grand">{t.gross}</dt><dd className="grand">{money(net + taxSum, lang)}</dd>
      </dl>
      <p className="pre pq-terms">{q.terms || (lang === 'en' ? a.terms_en : a.terms_de)}</p>
      <p>{(lang === 'en' ? a.closing_en : a.closing_de) || ''}<br />{q.owner?.name}<br />{a.company_name}</p>
      <div className="pq-footer">
        <div>{a.company_name}<br />{a.street}<br />{a.zip_city}</div>
        <div>{a.phone && <>Tel. {a.phone}<br /></>}{a.email}<br />{a.website}</div>
        <div>{a.register}<br />{a.vat_id && <>USt-IdNr. {a.vat_id}<br /></>}{a.managing_directors && <>{lang === 'en' ? 'Managing directors' : 'Geschäftsführung'}: {a.managing_directors}</>}</div>
        <div>{a.bank_name}<br />{a.iban && <>IBAN {a.iban}<br /></>}{a.bic && <>BIC {a.bic}</>}</div>
      </div>
    </div>
  )
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

  const [app, setApp] = useState(null)
  useEffect(() => {
    api.get('/quotes/settings').then(setCfg)
    api.get('/app-settings').then(setApp).catch(() => {})
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
      title: q.title, status: q.status, account_id: q.account_id, contact_id: q.contact_id, language: q.language || 'de',
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
            {!isNew && <select className="lang-select" value={q.language || 'de'} disabled={!canWrite} title="Sprache des Angebots" onChange={(e) => {
              const to = e.target.value, from = to === 'en' ? 'de' : 'en'
              setQ((x) => ({ ...x, language: to,
                intro_text: !x.intro_text || (app && x.intro_text === app[`intro_${from}`]) ? app?.[`intro_${to}`] ?? x.intro_text : x.intro_text,
                terms: !x.terms || (app && x.terms === app[`terms_${from}`]) ? app?.[`terms_${to}`] ?? x.terms : x.terms }))
              setSaved(false)
            }}>
              <option value="de">Deutsch</option><option value="en">English</option></select>}
            {!isNew && <button className="btn btn-ghost" onClick={() => window.print()}>Drucken / PDF</button>}
            {!isNew && <a className="btn btn-ghost" href={mailto(q, account, app)} title="E-Mail in Outlook öffnen – PDF vorher über „Drucken / PDF“ speichern und anhängen">✉ E-Mail</a>}
            {!isNew && canWrite && <button className="btn btn-ghost" onClick={duplicate}>Duplizieren</button>}
            {!isNew && canWrite && q.status === 'entwurf' && <button className="btn btn-danger-ghost" onClick={remove}>Löschen</button>}
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

      <div className="no-print" style={{ marginTop: 18 }}>
        {!isNew && <Attachments entity="quotes" entityId={q.id} title="Dokumente zum Angebot (Kundenanfrage, Bestellung, Zeichnungen …)" compact />}
      </div>

      {/* Druckansicht im Firmenlayout */}
      <PrintQuote q={q} account={account} app={app} net={net} taxSum={taxSum} tax={tax} />
    </div>
  )
}
