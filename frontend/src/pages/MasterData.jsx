import { useEffect, useState } from 'react'
import { api } from '../api'
import { resetThresholds } from '../components/BigProject'
import { Escalation, MachineRates, Templates } from './MasterExtras'
import { useAuth } from '../auth'
import ListPage from '../components/ListPage'
import { Badge, ErrorBox } from '../components/ui'
import { MACHINE_KINDS, machineKindLabel, num, num2 } from '../constants'

const machineFields = [
  { name: 'number', label: 'Maschinen-Nr.' },
  { name: 'name', label: 'Bezeichnung', required: true },
  { name: 'kind', label: 'Art', type: 'select', required: true, options: MACHINE_KINDS, hint: 'Montagelinien, Prüfstationen u. a. werden in der Kalkulation als weitere Arbeitsgänge gewählt' },
  { name: 'clamping_force_t', label: 'Schließkraft (t)', type: 'number', step: 'any' },
  { name: 'location', label: 'Standort / Halle' },
  { name: 'hourly_rate', label: 'Maschinenstundensatz €/h (ohne Personal)', type: 'number', step: 'any', required: true },
  { name: 'maintenance_rate', label: 'Instandhaltung €/h', type: 'number', step: 'any' },
  { name: 'productivity_pct', label: 'Standard-Produktivität %', type: 'number', step: 'any' },
  { name: 'operator_factor', label: 'Standard-Anteil Bediener %', type: 'number', step: 'any', scale: 100, hint: '30 = ein Bediener für ca. 3 Maschinen, 100 = fest an der Maschine, 120 = mit Springer' },
  { name: 'handling_pct', label: 'Standard-Anteil Handling %', type: 'number', step: 'any', hint: '0 … 100' },
  { name: 'automation_pct', label: 'Standard-Anteil Automatisierung %', type: 'number', step: 'any', hint: '0 … 100, z. B. bei Roboterzelle' },
  { name: 'available_hours_year', label: 'Verfügbare Stunden / Jahr', type: 'number', step: 'any', hint: 'Schichtmodell, z. B. 3-Schicht ≈ 6.000 h' },
  { name: 'base_load_pct', label: 'Grundauslastung Bestandsaufträge %', type: 'number', step: 'any', hint: 'für die Auslastungsvorschau' },
  { name: 'base_load_decline_pct', label: 'Auslauf Bestand % je Jahr', type: 'number', step: 'any', hint: 'z. B. 10 = Bestand sinkt jährlich um 10 %' },
  { name: 'power_kw', label: 'Leistungsaufnahme inkl. Peripherie (kW)', type: 'number', step: 'any', hint: 'für den CO₂-Fußabdruck' },
  { name: 'grid_factor', label: 'Strom-Emissionsfaktor Standort (kg CO₂e/kWh)', type: 'number', step: 'any', hint: 'leer = Parameter; z. B. eigener Wert für Werk Krupka' },
  { name: 'acquisition_value', label: 'Wiederbeschaffungswert €', type: 'number', step: 'any', hint: 'Herleitung Stundensatz' },
  { name: 'useful_life_years', label: 'Nutzungsdauer Jahre', type: 'number', step: 'any' },
  { name: 'interest_pct', label: 'Kalkulatorischer Zins %', type: 'number', step: 'any' },
  { name: 'floor_space_m2', label: 'Platzbedarf m²', type: 'number', step: 'any' },
  { name: 'maintenance_cost_year', label: 'Instandhaltungskosten €/Jahr', type: 'number', step: 'any' },
  { name: 'other_fixed_cost_year', label: 'Sonstige Fixkosten €/Jahr', type: 'number', step: 'any', hint: 'Versicherung, Software, Wartungsverträge' },
  { name: 'allocation_cost_year', label: 'Umlage Kostenstelle €/Jahr', type: 'number', step: 'any', hint: 'Meister, Logistik, Peripherie, Druckluft – nicht zusätzlich im FGK-Zuschlag' },
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
  { name: 'price_index', label: 'Bezugsindex Preisgleitung', hint: 'z. B. Marktbericht / Börsennotierung' },
  { name: 'active', label: 'Aktiv', type: 'checkbox' },
  { name: 'notes', label: 'Notizen', type: 'textarea', span: true },
]
const partFields = [
  { name: 'part_no', label: 'Artikel-Nr. (intern)' },
  { name: 'name', label: 'Bezeichnung', required: true },
  { name: 'supplier', label: 'Lieferant' },
  { name: 'supplier_part_no', label: 'Artikel-Nr. Lieferant' },
  { name: 'price', label: 'Preis €', type: 'number', step: 'any', required: true },
  { name: 'price_basis', label: 'Preiseinheit (Stück)', type: 'number', step: '1', hint: 'z. B. 1 oder 1000 – Preis gilt je Preiseinheit' },
  { name: 'unit', label: 'Mengeneinheit', hint: 'Stk, m, g …' },
  { name: 'moq', label: 'Mindestbestellmenge', type: 'number', step: 'any' },
  { name: 'lead_time_days', label: 'Wiederbeschaffungszeit (Tage)', type: 'number', step: '1' },
  { name: 'co2_kg_per_piece', label: 'CO₂ kg CO₂e je Einheit', type: 'number', step: 'any', hint: 'Lieferanten-PCF bzw. Richtwert' },
  { name: 'price_valid_from', label: 'Preis gültig ab', type: 'date' },
  { name: 'active', label: 'Aktiv (in Kalkulation auswählbar)', type: 'checkbox' },
  { name: 'notes', label: 'Notizen', type: 'textarea', span: true },
]
const PARAMS = [
  ['Lohnsätze', [['labor_rate_h', 'Lohnsatz Maschinenbediener', '€/h'], ['setup_rate_h', 'Lohnsatz Einrichter', '€/h'], ['assembly_rate_h', 'Lohnsatz Montage', '€/h'],
    ['handling_rate_h', 'Lohnsatz Handling', '€/h'], ['automation_rate_h', 'Lohnsatz Automatisierung', '€/h']]],
  ['Zuschläge', [['mgk_pct', 'Materialgemeinkosten', '%'], ['fgk_pct', 'Fertigungsgemeinkosten', '%'], ['scrap_pct', 'Ausschuss', '%'],
    ['vwgk_pct', 'Verwaltungsgemeinkosten', '%'], ['vtgk_pct', 'Vertriebsgemeinkosten', '%'], ['pm_pct', 'Projektmanagement', '%'],
    ['quality_pct', 'Qualität', '%'], ['toolshop_pct', 'Werkzeugbau', '%']]],
  ['Zukaufteile', [['purchased_mgk_pct', 'Eigener MGK-Satz Zukaufteile (leer = wie MGK)', '%'], ['side_mgk_pct', 'Nebenkalkulation: MGK', '%'],
    ['side_quality_pct', 'Nebenkalkulation: Qualität', '%'], ['side_scrap_pct', 'Nebenkalkulation: Ausschuss', '%'], ['side_markup_pct', 'Nebenkalkulation: Aufschlag', '%']]],
  ['Verpackung & Transport (pauschal)', [['pack_pct', 'Verpackung', '% auf HK'], ['transport_pct', 'Transport', '% auf HK']]],
  ['Gewinn & Konditionen', [['profit_pct', 'Gewinn', '%'], ['cash_discount_pct', 'Skonto', '%'], ['rebate_pct', 'Rabatt', '%']]],
  ['Fertigung', [['productivity_pct', 'Produktivität (ohne Maschine)', '%'], ['assembly_productivity_pct', 'Produktivität Montage', '%'],
    ['setup_time_h', 'Rüstzeit je Los', 'h'], ['setup_persons', 'Einrichter je Rüstvorgang', 'Pers.'], ['startup_scrap_pcs', 'Anfahrausschuss je Los', 'Stk']]],
  ['CO₂-Fußabdruck', [['co2_grid_kg_kwh', 'Strom-Emissionsfaktor', 'kg CO₂e/kWh'], ['co2_scope1_kg_h', 'Werksemissionen Scope 1', 'kg CO₂e/Masch.-h'],
    ['co2_masterbatch_kg_kg', 'Masterbatch', 'kg CO₂e/kg'], ['co2_transport_kg_tkm', 'Lkw-Transport', 'kg CO₂e/tkm']]],
  ['Stundensatz & Preisgleitung', [['space_cost_m2_year', 'Raumkosten', '€/m² · Jahr'], ['energy_price_kwh', 'Strompreis', '€/kWh'], ['escalation_threshold_pct', 'Preisgleitklausel ab Änderung', '± %']]],
  ['Großprojekte (Hervorhebung)', [['big_revenue_threshold', 'Ab Jahresumsatz', '€'], ['big_invest_threshold', 'Ab Invest (Einmalkosten)', '€']]],
  ['Nachkalkulation (Ampel)', [['nk_green_pct', 'Grün bis Abweichung Selbstkosten', '%'], ['nk_red_pct', 'Rot ab Abweichung Selbstkosten', '%']]],
]

