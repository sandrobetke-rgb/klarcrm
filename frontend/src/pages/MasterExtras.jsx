import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Badge, confirmDelete, ErrorBox, useFetch } from '../components/ui'
import { calcStatus, eur, fix4, fmtDate, num, num2 } from '../constants'

const PARTS = [['depreciation', 'Abschreibung'], ['interest', 'Zinsen'], ['space', 'Raum'], ['energy', 'Energie'], ['other', 'Sonst. Fixkosten'], ['allocation', 'Umlage KST']]

export function MachineRates({ tabs }) {
  const { isAdmin } = useAuth()
  const { data, error, reload } = useFetch('/calc/machine-rates')
  const [err, setErr] = useState(null)
  return (
    <div className="page">
      <header className="page-head">
        <div><h1>Stammdaten · Herleitung Maschinenstundensätze</h1>
          <p className="muted">Abschreibung, Zinsen, Raum, Energie und Fixkosten je Maschine – Werte unter „Maschinen“ pflegen, Parameter für Raumkosten und Strompreis</p></div>
        <div className="toolbar">{tabs}</div>
      </header>
      <ErrorBox error={error || err} />
      <div className="card card-flush">
        <table className="table">
          <thead><tr><th>Maschine</th>{PARTS.map(([k, l]) => <th key={k} className="num">{l} €/h</th>)}
            <th className="num">Hergeleitet €/h</th><th className="num">Aktuell €/h</th><th className="num">Instandh. hergel. / aktuell</th><th /></tr></thead>
          <tbody>{data?.map((r) => {
            const diff = r.current_hourly_rate ? (r.hourly_rate - r.current_hourly_rate) / r.current_hourly_rate * 100 : null
            return (
              <tr key={r.machine.id}>
                <td><strong>{r.machine.number} · {r.machine.name}</strong><br /><small className="muted">{num(r.hours)} h/Jahr</small></td>
                {PARTS.map(([k]) => <td key={k} className="num">{r.complete ? num2(r.parts[k]) : '–'}</td>)}
                <td className="num"><b>{r.complete ? num2(r.hourly_rate) : '–'}</b></td>
                <td className="num">{num2(r.current_hourly_rate)}{r.complete && diff != null && Math.abs(diff) >= 0.5 &&
                  <><br /><small className={diff > 0 ? 'delta-up' : 'delta-down'}>{diff > 0 ? '+' : ''}{num(diff, 1)} %</small></>}</td>
                <td className="num">{r.complete ? num2(r.maintenance_rate) : '–'} / {num2(r.current_maintenance_rate)}</td>
                <td>{isAdmin && r.complete && <button className="btn btn-ghost btn-sm" onClick={async () => {
                  setErr(null); try { await api.post(`/calc/machine-rates/${r.machine.id}/apply`); reload() } catch (e) { setErr(e) }
                }}>übernehmen</button>}{!r.complete && <small className="muted">Wiederbeschaffungswert / Nutzungsdauer fehlen</small>}</td>
              </tr>
            )
          })}</tbody>
        </table>
      </div>
      <p className="muted small">Formel: (Wiederbeschaffungswert / Nutzungsdauer + Wiederbeschaffungswert / 2 × Zins + m² × Raumkosten + sonstige Fixkosten + Umlage Kostenstelle) / verfügbare Stunden + kW × Strompreis. Wichtig: Umlagen (Meister, Logistik, Peripherie, Druckluft …) entweder hier ODER über den FGK-Zuschlag erfassen – nicht doppelt.
        Instandhaltung €/h = Instandhaltungskosten p. a. / verfügbare Stunden. Personal ist nicht enthalten (separat über Lohnsatz × Bedienfaktor). „Übernehmen“ ändert nur neue Kalkulationen; bestehende Versionen bleiben unverändert.</p>
    </div>
  )
}

