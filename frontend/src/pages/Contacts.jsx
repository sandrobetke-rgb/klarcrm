import { Link } from 'react-router-dom'
import ListPage from '../components/ListPage'
import { contactFields } from '../forms'

export default function Contacts() {
  return (
    <ListPage
      title="Kontakte" subtitle="Ansprechpartner bei Kunden und Interessenten" path="/contacts" entityLabel="Kontakt"
      fields={contactFields} defaultSort="last_name"
      columns={[
        { key: 'name', label: 'Name', sort: 'last_name', render: (r) => <strong>{r.salutation ? r.salutation + ' ' : ''}{r.first_name} {r.last_name}</strong> },
        { key: 'position', label: 'Position', sort: 'position' },
        { key: 'account', label: 'Firma', render: (r) => r.account
          ? <Link to={`/firmen/${r.account.id}`} onClick={(e) => e.stopPropagation()}>{r.account.name}</Link> : '–' },
        { key: 'email', label: 'E-Mail', render: (r) => r.email
          ? <a href={`mailto:${r.email}`} onClick={(e) => e.stopPropagation()}>{r.email}</a> : '–' },
        { key: 'phone', label: 'Telefon', render: (r) => r.phone || r.mobile || '–' },
        { key: 'owner', label: 'Verantwortlich', render: (r) => r.owner?.name || '–' },
      ]}
    />
  )
}
