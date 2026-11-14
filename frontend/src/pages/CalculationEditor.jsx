import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Badge, confirmDelete, EntityForm, ErrorBox } from '../components/ui'
import {
  CALC_STATUS, calcStatus, CLOSE_REASONS, eur, eur4, feasibility, FEASIBILITY, fix4, NO_BID_REASONS, noBidLabel, CLOSED_STATUS, fmtDate, fmtDateTime, INPUT_LABELS, num, num2, reasonLabel,
} from '../constants'
import { Light } from './Calculations'
import PostCalcTab from './PostCalcTab'
import ArticleAnalysis from './ArticleAnalysis'
import LifecycleTab from './LifecycleTab'
import ApprovalBar from '../components/Approval'
import AuditTable from '../components/AuditTable'
import Attachments from '../components/Attachments'
import CallPanel, { LastCall } from '../components/CallPanel'
import { BigBadge } from '../components/BigProject'

export const calcMetaFields = [
  { name: 'article_name', label: 'Artikelbezeichnung', required: true, span: true },
  { name: 'customer_article_no', label: 'Artikelnummer Kunde' },
  { name: 'own_article_no', label: 'Eigene Artikelnummer' },
  { name: 'account_id', label: 'Kunde', type: 'account' },
  { name: 'contact_id', label: 'Ansprechpartner Kunde', type: 'contact', dependsOn: 'account_id' },
  { name: 'opportunity_id', label: 'Verkaufschance (Projekt)', type: 'opportunity', dependsOn: 'account_id' },
  { name: 'owner_id', label: 'Verantwortlich', type: 'user' },
  { name: 'status', label: 'Status', type: 'select', required: true, options: CALC_STATUS },
  { name: 'probability', label: 'Wahrscheinlichkeit Auftrag %', type: 'number', min: 0, max: 100, hint: 'Wird beim Statuswechsel vorgeschlagen, frei änderbar' },
  { name: 'close_reason', label: 'Grund bei Verlust', type: 'select', options: CLOSE_REASONS, hint: 'nur bei Status „Verloren“' },
  { name: 'no_bid_reason', label: 'Grund „Kein Angebot“', type: 'select', options: NO_BID_REASONS, hint: 'nur bei Status „Kein Angebot abgegeben“' },
  { name: 'no_bid_note', label: 'Erläuterung (Freitext)', hint: 'z. B. bei „Sonstiges“' },
  { name: 'feasibility', label: 'Machbarkeit', type: 'select', options: FEASIBILITY, hint: 'Vorschlag siehe Reiter Artikelanalyse' },
  { name: 'feasibility_note', label: 'Machbarkeit – Anmerkung' },
  { name: 'inquiry_date', label: 'Anfrage vom', type: 'date' },
  { name: 'due_date', label: 'Angebotsabgabe bis', type: 'date' },
  { name: 'sop_date', label: 'Serienstart (SOP)', type: 'date' },
  { name: 'last_call_at', label: 'Zuletzt angerufen', type: 'datetime' },
  { name: 'sync_opportunity', label: 'Umsatz automatisch in Verkaufschance übernehmen', type: 'checkbox', span: true },
  { name: 'remark', label: 'Bemerkung', type: 'textarea', span: true, rows: 3 },
]

const TABS = [['calc', 'Kalkulation'], ['analysis', 'Artikelanalyse'], ['lifecycle', 'Lebensweg'], ['docs', 'Dokumente'], ['calls', 'Anrufe'], ['meta', 'Anfrage & Status'], ['versions', 'Versionen'], ['post', 'Nachkalkulation'], ['audit', 'Protokoll']]

export default function CalculationEditor() {
  const { id } = useParams()
  const nav = useNavigate()
  const { canWrite } = useAuth()
  const [calc, setCalc] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('calc')
  const [master, setMaster] = useState({ machines: [], materials: [], parts: [], settings: {} })

  useEffect(() => {
    Promise.all([api.get('/machines?limit=500&active=true'), api.get('/materials?limit=500&active=true'), api.get('/calc/settings'),
      api.get('/purchased-parts?limit=500&active=true')])
      .then(([m, mat, st, pp]) => setMaster({ machines: m.items, materials: mat.items, settings: st, parts: pp.items }))
  }, [])
  useEffect(() => {
    if (id === 'neu') return
    api.get(`/calculations/${id}`).then(setCalc).catch(setError)
  }, [id])

  if (id === 'neu') {
    return <NewCalc />
  }
  if (error) return <ErrorBox error={error} />
  if (!calc) return <div className="loading">Lade Kalkulation…</div>

  const st = calcStatus(calc.status)
  async function remove() {
    if (await confirmDelete(`Kalkulation ${calc.number} mit allen Versionen`, () => api.del(`/calculations/${calc.id}`))) nav('/kalkulationen')
  }
  return (
    <div className="page page-wide">
      <Link to="/kalkulationen" className="back no-print">‹ Alle Kalkulationen</Link>
      <header className="page-head">
        <div>
          <h1>{calc.number} · {calc.article_name} <Badge tone={st.tone}>{st.label}</Badge>
            {calc.last_traffic_light && <Light value={calc.last_traffic_light} />}
            <BigBadge revenue={calc.annual_revenue} invest={calc.invest} />
            {feasibility(calc.feasibility) && <Badge tone={feasibility(calc.feasibility).tone}>⚙ {feasibility(calc.feasibility).label}</Badge>}</h1>
          <p className="muted">
            {calc.account ? <Link to={`/firmen/${calc.account.id}`}>{calc.account.name}</Link> : 'kein Kunde'}
            {calc.customer_article_no && ` · Kd.-Art.-Nr. ${calc.customer_article_no}`}
            {` · Version ${calc.current_version} · ${calc.probability} % Wahrscheinlichkeit`}
            {calc.close_reason && ` · ${reasonLabel(calc.close_reason)}`}
            {calc.no_bid_reason && ` · Kein Angebot: ${noBidLabel(calc.no_bid_reason)}${calc.no_bid_note ? ` (${calc.no_bid_note})` : ''}`}
            {calc.opportunity && <> · Chance: <Link to="/pipeline">{calc.opportunity.name}</Link></>}
          </p>
          <div className="lastcall-head">
            <span className="muted small">Zuletzt angerufen:</span>
            <LastCall call={calc.last_call} date={calc.last_call_at} onClick={() => setTab('calls')}
              open={!CLOSED_STATUS.includes(calc.status)} />
            {calc.last_call?.note && <span className="lastcall-note">„{calc.last_call.note}“</span>}
          </div>
          <QuoteLinks calc={calc} />
        </div>
        {canWrite && <HeaderActions calc={calc} setCalc={setCalc} onDelete={remove} onCall={() => setTab('calls')} />}
      </header>
      <ApprovalBar calc={calc} setCalc={setCalc} />
      <div className="tabs no-print">
        {TABS.map(([k, l]) => (
          <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>
            {l}{k === 'versions' && <span className="count">{calc.versions.length}</span>}
            {k === 'post' && <span className="count">{calc.post_calcs.length}</span>}
          </button>
        ))}
      </div>
      {tab === 'calc' && <CalcTab calc={calc} setCalc={setCalc} master={master} />}
      {tab === 'meta' && (
        <div className="card card-flush" style={{ maxWidth: 820 }}>
          <EntityForm fields={calcMetaFields} initial={calc} submitLabel="Speichern"
            onSubmit={async (v) => { setCalc(await api.patch(`/calculations/${calc.id}`, v)); setTab('calc') }}
            onCancel={() => setTab('calc')} />
        </div>
      )}
      {tab === 'calls' && <CallPanel calc={calc} onChange={setCalc} />}
      {tab === 'analysis' && <ArticleAnalysis calc={calc} setCalc={setCalc} />}
      {tab === 'lifecycle' && <LifecycleTab calc={calc} setCalc={setCalc} />}
      {tab === 'docs' && <div style={{ maxWidth: 1100 }}><Attachments entity="calculations" entityId={calc.id} title="Dokumente zur Kalkulation (Zeichnung, 3D, Anfrage, Lastenheft …)" /></div>}
      {tab === 'audit' && <CalcAudit calc={calc} />}
      {tab === 'versions' && <VersionsTab calc={calc} />}
      {tab === 'post' && <PostCalcTab calc={calc} setCalc={setCalc} />}
    </div>
  )
}

