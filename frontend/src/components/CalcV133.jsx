// v1.33 Block 1 „Kalkulation rechnen“: Lieferjahre (C02/C04/C05), Staffelpreise (C01/C03), Varianten (C07)
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { eur, eur4, fix4, num, num2 } from '../constants'
import NumInput from './NumInput'
import { ErrorBox, Modal } from './ui'

const val = (e) => (e.target.value === '' ? '' : Number(e.target.value))

// ---------------------------------------------------------------- Staffelpreise
export function TierEditor({ rows, qtyKey, unit, priceUnit, onChange, max = 5 }) {
  const list = rows || []
  const upd = (n, patch) => onChange(list.map((r, j) => (j === n ? { ...r, ...patch } : r)))
  return (
    <div className="tier-editor">
      {list.map((t, n) => (
        <span key={n} className="tier-pair">
          <span className="muted small">ab</span>
          <NumInput type="number" step="any" className="num" value={t[qtyKey] ?? ''} placeholder={unit} onChange={(e) => upd(n, { [qtyKey]: val(e) })} />
          <span className="muted small">{unit} →</span>
          <NumInput type="number" step="any" className="num" value={t.price ?? ''} placeholder={priceUnit} onChange={(e) => upd(n, { price: val(e) })} />
          <span className="muted small">{priceUnit}</span>
          <button type="button" className="icon-btn" title="Staffel entfernen" onClick={() => onChange(list.filter((_, j) => j !== n))}>×</button>
        </span>
      ))}
      {list.length < max && <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange([...list, { [qtyKey]: '', price: '' }])}>+ Staffel</button>}
    </div>
  )
}

export function PurchaseHint({ hint, unit, priceUnit }) {
  if (!hint) return null
  return (
    <div className="ok-box small">💡 Einkaufsmenge: Mit der Staffel ab <b>{num(hint.qty)} {unit}</b> ({fix4(hint.price)} {priceUnit}) kostet der Einkauf
      {' '}<b>{eur(hint.cost_alt)}</b> statt {eur(hint.cost_now)} – <b>{eur(hint.saves)} günstiger</b>, obwohl {num(hint.extra)} {unit} mehr gekauft werden (Lager prüfen).</div>
  )
}

// ---------------------------------------------------------------- Material (C03)
export function MaterialBlock({ inputs, set, setInputs, materials, pickMaterial, r, priceField }) {
  const [free, setFree] = useState(!inputs.material_id && !!inputs.material_name)
  useEffect(() => { if (inputs.material_id) setFree(false) }, [inputs.material_id])
  const mp = r.material_purchase || {}
  return <>
    <div className="field span-2"><label>Material</label>
      <select value={free ? '__new' : (inputs.material_id ?? '')} onChange={(e) => {
        if (e.target.value === '__new') { setFree(true); setInputs((s) => ({ ...s, material_id: null })) } else { setFree(false); pickMaterial(e.target.value) }
      }}>
        <option value="">– frei / manuell –</option>
        {materials.map((m) => <option key={m.id} value={m.id}>{m.name} · {num2(m.price_per_kg)} €/kg{m.price_tiers?.length ? ' · Staffel' : ''}</option>)}
        <option value="__new">Neues Material (Freitext) …</option>
      </select>
      {free && <input className="mt-4" autoFocus value={inputs.material_name || ''} placeholder="z. B. PP Copolymer schwarz – wird beim Speichern in den Stammdaten angelegt"
        onChange={(e) => set('material_name', e.target.value)} />}
      {free && <small className="hint">Neue Materialien landen beim Speichern der Kalkulation automatisch unter Stammdaten → Material (mit Lieferant und Staffeln).</small>}
    </div>
    {priceField}
    <div className="field"><label>Lieferant Material</label>
      <input value={inputs.material_supplier || ''} placeholder="z. B. Borealis" onChange={(e) => set('material_supplier', e.target.value)} /></div>
    <div className="field"><label>Angebotsnummer Lieferant</label>
      <input value={inputs.material_offer_no || ''} onChange={(e) => set('material_offer_no', e.target.value)} /></div>
    <div className="field span-2"><label>Staffelpreise Material <span className="unit">nach Jahresbedarf, bis zu 5</span></label>
      <TierEditor rows={inputs.material_tiers} qtyKey="kg" unit="kg" priceUnit="€/kg" onChange={(v) => set('material_tiers', v)} />
      <small className="hint">Ohne Staffeln gilt der Materialpreis. Mit Staffeln wählt das CRM den Preis passend zum Jahresbedarf; unter der kleinsten Staffel gilt deren Preis.</small></div>
    {(inputs.material_tiers || []).length > 0 || mp.need_kg ? (
      <div className="field span-3"><div className="info-line">Jahresbedarf Material <b>{num(mp.need_kg)} kg</b> (inkl. Anguss und Ausschuss)
        {mp.tier_kg ? <> · Staffel ab {num(mp.tier_kg)} kg → <b>{num2(mp.price_kg)} €/kg</b></> : null}
        {mp.masterbatch_kg ? <> · Masterbatch {num(mp.masterbatch_kg, 1)} kg</> : null}
        {' '}· Vorschlag Einkaufsmenge pro Jahr: <b>{num(mp.hint ? mp.hint.qty : mp.need_kg)} kg</b></div>
        <PurchaseHint hint={mp.hint} unit="kg" priceUnit="€/kg" /></div>
    ) : null}
  </>
}

