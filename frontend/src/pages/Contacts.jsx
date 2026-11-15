import { Link } from 'react-router-dom'
import { useState } from 'react'
import ImportButton from '../components/ImportButton'
import ListPage from '../components/ListPage'
import { contactFields } from '../forms'

export default function Contacts() {
  const [rev, setRev] = useState(0)
  return (
    <ListPage key={rev}
      extraActions={<ImportButton entity="contacts" label="Kontakte" onDone={() => setRev((x) => x + 1)} />}
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