function QuoteLinks({ calc }) {
  const [rows, setRows] = useState([])
  useEffect(() => { api.get(`/calculations/${calc.id}/quotes`).then(setRows).catch(() => {}) }, [calc.id, calc.status])
  if (!rows.length) return null
  return (
    <div className="lastcall-head">
      <span className="muted small">Angebote:</span>
      {rows.map((q) => (
        <Link key={q.id} to={`/angebote/${q.id}`} className="small">{q.number}{q.articles > 1 ? ` (Sammelangebot, ${q.articles} Artikel)` : ''}</Link>
      ))}
    </div>
  )
}

function NewCalc() {
  const nav = useNavigate()
  const [templates, setTemplates] = useState([])
  const [tpl, setTpl] = useState('')
  useEffect(() => { api.get('/calc/templates').then(setTemplates).catch(() => {}) }, [])
  return (
    <div className="page page-narrow">
      <Link to="/kalkulationen" className="back">‹ Alle Kalkulationen</Link>
      <h1>Neue Anfrage / Kalkulation</h1>
      <p className="muted">Kalkulationsnummer wird automatisch vergeben. Danach öffnet sich das Kalkulationsschema.</p>
      {templates.length > 0 && (
        <div className="card">
          <div className="field"><label>Vorlage verwenden (optional)</label>
            <select value={tpl} onChange={(e) => setTpl(e.target.value)}>
              <option value="">– ohne Vorlage (Standardwerte aus Parametern) –</option>
              {templates.map((t) => <option key={t.id} value={t.id}>{t.name} · {t.source_calc}</option>)}
            </select>
            <small className="hint">Übernimmt alle Eingaben (Maschine, Material, Zykluszeit, Zuschläge …) – danach anpassen.</small></div>
        </div>
      )}
      <div className="card card-flush">
        <EntityForm fields={calcMetaFields.filter((f) => !['close_reason', 'last_call_at', 'no_bid_reason', 'no_bid_note', 'feasibility', 'feasibility_note'].includes(f.name))}
          initial={{ status: 'anfrage', sync_opportunity: true, inquiry_date: new Date().toISOString().slice(0, 10) }}
          submitLabel="Anlegen und kalkulieren"
          onSubmit={async (v) => {
            const t = templates.find((x) => String(x.id) === tpl)
            const c = await api.post('/calculations', { ...v, inputs: t ? t.inputs : undefined })
            nav(`/kalkulationen/${c.id}`, { replace: true })
          }}
          onCancel={() => nav('/kalkulationen')} />
      </div>
    </div>
  )
}

function CalcAudit({ calc }) {
  const [rows, setRows] = useState(null)
  useEffect(() => { api.get(`/audit/ref/calculations/${calc.id}`).then(setRows) }, [calc])
  return <div className="card card-flush">{rows ? <AuditTable rows={rows} /> : <div className="loading">Lade…</div>}</div>
}

function HeaderActions({ calc, setCalc, onDelete, onCall }) {
  const { isAdmin } = useAuth()
  const nav = useNavigate()
  const [err, setErr] = useState(null)
  const [lang, setLang] = useState('de')
  return (
    <div className="toolbar no-print">
      <button className="btn btn-ghost" onClick={onCall}>☎ Anruf dokumentieren</button>
      {!calc.opportunity_id && <button className="btn btn-ghost" onClick={async () => {
        try { setCalc(await api.post(`/calculations/${calc.id}/opportunity`)) } catch (e) { setErr(e) }
      }}>→ Verkaufschance anlegen</button>}
      <button className="btn btn-ghost" onClick={async () => {
        const name = window.prompt('Artikelbezeichnung der Kopie:', `${calc.article_name} (Kopie)`)
        if (name) { const c = await api.post(`/calculations/${calc.id}/copy`, { article_name: name }); nav(`/kalkulationen/${c.id}`) }
      }}>Kopieren</button>
      <button className="btn btn-ghost" onClick={async () => {
        const name = window.prompt('Name der Vorlage (z. B. „Abdeckkappe PA6 4-fach 110 t“):', calc.article_name)
        if (name) { try { await api.post('/calc/templates', { name, calc_id: calc.id }); setErr(null); window.alert('Vorlage gespeichert.') } catch (e) { setErr(e) } }
      }}>Als Vorlage</button>
      <button className="btn btn-ghost" onClick={() => window.print()}>Drucken</button>
      <button className="btn btn-ghost" onClick={async () => {
        setErr(null)
        try { const r = await api.post(`/calculations/${calc.id}/quote?lang=${lang}`); nav(`/angebote/${r.quote_id}`) } catch (e) { setErr(e) }
      }}>→ Angebot erstellen</button>
      <select className="lang-select" value={lang} onChange={(e) => setLang(e.target.value)} title="Sprache des Angebots"><option value="de">DE</option><option value="en">EN</option></select>
      {isAdmin && <button className="btn btn-danger-ghost" onClick={onDelete}>Löschen</button>}
      <ErrorBox error={err} />
    </div>
  )
}

