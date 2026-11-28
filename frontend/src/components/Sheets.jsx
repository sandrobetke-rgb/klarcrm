// v1.34 Block 1 Teil 2 „Zusatzblätter“: Werkzeugblatt (C06), Risikoanalyse (C08), neue Anlagen (C09), Kickoff (C10)
import { Fragment, useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { eur, fix4, num, num2 } from '../constants'
import NumInput from './NumInput'
import { ErrorBox } from './ui'

const val = (e) => (e.target.value === '' ? '' : Number(e.target.value))
const LEVEL = { hoch: ['hoch', 'critical'], mittel: ['mittel', 'warning'], niedrig: ['niedrig', 'good'] }
export function RiskBadge({ level, prefix = 'Risiko ' }) {
  if (!level) return null
  const [l, tone] = LEVEL[level] || [level, 'neutral']
  return <span className={`badge badge-${tone}`} title="Risikoanalyse (Reiter Risiko)">{prefix}{l}</span>
}

function useSheets(calc, setCalc) {
  const [s, setS] = useState(null)
  const [err, setErr] = useState(null)
  const load = () => api.get(`/calculations/${calc.id}/sheets`).then(setS).catch(setErr)
  useEffect(() => { load() }, [calc.id, calc.current_version, calc.status]) // eslint-disable-line react-hooks/exhaustive-deps
  async function save(kind, data) {
    setErr(null)
    try { setS(await api.put(`/calculations/${calc.id}/sheets/${kind}`, { data })); return true } catch (e) { setErr(e); return false }
  }
  async function post(path) {
    setErr(null)
    try { setS(await api.post(`/calculations/${calc.id}/${path}`, {})); setCalc(await api.get(`/calculations/${calc.id}`)) } catch (e) { setErr(e) }
  }
  return { s, err, save, post }
}

function SaveBar({ dirty, onSave, onReset, children }) {
  const { canWrite } = useAuth()
  if (!canWrite) return null
  return (
    <div className={`card version-bar no-print ${dirty ? 'is-dirty' : ''}`}>
      {dirty ? <span className="badge badge-info">ungespeicherte Änderungen</span> : <span className="muted small">gespeichert</span>}
      <span className="spacer" />
      {children}
      <button className="btn btn-primary" disabled={!dirty} onClick={onSave}>💾 Speichern</button>
      {dirty && <button className="btn btn-ghost" onClick={onReset}>Verwerfen</button>}
    </div>
  )
}

function N({ label, unit, value, onChange, hint, span }) {
  return (
    <div className={`field ${span ? 'span-' + span : ''}`}><label>{label}{unit && <span className="unit"> {unit}</span>}</label>
      <NumInput type="number" step="any" className="num" value={value ?? ''} onChange={(e) => onChange(val(e))} />
      {hint && <small className="hint">{hint}</small>}</div>
  )
}

// ---------------------------------------------------------------- Werkzeugblatt (C06)
export function ToolTab({ calc, setCalc }) {
  const { s, err, save, post } = useSheets(calc, setCalc)
  const [d, setD] = useState(null)
  useEffect(() => { if (s) setD(structuredClone(s.tool.data || {})) }, [s])
  if (!s || !d) return <div className="loading">Lade…</div>
  const e = s.tool.eval
  const dirty = JSON.stringify(d) !== JSON.stringify(s.tool.data || {})
  const set = (k, v) => setD((x) => ({ ...x, [k]: v }))
  const offers = d.offers || []
  const setOffer = (n, patch) => set('offers', offers.map((o, j) => (j === n ? { ...o, ...patch } : patch.chosen ? { ...o, chosen: false } : o)))
  return (
    <div className="sheet-page">
      <SaveBar dirty={dirty} onSave={() => save('tool', d)} onReset={() => setD(structuredClone(s.tool.data || {}))}>
        {!dirty && e.total > 0 && <button className="btn btn-ghost" onClick={() => post('sheets/tool/apply')}
          title="Werkzeugkosten und Angebotspreis als Einmalkosten „Werkzeug“ in die Kalkulation (neue Version)">→ in die Kalkulation übernehmen</button>}
      </SaveBar>
      <ErrorBox error={err} />
      <div className="sheet-grid">
        <div className="card">
          <h3>Werkzeugkosten</h3>
          <div className="form-grid">
            {s.meta.tool_costs.map(([k, l]) => (k === 'external' && e.chosen
              ? <div key={k} className="field"><label>{l}</label><input disabled value={`${eur(e.costs.external)} (Angebot ${e.chosen})`} /></div>
              : <N key={k} label={l} unit="€" value={d[k]} onChange={(v) => set(k, v)} />))}
            <div className="field field-check"><label>Heißkanal</label><input type="checkbox" checked={!!d.hot_runner_yes} onChange={(x) => set('hot_runner_yes', x.target.checked)} /></div>
            {d.hot_runner_yes && <N label="Heißkanal: Anzahl Düsen" value={d.hot_runner_nozzles} onChange={(v) => set('hot_runner_nozzles', v)} />}
            <div className="field field-check"><label>Druck-/Temperaturfühler</label><input type="checkbox" checked={!!d.sensors_yes} onChange={(x) => set('sensors_yes', x.target.checked)} /></div>
            <div className="field"><label>Werkzeugbau</label>
              <select value={d.toolmaker || ''} onChange={(x) => set('toolmaker', x.target.value)}>
                <option value="">–</option><option value="extern">extern (Werkzeugbauer)</option><option value="intern">intern (F&R)</option></select></div>
          </div>
          <table className="table table-compact sheet-sum"><tbody>
            <tr className="row-sum"><td>Werkzeugkosten gesamt</td><td className="num"><b>{eur(e.total)}</b></td></tr>
            <tr><td>Angebotspreis an den Kunden</td><td className="num"><NumInput type="number" step="any" className="num" value={d.offer_price ?? ''} onChange={(x) => set('offer_price', val(x))} /></td></tr>
            <tr><td>Marge Werkzeug</td><td className={`num ${e.margin < 0 ? 'text-critical' : ''}`}>{e.margin != null ? <>{eur(e.margin)} ({num(e.margin_pct, 1)} %)</> : '–'}</td></tr>
            <tr><td className="muted">zurzeit in der Kalkulation (Einmalkosten „Werkzeug“)</td><td className="num muted">{eur(e.in_calc.cost)} / Preis {eur(e.in_calc.price)}</td></tr>
          </tbody></table>
        </div>
        <div className="card">
          <h3>Termine und Standzeit</h3>
          <div className="form-grid">
            {s.meta.tool_weeks.map(([k, l]) => <N key={k} label={l} unit="Wochen nach Bestellung" value={d[`weeks_${k}`]} onChange={(v) => set(`weeks_${k}`, v)} />)}
            <div className="field"><label>SOP (Serienstart)</label><input value={calc.sop_date ? new Date(calc.sop_date).toLocaleDateString('de-DE') : 'im Reiter „Anfrage & Status“'} disabled /></div>
            <N label="Werkzeugstandzeit" unit="Schuss" value={d.tool_life_shots} onChange={(v) => set('tool_life_shots', v)} />
          </div>
          <p className="small">Schüsse über die Laufzeit: <b>{num(e.shots_project)}</b> (Summe Jahresmengen ÷ Fachzahl)
            {e.life_pct != null && <> · <span className={e.life_ok ? 'text-good' : 'text-critical'}>{num(e.life_pct, 1)} % der Standzeit{e.life_ok ? '' : ' – Ersatzwerkzeug oder Überholung einplanen'}</span></>}</p>
          <p className="muted small">FOT, Baumuster/EMPB, PPAP (und SOP) stehen im Angebot unter dem Artikel.</p>
        </div>
      </div>
      <div className="card">
        <div className="section-head"><h3>Vergleich Werkzeugangebote (WZB 1–4)</h3>
          {offers.length < 4 && <button className="btn btn-ghost btn-sm" onClick={() => set('offers', [...offers, { supplier: '', price: '', weeks: '' }])}>+ Angebot</button>}</div>
        {offers.length ? <table className="table table-compact">
          <thead><tr><th>WZB</th><th>Werkzeugbauer</th><th className="num">Preis €</th><th className="num">Lieferzeit Wochen</th><th>Bemerkung</th><th>gewählt</th><th /></tr></thead>
          <tbody>{offers.map((o, n) => (
            <tr key={n} className={o.chosen ? 'row-current' : ''}>
              <td>WZB {n + 1}</td>
              <td><input value={o.supplier || ''} onChange={(x) => setOffer(n, { supplier: x.target.value })} /></td>
              <td className="num"><NumInput type="number" step="any" className="num" value={o.price ?? ''} onChange={(x) => setOffer(n, { price: val(x) })} /></td>
              <td className="num"><NumInput type="number" step="any" className="num" value={o.weeks ?? ''} onChange={(x) => setOffer(n, { weeks: val(x) })} /></td>
              <td><input value={o.note || ''} onChange={(x) => setOffer(n, { note: x.target.value })} /></td>
              <td className="center"><input type="radio" checked={!!o.chosen} onChange={() => setOffer(n, { chosen: true })} /></td>
              <td><button className="icon-btn" onClick={() => set('offers', offers.filter((_, j) => j !== n))}>×</button></td>
            </tr>))}</tbody>
        </table> : <p className="muted small">Bis zu 4 Angebote von Werkzeugbauern vergleichen; das gewählte ersetzt „Werkzeugkosten extern“.</p>}
        {e.cheapest && <p className="small">Günstigstes Angebot: <b>{e.cheapest.supplier || '–'}</b> mit {eur(e.cheapest.price)}{e.chosen && e.chosen !== e.cheapest.supplier ? ' – gewählt ist ein anderes (Begründung in der Bemerkung)' : ''}</p>}
      </div>
      <div className="card"><h3>Bemerkungen zum Werkzeug</h3>
        <textarea rows={3} value={d.note || ''} onChange={(x) => set('note', x.target.value)} placeholder="z. B. Schieber, Kühlung, Werkzeugstahl, Abnahme beim Werkzeugbauer" /></div>
    </div>
  )
}

// ---------------------------------------------------------------- Risikoanalyse (C08)
export function RiskTab({ calc, setCalc }) {
  const { s, err, save } = useSheets(calc, setCalc)
  const [d, setD] = useState(null)
  useEffect(() => { if (s) setD(structuredClone({ answers: {}, notes: {}, measures: '', ...(s.risk.data || {}) })) }, [s])
  if (!s || !d) return <div className="loading">Lade…</div>
  const e = s.risk.eval
  const base = { answers: {}, notes: {}, measures: '', ...(s.risk.data || {}) }
  const dirty = JSON.stringify(d) !== JSON.stringify(base)
  const setA = (k, v) => setD((x) => ({ ...x, answers: { ...x.answers, [k]: v } }))
  const setN = (k, v) => setD((x) => ({ ...x, notes: { ...x.notes, [k]: v } }))
  const grp = { prozess: 'Fertigungsprozess', lieferkette: 'Lieferkette' }
  return (
    <div className="sheet-page">
      <SaveBar dirty={dirty} onSave={() => save('risk', d)} onReset={() => setD(base)} />
      <ErrorBox error={err} />
      <div className="card risk-head">
        <div><span className="muted small">Gesamt</span><div className="risk-pct">{num(e.pct, 1)} %</div><RiskBadge level={e.level} /></div>
        {Object.entries(e.groups).map(([k, g]) => (
          <div key={k}><span className="muted small">{grp[k]}</span><div className="risk-pct-sm">{g.yes} von {g.count} · {num(g.pct, 0)} %</div><RiskBadge level={g.level} prefix="" /></div>))}
        <div className="muted small risk-scale">Einstufung nach Anteil „ja“: <b>hoch</b> über 60 % · <b>mittel</b> 35–60 % · <b>niedrig</b> unter 35 %.
          {!e.complete && <><br /><span className="text-critical">{e.count - e.answered} Frage(n) noch offen.</span></>}</div>
      </div>
      <div className="card">
        <table className="table table-compact risk-table">
          <thead><tr><th>#</th><th>Frage</th><th>Bereich</th><th className="center">ja</th><th className="center">nein</th><th>Bemerkung</th></tr></thead>
          <tbody>{e.questions.map((q, n) => {
            const v = d.answers[q.key]
            const shown = v === true || v === false ? v : q.value
            return (
              <tr key={q.key}>
                <td>{n + 1}</td><td>{q.text}{q.auto && <small className="muted"> (aus der Kalkulation)</small>}</td><td className="muted small">{grp[q.group]}</td>
                <td className="center"><input type="radio" name={`r-${q.key}`} checked={shown === true} onChange={() => setA(q.key, true)} /></td>
                <td className="center"><input type="radio" name={`r-${q.key}`} checked={shown === false} onChange={() => setA(q.key, false)} /></td>
                <td><input value={d.notes[q.key] || ''} onChange={(x) => setN(q.key, x.target.value)} /></td>
              </tr>)
          })}</tbody>
        </table>
      </div>
      <div className="card"><h3>Maßnahmen</h3>
        <textarea rows={3} value={d.measures || ''} onChange={(x) => setD({ ...d, measures: x.target.value })} placeholder="z. B. Musterphase verlängern, zweiten Lieferanten qualifizieren, Rahmenvertrag vor SOP" />
        <small className="hint">Die Einstufung steht im Kopf der Kalkulation, in der Anfrage und im Kickoff.</small></div>
    </div>
  )
}

// ---------------------------------------------------------------- Neue Anlagen (C09)
const EQ_FIELDS = [
  ['invest_fr', 'Invest F&R', '€', 'wird abgeschrieben'], ['invest_external', 'Invest extern (z. B. Kunde)', '€', 'ohne Abschreibung'],
  ['useful_life_years', 'Nutzungsdauer', 'Jahre'], ['interest_pct', 'Finanzierung (Zins)', '% p. a.', 'auf ½ Invest F&R'],
  ['floor_space_m2', 'Fläche', 'm²'], ['power_kw', 'Leistung', 'kW'],
  ['operating_cost_year', 'Betriebskosten', '€/Jahr'], ['maintenance_pct', 'Instandhaltung', '% vom Invest p. a.'],
  ['overhead_pct', 'Overhead-Zuschlag', '%'], ['available_hours_year', 'Verfügbare Stunden', 'h/Jahr'],
  ['availability_pct', 'Verfügbarkeit', '%'], ['time_per_piece_s', 'Zeit je Stück', 's'], ['operator_factor', 'Personal an der Anlage', 'Faktor (0,5 = halbe Person)'],
]
export function EquipmentTab({ calc, setCalc }) {
  const { s, err, save, post } = useSheets(calc, setCalc)
  const [d, setD] = useState(null)
  useEffect(() => { if (s) setD(structuredClone({ rows: [], ...(s.equipment.data || {}) })) }, [s])
  if (!s || !d) return <div className="loading">Lade…</div>
  const ev = s.equipment.eval
  const base = { rows: [], ...(s.equipment.data || {}) }
  const dirty = JSON.stringify(d) !== JSON.stringify(base)
  const upd = (n, patch) => setD((x) => ({ ...x, rows: x.rows.map((r, j) => (j === n ? { ...r, ...patch } : r)) }))
  const add = () => setD((x) => ({ ...x, rows: [...x.rows, { name: '', useful_life_years: 8, interest_pct: 5, maintenance_pct: 3, overhead_pct: 10,
    available_hours_year: 6000, availability_pct: 85, dedicated: true, checks: { liquidity: 'offen', space: 'offen', staff: 'offen' } }] }))
  return (
    <div className="sheet-page">
      <SaveBar dirty={dirty} onSave={() => save('equipment', d)} onReset={() => setD(base)}>
        <button className="btn btn-ghost" onClick={add}>+ Neue Anlage</button>
      </SaveBar>
      <ErrorBox error={err} />
      {!d.rows.length && <div className="card"><p className="muted">Für diesen Artikel ist keine zusätzliche Anlage nötig – sonst „+ Neue Anlage“ (z. B. Montage- oder Schweißanlage, Roboter, Prüfstand).
        Der Stundensatz wird wie bei den Maschinen in den Stammdaten hergeleitet (Kap. 6.1) und kann als Arbeitsgang in die Kalkulation übernommen werden.</p></div>}
      {d.rows.map((r, n) => {
        const e = ev.rows[n]
        return (
          <div key={n} className="card">
            <div className="section-head"><input className="eq-name" value={r.name || ''} placeholder="Bezeichnung der Anlage" onChange={(x) => upd(n, { name: x.target.value })} />
              <span className="toolbar">
                {e && !dirty && <button className="btn btn-ghost btn-sm" onClick={() => post(`sheets/equipment/${n}/apply`)}>→ als Arbeitsgang in die Kalkulation</button>}
                <button className="icon-btn" title="Entfernen" onClick={() => setD((x) => ({ ...x, rows: x.rows.filter((_, j) => j !== n) }))}>×</button></span></div>
            <div className="form-grid">
              {EQ_FIELDS.map(([k, l, u, h]) => <N key={k} label={l} unit={u} hint={h} value={r[k]} onChange={(v) => upd(n, { [k]: v })} />)}
              <div className="field span-2"><label>Kostenbasis</label>
                <select value={r.dedicated === false ? 'shared' : 'dedicated'} onChange={(x) => upd(n, { dedicated: x.target.value === 'dedicated' })}>
                  <option value="dedicated">nur für diesen Artikel – Kosten auf die benötigten Stunden</option>
                  <option value="shared">auch für andere Aufträge – Kosten auf die verfügbaren Stunden</option></select></div>
            </div>
            <div className="eq-checks"><span className="muted small">Kapazitätsprüfung:</span>
              {s.meta.capacity_checks.map(([k, l]) => (
                <label key={k} className="inline-label">{l}
                  <select value={(r.checks || {})[k] || 'offen'} onChange={(x) => upd(n, { checks: { ...(r.checks || {}), [k]: x.target.value } })}>
                    <option value="offen">offen</option><option value="ja">vorhanden</option><option value="nein">nicht vorhanden</option></select></label>))}
            </div>
            {e && <div className="eq-result">
              <div><span className="muted small">Stundensatz</span><b>{num2(e.rate)} €/h</b></div>
              <div><span className="muted small">je Stück</span><b>{e.cost_per_piece != null ? `${fix4(e.cost_per_piece)} €` : '–'}</b></div>
              <div><span className="muted small">benötigt / verfügbar</span><b>{num(e.need_hours)} h / {num(e.hours_eff)} h</b></div>
              <div><span className="muted small">Auslastung</span><b>{e.utilization_pct != null ? `${num(e.utilization_pct, 1)} %` : '–'}</b></div>
              <div><span className="muted small">Invest gesamt</span><b>{eur(e.invest_total)}</b></div>
              <small className="muted span-all">Herleitung je Stunde: Abschreibung {num2(e.parts.depreciation)} · Zins {num2(e.parts.interest)} · Raum {num2(e.parts.space)} · Energie {num2(e.parts.energy)} ·
                Betrieb {num2(e.parts.other)} · Instandhaltung {num2(e.maintenance_rate)} · Overhead {num2(e.overhead)} € – Basis {num(e.basis_hours)} h/Jahr
                ({e.dedicated ? 'nur dieser Artikel' : 'verfügbare Stunden'}). Stunden mit der höchsten Jahresmenge.</small>
            </div>}
            {dirty && <p className="muted small">Speichern, dann wird gerechnet.</p>}
          </div>)
      })}
    </div>
  )
}

// ---------------------------------------------------------------- Kickoff (C10)
export function KickoffTab({ calc, setCalc }) {
  const { s, err, post } = useSheets(calc, setCalc)
  const { canWrite } = useAuth()
  if (!s) return <div className="loading">Lade…</div>
  const k = s.kickoff
  if (!k) return (
    <div className="card sheet-page"><h3>Kickoff</h3>
      <p>Der Kickoff entsteht <b>automatisch</b>, sobald der Artikel beauftragt ist (Auftrag erhalten / Status „gewonnen“). Er enthält alle Daten
        aus Kalkulation, Werkzeugblatt, Risikoanalyse und neuen Anlagen zum Zeitpunkt des Auftrags, und der Verantwortliche bekommt die Aufgabe „Kickoff durchführen“.</p>
      {calc.status === 'gewonnen' && canWrite && <button className="btn btn-primary" onClick={() => post('kickoff')}>Kickoff jetzt erzeugen</button>}
      <ErrorBox error={err} /></div>)
  const c = k.calc, m = k.commercial, p = k.production, mt = k.material
  return (
    <div className="sheet-page kickoff">
      <div className="toolbar no-print">
        <button className="btn btn-ghost" onClick={() => window.print()}>🖨 Kickoff drucken / PDF</button>
        {canWrite && <button className="btn btn-ghost" onClick={() => window.confirm('Kickoff mit dem aktuellen Stand neu erzeugen? Der bisherige Stand bleibt in der Historie vermerkt.') && post('kickoff')}>Neu erzeugen (aktueller Stand)</button>}
        <ErrorBox error={err} />
      </div>
      <div className="card kickoff-doc">
        <h2>Kickoff {c.number} · {c.article}</h2>
        <p className="muted">Erzeugt am {new Date(k.created_at).toLocaleString('de-DE')} von {k.created_by} ({k.reason}) · Kalkulation V{c.version}</p>
        {k.open_points?.length > 0 && <div className="warn-box"><b>Offene Punkte</b><ul>{k.open_points.map((x) => <li key={x}>{x}</li>)}</ul></div>}
        <div className="kick-grid">
          <section><h3>Kunde & Artikel</h3><dl>
            <dt>Kunde</dt><dd>{c.customer || '–'}{c.contact ? ` · ${c.contact}` : ''}</dd>
            <dt>Kunden-Art.-Nr.</dt><dd>{c.customer_article_no || '–'}</dd><dt>F&R-Art.-Nr.</dt><dd>{c.own_article_no || '–'}</dd>
            <dt>Verantwortlich</dt><dd>{c.owner || '–'}</dd><dt>SOP</dt><dd>{c.sop_date ? new Date(c.sop_date).toLocaleDateString('de-DE') : '–'}</dd></dl></section>
          <section><h3>Preis & Mengen</h3><dl>
            <dt>Preis</dt><dd>{fix4(m.unit_price)} €/Stk · {num2(m.price_per_1000)} € je 1.000 · Marge {num(m.margin_pct, 1)} %</dd>
            <dt>Jahresmenge / Los</dt><dd>{num(m.annual_volume)} Stk · Los {num(m.lot_size)}</dd>
            <dt>Lieferbedingung</dt><dd>{m.incoterm || (m.transport_mode && m.transport_mode !== 'keine' ? 'frei Haus' : 'ab Werk')}</dd>
            <dt>Einmalkosten</dt><dd>{(m.one_time || []).map((o) => `${o.label} ${eur(o.price)}`).join(' · ') || '–'}</dd></dl>
            {m.years?.length > 0 && <table className="table table-compact"><thead><tr><th>Jahr</th><th className="num">Menge</th><th className="num">Los</th><th className="num">€/Stk</th><th className="num">Std.</th><th className="num">kg</th></tr></thead>
              <tbody>{m.years.map((y) => <tr key={y.year}><td>{y.year}</td><td className="num">{num(y.qty)}</td><td className="num">{num(y.lot)}</td><td className="num">{fix4(y.price)}</td><td className="num">{num(y.machine_hours)}</td><td className="num">{num(y.material_kg)}</td></tr>)}</tbody></table>}
          </section>
          <section><h3>Fertigung</h3><dl>
            <dt>Maschine</dt><dd>{p.machine || '–'}{p.suggested_machine ? ` (Analyse: ${p.suggested_machine})` : ''}</dd>
            <dt>Fachzahl / Zyklus</dt><dd>{p.cavities}-fach · {num(p.cycle_time_s, 1)} s · {num(p.pieces_per_hour)} Stk/h</dd>
            <dt>Schließkraft</dt><dd>{p.clamping_force_t ? `${num(p.clamping_force_t)} t` : '–'}</dd>
            <dt>Maschinenstunden</dt><dd>{num(p.machine_hours_year)} h/Jahr</dd>
            <dt>Weitere Arbeitsgänge</dt><dd>{(p.operations || []).map((o) => o.name).join(' · ') || '–'}</dd>
            <dt>Verpackung</dt><dd>{p.pack_type || '–'}{p.pack_parts_per_unit ? `, ${num(p.pack_parts_per_unit)} Stk je VE` : ''}</dd></dl></section>
          <section><h3>Material & Zukaufteile</h3><dl>
            <dt>Material</dt><dd>{mt.name || '–'}{mt.supplier ? ` · ${mt.supplier}` : ''}{mt.offer_no ? ` · Angebot ${mt.offer_no}` : ''}</dd>
            <dt>Bedarf</dt><dd>{num(mt.need_kg)} kg/Jahr à {num2(mt.price_kg)} €/kg · Teil {num(mt.part_weight_g, 1)} g</dd>
            {mt.masterbatch?.pct ? <><dt>Masterbatch</dt><dd>{mt.masterbatch.name || '–'} {num(mt.masterbatch.pct, 1)} %{mt.masterbatch.supplier ? ` · ${mt.masterbatch.supplier}` : ''}</dd></> : null}
            {(mt.components || []).map((x, n) => <Fragment key={n}><dt>{x.label}</dt><dd>{x.material} · {num(x.weight_g, 1)} g</dd></Fragment>)}</dl>
            {k.purchased?.length > 0 && <table className="table table-compact"><thead><tr><th>Zukaufteil</th><th>Lieferant</th><th className="num">je Teil</th><th className="num">Bedarf/Jahr</th></tr></thead>
              <tbody>{k.purchased.map((x, n) => <tr key={n}><td>{x.name}</td><td>{x.supplier || '–'}</td><td className="num">{num(x.qty)}</td><td className="num">{num(x.need_year)}</td></tr>)}</tbody></table>}
          </section>
          {k.tool && <section><h3>Werkzeug</h3><dl>
            <dt>Kosten / Preis</dt><dd>{eur(k.tool.eval.total)} / {eur(k.tool.eval.offer_price)}{k.tool.eval.chosen ? ` · Werkzeugbauer ${k.tool.eval.chosen}` : ''}</dd>
            <dt>Termine</dt><dd>FOT {k.tool.eval.weeks.fot ?? '–'} · Baumuster/EMPB {k.tool.eval.weeks.sample ?? '–'} · PPAP {k.tool.eval.weeks.ppap ?? '–'} Wochen nach Bestellung</dd>
            <dt>Ausstattung</dt><dd>{[k.tool.sheet.hot_runner_yes && `Heißkanal${k.tool.sheet.hot_runner_nozzles ? ` (${k.tool.sheet.hot_runner_nozzles} Düsen)` : ''}`, k.tool.sheet.sensors_yes && 'Druck-/Temperaturfühler'].filter(Boolean).join(' · ') || '–'}</dd>
            <dt>Standzeit</dt><dd>{k.tool.eval.tool_life_shots ? `${num(k.tool.eval.tool_life_shots)} Schuss · Bedarf ${num(k.tool.eval.shots_project)} (${num(k.tool.eval.life_pct, 0)} %)` : '–'}</dd>
            {k.tool.sheet.note && <><dt>Bemerkung</dt><dd>{k.tool.sheet.note}</dd></>}</dl></section>}
          {k.equipment && <section><h3>Neue Anlagen</h3>
            <table className="table table-compact"><thead><tr><th>Anlage</th><th className="num">Invest</th><th className="num">€/h</th><th>Liquidität / Fläche / Personal</th></tr></thead>
              <tbody>{k.equipment.eval.rows.map((x) => <tr key={x.name}><td>{x.name}</td><td className="num">{eur(x.invest_total)}</td><td className="num">{num2(x.rate)}</td><td>{Object.values(x.checks).join(' / ')}</td></tr>)}</tbody></table></section>}
          {k.risk && <section><h3>Risiko</h3><dl>
            <dt>Einstufung</dt><dd><RiskBadge level={k.risk.level} prefix="" /> {num(k.risk.pct, 1)} % · Prozess {k.risk.groups.prozess.level} · Lieferkette {k.risk.groups.lieferkette.level}</dd>
            <dt>Mit „ja“</dt><dd>{k.risk.questions.filter((q) => q.value === true).map((q) => q.text).join(' · ') || '–'}</dd>
            {k.risk.measures && <><dt>Maßnahmen</dt><dd>{k.risk.measures}</dd></>}</dl></section>}
          <section><h3>Machbarkeit</h3><dl>
            <dt>Ergebnis</dt><dd>{k.analysis.feasibility || '–'}{k.analysis.tech_talk ? ' · technisches Gespräch erforderlich' : ''}</dd>
            {k.analysis.note && <><dt>Bemerkung</dt><dd>{k.analysis.note}</dd></>}
            {k.analysis.hints?.length > 0 && <><dt>Hinweise</dt><dd>{k.analysis.hints.join(' · ')}</dd></>}
            {k.co2_g && <><dt>CO₂</dt><dd>{num(k.co2_g, 1)} g CO₂e/Stk (Cradle-to-Gate)</dd></>}</dl></section>
        </div>
        <p className="muted small kickoff-sign">Teilnehmer / Unterschrift: ______________________ · Vertrieb · Projekt · Qualität · Fertigung · Einkauf · Werkzeugbau</p>
        {k.previous?.length > 0 && <p className="muted small">Frühere Stände: {k.previous.map((x) => `${new Date(x.created_at).toLocaleString('de-DE')} (${x.created_by})`).join(' · ')}</p>}
      </div>
    </div>
  )
}
