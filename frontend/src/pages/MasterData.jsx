import { useEffect, useState } from 'react'
import { api } from '../api'
import { resetThresholds } from '../components/BigProject'
import { Escalation, MachineRates, Templates } from './MasterExtras'
import { useAuth } from '../auth'
import ImportButton from '../components/ImportButton'
import ListPage from '../components/ListPage'
import { Badge, EntityForm, ErrorBox, Modal } from '../components/ui'
import { MACHINE_KINDS, machineKindLabel, num, num2 } from '../constants'
import NumInput from '../components/NumInput'

const machineFields = [
  { name: 'number', label: 'Maschinen-Nr.' },
  { name: 'name', label: 'Bezeichnung', required: true },
  { name: 'kind', label: 'Art', type: 'select', required: true, options: MACHINE_KINDS, hint: 'Montagelinien, Prüfstationen u. a. werden in der Kalkulation als weitere Arbeitsgänge gewählt' },
  { name: 'clamping_force_t', label: 'Schließkraft (t)', type: 'number', step: 'any' },
  { name: 'location', label: 'Halle / Bereich' },
  { name: 'hourly_rate', label: 'Maschinenstundensatz €/h (ohne Personal)', type: 'number', step: 'any', required: true },
  { name: 'maintenance_rate', label: 'Instandhaltung €/h', type: 'number', step: 'any' },
  { name: 'productivity_pct', label: 'Standard-Produktivität %', type: 'number', step: 'any' },
  { name: 'operator_factor', label: 'Standard-Anteil Bediener %', type: 'number', step: 'any', scale: 100, hint: '30 = ein Bediener für ca. 3 Maschinen, 100 = fest an der Maschine, 120 = mit Springer' },
  { name: 'handling_pct', label: 'Standard-Anteil Handling %', type: 'number', step: 'any', hint: '0 … 100' },
  { name: 'automation_pct', label: 'Standard-Anteil Automatisierung %', type: 'number', step: 'any', hint: '0 … 100, z. B. bei Roboterzelle' },
  { name: 'status', label: 'Bestand / Planung', type: 'select', required: true, options: [{ value: 'bestand', label: 'Bestandsmaschine (vorhanden)' }, { value: 'geplant', label: 'Planmaschine / Neuanlage (nur für Kalkulation)' }], hint: 'Planmaschinen erscheinen in der Kalkulation, aber nicht in der Auslastung des Bestands' },
  { name: 'shifts', label: 'Schichtmodell', type: 'select', options: [{ value: '1', label: '1 Schicht · 8 h × 240 Tage = 1.920 h' }, { value: '2', label: '2 Schichten · 16 h × 240 Tage = 3.840 h' }, { value: '3', label: '3 Schichten · 24 h × 240 Tage = 5.760 h' }], hint: 'setzt die verfügbaren Stunden; leer = Stunden frei eingeben' },
  { name: 'available_hours_year', label: 'Verfügbare Stunden / Jahr', type: 'number', step: 'any', hint: 'wird bei gewähltem Schichtmodell automatisch berechnet' },
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
  { name: 'number', label: 'Material-Nr. F&R', hint: 'z. B. RM05930 – für Preisliste und Import' },
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
    ['setup_time_h', 'Rüstzeit je Los', 'min', 60], ['setup_persons', 'Einrichter je Rüstvorgang', 'Pers.'], ['startup_scrap_pcs', 'Anfahrausschuss je Los', 'Stk']]],
  ['CO₂-Fußabdruck', [['co2_grid_kg_kwh', 'Strom-Emissionsfaktor', 'kg CO₂e/kWh'], ['co2_scope1_kg_h', 'Werksemissionen Scope 1', 'kg CO₂e/Masch.-h'],
    ['co2_masterbatch_kg_kg', 'Masterbatch', 'kg CO₂e/kg'], ['co2_transport_kg_tkm', 'Lkw-Transport', 'kg CO₂e/tkm']]],
  ['Stundensatz & Preisgleitung', [['space_cost_m2_year', 'Raumkosten', '€/m² · Jahr'], ['energy_price_kwh', 'Strompreis', '€/kWh'], ['machine_rate_pct', 'Faktor Maschinenstundensatz (Standort ohne eigene Maschine)', '%'], ['escalation_threshold_pct', 'Preisgleitklausel ab Änderung', '± %']]],
  ['Großprojekte (Hervorhebung)', [['big_revenue_threshold', 'Ab Jahresumsatz', '€'], ['big_invest_threshold', 'Ab Invest (Einmalkosten)', '€']]],
  ['Nachkalkulation (Ampel)', [['nk_green_pct', 'Grün bis Abweichung Selbstkosten', '%'], ['nk_red_pct', 'Rot ab Abweichung Selbstkosten', '%']]],
]