// ------------------------------------------------------------------ Kalkulation
function CalcTab({ calc, setCalc, master }) {
  const { canWrite } = useAuth()
  const latest = calc.versions[calc.versions.length - 1]
  const [baseNo, setBaseNo] = useState(latest.version_no)
  const base = calc.versions.find((v) => v.version_no === baseNo) || latest
  const [inputs, setInputs] = useState(() => structuredClone(base.inputs))
  const [results, setResults] = useState(base.results)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const dirty = JSON.stringify(inputs) !== JSON.stringify(base.inputs)
  const timer = useRef()

  useEffect(() => { setInputs(structuredClone(base.inputs)); setResults(base.results) }, [baseNo, calc.current_version])
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => api.post('/calc/preview', inputs).then(setResults).catch(setError), 250)
    return () => clearTimeout(timer.current)
  }, [inputs])

  const set = (k, v) => setInputs((s) => ({ ...s, [k]: v }))
  const machine = master.machines.find((m) => m.id === inputs.machine_id)
  const material = master.materials.find((m) => m.id === inputs.material_id)
  const S = master.settings
  // Standardwert je Feld (aus Stammdaten / Parametern) – Abweichungen werden markiert
  const defaults = useMemo(() => ({
    machine_rate_h: machine?.hourly_rate, maintenance_rate_h: machine?.maintenance_rate,
    productivity_pct: machine?.productivity_pct, operator_factor: machine?.operator_factor,
    material_price_kg: material?.price_per_kg,
    labor_rate_h: S.labor_rate_h, setup_rate_h: S.setup_rate_h, assembly_rate_h: S.assembly_rate_h,
    mgk_pct: S.mgk_pct, fgk_pct: S.fgk_pct, scrap_pct: S.scrap_pct, vwgk_pct: S.vwgk_pct, vtgk_pct: S.vtgk_pct,
    pm_pct: S.pm_pct, quality_pct: S.quality_pct, toolshop_pct: S.toolshop_pct, profit_pct: S.profit_pct, cash_discount_pct: S.cash_discount_pct, rebate_pct: S.rebate_pct,
    setup_time_h: S.setup_time_h, setup_persons: S.setup_persons, startup_scrap_pcs: S.startup_scrap_pcs,
    assembly_productivity_pct: S.assembly_productivity_pct,
    co2_material_kg_kg: material?.co2_kg_per_kg ?? undefined, machine_power_kw: machine?.power_kw ?? undefined,
    co2_grid_kg_kwh: machine?.grid_factor ?? S.co2_grid_kg_kwh, co2_scope1_kg_h: S.co2_scope1_kg_h,
    co2_masterbatch_kg_kg: S.co2_masterbatch_kg_kg, co2_transport_kg_tkm: S.co2_transport_kg_tkm,
    pack_pct: S.pack_pct, transport_pct: S.transport_pct,
  }), [machine, material, S])

  function pickMachine(mid) {
    const m = master.machines.find((x) => x.id === Number(mid))
    if (!m) { set('machine_id', null); return }
    setInputs((s) => ({ ...s, machine_id: m.id, machine_name: `${m.number ? m.number + ' · ' : ''}${m.name}`,
      machine_rate_h: m.hourly_rate, maintenance_rate_h: m.maintenance_rate,
      productivity_pct: m.productivity_pct, operator_factor: m.operator_factor,
      machine_power_kw: m.power_kw ?? s.machine_power_kw, co2_grid_kg_kwh: m.grid_factor ?? master.settings.co2_grid_kg_kwh ?? s.co2_grid_kg_kwh }))
  }
  function pickMaterial(mid) {
    const m = master.materials.find((x) => x.id === Number(mid))
    if (!m) { set('material_id', null); return }
    setInputs((s) => ({ ...s, material_id: m.id, material_name: m.name, material_price_kg: m.price_per_kg,
      co2_material_kg_kg: m.co2_kg_per_kg ?? s.co2_material_kg_kg }))
  }
  async function saveVersion() {
    setSaving(true); setError(null)
    try {
      const c = await api.post(`/calculations/${calc.id}/versions`, { inputs, change_note: note || null })
      setCalc(c); setNote(''); setBaseNo(c.current_version)
    } catch (e) { setError(e) } finally { setSaving(false) }
  }
  const F = (p) => <NumField {...p} value={inputs[p.k]} def={defaults[p.k]} onChange={(v) => set(p.k, v)} />
  const r = results || base.results

  return (
    <div className="calc-layout">
      <div className="calc-inputs">
        <div className="card version-bar no-print">
          <label className="inline-label">Basis
            <select value={baseNo} onChange={(e) => setBaseNo(Number(e.target.value))}>
              {[...calc.versions].reverse().map((v) => (
                <option key={v.version_no} value={v.version_no}>V{v.version_no} · {fmtDate(v.created_at)}{v.version_no === latest.version_no ? ' (aktuell)' : ''}</option>
              ))}
            </select>
          </label>
          {dirty ? <span className="badge badge-info">ungespeicherte Änderungen</span> : <span className="muted small">{base.change_note}</span>}
          <span className="spacer" />
          {canWrite && <>
            <input className="note-input" placeholder="Was wurde geändert? (für Versionshistorie)" value={note} onChange={(e) => setNote(e.target.value)} />
            <button className="btn btn-primary" disabled={!dirty || saving} onClick={saveVersion}>
              {saving ? 'Speichert…' : `Als Version ${latest.version_no + 1} speichern`}</button>
            {dirty && <button className="btn btn-ghost" onClick={() => setInputs(structuredClone(base.inputs))}>Verwerfen</button>}
          </>}
        </div>
        <ErrorBox error={error} />
        <fieldset disabled={!canWrite} className="calc-fieldset">
          <Section title="Mengen">
            {F({ k: 'annual_volume', label: 'Jahresmenge', unit: 'Stk', step: 1000 })}
            {F({ k: 'lot_size', label: 'Losgröße', unit: 'Stk', step: 500 })}
            {F({ k: 'project_years', label: 'Projektlaufzeit', unit: 'Jahre', step: 1 })}
            <div className="field span-3"><label>Staffelpreise – weitere Losgrößen <span className="unit">Stk (bis zu 3)</span></label>
              <div className="tier-inputs">
                {[0, 1, 2].map((n) => (
                  <input key={n} type="number" step="any" className="num" placeholder={`Staffel ${n + 1}`}
                    value={(inputs.lot_tiers || [])[n] ?? ''}
                    onChange={(e) => {
                      const t = [...(inputs.lot_tiers || [])]
                      t[n] = e.target.value === '' ? '' : Number(e.target.value)
                      set('lot_tiers', t)
                    }} />
                ))}
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => {
                  const l = Number(inputs.lot_size) || 10000
                  set('lot_tiers', [Math.round(l / 2), l * 2, l * 5])
                }}>Vorschlag ½× · 2× · 5×</button>
              </div>
              <small className="hint">Preis je Losgröße wird rechts angezeigt und ins Angebot übernommen.</small>
            </div>
            <div className="field span-3"><label>Staffelpreise – Jahresmengen <span className="unit">Stk/Jahr (bis zu 3)</span></label>
              <div className="tier-inputs">
                {[0, 1, 2].map((n) => (
                  <input key={n} type="number" step="any" className="num" placeholder={`Menge ${n + 1}`}
                    value={(inputs.volume_tiers || [])[n] ?? ''}
                    onChange={(e) => {
                      const t = [...(inputs.volume_tiers || [])]
                      t[n] = e.target.value === '' ? '' : Number(e.target.value)
                      set('volume_tiers', t)
                    }} />
                ))}
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => {
                  const v = Number(inputs.annual_volume) || 100000
                  set('volume_tiers', [Math.round(v / 2), v * 2, v * 3])
                }}>Vorschlag ½× · 2× · 3×</button>
              </div>
              <small className="hint">Gleiche Abrufhäufigkeit: Lose pro Jahr bleiben gleich, die Losgröße wächst mit der Menge.</small>
            </div>
          </Section>

          <Section title="Material">
            <div className="field span-2"><label>Material (Stammdaten)</label>
              <select value={inputs.material_id ?? ''} onChange={(e) => pickMaterial(e.target.value)}>
                <option value="">– frei / manuell –</option>
                {master.materials.map((m) => <option key={m.id} value={m.id}>{m.name} · {num2(m.price_per_kg)} €/kg</option>)}
              </select></div>
            {F({ k: 'material_price_kg', label: 'Materialpreis', unit: '€/kg', step: 0.05 })}
            {F({ k: 'part_weight_g', label: 'Teilgewicht', unit: 'g', step: 0.1 })}
            {F({ k: 'sprue_weight_g', label: 'Anguss je Schuss', unit: 'g', step: 0.1, hint: '0 bei Heißkanal' })}
            {F({ k: 'regrind_pct', label: 'Mahlgut-Rückführung Anguss', unit: '%' })}
            {F({ k: 'masterbatch_pct', label: 'Masterbatch-Anteil', unit: '%', step: 0.5 })}
            {F({ k: 'masterbatch_price_kg', label: 'Masterbatch-Preis', unit: '€/kg', step: 0.1 })}
            <ComponentsEditor rows={inputs.components || []} materials={master.materials} onChange={(v) => set('components', v)} result={r} />
            <PurchasedEditor rows={inputs.purchased_items || []} parts={master.parts} onChange={(v) => set('purchased_items', v)} result={r} />
            {F({ k: 'purchased_parts', label: 'Sonstige Zukaufteile pauschal je Stück', unit: '€', step: 0.01, hint: 'zusätzlich zur Liste, z. B. Kleinteile ohne Stammdaten' })}
            <Info>Gewicht je Stück inkl. Angussanteil: <b>{num(r.kg_per_piece * 1000, 2)} g</b> · Schussgewicht {num(r.shot_weight_g, 1)} g · Material p. a. {num(r.material_kg_year)} kg</Info>
          </Section>

          <Section title="Maschine & Fertigung">
            <div className="field span-2"><label>Maschine (Stammdaten)</label>
              <select value={inputs.machine_id ?? ''} onChange={(e) => pickMachine(e.target.value)}>
                <option value="">– frei / manuell –</option>
                {master.machines.filter((m) => (m.kind || 'spritzguss') === 'spritzguss' || m.id === inputs.machine_id)
                  .map((m) => <option key={m.id} value={m.id}>{m.number} · {m.name} · {num2(m.hourly_rate)} €/h</option>)}
              </select></div>
            {F({ k: 'machine_rate_h', label: 'Maschinenstundensatz', unit: '€/h', hint: 'ohne Personal' })}
            {F({ k: 'maintenance_rate_h', label: 'Instandhaltung', unit: '€/h' })}
            {F({ k: 'cycle_time_s', label: 'Zykluszeit', unit: 's', step: 0.5 })}
            {F({ k: 'cavities', label: inputs.family_group ? 'Fachzahl dieses Artikels' : 'Fachzahl', unit: 'Kav.', step: 1 })}
            {F({ k: 'productivity_pct', label: 'Produktivität / Nutzungsgrad', unit: '%' })}
            {F({ k: 'operator_factor', label: 'Bedienfaktor', unit: 'Pers./M.', step: 0.05 })}
            {F({ k: 'labor_rate_h', label: 'Lohnsatz Bediener', unit: '€/h' })}
            {F({ k: 'family_share_pct', label: 'Familienwerkzeug: Anteil dieses Artikels', unit: '% der Maschinenzeit', step: 5, hint: '100 % = eigenes Werkzeug' })}
            <div className="field span-2"><label htmlFor="in-family_group">Familienwerkzeug / Werkzeuggruppe</label>
              <input id="in-family_group" value={inputs.family_group || ''} placeholder="z. B. WZ-4711 Familie Steuergerät (leer = kein Familienwerkzeug)" onChange={(e) => set('family_group', e.target.value)} />
              <small className="hint">Anteil z. B. nach Kavitäten oder Schussgewicht aufteilen; Summe aller Artikel der Gruppe = 100 %.</small></div>
            <Info>Ausbringung: <b>{num(r.pieces_per_hour, 0)} Stk/h</b> (theoretisch {num(r.pieces_per_hour_theoretical, 0)}) · Maschinenstunden p. a. <b>{num(r.machine_hours_year, 0)} h</b></Info>
          </Section>

          <Section title="Rüsten">
            {F({ k: 'setup_time_h', label: 'Rüstzeit je Los', unit: 'h', step: 0.25 })}
            {F({ k: 'setup_persons', label: 'Einrichter', unit: 'Pers.', step: 0.5 })}
            {F({ k: 'setup_rate_h', label: 'Lohnsatz Einrichter', unit: '€/h' })}
            {F({ k: 'startup_scrap_pcs', label: 'Anfahrausschuss je Los', unit: 'Stk', step: 10 })}
            <Info>Rüstkosten je Los: <b>{eur(r.setup_cost_per_lot)}</b> · {num(r.lots_per_year, 1)} Lose p. a.</Info>
          </Section>

          <Section title="Montage & weitere Arbeitsgänge">
            {F({ k: 'assembly_time_s', label: 'Handmontage je Stück', unit: 's', step: 0.5, hint: 'ohne Anlage; Anlagen unten als Arbeitsgang' })}
            {F({ k: 'assembly_persons', label: 'Personen', unit: 'Pers.', step: 0.5 })}
            {F({ k: 'assembly_rate_h', label: 'Lohnsatz Montage', unit: '€/h' })}
            {F({ k: 'assembly_productivity_pct', label: 'Produktivität Montage', unit: '%' })}
            <OperationsEditor rows={inputs.operations || []} machines={master.machines} labor={inputs.labor_rate_h} onChange={(v) => set('operations', v)} result={r} />
          </Section>

          <Section title="Verpackung & Transport">
            <div className="field span-3"><label>Verpackungskosten</label>
              <div className="seg mode-seg">
                <button type="button" className={inputs.pack_mode === 'prozent' ? 'on' : ''} onClick={() => setInputs((x) => ({ ...x, pack_mode: 'prozent', pack_pct: x.pack_pct || S.pack_pct }))}>Pauschal in % auf HK</button>
                <button type="button" className={inputs.pack_mode !== 'prozent' ? 'on' : ''} onClick={() => set('pack_mode', 'detail')}>Detailliert (je Verpackungseinheit)</button>
              </div></div>
            {inputs.pack_mode === 'prozent' && F({ k: 'pack_pct', label: 'Verpackung', unit: '% auf HK', step: 0.5, hint: 'wenn die genauen Verpackungskosten nicht bekannt sind' })}
            <div className="field"><label htmlFor="in-pack_type">Verpackungsart</label>
              <input id="in-pack_type" list="pack-types" value={inputs.pack_type || ''} placeholder="z. B. KLT 6280" onChange={(e) => set('pack_type', e.target.value)} />
              <datalist id="pack-types">{['KLT 4280 Mehrweg', 'KLT 6280 Mehrweg', 'Karton Einweg', 'Gitterbox mit Zwischenlagen', 'Sonderladungsträger Kunde', 'Beutel + Karton'].map((t) => <option key={t} value={t} />)}</datalist></div>
            {F({ k: 'pack_parts_per_unit', label: 'Teile je Verpackungseinheit (VE)', unit: 'Stk', step: 1, hint: inputs.pack_mode === 'prozent' ? 'optional – für Paletten, Lieferung und CO₂' : undefined })}
            {inputs.pack_mode !== 'prozent' && <>
              {F({ k: 'pack_cost_per_unit', label: inputs.pack_reusable ? 'Kosten je Umlauf (Reinigung, Miete)' : 'Kosten je VE (inkl. Zwischenlagen)', unit: '€', step: 0.05 })}
              <div className="field field-check"><label htmlFor="in-pack_reusable">Mehrweg-Verpackung</label>
                <input id="in-pack_reusable" type="checkbox" checked={!!inputs.pack_reusable} onChange={(e) => set('pack_reusable', e.target.checked)} /></div>
              {F({ k: 'pack_time_s', label: 'Packzeit je VE', unit: 's', step: 5, hint: 'bewertet mit Lohnsatz Bediener' })}
            </>}
            {F({ k: 'pack_units_per_pallet', label: 'VE je Palette', unit: 'VE', step: 1 })}
            <Info>Verpackung{inputs.pack_mode === 'prozent' ? ' (pauschal)' : ''}: <b>{fix4(r.values?.packaging)} €/Stk</b> · {eur(r.packaging_cost_year)} p. a.
              {r.packaging_units_year > 0 && <> · {num(r.packaging_units_year)} VE p. a.</>}
              {r.pieces_per_pallet > 0 && <> · {num(r.pieces_per_pallet)} Stk/Palette · {num(r.pallets_year, 1)} Paletten p. a.</>}</Info>
            <div className="field"><label htmlFor="in-incoterm">Lieferbedingung (Incoterm)</label>
              <input id="in-incoterm" list="incoterms" value={inputs.incoterm || ''} placeholder="z. B. FCA Werk, DAP Kunde" onChange={(e) => set('incoterm', e.target.value)} />
              <datalist id="incoterms">{['EXW ab Werk', 'FCA Werk', 'DAP Kunde', 'DDP Kunde', 'CPT', 'frei Haus'].map((t) => <option key={t} value={t} />)}</datalist></div>
            <div className="field"><label htmlFor="in-transport_mode">Transportkosten</label>
              <select id="in-transport_mode" value={inputs.transport_mode || 'keine'} onChange={(e) => {
                const v = e.target.value
                setInputs((x) => ({ ...x, transport_mode: v, transport_pct: v === 'prozent' && !x.transport_pct ? S.transport_pct : x.transport_pct }))
              }}>
                <option value="keine">keine (ab Werk / Kunde holt ab)</option>
                <option value="palette">€ je Palette</option>
                <option value="lieferung">€ je Lieferung</option>
                <option value="prozent">pauschal in % auf Herstellkosten</option>
              </select></div>
            {inputs.transport_mode === 'palette' && F({ k: 'transport_cost_per_pallet', label: 'Frachtkosten je Palette', unit: '€', step: 1, hint: 'Teile je VE × VE je Palette werden genutzt' })}
            {inputs.transport_mode === 'lieferung' && F({ k: 'transport_cost_per_delivery', label: 'Kosten je Lieferung', unit: '€', step: 5 })}
            {inputs.transport_mode === 'lieferung' && F({ k: 'transport_deliveries_per_year', label: 'Lieferungen pro Jahr', unit: '', step: 1 })}
            {inputs.transport_mode === 'prozent' && F({ k: 'transport_pct', label: 'Transport', unit: '% auf HK', step: 0.5, hint: 'wenn Frachtkosten nicht genau bekannt sind' })}
            {(inputs.transport_mode || 'keine') !== 'keine' && <Info>Transport: <b>{fix4(r.values?.transport)} €/Stk</b> · {eur(r.transport_cost_year)} p. a.</Info>}
          </Section>

          <Section title="CO₂-Fußabdruck">
            {F({ k: 'co2_material_kg_kg', label: 'Emissionsfaktor Material', unit: 'kg CO₂e/kg', step: 0.1, hint: 'Cradle-to-Gate, am besten Lieferanten-PCF' })}
            {F({ k: 'co2_masterbatch_kg_kg', label: 'Emissionsfaktor Masterbatch', unit: 'kg CO₂e/kg', step: 0.1 })}
            {F({ k: 'machine_power_kw', label: 'Leistungsaufnahme Maschine inkl. Peripherie', unit: 'kW', step: 1, hint: 'Mittelwert, z. B. aus Energiemessung' })}
            {F({ k: 'co2_grid_kg_kwh', label: 'Strom-Emissionsfaktor', unit: 'kg CO₂e/kWh', step: 0.01, hint: 'Stromkennzeichnung des Versorgers; Ökostrom = 0' })}
            {F({ k: 'co2_scope1_kg_h', label: 'Werksemissionen Scope 1', unit: 'kg CO₂e/Masch.-h', step: 0.1, hint: 'Heizung, Gas – anteilig je Maschinenstunde' })}
            {F({ k: 'co2_purchased_parts', label: 'Zukaufteile', unit: 'kg CO₂e/Stk', step: 0.001 })}
            {F({ k: 'co2_pack_per_unit', label: 'Verpackung je VE', unit: 'kg CO₂e', step: 0.05, hint: 'Einweg je VE, Mehrweg je Umlauf' })}
            {F({ k: 'transport_km', label: 'Transportentfernung zum Kunden', unit: 'km', step: 10, hint: '0 = ab Werk, nicht bilanziert' })}
            {F({ k: 'co2_transport_kg_tkm', label: 'Transport-Emissionsfaktor', unit: 'kg CO₂e/tkm', step: 0.01 })}
            <div className="field field-check span-3"><label htmlFor="in-co2_on_quote">CO₂-Fußabdruck im Angebot ausweisen</label>
              <input id="in-co2_on_quote" type="checkbox" checked={inputs.co2_on_quote !== false} onChange={(e) => set('co2_on_quote', e.target.checked)} /></div>
          </Section>

          <Section title="Zuschläge & Gewinn">
            {F({ k: 'mgk_pct', label: 'Materialgemeinkosten', unit: '%', step: 0.5 })}
            {F({ k: 'fgk_pct', label: 'Fertigungsgemeinkosten', unit: '%', step: 0.5 })}
            {F({ k: 'scrap_pct', label: 'Ausschuss', unit: '%', step: 0.5 })}
            {F({ k: 'vwgk_pct', label: 'Verwaltungsgemeinkosten', unit: '%', step: 0.5 })}
            {F({ k: 'vtgk_pct', label: 'Vertriebsgemeinkosten', unit: '%', step: 0.5 })}
            {F({ k: 'pm_pct', label: 'Projektmanagement', unit: '%', step: 0.5 })}
            {F({ k: 'quality_pct', label: 'Qualität', unit: '%', step: 0.5, hint: 'Prüfung, Messtechnik, QS' })}
            <BaseSelect k="quality_base" value={inputs.quality_base} onChange={(v) => set('quality_base', v)} label="Basis Qualität" />
            {F({ k: 'toolshop_pct', label: 'Werkzeugbau', unit: '%', step: 0.5, hint: 'Wartung / Instandhaltung Werkzeuge' })}
            <BaseSelect k="toolshop_base" value={inputs.toolshop_base} onChange={(v) => set('toolshop_base', v)} label="Basis Werkzeugbau" />
            {F({ k: 'profit_pct', label: 'Gewinn', unit: '%', step: 0.5 })}
            {F({ k: 'cash_discount_pct', label: 'Skonto', unit: '%', step: 0.5 })}
            {F({ k: 'rebate_pct', label: 'Rabatt', unit: '%', step: 0.5 })}
          </Section>

          <ListSection title="Zusatzpositionen" hint="Peripherie, Nacharbeit, Bedrucken, Sonderkosten … (Verpackung und Transport oben im eigenen Bereich)"
            rows={inputs.extras} onChange={(v) => set('extras', v)}
            empty={{ label: '', amount: 0, basis: 'stueck', category: 'fertigung' }}
            cols={[
              { k: 'label', label: 'Bezeichnung', w: '40%' },
              { k: 'amount', label: 'Betrag €', type: 'number' },
              { k: 'basis', label: 'je', type: 'select', options: [['stueck', 'Stück'], ['tausend', '1.000 Stk'], ['los', 'Los'], ['jahr', 'Jahr']] },
              { k: 'category', label: 'Art', type: 'select', options: [['fertigung', 'Fertigung (vor Ausschuss)'], ['vertrieb', 'Vertrieb (nach HK)']] },
            ]} />

          <ListSection title="Einmalkosten" hint="Werkzeug, Bemusterung, Prüfmittel, Vorrichtungen – separat ausgewiesen oder auf den Stückpreis umgelegt (Amortisation)"
            rows={inputs.one_time} onChange={(v) => set('one_time', v)}
            empty={{ label: '', cost: 0, price: 0, amortize: false }}
            cols={[
              { k: 'label', label: 'Bezeichnung', w: '40%' },
              { k: 'cost', label: 'Kosten €', type: 'number' },
              { k: 'price', label: 'Preis an Kunde €', type: 'number' },
              { k: 'amortize', label: 'auf Stückpreis umlegen', type: 'checkbox' },
            ]}>
            {(inputs.one_time || []).some((o) => o.amortize) && (
              <div className="form-grid form-grid-3" style={{ marginTop: 10 }}>
                {F({ k: 'amort_quantity', label: 'Amortisation über', unit: 'Stk', step: 1000, hint: `leer/0 = Jahresmenge × Laufzeit (${num((Number(inputs.annual_volume) || 0) * (Number(inputs.project_years) || 1))} Stk)` })}
                <Info>Werkzeugamortisation: <b>{fix4(r.amortization_per_piece)} €/Stk</b> ({num2(r.amortization_per_piece * 1000)} € je 1.000) · {eur(r.amortization_total)} über {num(r.amortization_quantity)} Stk · ohne Gewinnaufschlag</Info>
              </div>
            )}
          </ListSection>
        </fieldset>
      </div>

      <aside className="calc-results">
        <Results r={r} inputs={inputs} set={set} canWrite={canWrite} calc={calc} versionNo={dirty ? `V${latest.version_no + 1} (Entwurf)` : `V${base.version_no}`} />
      </aside>
    </div>
  )
}

