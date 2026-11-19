import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, downloadFile, qs } from '../api'
import { useAuth } from '../auth'
import NumInput from '../components/NumInput'
import { Badge, ErrorBox, Modal, RefSelect, SearchInput, useFetch } from '../components/ui'
import { eur, fmtDate, fmtDateTime, num } from '../constants'

// Preisliste (lebende VK-Preisliste): Artikel je Kunde, Materialpreise, Preisänderungen mit Kennzeichnung
export const PL_STATUS = [
  { value: 'offen', label: 'offen', tone: 'warning' },
  { value: 'weitergegeben', label: 'an Kunden weitergegeben', tone: 'good' },
  { value: 'vertraglich_gebunden', label: 'nicht weitergegeben – vertraglich gebunden', tone: 'info' },
  { value: 'sonstiges', label: 'Sonstiges (Freitext)', tone: 'neutral' },
]
const plStatus = (v) => PL_STATUS.find((s) => s.value === v) || PL_STATUS[0]
const KIND = { material: 'Materialpreis (manuell)', material_import: 'Import Materialpreise', vk_import: 'Import VK-Preise', manuell: 'manuell' }
const SOURCE = { erstanlage: 'Erstanlage', import: 'Import', preisaenderung: 'Preisänderung', manuell: 'manuell', stammdaten: 'Stammdaten', preisliste: 'Preisliste' }
const p4 = (v) => (v == null ? '–' : Number(v).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 4 }))
const signed = (v, f = p4) => (v == null ? '–' : `${v > 0 ? '+' : ''}${f(v)}`)

export default function PriceList() {
  const [tab, setTab] = useState(() => new URLSearchParams(window.location.search).get('tab') || 'articles')
  return (
    <div className="page page-wide">
      <header className="page-head">
        <div><h1>Preisliste</h1>
          <p className="muted">Alle VK-Artikel je Kunde mit Material und Preisbasis. Neue Materialpreise zeigen sofort die betroffenen Artikel;
            je Artikel wird gekennzeichnet, ob die Änderung weitergegeben wurde. Alle Preise mit Historie.</p></div>
      </header>
      <div className="tabs no-print">
        {[['articles', 'Artikel'], ['materials', 'Materialpreise'], ['changes', 'Preisänderungen']].map(([k, l]) => (
          <button key={k} className={tab === k ? 'on' : ''} onClick={() => { setTab(k); window.history.replaceState(null, '', `?tab=${k}`) }}>{l}</button>))}
      </div>
      {tab === 'articles' && <Articles />}
      {tab === 'materials' && <Materials />}
      {tab === 'changes' && <Changes />}
    </div>
  )
}