// ---------------------------------------------------------------- Lieferjahre (C02 / C04 / C05)
export function YearVolumes({ inputs, setInputs, r }) {
  const years = Math.min(Math.max(Math.ceil(Number(inputs.project_years) || 1), 1), 15)
  const rows = r.years || []
  const yv = inputs.year_volumes || []
  const yl = inputs.year_lots || []
  const setArr = (key, y, v) => setInputs((s) => {
    const a = [...(s[key] || [])]
    while (a.length <= y) a.push('')
    a[y] = v
    while (a.length && (a[a.length - 1] === '' || a[a.length - 1] == null)) a.pop()
    return { ...s, [key]: a }
  })
  const suggest = () => setInputs((s) => {
    const a = [...(s.year_lots || [])]
    rows.forEach((y, n) => { if (n > 0 && y.lot_suggestion) { while (a.length <= n) a.push(''); a[n] = y.lot_suggestion } })
    return { ...s, year_lots: a }
  })
  const tot = rows.reduce((a, y) => ({ qty: a.qty + y.qty, rev: a.rev + y.revenue, h: a.h + y.machine_hours, kg: a.kg + y.material_kg, pcs: a.pcs + y.purchased_pcs, profit: a.profit + y.profit }),
    { qty: 0, rev: 0, h: 0, kg: 0, pcs: 0, profit: 0 })
  return (
    <div className="field span-3">
      <div className="section-head"><label>Mengen je Lieferjahr</label>
        <span className="toolbar">
          <button type="button" className="btn btn-ghost btn-sm" onClick={suggest} title="Ab Jahr 2: Losgröße = Jahresmenge ÷ 12">Losgröße ab Jahr 2 = Menge ÷ 12</button>
          {years < 15 && <button type="button" className="btn btn-ghost btn-sm" onClick={() => setInputs((s) => ({ ...s, project_years: years + 1 }))}>+ Jahr</button>}
          {years > 1 && <button type="button" className="btn btn-ghost btn-sm" onClick={() => setInputs((s) => ({ ...s, project_years: years - 1,
            year_volumes: (s.year_volumes || []).slice(0, years - 1), year_lots: (s.year_lots || []).slice(0, years - 1) }))}>− Jahr</button>}
        </span></div>
      <table className="table table-compact year-table years-v133">
        <thead><tr><th>Jahr</th><th className="num">Menge Stk</th><th className="num">Losgröße</th><th className="num">Lose</th>
          <th className="num">Masch.-Std.</th><th className="num">Material kg</th><th className="num">Zukaufteile Stk</th>
          <th className="num">€/Stk</th><th className="num">Umsatz</th><th className="num">Marge</th></tr></thead>
        <tbody>{rows.map((y, n) => (
          <tr key={y.year}>
            <td className="nowrap">Jahr {y.year}{n === 0 ? <><br /><small className="muted">Anlauf</small></> : null}</td>
            <td className="num"><NumInput type="number" step="any" className="num" placeholder={num(inputs.annual_volume)} value={yv[n] ?? ''} onChange={(e) => setArr('year_volumes', n, val(e))} /></td>
            <td className="num"><NumInput type="number" step="any" className="num" placeholder={num(inputs.lot_size)} value={yl[n] ?? ''}
              title={n === 0 ? 'Jahr 1 (Anlauf): Losgröße von Hand' : `Vorschlag ${num(y.lot_suggestion)} (Menge ÷ 12)`} onChange={(e) => setArr('year_lots', n, val(e))} />
              {n > 0 && !y.lot_manual && y.lot_suggestion ? <small className="hint">Vorschlag {num(y.lot_suggestion)}</small> : null}</td>
            <td className="num">{num(y.lots, 1)}</td><td className="num">{num(y.machine_hours)}</td><td className="num">{num(y.material_kg)}</td>
            <td className="num">{y.purchased_pcs ? num(y.purchased_pcs) : '–'}</td><td className="num">{fix4(y.price)}</td>
            <td className="num">{eur(y.revenue)}</td><td className={`num ${y.margin_pct < 0 ? 'text-critical' : ''}`}>{num(y.margin_pct, 1)} %</td>
          </tr>))}
          <tr className="row-sum"><td><b>Projekt</b></td><td className="num"><b>{num(tot.qty)}</b></td><td /><td /><td className="num">{num(tot.h)}</td>
            <td className="num">{num(tot.kg)}</td><td className="num">{tot.pcs ? num(tot.pcs) : '–'}</td><td /><td className="num"><b>{eur(tot.rev)}</b></td>
            <td className={`num ${tot.profit < 0 ? 'text-critical' : ''}`}>{tot.rev ? `${num(tot.profit / tot.rev * 100, 1)} %` : '–'}</td></tr>
        </tbody>
      </table>
      <small className="hint">Leere Felder = Jahresmenge bzw. Losgröße oben. Der Stückpreis wird mit der Jahresmenge oben (Kalkulationsmenge) gerechnet;
        je Jahr rechnet das CRM Stunden, Material, Zukaufteile, Selbstkosten und Marge mit der Menge und Losgröße des Jahres. Jahr 1 (Anlauf): Losgröße von Hand.
        Neuumsatz (Vertriebsziel) = Umsatz des stärksten Jahres.</small>
      <label className="check-inline"><input type="checkbox" checked={!!inputs.quote_show_years} onChange={(e) => setInputs((s) => ({ ...s, quote_show_years: e.target.checked }))} />
        {' '}Preise und Mengen je Lieferjahr im Angebot zeigen</label>
    </div>
  )
}

