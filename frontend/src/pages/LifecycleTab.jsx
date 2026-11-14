import { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { ErrorBox } from '../components/ui'
import { num } from '../constants'

const REL = [['gering', 'gering'], ['mittel', 'mittel'], ['hoch', 'hoch']]
const RECYCLE = [['gut', 'gut (Monomaterial, sortenrein)'], ['eingeschraenkt', 'eingeschränkt'], ['schlecht', 'schlecht (Verbund, nicht trennbar)']]
const EOL = [['stofflich', 'stoffliche Verwertung (Recycling)'], ['thermisch', 'thermische Verwertung'], ['deponie', 'Deponie'], ['unbekannt', 'unbekannt / beim Kunden']]

/** Lebenswegbetrachtung (ISO 14001, 6.1.2) – kurz und knapp in 5 Phasen. */
export default function LifecycleTab({ calc, setCalc }) {
  const { canWrite } = useAuth()
  const ver = calc.versions.find((v) => v.version_no === calc.current_version)
  const r = ver.results, inp = ver.inputs, co2 = r.co2 || {}
  const mono = !(inp.components || []).length && !Number(inp.purchased_parts)
  const [lc, setLc] = useState(() => ({ use_relevance: 'gering', recyclability: mono ? 'gut' : 'eingeschraenkt', eol_route: 'stofflich', ...(calc.lifecycle || {}) }))
  const [err, setErr] = useState(null)
  const [saved, setSaved] = useState(false)
  const set = (k, v) => { setSaved(false); setLc((s) => ({ ...s, [k]: v })) }
  const g = (kg) => (kg ? `${num(kg * 1000, 1)} g CO₂e/Stk` : '–')
  const share = (kg) => (co2.total ? ` (${num((kg / co2.total) * 100, 0)} %)` : '')
  const phases = [
    ['Rohstoffe', co2.material + (co2.purchased || 0)], ['Herstellung', co2.scope12], ['Transport & Verpackung', (co2.transport || 0) + (co2.packaging || 0)],
  ]
  const main = co2.active ? phases.reduce((a, b) => (b[1] > a[1] ? b : a))[0] : null
  const sel = (k, opts) => <select disabled={!canWrite} value={lc[k] || ''} onChange={(e) => set(k, e.target.value)}>{opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
  const txt = (k, ph) => <input disabled={!canWrite} value={lc[k] || ''} placeholder={ph} onChange={(e) => set(k, e.target.value)} />

  return (
    <div className="stack" style={{ maxWidth: 1100 }}>
      <div className="card">
        <h3>Lebenswegbetrachtung <span className="muted small">(ISO 14001, 6.1.2 – Kurzfassung je Artikel)</span></h3>
        <table className="table lc-table">
          <thead><tr><th style={{ width: 190 }}>Phase</th><th style={{ width: 260 }}>Kennzahlen (aus Kalkulation)</th><th>Bewertung / Angaben</th></tr></thead>
          <tbody>
            <tr><td><b>1 · Rohstoffe</b></td>
              <td className="small">{inp.material_name || '–'}{(inp.components || []).map((c) => ` + ${c.material_name || c.label}`)}<br />{g(co2.material)}{share(co2.material)}</td>
              <td><div className="lc-grid">
                <label>Rezyklatanteil % <input type="number" disabled={!canWrite} className="num" value={lc.recycled_pct ?? ''} onChange={(e) => set('recycled_pct', e.target.value === '' ? '' : Number(e.target.value))} /></label>
                <label>Biobasierter Anteil {sel('biobased', [['nein', 'nein'], ['teilweise', 'teilweise'], ['ja', 'ja']])}</label>
                <label className="span-2">Anmerkung {txt('raw_note', 'z. B. Rezyklat beim Kunden freigegeben?')}</label>
              </div></td></tr>
            <tr><td><b>2 · Herstellung</b></td>
              <td className="small">Strom {co2.kwh_per_piece ? `${num(co2.kwh_per_piece * 1000, 1)} Wh/Stk` : '–'} · Ausschuss {num(inp.scrap_pct, 1)} %<br />Mahlgut {num(inp.regrind_pct, 0)} % · {g(co2.scope12)}{share(co2.scope12)}</td>
              <td><label className="lc-full">Anmerkung {txt('prod_note', 'z. B. Ökostrom, Heißkanal ohne Anguss, Mahlgutrückführung')}</label></td></tr>
            <tr><td><b>3 · Transport &amp; Verpackung</b></td>
              <td className="small">{inp.pack_reusable ? 'Mehrweg' : (inp.pack_type || 'Verpackung')} · {inp.incoterm || 'ab Werk'}<br />{g((co2.transport || 0) + (co2.packaging || 0))}</td>
              <td><label className="lc-full">Anmerkung {txt('transport_note', 'z. B. Mehrweg-KLT im Kreislauf mit Kunde')}</label></td></tr>
            <tr><td><b>4 · Nutzung</b></td>
              <td className="small muted">beim Kunden</td>
              <td><div className="lc-grid">
                <label>Umweltrelevanz {sel('use_relevance', REL)}</label>
                <label className="span-2">Anmerkung {txt('use_note', 'z. B. Leichtbau statt Metall senkt Verbrauch im Fahrzeug')}</label>
              </div></td></tr>
            <tr><td><b>5 · Ende des Lebenswegs</b></td>
              <td className="small">{mono ? 'Monomaterial' : 'Materialverbund / Einlegeteile'}</td>
              <td><div className="lc-grid">
                <label>Recyclingfähigkeit {sel('recyclability', RECYCLE)}</label>
                <label>Verwertungsweg {sel('eol_route', EOL)}</label>
                <label>Werkstoffkennzeichnung {txt('marking', 'z. B. >PA6-GF30<')}</label>
                <label>Anmerkung {txt('eol_note', 'z. B. Demontage ohne Werkzeug möglich')}</label>
              </div></td></tr>
          </tbody>
        </table>
      </div>
      <div className="card lc-summary">
        <div><span className="muted small">Wesentlicher Umweltaspekt</span><b>{main || 'CO₂-Daten fehlen'}</b></div>
        <label className="lc-full">Verbesserungsmaßnahme / Ziel {txt('improvement', 'z. B. Rezyklatanteil 30 % prüfen, Wandstärke optimieren')}</label>
        <label className="lc-check"><input type="checkbox" disabled={!canWrite} checked={!!lc.on_quote} onChange={(e) => set('on_quote', e.target.checked)} /> Kurzfassung im Angebot ausweisen (Rezyklat, Kennzeichnung, Verwertung, Monomaterial)</label>
        <ErrorBox error={err} />
        {canWrite && <div className="form-actions"><span className="spacer" />
          <button className="btn btn-primary" onClick={async () => {
            setErr(null)
            try { setCalc(await api.put(`/calculations/${calc.id}/lifecycle`, { lifecycle: { ...lc, main_aspect: main } })); setSaved(true) } catch (e) { setErr(e) }
          }}>{saved ? '✓ Gespeichert' : 'Lebensweg speichern'}</button></div>}
      </div>
    </div>
  )
}
