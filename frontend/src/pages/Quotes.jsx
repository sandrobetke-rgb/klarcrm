import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import ListPage from '../components/ListPage'
import { Badge } from '../components/ui'
import { BigBadge, bigReasons, quoteSplit, useThresholds } from '../components/BigProject'
import { eur, fmtDate, QUOTE_STATUS } from '../constants'
import { LightBadge } from '../components/Followup'
import { Link } from 'react-router-dom'

export const quoteTone = { entwurf: 'neutral', versendet: 'info', angenommen: 'good', abgelehnt: 'critical', ersetzt: 'neutral' }

export default function Quotes() {
  const nav = useNavigate()
  const { canWrite } = useAuth()
  const t = useThresholds()
  return (
    <ListPage
      title="Angebote" subtitle="Angebote erstellen, versenden und nachverfolgen" path="/quotes" entityLabel="Angebot"
      onRowClick={(r) => nav(`/angebote/${r.id}`)}
      rowClass={(r) => { const x = quoteSplit(r); return bigReasons(t, x.revenue, x.invest).length ? 'row-big' : '' }}
      extraActions={canWrite && <button className="btn btn-primary" onClick={() => nav('/angebote/neu')}>+ Angebot erstellen</button>}
      filters={[{ name: 'status', label: 'Status', options: QUOTE_STATUS }]}
      columns={[
        { key: 'number', label: 'Nummer', render: (r) => <strong>{r.number}</strong> },
        { key: 'title', label: 'Titel', render: (r) => { const x = quoteSplit(r); return <>{r.title}<div><BigBadge revenue={x.revenue} invest={x.invest} /></div></> } },
        { key: 'account', label: 'Firma / Anfrage', render: (r) => <>{r.account?.name || '–'}{r.opportunity && <><br /><Link to={`/anfragen/${r.opportunity.id}`} onClick={(e) => e.stopPropagation()}><small>{r.opportunity.number || r.opportunity.name}</small></Link></>}</> },
        { key: 'quote_date', label: 'Datum', render: (r) => <>{fmtDate(r.quote_date)}{r.sent_at && <><br /><small className="muted">versendet {fmtDate(r.sent_at)}</small></>}</> },
        { key: 'status', label: 'Status', render: (r) => <Badge tone={quoteTone[r.status]}>{QUOTE_STATUS.find((s) => s.value === r.status)?.label}</Badge> },
        // REV01-P04: Status und letzte Rückmeldung / Anruf direkt in der Liste
        { key: 'followup', label: 'Verfolgung', render: (r) => (r.followup ? <LightBadge light={r.followup.light} due={r.followup.due_at} /> : '–') },
        { key: 'last_contact', label: 'Letzte Rückmeldung', render: (r) => (r.last_contact_at ? <small>{fmtDate(r.last_contact_at)} · {r.last_contact_note}</small> : <small className="muted">–</small>) },
        { key: 'net_total', label: 'Netto', className: 'num', render: (r) => eur(r.net_total, true) },
      ]}
    />
  )
}