// ------------------------------------------------------------------ Artikel
function Articles() {
  const { canWrite } = useAuth()
  const [f, setF] = useState(() => { const u = new URLSearchParams(window.location.search); return { account_id: u.get('account_id') || null, material_id: u.get('material_id') || null } })
  const [edit, setEdit] = useState(null)
  const [imp, setImp] = useState(false)
  const [err, setErr] = useState(null)
  const params = { q: f.q, account_id: f.account_id, material_id: f.material_id, contract: f.contract, gap: f.gap || undefined }
  const { data, error, reload } = useFetch('/pricelist/articles' + qs(params))
  const { data: mats } = useFetch('/pricelist/materials')
  const set = (k, v) => setF((s) => ({ ...s, [k]: v || null }))
  return (
    <>
      <div className="filters">
        <SearchInput value={f.q || ''} onChange={(v) => set('q', v)} placeholder="Art.-Nr., Kunden-Nr., Bezeichnung…" />
        <label className="inline-label">Kunde <RefSelect kind="customer" value={f.account_id ? Number(f.account_id) : null} onChange={(v) => set('account_id', v)} /></label>
        <select value={f.material_id || ''} onChange={(e) => set('material_id', e.target.value)}>
          <option value="">alle Materialien</option>{(mats || []).filter((m) => m.articles).map((m) => <option key={m.id} value={m.id}>{m.number ? `${m.number} · ` : ''}{m.name}</option>)}</select>
        <select value={f.contract || ''} onChange={(e) => set('contract', e.target.value)}>
          <option value="">Preisbindung: alle</option><option value="ja">nur mit Preisbindung</option><option value="nein">ohne Preisbindung</option></select>
        <label className="radio-row"><input type="checkbox" checked={!!f.gap} onChange={(e) => set('gap', e.target.checked)} /> nur mit offener Materialdifferenz</label>
        <span className="spacer" />
        <button className="btn btn-ghost" onClick={() => downloadFile('/pricelist/export' + qs({ account_id: f.account_id, material_id: f.material_id, q: f.q, contract: f.contract }), 'Preisliste.xlsx').catch(setErr)}>Export Excel</button>
        {canWrite && <button className="btn btn-ghost" onClick={() => setImp(true)}>Import Preisliste</button>}
        {canWrite && <button className="btn btn-primary" onClick={() => setEdit({ price_unit: 100, currency: 'EUR', mgk_pct: 8, materials: [{}], parts: [], account_id: f.account_id ? Number(f.account_id) : null })}>+ Artikel</button>}
      </div>
      <ErrorBox error={error || err} />
      {data && <div className="kpi-grid">
        <div className="kpi"><span className="kpi-label">Artikel</span><span className="kpi-value">{data.total}</span></div>
        <div className="kpi"><span className="kpi-label">Umsatz p. a. (Planmenge × Preis)</span><span className="kpi-value">{eur(data.sum.annual_revenue)}</span></div>
        <div className="kpi"><span className="kpi-label">Nicht weitergegebene Materialdifferenz p. a.</span><span className="kpi-value">{eur(data.sum.open_gap_annual)}</span>
          <span className="kpi-sub">aktueller Materialpreis gegenüber Basis im VK-Preis</span></div>
      </div>}
      <div className="card table-wrap">
        <table className="table table-compact">
          <thead><tr><th>Kunde</th><th>Art.-Nr. F&amp;R</th><th>Art.-Nr. Kunde</th><th>Bezeichnung</th><th>Material (Basis → aktuell €/kg)</th>
            <th className="num">Preis / PE</th><th>gültig ab</th><th className="num">Planmenge</th><th className="num">Umsatz p. a.</th><th>Vertrag</th><th className="num">offene Δ / PE</th></tr></thead>
          <tbody>{(data?.items || []).map((a) => (
            <tr key={a.id} className="clickable" onClick={() => setEdit({ id: a.id })}>
              <td>{a.account || '–'}</td><td><strong>{a.article_no || '–'}</strong></td><td>{a.customer_part_no || '–'}</td><td>{a.description}</td>
              <td>{a.materials.map((m, i) => <div key={i} className="small">{m.name} <span className="muted">{p4(m.price_basis)}{m.current_price != null && Math.abs(m.current_price - (m.price_basis || 0)) > 1e-9 ? <> → <strong>{p4(m.current_price)}</strong></> : ''}</span></div>)}</td>
              <td className="num">{p4(a.price)} <small className="muted">/{a.price_unit}</small></td><td>{fmtDate(a.price_valid_from)}</td>
              <td className="num">{num(a.forecast_qty)}</td><td className="num">{eur(a.annual_revenue)}</td>
              <td>{a.contract_bound ? <Badge tone="info">Preisbindung{a.contract_until ? ` bis ${fmtDate(a.contract_until)}` : ''}</Badge> : null}{a.contract_note && <div className="small muted">{a.contract_note}</div>}</td>
              <td className={`num ${a.open_gap > 0 ? 'text-critical' : ''}`}>{a.open_gap ? signed(a.open_gap) : '–'}{a.open_gap ? <div className="small muted">{eur(a.open_gap_annual)} p. a.</div> : null}</td>
            </tr>))}
            {data && !data.items.length && <tr><td colSpan={11} className="muted">Keine Artikel – „Import Preisliste“ oder „+ Artikel“.</td></tr>}
          </tbody>
        </table>
      </div>
      {edit && <ArticleDialog init={edit} mats={mats || []} canWrite={canWrite} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); reload() }} />}
      {imp && <ImportDialog kind="articles" onClose={() => setImp(false)} onDone={() => { setImp(false); reload() }} defaultAccount={f.account_id} />}
    </>
  )
}