export default function MasterData() {
  const [tab, setTab] = useState('machines')
  const tabs = <div className="seg">
    {[['machines', 'Maschinen & Anlagen'], ['rates', 'Stundensätze'], ['materials', 'Materialien'], ['parts', 'Zukaufteile'], ['prices', 'Preisgleitung'], ['templates', 'Vorlagen'], ['params', 'Parameter']].map(([k, l]) =>
      <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>)}
  </div>
  if (tab === 'params') return <Params tabs={tabs} />
  if (tab === 'rates') return <MachineRates tabs={tabs} />
  if (tab === 'prices') return <Escalation tabs={tabs} />
  if (tab === 'templates') return <Templates tabs={tabs} />
  if (tab === 'parts') {
    return <ListPage key="parts" title="Stammdaten · Zukaufteile" subtitle="Einlegeteile, Buchsen, Dichtungen, Clips, Schrauben, Etiketten – in der Kalkulation je Artikel mit Menge auswählbar"
      path="/purchased-parts" entityLabel="Zukaufteil" fields={partFields} defaultSort="name" newDefaults={{ active: true, price_basis: 1, unit: 'Stk' }} extraActions={tabs}
      columns={[
        { key: 'part_no', label: 'Art.-Nr.', sort: 'part_no' },
        { key: 'name', label: 'Bezeichnung', sort: 'name', render: (r) => <strong>{r.name}</strong> },
        { key: 'supplier', label: 'Lieferant', sort: 'supplier', render: (r) => <>{r.supplier || '–'}{r.supplier_part_no && <><br /><small className="muted">{r.supplier_part_no}</small></>}</> },
        { key: 'price', label: 'Preis', sort: 'price', className: 'num', render: (r) => <>{num(r.price, 4)} € / {num(r.price_basis || 1)} {r.unit || 'Stk'}{r.price_valid_from && <><br /><small className="muted">ab {new Date(r.price_valid_from).toLocaleDateString('de-DE')}</small></>}</> },
        { key: 'per_piece', label: '€ je Einheit', className: 'num', render: (r) => num(r.price / (r.price_basis || 1), 4) },
        { key: 'moq', label: 'MOQ', className: 'num', render: (r) => (r.moq ? num(r.moq) : '–') },
        { key: 'lead_time_days', label: 'WBZ', className: 'num', render: (r) => (r.lead_time_days ? `${r.lead_time_days} T.` : '–') },
        { key: 'co2_kg_per_piece', label: 'kg CO₂e', className: 'num', render: (r) => (r.co2_kg_per_piece != null ? num(r.co2_kg_per_piece, 4) : '–') },
        { key: 'active', label: 'Status', render: (r) => (r.active ? <Badge tone="good">aktiv</Badge> : <Badge>inaktiv</Badge>) },
      ]} />
  }
  if (tab === 'materials') {
    return <ListPage key="mat" title="Stammdaten · Materialien" subtitle="Preise werden in der Kalkulation vorbelegt und sind dort überschreibbar"
      path="/materials" entityLabel="Material" fields={materialFields} defaultSort="name" newDefaults={{ active: true }} extraActions={tabs}
      columns={[
        { key: 'name', label: 'Material', sort: 'name', render: (r) => <strong>{r.name}</strong> },
        { key: 'family', label: 'Gruppe', sort: 'family' },
        { key: 'supplier', label: 'Lieferant' },
        { key: 'price_per_kg', label: '€/kg', sort: 'price_per_kg', className: 'num', render: (r) => <>{num2(r.price_per_kg)}{r.price_valid_from && <><br /><small className="muted">ab {new Date(r.price_valid_from).toLocaleDateString('de-DE')}</small></>}</> },
        { key: 'density', label: 'Dichte', className: 'num', render: (r) => (r.density ? num(r.density, 2) : '–') },
        { key: 'co2_kg_per_kg', label: 'kg CO₂e/kg', className: 'num', render: (r) => (r.co2_kg_per_kg != null ? num(r.co2_kg_per_kg, 2) : '–') },
        { key: 'active', label: 'Status', render: (r) => (r.active ? <Badge tone="good">aktiv</Badge> : <Badge>inaktiv</Badge>) },
      ]} />
  }
  return <ListPage key="mach" title="Stammdaten · Maschinen & Anlagen" subtitle="Spritzgießmaschinen, Montagelinien, Nachbearbeitung und Prüfstationen – Stundensätze, Instandhaltung, Produktivität"
    path="/machines" entityLabel="Maschine" fields={machineFields} defaultSort="number"
    filters={[{ name: 'kind', label: 'Art', options: MACHINE_KINDS.map((k) => ({ ...k, label: machineKindLabel(k.value) })) }]}
    newDefaults={{ active: true, kind: 'spritzguss', productivity_pct: 85, operator_factor: 0.3, available_hours_year: 6000, base_load_pct: 0, base_load_decline_pct: 0 }} extraActions={tabs}
    columns={[
      { key: 'number', label: 'Nr.', sort: 'number' },
      { key: 'name', label: 'Maschine / Anlage', sort: 'name', render: (r) => <><strong>{r.name}</strong><br /><small className="muted">{machineKindLabel(r.kind)}</small></> },
      { key: 'clamping_force_t', label: 'Schließkraft', sort: 'clamping_force_t', className: 'num', render: (r) => (r.clamping_force_t ? `${num(r.clamping_force_t)} t` : '–') },
      { key: 'hourly_rate', label: '€/h Maschine', sort: 'hourly_rate', className: 'num', render: (r) => num2(r.hourly_rate) },
      { key: 'maintenance_rate', label: '€/h Instandh.', className: 'num', render: (r) => num2(r.maintenance_rate) },
      { key: 'productivity_pct', label: 'Produktivität', className: 'num', render: (r) => `${num(r.productivity_pct, 1)} %` },
      { key: 'operator_factor', label: 'Personal', className: 'num', render: (r) => <>{num((r.operator_factor || 0) * 100, 0)} % Bed.{r.handling_pct ? <><br /><small className="muted">{num(r.handling_pct, 0)} % Handling</small></> : null}{r.automation_pct ? <><br /><small className="muted">{num(r.automation_pct, 0)} % Autom.</small></> : null}</> },
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
