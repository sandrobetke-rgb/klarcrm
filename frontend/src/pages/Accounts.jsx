import { useNavigate } from 'react-router-dom'
import ListPage from '../components/ListPage'
import { Badge } from '../components/ui'
import { ACCOUNT_TYPES, fmtDate } from '../constants'
import { accountFields } from '../forms'

export const typeTone = { kunde: 'good', interessent: 'info', partner: 'neutral', lieferant: 'neutral' }

export default function Accounts() {
  const nav = useNavigate()
  return (
    <ListPage
      title="Firmen" subtitle="Kunden, Interessenten und Partner" path="/accounts" entityLabel="Firma"
      fields={accountFields} defaultSort="name" newDefaults={{ type: 'interessent', country: 'Deutschland' }}
      onRowClick={(r) => nav(`/firmen/${r.id}`)}
      filters={[{ name: 'type', label: 'Typ', options: ACCOUNT_TYPES }]}
      columns={[
        { key: 'name', label: 'Firma', sort: 'name', render: (r) => <strong>{r.name}</strong> },
        { key: 'type', label: 'Typ', sort: 'type', render: (r) => <Badge tone={typeTone[r.type]}>{ACCOUNT_TYPES.find((t) => t.value === r.type)?.label}</Badge> },
        { key: 'industry', label: 'Branche', sort: 'industry' },
        { key: 'city', label: 'Ort', sort: 'city' },
        { key: 'phone', label: 'Telefon' },
        { key: 'owner', label: 'Verantwortlich', render: (r) => r.owner?.name || '–' },
        { key: 'updated_at', label: 'Geändert', sort: 'updated_at', render: (r) => fmtDate(r.updated_at) },
      ]}
    />
  )
}