// Parameter, die je Standort abweichen dürfen (wie SITE_KEYS im Backend)
const SITE_KEYS = ['labor_rate_h', 'setup_rate_h', 'assembly_rate_h', 'handling_rate_h', 'automation_rate_h', 'mgk_pct', 'fgk_pct',
  'scrap_pct', 'vwgk_pct', 'vtgk_pct', 'pm_pct', 'quality_pct', 'toolshop_pct', 'profit_pct', 'cash_discount_pct', 'rebate_pct',
  'productivity_pct', 'assembly_productivity_pct', 'setup_time_h', 'setup_persons', 'startup_scrap_pcs', 'co2_grid_kg_kwh',
  'co2_scope1_kg_h', 'co2_masterbatch_kg_kg', 'co2_transport_kg_tkm', 'purchased_mgk_pct', 'side_mgk_pct', 'side_quality_pct',
  'side_scrap_pct', 'side_markup_pct', 'energy_price_kwh', 'pack_pct', 'transport_pct', 'machine_rate_pct']
const siteFields = [
  { name: 'code', label: 'Kürzel', required: true }, { name: 'name', label: 'Name', required: true },
  { name: 'country', label: 'Land' }, { name: 'address', label: 'Anschrift' },
  { name: 'sort', label: 'Reihenfolge', type: 'number', step: '1' }, { name: 'active', label: 'Aktiv', type: 'checkbox' },
]