function ArticleDialog({ init, mats, canWrite, onClose, onSaved }) {
  const [a, setA] = useState(init.id ? null : init)
  const [full, setFull] = useState(null)
  const [err, setErr] = useState(null)
  const [orig, setOrig] = useState(null)
  useEffect(() => {
    if (init.id) api.get(`/pricelist/articles/${init.id}`).then((r) => { setFull(r); setOrig(r.price); setA({ ...r, materials: r.materials.length ? r.materials : [{}] }) }).catch(setErr)
  }, [init.id])
  if (!a) return <Modal title="Artikel" onClose={onClose}><ErrorBox error={err} /><div className="loading">Lade…</div></Modal>
  const set = (k, v) => setA((s) => ({ ...s, [k]: v }))
  const setLine = (key, i, k, v) => setA((s) => ({ ...s, [key]: s[key].map((l, j) => (j === i ? { ...l, [k]: v } : l)) }))
  const nb = (v) => (v === '' || v == null ? null : Number(v))
  async function save() {
    setErr(null)
    try {
      const body = { ...a, price: Number(a.price || 0), price_unit: Number(a.price_unit || 100),
        materials: a.materials.filter((m) => m.material_id || m.name).map((m) => ({ material_id: m.material_id ? Number(m.material_id) : null, name: m.name || null, weight_g: nb(m.weight_g), price_basis: nb(m.price_basis) })),
        parts: a.parts.filter((p) => p.name).map((p) => ({ name: p.name, qty_per_part: Number(p.qty_per_part || 1), price_basis: nb(p.price_basis), current_price: nb(p.current_price), supplier: p.supplier || null })) }
      for (const k of ['forecast_qty', 'qty_last_year', 'revenue_last_year', 'moq', 'shot_weight_g', 'part_weight_g', 'mgk_pct', 'surcharge_pct', 'ratio_per_unit']) body[k] = nb(a[k])
      if (a.id) await api.patch(`/pricelist/articles/${a.id}`, body); else await api.post('/pricelist/articles', body)
      onSaved()
    } catch (e) { setErr(e) }
  }
  const F = (k, l, type = 'text', extra = {}) => (
    <div className={`field ${extra.span ? 'span-2' : ''}`}><label>{l}</label>
      {type === 'number' ? <NumInput type="number" value={a[k] ?? ''} disabled={!canWrite} onChange={(e) => set(k, e.target.value)} />
        : <input type={type} value={a[k] ?? ''} disabled={!canWrite} onChange={(e) => set(k, e.target.value)} />}
      {extra.hint && <small className="hint">{extra.hint}</small>}</div>)
  const priceChanged = a.id && orig != null && Math.abs(Number(a.price) - orig) > 1e-9
  return (
    <Modal title={a.id ? `Artikel ${a.article_no || a.customer_part_no || ''}` : 'Neuer Artikel'} onClose={onClose} wide>
      <ErrorBox error={err} />
      <div className="form-grid form-grid-3">
        <div className="field"><label>Kunde *</label><RefSelect kind="customer" value={a.account_id} onChange={(v) => set('account_id', v)} /></div>
        {F('article_no', 'Artikel-Nr. F&R')}{F('customer_part_no', 'Artikel-Nr. Kunde')}
        {F('description', 'Bezeichnung', 'text', { span: true })}{F('location', 'Fertigungsort / Land')}
        {F('price', 'Preis je PE', 'number', { hint: priceChanged ? 'Preis geändert – wird mit Grund in der Historie gespeichert' : '' })}
        {F('price_unit', 'Preiseinheit (Stk)', 'number')}{F('price_valid_from', 'gültig ab', 'date')}
        {priceChanged && <div className="field span-2"><label>Grund der Preisänderung</label><input value={a.price_note || ''} onChange={(e) => set('price_note', e.target.value)} /></div>}
        {F('forecast_qty', 'Planmenge p. a.', 'number')}{F('qty_last_year', 'Menge Vorjahr', 'number')}{F('revenue_last_year', 'Umsatz Vorjahr', 'number')}
        {F('shot_weight_g', 'Schussgewicht g', 'number')}{F('part_weight_g', 'Teilgewicht g', 'number')}{F('moq', 'MOQ', 'number')}
        {F('mgk_pct', 'MGK % auf Materialdifferenz', 'number')}{F('surcharge_pct', 'NK-Zuschlag %', 'number')}{F('ratio_per_unit', 'Ratio je PE', 'number')}
        <div className="field"><label className="radio-row"><input type="checkbox" checked={!!a.contract_bound} disabled={!canWrite} onChange={(e) => set('contract_bound', e.target.checked)} /> Preisbindung (vertraglich)</label></div>
        {F('contract_until', 'Preisbindung bis', 'date')}{F('contract_note', 'Vertrag', 'text', { hint: 'z. B. Festpreis, Preisgleitklausel Material, Rahmenvertrag' })}
        {F('comment', 'Bemerkung', 'text', { span: true })}
      </div>
      <h4>Materialien <small className="muted">– Basis = Materialpreis €/kg, der im aktuellen VK-Preis steckt</small></h4>
      <table className="table table-compact"><thead><tr><th>Material</th><th className="num">Gewicht g/Teil</th><th className="num">Basis €/kg</th><th className="num">aktuell €/kg</th><th /></tr></thead>
        <tbody>{a.materials.map((m, i) => (
          <tr key={i}>
            <td><select value={m.material_id || ''} disabled={!canWrite} onChange={(e) => setLine('materials', i, 'material_id', e.target.value)}>
              <option value="">– Material wählen –</option>{mats.map((x) => <option key={x.id} value={x.id}>{x.number ? `${x.number} · ` : ''}{x.name}</option>)}</select></td>
            <td className="num"><NumInput type="number" value={m.weight_g ?? ''} disabled={!canWrite} onChange={(e) => setLine('materials', i, 'weight_g', e.target.value)} /></td>
            <td className="num"><NumInput type="number" value={m.price_basis ?? ''} disabled={!canWrite} onChange={(e) => setLine('materials', i, 'price_basis', e.target.value)} /></td>
            <td className="num">{p4(mats.find((x) => x.id === Number(m.material_id))?.price_per_kg)}</td>
            <td>{canWrite && <button className="btn-x" onClick={() => setA((s) => ({ ...s, materials: s.materials.filter((_, j) => j !== i) }))}>×</button>}</td>
          </tr>))}</tbody></table>
      {canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setA((s) => ({ ...s, materials: [...s.materials, {}] }))}>+ Material (z. B. Masterbatch)</button>}
      <h4>Zukaufteile</h4>
      <table className="table table-compact"><thead><tr><th>Bezeichnung</th><th className="num">Stk je Teil</th><th className="num">Basis €/Stk</th><th className="num">aktuell €/Stk</th><th>Lieferant</th><th /></tr></thead>
        <tbody>{a.parts.map((p, i) => (
          <tr key={i}>
            <td><input value={p.name || ''} disabled={!canWrite} onChange={(e) => setLine('parts', i, 'name', e.target.value)} /></td>
            <td className="num"><NumInput type="number" value={p.qty_per_part ?? 1} disabled={!canWrite} onChange={(e) => setLine('parts', i, 'qty_per_part', e.target.value)} /></td>
            <td className="num"><NumInput type="number" value={p.price_basis ?? ''} disabled={!canWrite} onChange={(e) => setLine('parts', i, 'price_basis', e.target.value)} /></td>
            <td className="num"><NumInput type="number" value={p.current_price ?? ''} disabled={!canWrite} onChange={(e) => setLine('parts', i, 'current_price', e.target.value)} /></td>
            <td><input value={p.supplier || ''} disabled={!canWrite} onChange={(e) => setLine('parts', i, 'supplier', e.target.value)} /></td>
            <td>{canWrite && <button className="btn-x" onClick={() => setA((s) => ({ ...s, parts: s.parts.filter((_, j) => j !== i) }))}>×</button>}</td>
          </tr>))}</tbody></table>
      {canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setA((s) => ({ ...s, parts: [...s.parts, { qty_per_part: 1 }] }))}>+ Zukaufteil</button>}
      {full && <>
        <h4>Preishistorie</h4>
        <table className="table table-compact"><thead><tr><th>gültig ab</th><th className="num">alt</th><th className="num">neu</th><th>Quelle</th><th>Notiz</th><th>von / am</th></tr></thead>
          <tbody>{full.history.map((h) => <tr key={h.id}><td>{fmtDate(h.valid_from)}</td><td className="num">{p4(h.old_price)}</td><td className="num"><strong>{p4(h.price)}</strong></td>
            <td>{SOURCE[h.source] || h.source}</td><td className="small">{h.note}</td><td className="small muted">{h.by} · {fmtDateTime(h.at)}</td></tr>)}</tbody></table>
        {full.impacts.length > 0 && <>
          <h4>Preisänderungen (Material / Import)</h4>
          <table className="table table-compact"><thead><tr><th>Vorgang</th><th className="num">Δ / PE</th><th className="num">Jahreseffekt</th><th>Kennzeichnung</th><th>Notiz</th></tr></thead>
            <tbody>{full.impacts.map((i) => <tr key={i.id}><td><Link to={`/preisliste/aenderungen/${i.change_id}`}>{i.change_number}</Link> <small className="muted">{i.change_title}</small></td>
              <td className="num">{signed(i.delta)}</td><td className="num">{eur(i.annual_effect)}</td><td><Badge tone={plStatus(i.status).tone}>{plStatus(i.status).label}</Badge></td><td className="small">{i.note}</td></tr>)}</tbody></table>
        </>}
      </>}
      <div className="form-actions"><span className="spacer" />
        <button className="btn btn-ghost" onClick={onClose}>Schließen</button>
        {canWrite && <button className="btn btn-primary" disabled={!a.account_id} onClick={save}>Speichern</button>}
      </div>
    </Modal>
  )
}