// ---------------------------------------------------------------- Varianten (C07)
export function VariantButton({ calc }) {
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const cur = calc.versions.find((v) => v.version_no === calc.current_version)?.inputs?.cavities
  const [cav, setCav] = useState('')
  const [label, setLabel] = useState('')
  const [err, setErr] = useState(null)
  async function go() {
    setErr(null)
    try { const c = await api.post(`/calculations/${calc.id}/variant`, { cavities: cav, label }); setOpen(false); nav(`/kalkulationen/${c.id}`) } catch (e) { setErr(e) }
  }
  return <>
    <button className="btn btn-ghost" onClick={() => { setCav(cur ? Number(cur) * 2 : 2); setOpen(true) }} title="Kopie mit anderer Fachzahl, als Variante verknüpft">⎘ Variante anlegen</button>
    {open && <Modal title="Variante anlegen" onClose={() => setOpen(false)}>
      <div className="version-body">
        <p className="muted">Alle Werte werden übernommen, die Fachzahl geändert. Schließkraft und Artikelanalyse rechnen mit der neuen Fachzahl neu.
          <b> Werkzeugkosten und Zykluszeit bitte in der Variante selbst anpassen.</b> Die Variante gehört zur selben Anfrage.</p>
        <div className="form-grid">
          <div className="field"><label>Fachzahl bisher</label><input value={cur ?? '–'} disabled /></div>
          <div className="field"><label>Fachzahl der Variante</label><NumInput type="number" step="1" min="1" className="num" autoFocus value={cav} onChange={(e) => setCav(val(e))} /></div>
          <div className="field span-2"><label>Bezeichnung der Variante (optional)</label><input value={label} placeholder={cav ? `${cav}-fach` : ''} onChange={(e) => setLabel(e.target.value)} /></div>
        </div>
        <ErrorBox error={err} />
        <div className="toolbar"><button className="btn btn-primary" disabled={!cav} onClick={go}>Variante anlegen</button>
          <button className="btn btn-ghost" onClick={() => setOpen(false)}>Abbrechen</button></div>
      </div>
    </Modal>}
  </>
}