function BaseSelect({ k, value, onChange, label }) {
  return (
    <div className="field"><label htmlFor={`in-${k}`}>{label}</label>
      <select id={`in-${k}`} value={value || (k === 'quality_base' ? 'hk' : 'fek')} onChange={(e) => onChange(e.target.value)}>
        <option value="fek">auf FEK (in den HK)</option>
        <option value="hk">auf HK (nach den HK)</option>
      </select></div>
  )
}

function Section({ title, children }) {
  return <div className="card"><h3>{title}</h3><div className="form-grid form-grid-3">{children}</div></div>
}
function Info({ children }) {
  return <div className="calc-info span-3">{children}</div>
}

function NumField({ k, label, unit, value, def, onChange, step = 'any', hint }) {
  const changed = def != null && value !== '' && value != null && Number(value) !== Number(def)
  return (
    <div className={`field ${changed ? 'field-changed' : ''}`}>
      <label htmlFor={`in-${k}`}>{label}{unit && <span className="unit"> {unit}</span>}</label>
      <input id={`in-${k}`} type="number" step={step} className="num" value={value ?? ''}
        onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))} />
      {changed
        ? <button type="button" className="std-reset" onClick={() => onChange(def)} title="Auf Standardwert zurücksetzen">≠ Standard {num(def, 4)} ↺</button>
        : hint && <small className="hint">{hint}</small>}
    </div>
  )
}