// ------------------------------------------------------------------ Materialpreise
function Materials() {
  const { canWrite } = useAuth()
  const nav = useNavigate()
  const { data, error, reload } = useFetch('/pricelist/materials')
  const [chg, setChg] = useState(null)
  const [hist, setHist] = useState(null)
  const [imp, setImp] = useState(false)
  const [onlyUsed, setOnlyUsed] = useState(true)
  return (
    <>
      <div className="filters">
        <label className="radio-row"><input type="checkbox" checked={onlyUsed} onChange={(e) => setOnlyUsed(e.target.checked)} /> nur Materialien mit Artikeln in der Preisliste</label>
        <span className="spacer" />
        {canWrite && <button className="btn btn-primary" onClick={() => setImp(true)}>Import Materialpreise (monatlich)</button>}
      </div>
      <ErrorBox error={error} />
      <div className="card table-wrap"><table className="table table-compact">
        <thead><tr><th>Mat.-Nr.</th><th>Material</th><th>Lieferant</th><th className="num">Preis €/kg</th><th>gültig ab</th><th>letzte Änderung</th><th className="num">Artikel</th><th /></tr></thead>
        <tbody>{(data || []).filter((m) => !onlyUsed || m.articles).map((m) => (
          <tr key={m.id}><td>{m.number || '–'}</td><td><strong>{m.name}</strong></td><td>{m.supplier || '–'}</td><td className="num">{p4(m.price_per_kg)}</td>
            <td>{fmtDate(m.price_valid_from)}</td>
            <td className="small">{m.last_change ? <>{p4(m.last_change.old)} → {p4(m.last_change.new)} <span className="muted">({SOURCE[m.last_change.source] || m.last_change.source})</span></> : '–'}</td>
            <td className="num">{m.articles ? <a href={`/preisliste?tab=articles&material_id=${m.id}`}>{m.articles}</a> : 0}</td>
            <td className="nowrap"><button className="btn btn-ghost btn-sm" onClick={() => setHist(m)}>Historie</button>
              {canWrite && <button className="btn btn-primary btn-sm" onClick={() => setChg(m)}>Neuer Preis</button>}</td></tr>))}
        </tbody></table></div>
      {chg && <MaterialChangeDialog m={chg} onClose={() => setChg(null)} onDone={(id) => { setChg(null); nav(`/preisliste/aenderungen/${id}`) }} />}
      {hist && <MaterialHistory m={hist} onClose={() => setHist(null)} />}
      {imp && <ImportDialog kind="materials" onClose={() => setImp(false)} onDone={(r) => { setImp(false); r?.change ? nav(`/preisliste/aenderungen/${r.change.id}`) : reload() }} />}
    </>
  )
}