export function VariantsCard({ calc }) {
  const [rows, setRows] = useState([])
  useEffect(() => { api.get(`/calculations/${calc.id}/variants`).then((d) => setRows(d.rows)).catch(() => setRows([])) }, [calc.id, calc.current_version])
  if (rows.length < 2) return null
  const best = Math.min(...rows.map((x) => x.unit_price || Infinity))
  return (
    <div className="card variants-card">
      <h3>Varianten im Vergleich</h3>
      <table className="table table-compact">
        <thead><tr><th>Kalkulation</th><th className="num">Fachzahl</th><th className="num">Zyklus s</th><th className="num">Schließkraft t</th>
          <th className="num">Werkzeug</th><th className="num">Invest</th><th className="num">€/1.000</th><th className="num">Marge</th></tr></thead>
        <tbody>{rows.map((x) => (
          <tr key={x.id} className={x.current ? 'row-current' : ''}>
            <td>{x.current ? <b>{x.number}</b> : <Link to={`/kalkulationen/${x.id}`}>{x.number}</Link>}
              <br /><small className="muted">{x.variant_of_id ? '↳ Variante' : 'Ausgangskalkulation'}</small></td>
            <td className="num"><b>{x.cavities}</b></td><td className="num">{num(x.cycle_time_s, 1)}</td>
            <td className="num">{x.clamp_t ? num(x.clamp_t) : '–'}</td><td className="num">{eur(x.tool_cost)}</td><td className="num">{eur(x.invest)}</td>
            <td className={`num ${x.unit_price === best ? 'text-good' : ''}`}><b>{num2(x.price_per_1000)}</b></td>
            <td className={`num ${x.margin_pct < 0 ? 'text-critical' : ''}`}>{num(x.margin_pct, 1)} %</td>
          </tr>))}</tbody>
      </table>
      <small className="hint">Alle Varianten stehen in derselben Anfrage und im Angebot. In der Pipeline zählt je Artikel nur die größte Variante.
        Beauftragt der Kunde eine Variante, die anderen mit „Andere Variante beauftragt“ abschließen – das zählt nicht als Verlust. Grün = günstigster Preis.</small>
    </div>
  )
}

// ---------------------------------------------------------------- Zukaufteil-Zeile: Lieferant, Staffeln, Jahresbedarf (C01)
export function PurchasedExtra({ p, res, onChange }) {
  return (
    <div className="purchased-extra">
      <label className="inline-label">Lieferant <input value={p.supplier || ''} placeholder="z. B. Böllhoff" onChange={(e) => onChange({ supplier: e.target.value })} /></label>
      <span className="muted small">Staffelpreise nach Jahresbedarf:</span>
      <TierEditor rows={p.tiers} qtyKey="qty" unit="Stk" priceUnit="€/Stk" onChange={(v) => onChange({ tiers: v })} />
      {res && <span className="small">Jahresbedarf <b>{num(res.need_year)} Stk</b>{res.tier_qty ? <> · Staffel ab {num(res.tier_qty)} → <b>{fix4(res.price_per_piece)} €</b></> : null}</span>}
      {!p.part_id && p.name && <span className="badge badge-info">wird beim Speichern in den Stammdaten angelegt</span>}
      <PurchaseHint hint={res?.hint} unit="Stk" priceUnit="€/Stk" />
    </div>
  )
}

export const eurUnit = eur4