function ListSection({ title, hint, rows, onChange, cols, empty, children }) {
  const upd = (i, k, v) => onChange(rows.map((r, j) => (j === i ? { ...r, [k]: v } : r)))
  return (
    <div className="card">
      <div className="section-head"><h3>{title}</h3>
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange([...(rows || []), { ...empty }])}>+ Position</button></div>
      <p className="card-sub">{hint}</p>
      {rows?.length ? (
        <table className="table items-table">
          <thead><tr>{cols.map((c) => <th key={c.k} style={{ width: c.w }}>{c.label}</th>)}<th /></tr></thead>
          <tbody>{rows.map((row, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c.k}>{c.type === 'checkbox'
                  ? <input type="checkbox" checked={!!row[c.k]} onChange={(e) => upd(i, c.k, e.target.checked)} />
                  : c.type === 'select'
                  ? <select value={row[c.k]} onChange={(e) => upd(i, c.k, e.target.value)}>{c.options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
                  : <input type={c.type || 'text'} step="any" className={c.type === 'number' ? 'num' : ''} value={row[c.k] ?? ''}
                    onChange={(e) => upd(i, c.k, c.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)} />}
                </td>))}
              <td><button type="button" className="icon-btn" title="Entfernen" onClick={() => onChange(rows.filter((_, j) => j !== i))}>×</button></td>
            </tr>))}
          </tbody>
        </table>
      ) : <div className="empty small">Keine Positionen</div>}
      {children}
    </div>
  )
}