function Sites({ tabs, onChange }) {
  const { isAdmin } = useAuth()
  const [sites, setSites] = useState(null)
  const [group, setGroup] = useState({})
  const [draft, setDraft] = useState({})
  const [edit, setEdit] = useState(null)
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const load = () => api.get('/sites?limit=50&sort=sort').then((x) => {
    setSites(x.items)
    setDraft(Object.fromEntries(x.items.map((st) => [st.id, { ...(st.settings || {}) }])))
    onChange?.(x.items)
  })
  useEffect(() => { load(); api.get('/calc/settings').then(setGroup) }, [])
  if (!sites) return <div className="loading">Lade…</div>
  const setVal = (sid, k, v) => { setMsg(null); setDraft((d) => ({ ...d, [sid]: { ...d[sid], [k]: v === '' ? null : Number(v) } })) }
  async function saveAll() {
    setErr(null)
    try {
      for (const st of sites) {
        const clean = Object.fromEntries(Object.entries(draft[st.id] || {}).filter(([, v]) => v !== null && v !== '' && !Number.isNaN(v)))
        // eslint-disable-next-line no-await-in-loop
        await api.put(`/sites/${st.id}`, { settings: clean })
      }
      setMsg('Standort-Sätze gespeichert – gelten für neue Kalkulationen und Standortwechsel/-vergleich.')
      load()
    } catch (e) { setErr(e) }
  }
  const groups = PARAMS.map(([t, rows]) => [t, rows.filter(([k]) => SITE_KEYS.includes(k))]).filter(([, rows]) => rows.length)
  const norm = (o) => JSON.stringify(Object.entries(o || {}).filter(([, v]) => v !== null && v !== '').sort())
  const matrixDirty = sites.some((st) => norm(draft[st.id]) !== norm(st.settings))
  return (
    <div className="page">
      <div className="page-head">
        <div><h1>Stammdaten · Standorte</h1><p className="muted">Standorte der Gruppe mit abweichenden Sätzen. Leeres Feld = Gruppen-Parameter gilt.</p></div>
        <div className="toolbar">{tabs}</div>
      </div>
      {msg && <div className="ok-box">{msg}</div>}<ErrorBox error={err} />
      <div className="card card-flush">
        <table className="table">
          <thead><tr><th>Kürzel</th><th>Standort</th><th>Land</th><th>Anschrift</th><th className="num">abweichende Sätze</th><th>Status</th><th /></tr></thead>
          <tbody>{sites.map((st) => (
            <tr key={st.id}><td>{st.code}</td><td><strong>{st.name}</strong></td><td>{st.country || '–'}</td><td>{st.address || '–'}</td>
              <td className="num">{Object.keys(st.settings || {}).length}</td>
              <td>{st.active ? <Badge tone="good">aktiv</Badge> : <Badge>inaktiv</Badge>}</td>
              <td>{isAdmin && <button className="btn btn-ghost btn-sm" onClick={() => setEdit(st)}>Bearbeiten</button>}</td></tr>))}</tbody>
        </table>
        {isAdmin && <div style={{ padding: 12 }}><button className="btn btn-ghost btn-sm" onClick={() => setEdit({ active: true, sort: sites.length })}>+ Standort</button></div>}
      </div>
      <div className="card">
        <div className={`section-head version-bar-sticky ${matrixDirty ? 'is-dirty' : ''}`}><h3>Sätze je Standort</h3>
          {matrixDirty && <span className="badge badge-info">ungespeicherte Änderungen – erst nach „Speichern“ wirksam</span>}
          {isAdmin && <button className="btn btn-primary" disabled={!matrixDirty} onClick={saveAll}>Speichern</button>}</div>
        <div className="table-wrap"><table className="table table-compact site-matrix">
          <thead><tr><th>Parameter</th><th className="num">Gruppe (Standard)</th>{sites.map((st) => <th key={st.id} className="num">{st.name}</th>)}</tr></thead>
          <tbody>{groups.map(([t, rows]) => [
            <tr key={t} className="group-row"><td colSpan={2 + sites.length}><b>{t}</b></td></tr>,
            ...rows.map(([k, l, u, sc = 1]) => (
              <tr key={k}><td>{l} <span className="muted small">{u}</span></td><td className="num muted">{group[k] != null ? Math.round(group[k] * sc * 1e6) / 1e6 : '–'}</td>
                {sites.map((st) => {
                  const v = draft[st.id]?.[k]
                  return <td key={st.id} className="num"><NumInput type="number" step="any" className={`num ${v != null ? 'site-over' : ''}`} disabled={!isAdmin}
                    value={v == null ? '' : Math.round(v * sc * 1e6) / 1e6} placeholder={group[k] != null ? String(Math.round(group[k] * sc * 1e6) / 1e6) : ''}
                    onChange={(e) => setVal(st.id, k, e.target.value === '' ? '' : Number(e.target.value) / sc)} /></td>
                })}</tr>)),
          ])}</tbody>
        </table></div>
        <small className="hint">Blau hinterlegte Felder weichen vom Gruppen-Standard ab. Maschinenstundensätze stehen je Maschine (Reiter „Maschinen & Anlagen“, Feld Standort).</small>
      </div>
      {edit && <Modal title={edit.id ? `Standort ${edit.name}` : 'Neuer Standort'} onClose={() => setEdit(null)}>
        <EntityForm fields={siteFields} initial={edit} onCancel={() => setEdit(null)}
          onSubmit={async (v) => { if (edit.id) await api.put(`/sites/${edit.id}`, v); else await api.post('/sites', { ...v, settings: {} }); setEdit(null); load() }} />
      </Modal>}
    </div>
  )
}

