import { useEffect, useState } from 'react'
import { api } from '../api'
import { resetThresholds } from '../components/BigProject'
import { useAuth } from '../auth'
import ListPage from '../components/ListPage'
import { Badge, ErrorBox } from '../components/ui'
import { num, num2 } from '../constants'

const machineFields = [
  { name: 'number', label: 'Maschinen-Nr.' },
  { name: 'name', label: 'Bezeichnung', required: true },
  { name: 'clamping_force_t', label: 'Schließkraft (t)', type: 'number', step: 'any' },
  { name: 'location', label: 'Standort / Halle' },
  { name: 'hourly_rate', label: 'Maschinenstundensatz €/h (ohne Personal)', type: 'number', step: 'any', required: true },
  { name: 'maintenance_rate', label: 'Instandhaltung €/h', type: 'number', step: 'any' },
  { name: 'productivity_pct', label: 'Standard-Produktivität %', type: 'number', step: 'any' },
  { name: 'operator_factor', label: 'Standard-Bedienfaktor (Pers./Masch.)', type: 'number', step: 'any' },
  { name: 'available_hours_year', label: 'Verfügbare Stunden / Jahr', type: 'number', step: 'any', hint: 'Schichtmodell, z. B. 3-Schicht ≈ 6.000 h' },
  { name: 'base_load_pct', label: 'Grundauslastung Bestandsaufträge %', type: 'number', step: 'any', hint: 'für die Auslastungsvorschau' },
  { name: 'base_load_decline_pct', label: 'Auslauf Bestand % je Jahr', type: 'number', step: 'any', hint: 'z. B. 10 = Bestand sinkt jährlich um 10 %' },
  { name: 'power_kw', label: 'Leistungsaufnahme inkl. Peripherie (kW)', type: 'number', step: 'any', hint: 'für den CO₂-Fußabdruck' },
  { name: 'grid_factor', label: 'Strom-Emissionsfaktor Standort (kg CO₂e/kWh)', type: 'number', step: 'any', hint: 'leer = Parameter; z. B. eigener Wert für Werk Krupka' },
  { name: 'active', label: 'Aktiv (in Kalkulation auswählbar)', type: 'checkbox' },
  { name: 'notes', label: 'Notizen', type: 'textarea', span: true },
]
const materialFields = [
  { name: 'name', label: 'Bezeichnung', required: true, span: true },
  { name: 'family', label: 'Werkstoffgruppe', hint: 'z. B. PA6, PP, ABS' },
  { name: 'supplier', label: 'Lieferant' },
  { name: 'price_per_kg', label: 'Preis €/kg', type: 'number', step: 'any', required: true },
  { name: 'density', label: 'Dichte g/cm³', type: 'number', step: 'any' },
  { name: 'co2_kg_per_kg', label: 'CO₂-Emissionsfaktor kg CO₂e/kg', type: 'number', step: 'any', hint: 'Cradle-to-Gate, möglichst Lieferanten-PCF' },
  { name: 'active', label: 'Aktiv', type: 'checkbox' },
  { name: 'notes', label: 'Notizen', type: 'textarea', span: true },
]
const PARAMS = [
  ['Lohnsätze', [['labor_rate_h', 'Lohnsatz Maschinenbediener', '€/h'], ['setup_rate_h', 'Lohnsatz Einrichter', '€/h'], ['assembly_rate_h', 'Lohnsatz Montage', '€/h']]],
  ['Zuschläge', [['mgk_pct', 'Materialgemeinkosten', '%'], ['fgk_pct', 'Fertigungsgemeinkosten', '%'], ['scrap_pct', 'Ausschuss', '%'],
    ['vwgk_pct', 'Verwaltungsgemeinkosten', '%'], ['vtgk_pct', 'Vertriebsgemeinkosten', '%'], ['pm_pct', 'Projektmanagement', '%'],
    ['quality_pct', 'Qualität', '%'], ['toolshop_pct', 'Werkzeugbau', '%']]],
  ['Gewinn & Konditionen', [['profit_pct', 'Gewinn', '%'], ['cash_discount_pct', 'Skonto', '%'], ['rebate_pct', 'Rabatt', '%']]],
  ['Fertigung', [['productivity_pct', 'Produktivität (ohne Maschine)', '%'], ['assembly_productivity_pct', 'Produktivität Montage', '%'],
    ['setup_time_h', 'Rüstzeit je Los', 'h'], ['setup_persons', 'Einrichter je Rüstvorgang', 'Pers.'], ['startup_scrap_pcs', 'Anfahrausschuss je Los', 'Stk']]],
  ['CO₂-Fußabdruck', [['co2_grid_kg_kwh', 'Strom-Emissionsfaktor', 'kg CO₂e/kWh'], ['co2_scope1_kg_h', 'Werksemissionen Scope 1', 'kg CO₂e/Masch.-h'],
    ['co2_masterbatch_kg_kg', 'Masterbatch', 'kg CO₂e/kg'], ['co2_transport_kg_tkm', 'Lkw-Transport', 'kg CO₂e/tkm']]],
  ['Großprojekte (Hervorhebung)', [['big_revenue_threshold', 'Ab Jahresumsatz', '€'], ['big_invest_threshold', 'Ab Invest (Einmalkosten)', '€']]],
  ['Nachkalkulation (Ampel)', [['nk_green_pct', 'Grün bis Abweichung Selbstkosten', '%'], ['nk_red_pct', 'Rot ab Abweichung Selbstkosten', '%']]],
]