function OperationsEditor({ rows, machines, labor, onChange, result }) {
  const upd = (i, patch) => onChange(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)))
  const fromMachine = (m) => ({ machine_id: m.id, name: m.name, kind: m.kind, rate_h: m.hourly_rate, maintenance_h: m.maintenance_rate || 0,
    productivity_pct: m.productivity_pct ?? 100, operator_factor: m.operator_factor ?? 1, power_kw: m.power_kw || 0 })
  const pick = (i, id) => {
    const m = machines.find((x) => x.id === Number(id))
    upd(i, m ? fromMachine(m) : { machine_id: null })
  }
  const others = machines.filter((m) => (m.kind || 'spritzguss') !== 'spritzguss')
  const add = () => {
    const m = others[0]
    onChange([...rows, { name: 'Arbeitsgang', rate_h: 0, maintenance_h: 0, cycle_s: 10, parts_per_cycle: 1, productivity_pct: 90,
      operator_factor: 1, labor_rate_h: labor ?? 38, setup_h: 0, setup_persons: 1, power_kw: 0, ...(m ? fromMachine(m) : {}) }])
  }
  const cols = [['cycle_s', 'Takt s'], ['parts_per_cycle', 'Teile/Takt'], ['rate_h', '€/h Anlage'], ['maintenance_h', 'IH €/h'],
    ['operator_factor', 'Pers.'], ['labor_rate_h', 'Lohn €/h'], ['productivity_pct', 'Prod. %'], ['setup_h', 'Rüsten h/Los'], ['power_kw', 'kW']]
  return (
    <div className="field span-3">
      <div className="section-head"><label>Weitere Arbeitsgänge (Montagelinie, Schweißen, Bedrucken, Prüfung …)</label>
        <button type="button" className="btn btn-ghost btn-sm" onClick={add}>+ Arbeitsgang</button></div>
      {rows.length > 0 ? (
        <table className="table items-table comp-table ops-table">
          <thead><tr><th>Anlage (Stammdaten)</th><th>Bezeichnung</th><th className="num">€/Stk</th><th className="num">Stk/h</th><th className="num">h p. a.</th>{cols.map(([k, l]) => <th key={k} className="num">{l}</th>)}<th /></tr></thead>
          <tbody>{rows.map((o, i) => {
            const res = result?.operations?.[i]
            return (
              <tr key={i}>
                <td><select value={o.machine_id ?? ''} onChange={(e) => pick(i, e.target.value)}>
                  <option value="">– frei –</option>
                  {others.length > 0 && <optgroup label="Montage / Nachbearbeitung / Prüfung">{others.map((m) => <option key={m.id} value={m.id}>{m.number} · {m.name}</option>)}</optgroup>}
                  <optgroup label="Spritzgießmaschinen">{machines.filter((m) => (m.kind || 'spritzguss') === 'spritzguss').map((m) => <option key={m.id} value={m.id}>{m.number} · {m.name}</option>)}</optgroup>
                </select></td>
                <td><input value={o.name || ''} onChange={(e) => upd(i, { name: e.target.value })} /></td>
                <td className="num"><b>{fix4(res?.cost)}</b></td>
                <td className="num">{num(res?.pieces_per_hour, 0)}</td>
                <td className="num">{num(res?.hours_year, 0)}</td>
                {cols.map(([k]) => (
                  <td key={k}><input type="number" step="any" className="num" value={o[k] ?? ''} onChange={(e) => upd(i, { [k]: e.target.value === '' ? '' : Number(e.target.value) })} /></td>
                ))}
                <td><button type="button" className="icon-btn" title="Entfernen" onClick={() => onChange(rows.filter((_, j) => j !== i))}>×</button></td>
              </tr>)
          })}</tbody>
        </table>
      ) : <small className="hint">1 … N Anlagen je Artikel: Satz, Instandhaltung, Produktivität und Leistung werden aus den Stammdaten vorbelegt und sind überschreibbar. Stunden fließen in die Auslastung der Anlage.</small>}
      {rows.length > 0 && <small className="hint">Summe Arbeitsgänge: <b>{fix4(result?.operations_cost)} €/Stk</b> (vor Zuschlägen; FGK, Ausschuss usw. wirken wie bei der Spritzgießmaschine).</small>}
    </div>
  )
}

function PurchasedEditor({ rows, parts, onChange, result }) {
  const upd = (i, patch) => onChange(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)))
  const fromPart = (p) => ({ part_id: p.id, part_no: p.part_no, name: p.name, price_per_piece: Number((p.price / (p.price_basis || 1)).toFixed(6)),
    co2_kg_per_piece: p.co2_kg_per_piece ?? 0 })
  const pick = (i, id) => {
    const p = parts.find((x) => x.id === Number(id))
    upd(i, p ? fromPart(p) : { part_id: null })
  }
  return (
    <div className="field span-3">
      <div className="section-head"><label>Zukaufteile (Stammdaten)</label>
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange([...rows, { qty: 1, price_per_piece: 0, co2_kg_per_piece: 0, ...(parts[0] ? fromPart(parts[0]) : { name: 'Zukaufteil' }) }])}>+ Zukaufteil</button></div>
      {rows.length > 0 ? (
        <table className="table items-table comp-table">
          <thead><tr><th>Zukaufteil</th><th>Bezeichnung</th><th className="num">Menge je Artikel</th><th className="num">€ je Einheit</th><th className="num">kg CO₂e je Einheit</th><th className="num">€/Stk</th><th /></tr></thead>
          <tbody>{rows.map((p, i) => (
            <tr key={i}>
              <td><select value={p.part_id ?? ''} onChange={(e) => pick(i, e.target.value)}>
                <option value="">– frei –</option>{parts.map((x) => <option key={x.id} value={x.id}>{x.part_no ? `${x.part_no} · ` : ''}{x.name}</option>)}</select></td>
              <td><input value={p.name || ''} onChange={(e) => upd(i, { name: e.target.value })} /></td>
              {['qty', 'price_per_piece', 'co2_kg_per_piece'].map((k) => (
                <td key={k}><input type="number" step="any" className="num" value={p[k] ?? ''} onChange={(e) => upd(i, { [k]: e.target.value === '' ? '' : Number(e.target.value) })} /></td>
              ))}
              <td className="num"><b>{fix4(result?.purchased_items?.[i]?.cost)}</b></td>
              <td><button type="button" className="icon-btn" title="Entfernen" onClick={() => onChange(rows.filter((_, j) => j !== i))}>×</button></td>
            </tr>))}</tbody>
        </table>
      ) : <small className="hint">Einlegeteile, Buchsen, Dichtungen, Clips, Schrauben, Etiketten … aus den Stammdaten wählen; Preis je Einheit wird aus Preis ÷ Preiseinheit vorbelegt. MGK wirkt auf die Zukaufteile.</small>}
    </div>
  )
}