function MaterialHistory({ m, onClose }) {
  const { data } = useFetch(`/pricelist/materials/${m.id}/history`)
  return (
    <Modal title={`Preishistorie ${m.name}`} onClose={onClose}>
      <table className="table table-compact"><thead><tr><th>gültig ab</th><th className="num">alt</th><th className="num">neu €/kg</th><th>Quelle</th><th>Notiz</th><th>von / am</th></tr></thead>
        <tbody>{(data || []).map((h, i) => <tr key={i}><td>{fmtDate(h.valid_from)}</td><td className="num">{p4(h.old_price)}</td><td className="num"><strong>{p4(h.price)}</strong></td>
          <td>{SOURCE[h.source] || h.source}{h.change_id && <> · <Link to={`/preisliste/aenderungen/${h.change_id}`}>Vorgang</Link></>}</td><td className="small">{h.note}</td><td className="small muted">{h.by} · {fmtDateTime(h.at)}</td></tr>)}
          {data && !data.length && <tr><td colSpan={6} className="muted">Noch keine Änderungen erfasst.</td></tr>}</tbody></table>
    </Modal>
  )
}

function MaterialChangeDialog({ m, onClose, onDone }) {
  const [price, setPrice] = useState('')
  const [vf, setVf] = useState(new Date().toISOString().slice(0, 10))
  const [note, setNote] = useState('')
  const [pv, setPv] = useState(null)
  const [err, setErr] = useState(null)
  useEffect(() => {
    if (!price || Number(price) <= 0) { setPv(null); return }
    const t = setTimeout(() => api.post('/pricelist/material-change/preview', { items: [{ material_id: m.id, new_price: Number(price) }] }).then(setPv).catch(setErr), 300)
    return () => clearTimeout(t)
  }, [price])
  async function commit() {
    try {
      const r = await api.post('/pricelist/material-change', { items: [{ material_id: m.id, new_price: Number(price) }], valid_from: vf, note: note || null })
      onDone(r.id)
    } catch (e) { setErr(e) }
  }
  return (
    <Modal title={`Neuer Materialpreis: ${m.name}`} onClose={onClose} wide>
      <ErrorBox error={err} />
      <div className="form-grid form-grid-3">
        <div className="field"><label>bisher €/kg</label><input disabled value={p4(m.price_per_kg)} /></div>
        <div className="field"><label>neu €/kg *</label><NumInput type="number" value={price} onChange={(e) => setPrice(e.target.value)} autoFocus /></div>
        <div className="field"><label>gültig ab</label><input type="date" value={vf} onChange={(e) => setVf(e.target.value)} /></div>
        <div className="field span-3"><label>Notiz / Quelle</label><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="z. B. Lieferantenschreiben vom …, Marktbericht" /></div>
      </div>
      {pv && <>
        <div className="kpi-grid">
          <div className="kpi"><span className="kpi-label">betroffene Artikel</span><span className="kpi-value">{pv.count}</span><span className="kpi-sub">davon {pv.contract_bound} mit Preisbindung</span></div>
          <div className="kpi"><span className="kpi-label">Jahreseffekt</span><span className="kpi-value">{eur(pv.annual_effect)}</span><span className="kpi-sub">Δ × Planmenge</span></div>
        </div>
        <table className="table table-compact"><thead><tr><th>Kunde</th><th>Artikel</th><th className="num">Basis €/kg</th><th className="num">g/Teil</th><th className="num">Preis / PE</th><th className="num">Δ / PE</th><th className="num">neu</th><th className="num">Δ %</th><th className="num">Jahreseffekt</th><th>Vertrag</th></tr></thead>
          <tbody>{pv.rows.map((r) => <tr key={r.article_id}><td>{r.account}</td><td><strong>{r.article_no}</strong> {r.description}</td>
            <td className="num">{p4(r.detail[0]?.basis)}</td><td className="num">{num(r.detail[0]?.weight_g, 1)}</td><td className="num">{p4(r.old_price)}</td>
            <td className="num">{signed(r.delta)}</td><td className="num"><strong>{p4(r.new_price)}</strong></td><td className="num">{r.delta_pct != null ? `${signed(r.delta_pct, (x) => num(x, 2))} %` : '–'}</td>
            <td className="num">{eur(r.annual_effect)}</td><td>{r.contract_bound && <Badge tone="info">Preisbindung</Badge>} <small className="muted">{r.contract_note}</small></td></tr>)}
            {!pv.rows.length && <tr><td colSpan={10} className="muted">Kein Artikel betroffen.</td></tr>}</tbody></table>
        <p className="small muted">Δ = (neu − Basis) × Gewicht/1000 × Preiseinheit × (1 + MGK %). Mit „Übernehmen“ wird der Materialpreis gespeichert (Historie) und ein Vorgang angelegt,
          in dem Sie je Artikel kennzeichnen: weitergegeben · vertraglich gebunden · Sonstiges.</p>
      </>}
      <div className="form-actions"><span className="spacer" />
        <button className="btn btn-ghost" onClick={onClose}>Abbrechen</button>
        <button className="btn btn-primary" disabled={!price || Number(price) <= 0} onClick={commit}>Übernehmen und Vorgang anlegen</button>
      </div>
    </Modal>
  )
}

