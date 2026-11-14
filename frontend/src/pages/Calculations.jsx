import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { BarList } from '../components/charts'
import ListPage from '../components/ListPage'
import { Badge, useFetch } from '../components/ui'
import { CALC_STATUS, calcStatus, CLOSE_REASONS, contactName, eur, eur4, fmtDate, LIGHTS, num, reasonLabel } from '../constants'

export function Light({ value, withText }) {
  if (!value) return <span className="muted">–</span>
  const l = LIGHTS[value]
  return <span className="light-wrap" title={`Nachkalkulation: ${l.label} – ${l.text}`}><span className={`light ${l.cls}`} />{withText && l.label}</span>
}

const callAge = (d) => (d ? (Date.now() - new Date(d)) / 86400000 : Infinity)

function Stats() {
  const { data } = useFetch('/calculations/stats')
  if (!data) return null
  return (
    <section className="calc-stats">
      <div className="kpi-grid">
        <div className="kpi"><span className="kpi-label">Offene Anfragen</span><span className="kpi-value">{data.count_open}</span>
          <span className="kpi-sub">{data.overdue_calls} seit &gt; 14 Tagen nicht angerufen</span></div>
        <div className="kpi"><span className="kpi-label">Potenzial Jahresumsatz (offen)</span><span className="kpi-value">{eur(data.open_revenue)}</span>
          <span className="kpi-sub">gewichtet {eur(data.open_weighted)}</span></div>
        <div className="kpi"><span className="kpi-label">Werkzeuge / Einmalumsatz (offen)</span><span className="kpi-value">{eur(data.open_tooling)}</span></div>
        <div className="kpi"><span className="kpi-label">Gewonnen</span><span className="kpi-value">{eur(data.won_revenue)}</span>
          <span className="kpi-sub">{data.won_count} Artikel · Trefferquote {data.hit_rate != null ? `${num(data.hit_rate, 1)} %` : '–'}</span></div>
        <div className="kpi"><span className="kpi-label">Verloren</span><span className="kpi-value">{eur(data.lost_revenue)}</span>
          <span className="kpi-sub">{data.lost_count} Artikel</span></div>
        <div className="kpi"><span className="kpi-label">Nachkalkulation</span>
          <span className="kpi-value lights-row">
            <span><Light value="gruen" /> {data.traffic_lights.gruen}</span>
            <span><Light value="gelb" /> {data.traffic_lights.gelb}</span>
            <span><Light value="rot" /> {data.traffic_lights.rot}</span>
          </span><span className="kpi-sub">letzte Nachkalk. je Artikel</span></div>
      </div>
      {data.lost_by_reason.length > 0 && (
        <div className="card">
          <h3>Verlustgründe</h3>
          <p className="card-sub">Verlorener Jahresumsatz je Grund · Anzahl Artikel</p>
          <BarList data={data.lost_by_reason.map((r) => ({ label: r.label, value: r.revenue, note: `${r.count}×`, tone: 'muted' }))} />
        </div>
      )}
    </section>
  )
}

export default function Calculations() {
  const nav = useNavigate()
  const { canWrite } = useAuth()
  return (
    <ListPage
      title="Kalkulationen" subtitle="Anfragen, Kalkulationen und ihr Weg zum Auftrag" path="/calculations"
      entityLabel="Kalkulation" defaultSort="-updated_at" limit={100}
      top={<Stats />}
      onRowClick={(r) => nav(`/kalkulationen/${r.id}`)}
      extraActions={canWrite && <button className="btn btn-primary" onClick={() => nav('/kalkulationen/neu')}>+ Neue Anfrage / Kalkulation</button>}
      filters={[
        { name: 'status', label: 'Status', options: CALC_STATUS },
        { name: 'close_reason', label: 'Verlustgrund', options: CLOSE_REASONS },
      ]}
      columns={[
        { key: 'number', label: 'Kalk.-Nr.', sort: 'number', render: (r) => <><strong>{r.number}</strong><br /><small className="muted">V{r.current_version}</small></> },
        { key: 'article_name', label: 'Artikel', sort: 'article_name', render: (r) => <>{r.article_name}{r.own_article_no && <><br /><small className="muted">{r.own_article_no}</small></>}</> },
        { key: 'customer_article_no', label: 'Art.-Nr. Kunde', sort: 'customer_article_no' },
        { key: 'account', label: 'Kunde / Ansprechpartner', render: (r) => <>
          {r.account ? <Link to={`/firmen/${r.account.id}`} onClick={(e) => e.stopPropagation()}>{r.account.name}</Link> : '–'}
          {r.contact && <><br /><small className="muted">{contactName(r.contact)}</small></>}</> },
        { key: 'status', label: 'Status', sort: 'status', render: (r) => <>
          <Badge tone={calcStatus(r.status).tone}>{calcStatus(r.status).label}</Badge>
          {r.close_reason && <><br /><small className="muted">{reasonLabel(r.close_reason)}</small></>}</> },
        { key: 'unit_price', label: '€/Stk', sort: 'unit_price', className: 'num', render: (r) => eur4(r.unit_price) },
        { key: 'annual_volume', label: 'Menge p. a.', sort: 'annual_volume', className: 'num', render: (r) => num(r.annual_volume) },
        { key: 'annual_revenue', label: 'Umsatz p. a.', sort: 'annual_revenue', className: 'num', render: (r) => <>{eur(r.annual_revenue)}{r.one_time_revenue > 0 && <><br /><small className="muted">+ {eur(r.one_time_revenue)} einm.</small></>}</> },
        { key: 'probability', label: 'Wahrsch.', sort: 'probability', className: 'num', render: (r) => <>{r.probability} %<br /><small className="muted">{eur(r.annual_revenue * r.probability / 100)}</small></> },
        { key: 'last_call_at', label: 'Zuletzt angerufen', sort: 'last_call_at', render: (r) => {
          const open = !['gewonnen', 'verloren', 'zurueckgestellt'].includes(r.status)
          return <span className={open && callAge(r.last_call_at) > 14 ? 'text-critical' : ''}>{fmtDate(r.last_call_at)}</span>
        } },
        { key: 'remark', label: 'Bemerkung', render: (r) => <span className="truncate" title={r.remark || ''}>{r.remark || '–'}</span> },
        { key: 'nk', label: 'NK', render: (r) => <Light value={r.last_traffic_light} /> },
      ]}
    />
  )
}