export default function MasterData() {
  const { user } = useAuth()
  const [tab, setTab] = useState('machines')
  const [sites, setSites] = useState([])
  const [rev, setRev] = useState(0)
  const bump = () => setRev((x) => x + 1)
  useEffect(() => { api.get('/sites?limit=50&sort=sort').then((x) => setSites(x.items)).catch(() => {}) }, [])
  const siteOpts = sites.map((x) => ({ value: x.id, label: x.name }))
  const siteName = (id) => sites.find((x) => x.id === id)?.name
  const tabs = <div className="seg">
    {[['machines', 'Maschinen & Anlagen'], ['sites', 'Standorte'], ['rates', 'Stundensätze'], ['materials', 'Materialien'], ['parts', 'Zukaufteile'], ['prices', 'Preisgleitung'], ['templates', 'Vorlagen'], ['params', 'Parameter']].map(([k, l]) =>
      <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>)}
  </div>
  if (tab === 'params') return <Params tabs={tabs} />
  if (tab === 'sites') return <Sites tabs={tabs} onChange={setSites} />
  if (tab === 'rates') return <MachineRates tabs={tabs} />
  if (tab === 'prices') return <Escalation tabs={tabs} />
  if (tab === 'templates') return <Templates tabs={tabs} />
  if (tab === 'parts') {
    return <ListPage key={`parts-${rev}`} title="Stammdaten · Zukaufteile" subtitle="Einlegeteile, Buchsen, Dichtungen, Clips, Schrauben, Etiketten – in der Kalkulation je Artikel mit Menge auswählbar"
      path="/purchased-parts" entityLabel="Zukaufteil" fields={partFields} defaultSort="name" newDefaults={{ active: true, price_basis: 1, unit: 'Stk' }} extraActions={<>{tabs}<ImportButton entity="purchased-parts" label="Zukaufteile" adminOnly onDone={bump} /></>}
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
    return <ListPage key={`mat-${rev}`} title="Stammdaten · Materialien" subtitle="Preise werden in der Kalkulation vorbelegt und sind dort überschreibbar"
      path="/materials" entityLabel="Material" fields={materialFields} defaultSort="name" newDefaults={{ active: true }} extraActions={<>{tabs}<ImportButton entity="materials" label="Materialien" adminOnly onDone={bump} /></>}
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
  return <ListPage key={`mach-${rev}`} title="Stammdaten · Maschinen & Anlagen" subtitle="Spritzgießmaschinen, Montagelinien, Nachbearbeitung und Prüfstationen – Stundensätze, Instandhaltung, Produktivität"
    path="/machines" entityLabel="Maschine" defaultSort="number"
    fields={[...machineFields.slice(0, 3), { name: 'site_id', label: 'Standort', type: 'select', options: siteOpts, hint: 'Sätze und Auslastung je Standort' }, ...machineFields.slice(3)]}
    filters={[{ name: 'kind', label: 'Art', options: MACHINE_KINDS.map((k) => ({ ...k, label: machineKindLabel(k.value) })) },
      ...(siteOpts.length ? [{ name: 'site_id', label: 'Standort', options: siteOpts }] : [])]}
    toForm={(r) => ({ ...r, shifts: r.shifts ? String(r.shifts) : '' })}
    customDelete={async (m) => {
      // REV01-M01/M03: nicht löschbar, wenn in offener Kalkulation; Löschen im Vier-Augen-Prinzip
      try {
        const u = await api.get(`/machines/${m.id}/usage`)
        if (u.open.length) { window.alert(`Die Maschine wird in offenen Kalkulationen verwendet (${u.open.join(', ')}).\nBitte stattdessen deaktivieren („Aktiv“ abwählen).`); return false }
        if (!m.delete_requested_by) {
          if (!window.confirm('Löschantrag stellen? Ein zweiter Administrator muss die Löschung bestätigen (Vier-Augen-Prinzip).')) return false
          await api.post(`/machines/${m.id}/delete-request`); window.alert('Löschantrag gestellt.'); return true
        }
        if (m.delete_requested_by === user?.id) {
          if (window.confirm('Sie haben den Löschantrag gestellt – ein anderer Administrator muss bestätigen. Antrag zurückziehen?')) { await api.post(`/machines/${m.id}/delete-request?cancel=true`); return true }
          return false
        }
        if (!window.confirm(`Löschung bestätigen? ${u.all.length ? `Die Maschine steht in abgeschlossenen Kalkulationen (${u.all.join(', ')}) – diese behalten ihre gespeicherten Werte.` : ''} Das kann nicht rückgängig gemacht werden.`)) return false
        await api.del(`/machines/${m.id}`); return true
      } catch (e) { window.alert(e.message || String(e)); return false }
    }}
    newDefaults={{ active: true, status: 'bestand', kind: 'spritzguss', productivity_pct: 85, operator_factor: 0.3, available_hours_year: 6000, base_load_pct: 0, base_load_decline_pct: 0 }} extraActions={<>{tabs}<ImportButton entity="machines" label="Maschinen" adminOnly onDone={bump} /></>}
    columns={[
      { key: 'number', label: 'Nr.', sort: 'number' },
      { key: 'name', label: 'Maschine / Anlage', sort: 'name', render: (r) => <><strong>{r.name}</strong><br /><small className="muted">{machineKindLabel(r.kind)}</small>
        {r.status === 'geplant' && <> <Badge tone="info">Planmaschine</Badge></>}{r.delete_requested_by && <> <Badge tone="critical">Löschantrag</Badge></>}</> },
      { key: 'clamping_force_t', label: 'Schließkraft', sort: 'clamping_force_t', className: 'num', render: (r) => (r.clamping_force_t ? `${num(r.clamping_force_t)} t` : '–') },
      { key: 'hourly_rate', label: '€/h Maschine', sort: 'hourly_rate', className: 'num', render: (r) => num2(r.hourly_rate) },
      { key: 'maintenance_rate', label: '€/h Instandh.', className: 'num', render: (r) => num2(r.maintenance_rate) },
      { key: 'productivity_pct', label: 'Produktivität', className: 'num', render: (r) => `${num(r.productivity_pct, 1)} %` },
      { key: 'operator_factor', label: 'Personal', className: 'num', render: (r) => <>{num((r.operator_factor || 0) * 100, 0)} % Bed.{r.handling_pct ? <><br /><small className="muted">{num(r.handling_pct, 0)} % Handling</small></> : null}{r.automation_pct ? <><br /><small className="muted">{num(r.automation_pct, 0)} % Autom.</small></> : null}</> },
      { key: 'available_hours_year', label: 'h/Jahr', className: 'num', render: (r) => <>{num(r.available_hours_year)}{r.shifts ? <><br /><small className="muted">{r.shifts}-schichtig</small></> : null}</> },
      { key: 'base_load_pct', label: 'Grundlast', className: 'num', render: (r) => `${num(r.base_load_pct, 0)} % (−${num(r.base_load_decline_pct, 0)} %/J.)` },
      { key: 'power_kw', label: 'kW', className: 'num', render: (r) => (r.power_kw != null ? num(r.power_kw, 1) : '–') },
      { key: 'site_id', label: 'Standort', render: (r) => siteName(r.site_id) || r.location || '–' },
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
                {fields.map(([k, l, u, sc = 1]) => (
                  <div key={k} className="field"><label>{l} <span className="unit">{u}</span></label>
                    <NumInput type="number" step="any" className="num" value={vals[k] === '' || vals[k] == null ? '' : Math.round(vals[k] * sc * 1e6) / 1e6}
                      onChange={(e) => { setMsg(null); setVals({ ...vals, [k]: e.target.value === '' ? '' : Number(e.target.value) / sc }) }} /></div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </fieldset>
    </div>
  )
}