// ------------------------------------------------------------------ Import
function ImportDialog({ kind, onClose, onDone, defaultAccount }) {
  const [file, setFile] = useState(null)
  const [acc, setAcc] = useState(defaultAccount ? Number(defaultAccount) : null)
  const [vf, setVf] = useState(new Date().toISOString().slice(0, 10))
  const [note, setNote] = useState('')
  const [createUnknown, setCreateUnknown] = useState(true)
  const [pv, setPv] = useState(null)
  const [res, setRes] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const form = () => {
    const fd = new FormData()
    fd.append('file', file)
    if (kind === 'articles' && acc) fd.append('account_id', acc)
    return fd
  }
  async function preview() {
    setErr(null); setBusy(true)
    try { setPv(await api.upload(`/pricelist/import/${kind}/preview`, form())) } catch (e) { setErr(e) } finally { setBusy(false) }
  }
  async function commit() {
    setErr(null); setBusy(true)
    try {
      const fd = form(); fd.append('valid_from', vf); if (note) fd.append('note', note)
      if (kind === 'materials') fd.append('create_unknown', createUnknown ? 'true' : 'false')
      setRes(await api.upload(`/pricelist/import/${kind}/commit`, fd))
    } catch (e) { setErr(e) } finally { setBusy(false) }
  }
  const ST = { neu: ['neu', 'info'], preis_geaendert: ['Preis geändert', 'warning'], unveraendert: ['unverändert', 'neutral'], fehler: ['Fehler', 'critical'],
    geaendert: ['Preis geändert', 'warning'], unbekannt: ['unbekannt', 'info'] }
  return (
    <Modal title={kind === 'articles' ? 'Import Preisliste (VK-Artikel)' : 'Import Materialpreise'} onClose={onClose} wide>
      <ErrorBox error={err} />
      {res ? <>
        <div className="notice-ok">✓ {kind === 'articles' ? `${res.created} neu angelegt, ${res.updated} aktualisiert, davon ${res.price_changed} mit geändertem Preis${res.skipped ? `, ${res.skipped} Zeilen mit Fehlern übersprungen` : ''}.`
          : `${res.changed} Materialpreis(e) geändert${res.created ? `, ${res.created} Material(ien) neu angelegt` : ''}.`}
          {res.change && <> Vorgang <strong>{res.change.number}</strong> angelegt – dort je Artikel kennzeichnen.</>}</div>
        <div className="form-actions"><span className="spacer" /><button className="btn btn-primary" onClick={() => onDone(res)}>{res.change ? 'Zum Vorgang' : 'Schließen'}</button></div>
      </> : <>
        <p className="small muted">{kind === 'articles'
          ? 'Excel oder CSV. Die F&R-Vorlage „Annual Price Inquiry List“ wird automatisch erkannt (Kopfzeile 7). Abgleich über Artikel-Nr. F&R, sonst Kunden-Artikel-Nr. + Kunde. Geänderte Preise kommen mit Historie in einen Vorgang „Import VK-Preise“. Unbekannte Materialien werden in den Stammdaten angelegt.'
          : 'Excel oder CSV mit Material-Nr. und/oder Bezeichnung und Preis €/kg. Die Vorschau zeigt geänderte Preise und die betroffenen Artikel. Beim Übernehmen entsteht ein Vorgang, in dem je Artikel gekennzeichnet wird.'}
          {' '}<a href="#" onClick={(e) => { e.preventDefault(); downloadFile(`/pricelist/import/${kind}/template`, `Vorlage_Preisliste_${kind}.csv`) }}>Vorlage (CSV)</a></p>
        <div className="form-grid form-grid-3">
          <div className="field span-2"><label>Datei *</label><input type="file" accept=".xlsx,.xlsm,.csv,.txt" onChange={(e) => { setFile(e.target.files[0]); setPv(null) }} /></div>
          {kind === 'articles' && <div className="field"><label>Kunde (für Zeilen ohne Kundenspalte)</label><RefSelect kind="customer" value={acc} onChange={(v) => { setAcc(v); setPv(null) }} /></div>}
          <div className="field"><label>Preise gültig ab</label><input type="date" value={vf} onChange={(e) => setVf(e.target.value)} /></div>
          <div className="field span-2"><label>Notiz</label><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="z. B. Monatsimport ERP November" /></div>
          {kind === 'materials' && <div className="field"><label className="radio-row"><input type="checkbox" checked={createUnknown} onChange={(e) => setCreateUnknown(e.target.checked)} /> unbekannte Materialien anlegen</label></div>}
        </div>
        {pv && <>
          <div className="toolbar" style={{ margin: '8px 0' }}>{Object.entries(pv.counts).map(([k, n]) => <Badge key={k} tone={ST[k]?.[1]}>{ST[k]?.[0] || k}: {n}</Badge>)}
            {pv.template && <Badge tone="good">F&amp;R-Vorlage erkannt</Badge>}
            {kind === 'materials' && <span className="small">→ {pv.articles} Artikel betroffen · Jahreseffekt {eur(pv.annual_effect)}</span>}</div>
          {pv.columns && <p className="small muted">Zuordnung: {pv.columns.map((c) => `${c.col.replace(/\n/g, ' ')} → ${c.field}`).join(' · ')}</p>}
          <div className="table-wrap" style={{ maxHeight: 340 }}><table className="table table-compact">
            {kind === 'articles' ? <>
              <thead><tr><th>Zeile</th><th>Status</th><th>Art.-Nr.</th><th>Kunden-Nr.</th><th>Bezeichnung</th><th>Material</th><th className="num">bisher</th><th className="num">Preis</th><th>Fehler</th></tr></thead>
              <tbody>{pv.rows.map((r) => <tr key={r.row}><td>{r.row}</td><td><Badge tone={ST[r.status]?.[1]}>{ST[r.status]?.[0]}</Badge></td><td>{r.values.article_no}</td><td>{r.values.customer_part_no}</td>
                <td>{r.values.description}</td><td className="small">{r.values.mat1_name || r.values.mat1_number}</td><td className="num">{p4(r.existing?.price)}</td><td className="num"><strong>{p4(r.values.price)}</strong></td><td className="small text-critical">{r.errors.join('; ')}</td></tr>)}</tbody>
            </> : <>
              <thead><tr><th>Zeile</th><th>Status</th><th>Mat.-Nr.</th><th>Material</th><th className="num">bisher</th><th className="num">neu €/kg</th><th className="num">Artikel</th><th className="num">Jahreseffekt</th><th>Fehler</th></tr></thead>
              <tbody>{pv.rows.map((r) => <tr key={r.row}><td>{r.row}</td><td><Badge tone={ST[r.status]?.[1]}>{ST[r.status]?.[0]}</Badge></td><td>{r.values.number || r.material?.number}</td><td>{r.material?.name || r.values.name}</td>
                <td className="num">{p4(r.material?.price)}</td><td className="num"><strong>{p4(r.values.price)}</strong></td><td className="num">{r.affected || ''}</td><td className="num">{r.effect ? eur(r.effect) : ''}</td><td className="small text-critical">{r.errors.join('; ')}</td></tr>)}</tbody>
            </>}
          </table></div>
        </>}
        <div className="form-actions"><span className="spacer" />
          <button className="btn btn-ghost" onClick={onClose}>Abbrechen</button>
          <button className="btn btn-ghost" disabled={!file || busy} onClick={preview}>Vorschau</button>
          <button className="btn btn-primary" disabled={!pv || busy} onClick={commit}>Übernehmen</button>
        </div>
      </>}
    </Modal>
  )
}