export default function MasterData() {
  const [tab, setTab] = useState('machines')
  const tabs = <div className="seg">
    {[['machines', 'Maschinen'], ['materials', 'Materialien'], ['params', 'Parameter']].map(([k, l]) =>
      <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>)}
  </div>
  if (tab === 'params') return <Params tabs={tabs} />
  if (tab === 'materials') {
    return <ListPage key="mat" title="Stammdaten · Materialien" subtitle="Preise werden in der Kalkulation vorbelegt und sind dort überschreibbar"
      path="/materials" entityLabel="Material" fields={materialFields} defaultSort="name" newDefaults={{ active: true }} extraActions={tabs}
      columns={[
        { key: 'name', label: 'Material', sort: 'name', render: (r) => <strong>{r.name}</strong> },
        { key: 'family', label: 'Gruppe', sort: 'family' },
        { key: 'supplier', label: 'Lieferant' },
        { key: 'price_per_kg', label: '€/kg', sort: 'price_per_kg', className: 'num', render: (r) => num2(r.price_per_kg) },
        { key: 'density', label: 'Dichte', className: 'num', render: (r) => (r.density ? num(r.density, 2) : '–') },
        { key: 'co2_kg_per_kg', label: 'kg CO₂e/kg', className: 'num', render: (r) => (r.co2_kg_per_kg != null ? num(r.co2_kg_per_kg, 2) : '–') },
        { key: 'active', label: 'Status', render: (r) => (r.active ? <Badge tone="good">aktiv</Badge> : <Badge>inaktiv</Badge>) },
      ]} />
  }
  return <ListPage key="mach" title="Stammdaten · Maschinen" subtitle="Standard-Stundensätze, Instandhaltung und Produktivität je Maschine"
    path="/machines" entityLabel="Maschine" fields={machineFields} defaultSort="number"
    newDefaults={{ active: true, productivity_pct: 85, operator_factor: 0.3, available_hours_year: 6000, base_load_pct: 0, base_load_decline_pct: 0 }} extraActions={tabs}
    columns={[
      { key: 'number', label: 'Nr.', sort: 'number' },
      { key: 'name', label: 'Maschine', sort: 'name', render: (r) => <strong>{r.name}</strong> },
      { key: 'clamping_force_t', label: 'Schließkraft', sort: 'clamping_force_t', className: 'num', render: (r) => (r.clamping_force_t ? `${num(r.clamping_force_t)} t` : '–') },
      { key: 'hourly_rate', label: '€/h Maschine', sort: 'hourly_rate', className: 'num', render: (r) => num2(r.hourly_rate) },
      { key: 'maintenance_rate', label: '€/h Instandh.', className: 'num', render: (r) => num2(r.maintenance_rate) },
      { key: 'productivity_pct', label: 'Produktivität', className: 'num', render: (r) => `${num(r.productivity_pct, 1)} %` },
      { key: 'operator_factor', label: 'Bedienfaktor', className: 'num', render: (r) => num(r.operator_factor, 2) },
      { key: 'available_hours_year', label: 'h/Jahr', className: 'num', render: (r) => num(r.available_hours_year) },
      { key: 'base_load_pct', label: 'Grundlast', className: 'num', render: (r) => `${num(r.base_load_pct, 0)} % (−${num(r.base_load_decline_pct, 0)} %/J.)` },
      { key: 'power_kw', label: 'kW', className: 'num', render: (r) => (r.power_kw != null ? num(r.power_kw, 1) : '–') },
      { key: 'location', label: 'Standort' },
      { key: 'active', label: 'Status', render: (r) => (r.active ? <Badge tone="good">aktiv</Badge> : <Badge>inaktiv</Badge>) },
    ]} />
}

function Params({ tabs }) {
  const { isAdmin } = useAuth()
  const [vals, setVals] = useState(null)
  const [msg, setMsg] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => { api.get('/calc/settings').then(setVals) }, [])
  if (!vals) return <div className="loading">Lade…</div>
  async function save() {
    setError(null)
    try { setVals(await api.put('/calc/settings', vals)); resetThresholds(); setMsg('Gespeichert. Gilt für neue Kalkulationen; bestehende Versionen bleiben unverändert.') }
    catch (e) { setError(e) }
  }
  return (
    <div className="page">
      <header className="page-head">
        <div><h1>Stammdaten · Parameter</h1>
          <p className="muted">Standardwerte für neue Kalkulationen. In jeder Kalkulation einzeln überschreibbar.</p></div>
        <div className="toolbar">{tabs}{isAdmin && <button className="btn btn-primary" onClick={save}>Speichern</button>}</div>
      </header>
      {!isAdmin && <div className="warn-box">Nur Administratoren können die Standardwerte ändern.</div>}
      {msg && <div className="ok-box">{msg}</div>}
      <ErrorBox error={error} />
      <fieldset disabled={!isAdmin} className="calc-fieldset">
        <div className="grid-2">
          {PARAMS.map(([title, fields]) => (
            <div key={title} className="card">
              <h3>{title}</h3>
              <div className="form-grid">
                {fields.map(([k, l, u]) => (
                  <div key={k} className="field"><label>{l} <span className="unit">{u}</span></label>
                    <input type="number" step="any" className="num" value={vals[k] ?? ''}
                      onChange={(e) => { setMsg(null); setVals({ ...vals, [k]: e.target.value === '' ? '' : Number(e.target.value) }) }} /></div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </fieldset>
    </div>
  )
}
