import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import ListPage from '../components/ListPage'
import { Badge } from '../components/ui'
import { BigBadge, bigReasons, quoteSplit, useThresholds } from '../components/BigProject'
import { eur, fmtDate, QUOTE_STATUS } from '../constants'

export const quoteTone = { entwurf: 'neutral', versendet: 'info', angenommen: 'good', abgelehnt: 'critical' }

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
        { key: 'account', label: 'Firma', render: (r) => r.account?.name || '–' },
        { key: 'quote_date', label: 'Datum', render: (r) => fmtDate(r.quote_date) },
        { key: 'valid_until', label: 'Gültig bis', render: (r) => fmtDate(r.valid_until) },
        { key: 'status', label: 'Status', render: (r) => <Badge tone={quoteTone[r.status]}>{QUOTE_STATUS.find((s) => s.value === r.status)?.label}</Badge> },
        { key: 'net_total', label: 'Netto', className: 'num', render: (r) => eur(r.net_total, true) },
      ]}
    />
  )
}