function ComponentsEditor({ rows, materials, onChange, result }) {
  const upd = (i, patch) => onChange(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)))
  const pick = (i, id) => {
    const m = materials.find((x) => x.id === Number(id))
    upd(i, m ? { material_id: m.id, material_name: m.name, price_kg: m.price_per_kg, co2_kg_kg: m.co2_kg_per_kg ?? 0, label: rows[i].label || m.family || m.name }
      : { material_id: null })
  }
  return (
    <div className="field span-3">
      <div className="section-head"><label>Weitere Komponenten (2K / 3K …)</label>
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange([...rows, { label: `Komponente ${String.fromCharCode(66 + rows.length)}`, part_weight_g: 0, sprue_weight_g: 0, regrind_pct: 0, price_kg: 0, co2_kg_kg: 0 }])}>+ Komponente</button></div>
      {rows.length > 0 ? (
        <table className="table items-table comp-table">
          <thead><tr><th>Bezeichnung</th><th>Material</th><th className="num">€/kg</th><th className="num">Teilgewicht g</th><th className="num">Anguss/Schuss g</th><th className="num">Mahlgut %</th><th className="num">kg CO₂e/kg</th><th className="num">€/Stk</th><th /></tr></thead>
          <tbody>{rows.map((c, i) => (
            <tr key={i}>
              <td><input value={c.label || ''} onChange={(e) => upd(i, { label: e.target.value })} /></td>
              <td><select value={c.material_id ?? ''} onChange={(e) => pick(i, e.target.value)}>
                <option value="">– frei –</option>{materials.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select></td>
              {['price_kg', 'part_weight_g', 'sprue_weight_g', 'regrind_pct', 'co2_kg_kg'].map((k) => (
                <td key={k}><input type="number" step="any" className="num" value={c[k] ?? ''} onChange={(e) => upd(i, { [k]: e.target.value === '' ? '' : Number(e.target.value) })} /></td>
              ))}
              <td className="num">{fix4(result?.components?.[i]?.cost)}</td>
              <td><button type="button" className="icon-btn" onClick={() => onChange(rows.filter((_, j) => j !== i))}>×</button></td>
            </tr>))}</tbody>
        </table>
      ) : <small className="hint">Für Mehrkomponenten-Teile weitere Materialien hinzufügen. Komponente A = Material oben.</small>}
    </div>
  )
}