// ------------------------------------------------------------------ Preisänderungen
function Changes() {
  const nav = useNavigate()
  const { data, error } = useFetch('/pricelist/changes')
  return (
    <>
      <ErrorBox error={error} />
      <div className="card table-wrap"><table className="table">
        <thead><tr><th>Vorgang</th><th>Art</th><th>Titel</th><th>gültig ab</th><th className="num">Artikel</th><th>Kennzeichnung</th><th className="num">Jahreseffekt</th><th className="num">davon weitergegeben</th></tr></thead>
        <tbody>{(data || []).map((c) => (
          <tr key={c.id} className="clickable" onClick={() => nav(`/preisliste/aenderungen/${c.id}`)}>
            <td><strong>{c.number}</strong><br /><small className="muted">{fmtDateTime(c.created_at)} · {c.by}</small></td><td>{KIND[c.kind] || c.kind}</td><td>{c.title}</td><td>{fmtDate(c.valid_from)}</td>
            <td className="num">{c.count}</td>
            <td>{c.status_count.offen > 0 ? <Badge tone="warning">{c.status_count.offen} offen</Badge> : <Badge tone="good">✓ alle gekennzeichnet</Badge>}</td>
            <td className="num">{eur(c.annual_effect)}</td><td className="num">{eur(c.effect.weitergegeben)}</td></tr>))}
          {data && !data.length && <tr><td colSpan={8} className="muted">Noch keine Preisänderungen. Unter „Materialpreise“ einen neuen Preis eingeben oder importieren.</td></tr>}
        </tbody></table></div>
    </>
  )
}