export function Escalation({ tabs }) {
  const { canWrite } = useAuth()
  const mats = useFetch('/materials?limit=500&sort=name')
  const [mid, setMid] = useState('')
  const [data, setData] = useState(null)
  const [hist, setHist] = useState([])
  const [sel, setSel] = useState({})
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const load = (id) => {
    if (!id) return
    api.get(`/calc/escalation?material_id=${id}`).then((d) => { setData(d); setSel(Object.fromEntries(d.items.filter((x) => x.exceeds_threshold).map((x) => [x.id, true]))) })
    api.get(`/calc/material-prices/${id}`).then(setHist)
  }
  useEffect(() => { if (!mid && mats.data?.items.length) { const pa = mats.data.items.find((m) => m.name.startsWith('PA6')) || mats.data.items[0]; setMid(String(pa.id)); load(pa.id) } }, [mats.data])
  const chosen = Object.keys(sel).filter((k) => sel[k]).map(Number)
  return (
    <div className="page">
      <header className="page-head">
        <div><h1>Stammdaten · Rohstoffpreise &amp; Preisgleitung</h1>
          <p className="muted">Preishistorie je Material und Auswirkung auf offene und gewonnene Kalkulationen</p></div>
        <div className="toolbar">{tabs}</div>
      </header>
      <div className="filters">
        <label className="inline-label">Material
          <select value={mid} onChange={(e) => { setMid(e.target.value); setMsg(null); load(e.target.value) }}>
            {mats.data?.items.map((m) => <option key={m.id} value={m.id}>{m.name} · {num2(m.price_per_kg)} €/kg</option>)}
          </select></label>
        {data && <span className="muted small">Schwelle Preisgleitklausel ± {num(data.threshold_pct, 1)} % · Index: {data.material.price_index || '–'}</span>}
      </div>
      <ErrorBox error={err} />{msg && <div className="ok-box">{msg}</div>}
      <div className="grid-2 grid-2-wide">
        <div className="card card-flush">
          <table className="table">
            <thead><tr><th>Kalkulation</th><th>Kunde</th><th className="num">Basis €/kg</th><th className="num">aktuell €/kg</th><th className="num">Δ Material</th><th className="num">€/Stk alt → neu</th><th className="num">Wirkung p. a.</th>{canWrite && <th />}</tr></thead>
            <tbody>
              {data?.items.map((x) => (
                <tr key={x.id} className={x.exceeds_threshold ? 'row-big' : ''}>
                  <td><Link to={`/kalkulationen/${x.id}`}>{x.number}</Link> V{x.version}<br /><small className="muted">{x.article_name} · {calcStatus(x.status).label}{x.component !== 'Hauptmaterial' ? ` · ${x.component}` : ''}</small></td>
                  <td>{x.account || '–'}</td>
                  <td className="num">{num2(x.old_material_price)}</td><td className="num">{num2(x.new_material_price)}</td>
                  <td className={`num ${x.material_delta_pct > 0 ? 'delta-up' : x.material_delta_pct < 0 ? 'delta-down' : 'muted'}`}>{x.material_delta_pct > 0 ? '+' : ''}{num(x.material_delta_pct, 1)} %{x.exceeds_threshold && ' ⚠'}</td>
                  <td className="num">{fix4(x.old_unit_price)} → <b>{fix4(x.new_unit_price)}</b><br /><small className="muted">{x.unit_price_delta_pct > 0 ? '+' : ''}{num(x.unit_price_delta_pct, 1)} %</small></td>
                  <td className="num">{eur(x.annual_impact)}</td>
                  {canWrite && <td><input type="checkbox" checked={!!sel[x.id]} onChange={(e) => setSel({ ...sel, [x.id]: e.target.checked })} /></td>}
                </tr>
              ))}
              {data && !data.items.length && <tr><td colSpan={8} className="empty">Keine Kalkulation nutzt dieses Material.</td></tr>}
            </tbody>
          </table>
          {canWrite && data?.items.length > 0 && (
            <div className="items-foot">
              <span className="muted small">Markiert: Abweichung über der Schwelle. Neue Version je Kalkulation mit aktuellem Materialpreis, Änderungsnotiz automatisch.</span>
              <button className="btn btn-primary btn-sm" disabled={!chosen.length} onClick={async () => {
                setErr(null)
                try { const r = await api.post('/calc/escalation/apply', { material_id: Number(mid), calc_ids: chosen }); setMsg(`Neue Versionen angelegt: ${r.updated.join(', ')}`); load(mid) } catch (e) { setErr(e) }
              }}>Neue Versionen anlegen ({chosen.length})</button>
            </div>
          )}
        </div>
        <div className="card">
          <h3>Preishistorie</h3>
          <table className="table table-compact">
            <thead><tr><th>gültig ab</th><th className="num">€/kg</th><th>Hinweis</th></tr></thead>
            <tbody>{hist.map((h) => <tr key={h.id}><td>{fmtDate(h.valid_from)}</td><td className="num">{num2(h.price_per_kg)}</td><td className="small muted">{h.note}{h.user ? ` · ${h.user}` : ''}</td></tr>)}</tbody>
          </table>
          <p className="hint">Neuen Preis unter „Materialien“ eintragen – die Historie wird automatisch fortgeschrieben.</p>
        </div>
      </div>
    </div>
  )
}

export function Templates({ tabs }) {
  const { canWrite } = useAuth()
  const { data, error, reload } = useFetch('/calc/templates')
  return (
    <div className="page">
      <header className="page-head">
        <div><h1>Stammdaten · Kalkulationsvorlagen</h1>
          <p className="muted">Vorlagen entstehen in einer Kalkulation über „Als Vorlage speichern“ und stehen bei „Neue Anfrage“ zur Auswahl</p></div>
        <div className="toolbar">{tabs}</div>
      </header>
      <ErrorBox error={error} />
      <div className="card card-flush">
        <table className="table">
          <thead><tr><th>Vorlage</th><th>Beschreibung</th><th>Quelle</th><th>Maschine / Material</th><th>Angelegt</th>{canWrite && <th />}</tr></thead>
          <tbody>
            {data?.map((t) => (
              <tr key={t.id}>
                <td><strong>{t.name}</strong></td><td>{t.description || '–'}</td><td>{t.source_calc}</td>
                <td className="small">{t.inputs.machine_name || '–'}<br /><span className="muted">{t.inputs.material_name || '–'}</span></td>
                <td>{fmtDate(t.created_at)}<br /><small className="muted">{t.created_by}</small></td>
                {canWrite && <td><button className="icon-btn" title="Löschen" onClick={async () => { if (await confirmDelete(`Vorlage „${t.name}“`, () => api.del(`/calc/templates/${t.id}`))) reload() }}>×</button></td>}
              </tr>
            ))}
            {data && !data.length && <tr><td colSpan={6} className="empty">Noch keine Vorlagen.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}