function Results({ r, inputs, set, canWrite, calc, versionNo }) {
  return (
    <div className="stack">
      <div className="card result-card">
        <div className="result-head">
          <span className="muted small">{calc.number} · {versionNo}</span>
          <span className="result-price">{eur4(r.unit_price)} <small>/ Stk</small></span>
          <span className="muted">{num2(r.price_per_100)} € je 100 · <b>{num2(r.price_per_1000)} € je 1.000</b></span>
        </div>
        <div className="result-kpis">
          <div><span>Jahresumsatz</span><b>{eur(r.annual_revenue)}</b></div>
          <div><span>Gewinn p. a.</span><b className={r.annual_profit < 0 ? 'text-critical' : ''}>{eur(r.annual_profit)}</b></div>
          <div><span>Marge</span><b className={r.margin_pct < 0 ? 'text-critical' : ''}>{num(r.margin_pct, 1)} %</b></div>
          <div><span>Projektumsatz</span><b>{eur(r.project_revenue)}</b></div>
          <div><span>Einmalumsatz</span><b>{eur(r.one_time_price)}</b></div>
          <div><span>1. Jahr gesamt</span><b>{eur(r.first_year_revenue)}</b></div>
        </div>
        {r.warnings?.map((w) => <div key={w} className="warn-box">⚠ {w}</div>)}
      </div>

      <div className="card card-flush">
        <table className="table table-calc">
          <thead><tr><th>Kalkulationsschema</th><th className="num">€/Stk</th><th className="num">€/100</th><th className="num">€/1.000</th><th className="num">%</th></tr></thead>
          <tbody>
            {r.lines.filter((l) => l.per_piece !== 0 || ['summe'].includes(l.group)).map((l) => (
              <tr key={l.key} className={`calc-row-${l.group}`}>
                <td>{l.label}</td>
                <td className="num">{fix4(l.per_piece)}</td>
                <td className="num">{num2(l.per_100)}</td>
                <td className="num">{num2(l.per_1000)}</td>
                <td className="num">{num(l.share_pct, 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Co2Card co2={r.co2} lot={inputs.lot_size} annual={inputs.annual_volume} />

      {r.volume_tiers?.length > 0 && (
        <div className="card">
          <h3>Staffelpreise nach Jahresmenge</h3>
          <table className="table table-compact">
            <thead><tr><th className="num">Menge p. a.</th><th className="num">Losgröße</th><th className="num">€/Stk</th><th className="num">€/1.000</th><th className="num">Umsatz p. a.</th><th className="num">Δ</th></tr></thead>
            <tbody>{r.volume_tiers.map((t) => (
              <tr key={t.annual_volume} className={Number(t.annual_volume) === Number(inputs.annual_volume) ? 'row-latest' : ''}>
                <td className="num">{num(t.annual_volume)}</td><td className="num">{num(t.lot_size)}</td>
                <td className="num"><b>{fix4(t.unit_price)}</b></td><td className="num">{num2(t.price_per_1000)}</td>
                <td className="num">{eur(t.annual_revenue)}</td>
                <td className={`num ${t.delta_pct > 0 ? 'delta-up' : t.delta_pct < 0 ? 'delta-down' : 'muted'}`}>{t.delta_pct > 0 ? '+' : ''}{num(t.delta_pct, 1)} %</td>
              </tr>))}</tbody>
          </table>
        </div>
      )}

      {r.lot_tiers?.length > 0 && (
        <div className="card">
          <h3>Staffelpreise nach Losgröße</h3>
          <table className="table table-compact">
            <thead><tr><th className="num">Losgröße</th><th className="num">Rüsten €/Stk</th><th className="num">€/Stk</th><th className="num">€/1.000</th><th className="num">Δ</th></tr></thead>
            <tbody>{r.lot_tiers.map((t) => (
              <tr key={t.lot_size} className={Number(t.lot_size) === Number(inputs.lot_size) ? 'row-latest' : ''}>
                <td className="num">{num(t.lot_size)}</td><td className="num">{fix4(t.setup_per_piece)}</td>
                <td className="num"><b>{fix4(t.unit_price)}</b></td><td className="num">{num2(t.price_per_1000)}</td>
                <td className={`num ${t.delta_pct > 0 ? 'delta-up' : t.delta_pct < 0 ? 'delta-down' : 'muted'}`}>{t.delta_pct > 0 ? '+' : ''}{num(t.delta_pct, 1)} %</td>
              </tr>))}</tbody>
          </table>
          <small className="hint">Δ gegenüber kalkuliertem Preis bei Basis-Losgröße {num(inputs.lot_size)} Stk{inputs.price_override ? ' (manueller Preis bleibt für Staffeln unberücksichtigt)' : ''}.</small>
        </div>
      )}

      <div className="card">
        <h3>Verkaufspreis festlegen</h3>
        <div className="field">
          <label>Preis manuell (€/Stk) – leer = kalkulierter Preis</label>
          <input type="number" step="0.0001" className="num" disabled={!canWrite} value={inputs.price_override ?? ''}
            onChange={(e) => set('price_override', e.target.value === '' ? null : Number(e.target.value))} />
          <small className="hint">{r.price_source === 'manuell' ? 'Gewinn ergibt sich als Differenz zu den Selbstkosten.' : `Kalkuliert mit ${num(inputs.profit_pct, 1)} % Gewinn auf Selbstkosten.`}</small>
        </div>
      </div>

      {r.one_time?.length > 0 && (
        <div className="card">
          <h3>Einmalkosten</h3>
          <table className="table table-compact">
            <thead><tr><th>Position</th><th className="num">Kosten</th><th className="num">Preis</th></tr></thead>
            <tbody>
              {r.one_time.map((o, i) => <tr key={i}><td>{o.label}{o.amortize && <small className="muted"> · amortisiert</small>}</td><td className="num">{eur(o.cost)}</td><td className="num">{o.amortize ? <span className="muted">im Stückpreis</span> : eur(o.price)}</td></tr>)}
              <tr className="calc-row-summe"><td>Summe · Ergebnis {eur(r.one_time_margin)}</td><td className="num">{eur(r.one_time_cost)}</td><td className="num">{eur(r.one_time_price)}</td></tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

const CO2_PARTS = [
  ['material', 'Material', 'Scope 3 · vorgelagert'], ['purchased', 'Zukaufteile', 'Scope 3 · vorgelagert'],
  ['energy', 'Strom Fertigung', 'Scope 2'], ['scope1', 'Werksemissionen', 'Scope 1'],
  ['packaging', 'Verpackung', 'Scope 3 · vorgelagert'], ['transport', 'Transport zum Kunden', 'Scope 3 · nachgelagert'],
]
function Co2Card({ co2, lot, annual }) {
  if (!co2) return null
  if (!co2.active) {
    return <div className="card"><h3>CO₂-Fußabdruck</h3><div className="empty small">Emissionsfaktor Material oder Maschinenleistung eintragen (Bereich „CO₂-Fußabdruck“).</div></div>
  }
  const g = (kg) => num(kg * 1000, 1)
  return (
    <div className="card co2-card">
      <h3>CO₂-Fußabdruck</h3>
      <div className="co2-head">
        <div><span className="co2-big">{g(co2.total)}</span> <span className="muted">g CO₂e je Stück</span></div>
        <div className="muted small">Cradle-to-Gate {g(co2.cradle_to_gate)} g · davon Scope 1+2 {g(co2.scope12)} g</div>
      </div>
      <div className="result-kpis">
        <div><span>je 1.000 Stk</span><b>{num(co2.per_1000_kg, 2)} kg</b></div>
        <div><span>je Los ({num(lot)} Stk)</span><b>{num(co2.per_lot_kg, 1)} kg</b></div>
        <div><span>Jahresmenge ({num(annual)} Stk)</span><b>{num(co2.per_year_t, 2)} t</b></div>
        {co2.per_delivery_kg != null && <div><span>je Lieferung</span><b>{num(co2.per_delivery_kg, 1)} kg</b></div>}
        <div><span>je kg Teil</span><b>{co2.per_kg_part != null ? `${num(co2.per_kg_part, 2)} kg` : '–'}</b></div>
        <div><span>Strom</span><b>{num(co2.kwh_per_piece * 1000, 1)} Wh/Stk</b></div>
      </div>
      <table className="table table-compact">
        <thead><tr><th>Quelle</th><th>Scope</th><th className="num">g/Stk</th><th className="num">Anteil</th></tr></thead>
        <tbody>{CO2_PARTS.filter(([k]) => co2[k] > 0).map(([k, l, sc]) => (
          <tr key={k}><td>{l}</td><td className="muted small">{sc}</td><td className="num">{g(co2[k])}</td>
            <td className="num"><span className="co2-share"><span style={{ width: `${(co2[k] / co2.total) * 100}%` }} /></span>{num((co2[k] / co2.total) * 100, 0)} %</td></tr>
        ))}</tbody>
      </table>
      <p className="hint" style={{ marginBottom: 0 }}>Strom p. a. {num(co2.kwh_year)} kWh · Scope 1+2 p. a. {num(co2.scope12_year_t, 2)} t. Richtwerte – Faktoren unter Stammdaten pflegen.</p>
    </div>
  )
}

// ------------------------------------------------------------------ Versionen
const KEY_RESULTS = [
  ['unit_price', 'Verkaufspreis €/Stk', 4], ['self_cost', 'Selbstkosten €/Stk', 4], ['margin_pct', 'Marge %', 1],
  ['pieces_per_hour', 'Stück/h', 0], ['annual_revenue', 'Jahresumsatz €', 0], ['annual_profit', 'Gewinn p. a. €', 0],
  ['one_time_price', 'Einmalumsatz €', 0], ['machine_hours_year', 'Maschinenstunden p. a.', 0],
]

function VersionsTab({ calc }) {
  const vs = calc.versions
  const [a, setA] = useState(vs.length > 1 ? vs[vs.length - 2].version_no : vs[0].version_no)
  const [b, setB] = useState(vs[vs.length - 1].version_no)
  const A = vs.find((v) => v.version_no === a)
  const B = vs.find((v) => v.version_no === b)
  const changed = Object.keys({ ...A.inputs, ...B.inputs })
    .filter((k) => !k.endsWith('_id') && JSON.stringify(A.inputs[k]) !== JSON.stringify(B.inputs[k]))
  const show = (k, v) => {
    if (Array.isArray(v)) return v.map((x) => {
      if (!x || typeof x !== 'object') return num(x)
      if (k === 'operations') return `${x.name}: ${num(x.cycle_s, 1)} s, ${num(x.rate_h, 2)} €/h`
      if (k === 'purchased_items') return `${num(x.qty, 2)} × ${x.name} à ${num(x.price_per_piece, 4)} €`
      if (k === 'components') return `${x.label}: ${x.material_name || ''} ${num(x.part_weight_g, 1)} g`
      return `${x.label}: ${num(x.amount ?? x.price ?? x.cost ?? 0, 2)}`
    }).join('; ') || '–'
    if (v === null || v === '' || v === undefined) return '–'
    return typeof v === 'number' ? num(v, 4) : String(v)
  }
  return (
    <div className="stack">
      <div className="card card-flush">
        <table className="table">
          <thead><tr><th>Version</th><th>Datum</th><th>Von</th><th>Änderung</th><th className="num">€/Stk</th><th className="num">€/1.000</th><th className="num">Marge</th><th className="num">Umsatz p. a.</th><th>Vergleich</th></tr></thead>
          <tbody>
            {[...vs].reverse().map((v) => (
              <tr key={v.id}>
                <td><strong>V{v.version_no}</strong>{v.version_no === calc.current_version && <> <Badge tone="info">aktuell</Badge></>}</td>
                <td>{fmtDateTime(v.created_at)}</td>
                <td>{v.created_by?.name || '–'}</td>
                <td>{v.change_note || <span className="muted">–</span>}</td>
                <td className="num">{eur4(v.results.unit_price)}</td>
                <td className="num">{num2(v.results.price_per_1000)}</td>
                <td className="num">{num(v.results.margin_pct, 1)} %</td>
                <td className="num">{eur(v.results.annual_revenue)}</td>
                <td className="nowrap">
                  <label className="cmp"><input type="radio" name="va" checked={a === v.version_no} onChange={() => setA(v.version_no)} /> A</label>
                  <label className="cmp"><input type="radio" name="vb" checked={b === v.version_no} onChange={() => setB(v.version_no)} /> B</label>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="grid-2">
        <div className="card">
          <h3>Geänderte Eingaben V{a} → V{b}</h3>
          {changed.length ? (
            <table className="table table-compact">
              <thead><tr><th>Wert</th><th className="num">V{a}</th><th className="num">V{b}</th></tr></thead>
              <tbody>{changed.map((k) => (
                <tr key={k}><td>{INPUT_LABELS[k]?.[0] || k} <small className="muted">{INPUT_LABELS[k]?.[1]}</small></td>
                  <td className="num">{show(k, A.inputs[k])}</td><td className="num"><b>{show(k, B.inputs[k])}</b></td></tr>
              ))}</tbody>
            </table>
          ) : <div className="empty small">Keine Unterschiede in den Eingaben.</div>}
        </div>
        <div className="card">
          <h3>Auswirkung</h3>
          <table className="table table-compact">
            <thead><tr><th>Kennzahl</th><th className="num">V{a}</th><th className="num">V{b}</th><th className="num">Δ</th></tr></thead>
            <tbody>{KEY_RESULTS.map(([k, l, d]) => {
              const x = A.results[k] || 0, y = B.results[k] || 0
              const pct = x ? ((y - x) / Math.abs(x)) * 100 : 0
              return (
                <tr key={k}><td>{l}</td><td className="num">{num(x, d)}</td><td className="num">{num(y, d)}</td>
                  <td className={`num ${y - x !== 0 ? 'delta-neutral' : 'muted'}`}>
                    {y - x === 0 ? '–' : `${y - x > 0 ? '+' : ''}${num(y - x, d)}${k !== 'margin_pct' ? ` (${pct > 0 ? '+' : ''}${num(pct, 1)} %)` : ' Pkt.'}`}</td></tr>
              )
            })}</tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