export function PriceChangeDetail() {
  const { id } = useParams()
  const { canWrite } = useAuth()
  const { data: c, error, reload } = useFetch(`/pricelist/changes/${id}`)
  const [sel, setSel] = useState([])
  const [bulk, setBulk] = useState({ status: 'weitergegeben', note: '' })
  const [edit, setEdit] = useState(null)
  const [err, setErr] = useState(null)
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!c) return <div className="page"><div className="loading">Lade…</div></div>
  const toggle = (iid) => setSel((s) => (s.includes(iid) ? s.filter((x) => x !== iid) : [...s, iid]))
  const open = c.impacts.filter((i) => i.status === 'offen')
  async function doBulk() {
    setErr(null)
    try { await api.post(`/pricelist/changes/${c.id}/bulk`, { impact_ids: sel, status: bulk.status, note: bulk.note || null }); setSel([]); reload() } catch (e) { setErr(e) }
  }
  return (
    <div className="page page-wide">
      <header className="page-head"><div>
        <Link to="/preisliste?tab=changes" className="muted small">← Preisänderungen</Link>
        <h1>{c.number} · {c.title}</h1>
        <p className="muted">{KIND[c.kind] || c.kind} · gültig ab {fmtDate(c.valid_from)} · angelegt {fmtDateTime(c.created_at)} von {c.by}{c.note && ` · ${c.note}`}</p>
      </div></header>
      <ErrorBox error={err} />
      <div className="kpi-grid">
        <div className="kpi"><span className="kpi-label">Artikel</span><span className="kpi-value">{c.count}</span><span className="kpi-sub">{c.status_count.offen} noch offen</span></div>
        <div className="kpi"><span className="kpi-label">Jahreseffekt gesamt</span><span className="kpi-value">{eur(c.annual_effect)}</span></div>
        {PL_STATUS.slice(1).map((s) => <div key={s.value} className="kpi"><span className="kpi-label">{s.label}</span><span className="kpi-value">{c.status_count[s.value]}</span><span className="kpi-sub">{eur(c.effect[s.value])} p. a.</span></div>)}
      </div>
      {canWrite && <div className="bulk-bar card no-print">
        <strong>{sel.length} ausgewählt</strong>
        <button className="btn btn-ghost btn-sm" onClick={() => setSel(open.map((i) => i.id))}>alle offenen</button>
        <button className="btn btn-ghost btn-sm" onClick={() => setSel(open.filter((i) => i.contract_bound).map((i) => i.id))}>offene mit Preisbindung</button>
        <select value={bulk.status} onChange={(e) => setBulk({ ...bulk, status: e.target.value })}>{PL_STATUS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}</select>
        <input placeholder={bulk.status === 'sonstiges' ? 'Freitext (Pflicht)' : 'Notiz (optional)'} value={bulk.note} onChange={(e) => setBulk({ ...bulk, note: e.target.value })} />
        <button className="btn btn-primary btn-sm" disabled={!sel.length || (bulk.status === 'sonstiges' && !bulk.note.trim())} onClick={doBulk}>Kennzeichnen</button>
        <small className="muted">„weitergegeben“ übernimmt den neuen Preis in die Preisliste (Historie)</small>
      </div>}
      <div className="card table-wrap"><table className="table table-compact">
        <thead><tr><th /><th>Kunde</th><th>Artikel</th><th>Vertrag</th><th className="num">Preis vorher</th><th className="num">Δ / PE</th><th className="num">neu</th><th className="num">Jahreseffekt</th><th>Kennzeichnung</th><th /></tr></thead>
        <tbody>{c.impacts.map((i) => (
          <tr key={i.id}>
            <td>{canWrite && <input type="checkbox" checked={sel.includes(i.id)} onChange={() => toggle(i.id)} />}</td>
            <td>{i.account}</td><td><strong>{i.article_no}</strong> {i.description}<br /><small className="muted">{i.customer_part_no}</small>
              {i.detail?.filter((d) => d.type === 'material').map((d, k) => <div key={k} className="small muted">{d.name}: {p4(d.basis)} → {p4(d.new)} €/kg × {num(d.weight_g, 1)} g</div>)}</td>
            <td>{i.contract_bound && <Badge tone="info">Preisbindung</Badge>}<div className="small muted">{i.contract_note}</div></td>
            <td className="num">{p4(i.old_price)}</td><td className="num">{signed(i.delta)}</td><td className="num"><strong>{p4(i.new_price)}</strong></td><td className="num">{eur(i.annual_effect)}</td>
            <td><Badge tone={plStatus(i.status).tone}>{plStatus(i.status).label}</Badge>
              {i.passed_price != null && i.status === 'weitergegeben' && <div className="small">Preis {p4(i.passed_price)} ab {fmtDate(i.effective_date)}</div>}
              {i.note && <div className="small muted">{i.note}</div>}{i.by && <div className="small muted">{i.by} · {fmtDateTime(i.decided_at)}</div>}</td>
            <td>{canWrite && <button className="btn btn-ghost btn-sm" onClick={() => setEdit({ ...i, passed: i.passed_price ?? i.new_price, date: i.effective_date || c.valid_from, st: i.status === 'offen' ? 'weitergegeben' : i.status })}>kennzeichnen</button>}</td>
          </tr>))}</tbody></table></div>
      {edit && <Modal title={`Kennzeichnen: ${edit.article_no} ${edit.description || ''}`} onClose={() => setEdit(null)}>
        <ErrorBox error={err} />
        <div className="form">
          <div className="field"><label>Kennzeichnung</label>{PL_STATUS.map((s) => <label key={s.value} className="radio-row"><input type="radio" checked={edit.st === s.value} onChange={() => setEdit({ ...edit, st: s.value })} /> {s.label}</label>)}</div>
          {edit.st === 'weitergegeben' && c.kind !== 'vk_import' && <div className="form-grid">
            <div className="field"><label>an Kunden weitergegebener Preis je PE</label><NumInput type="number" value={edit.passed} onChange={(e) => setEdit({ ...edit, passed: e.target.value })} />
              <small className="hint">Vorschlag {p4(edit.new_price)} – abweichend bei teilweiser Weitergabe</small></div>
            <div className="field"><label>gültig ab</label><input type="date" value={edit.date || ''} onChange={(e) => setEdit({ ...edit, date: e.target.value })} /></div></div>}
          <div className="field"><label>{edit.st === 'sonstiges' ? 'Freitext *' : 'Notiz'}</label><textarea rows={2} value={edit.note || ''} onChange={(e) => setEdit({ ...edit, note: e.target.value })} /></div>
          <div className="form-actions"><span className="spacer" /><button className="btn btn-ghost" onClick={() => setEdit(null)}>Abbrechen</button>
            <button className="btn btn-primary" disabled={edit.st === 'sonstiges' && !(edit.note || '').trim()} onClick={async () => {
              setErr(null)
              try { await api.patch(`/pricelist/impacts/${edit.id}`, { status: edit.st, note: edit.note || null, passed_price: edit.passed === '' || edit.passed == null ? null : Number(edit.passed), effective_date: edit.date || null }); setEdit(null); reload() } catch (e) { setErr(e) }
            }}>Speichern</button></div>
        </div>
      </Modal>}
    </div>
  )
}
