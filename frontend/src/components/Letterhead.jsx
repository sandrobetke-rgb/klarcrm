/** Gemeinsamer Briefkopf und Fußzeile für Angebot, Werkzeuganfrage und Vorschau (Firma & Layout). */
const LOGO_H = { klein: '12mm', mittel: '18mm', gross: '26mm' }

export function LetterHead({ a = {} }) {
  return (
    <>
      <div className="pq-head">
        <div className="pq-company">
          <strong>{a.company_name}</strong><br />{a.street}<br />{a.zip_city}{a.country && a.country !== 'Deutschland' ? `, ${a.country}` : ''}
          {a.locations && <><br /><span className="pq-locations">{a.locations}</span></>}
        </div>
        {a.logo_attachment_id && <img className="pq-logo" style={{ maxHeight: LOGO_H[a.logo_size] || LOGO_H.mittel }} src={a.logo_src || '/api/public/logo'} alt="" />}
      </div>
      <div className="pq-sender">{[a.company_name, a.street, a.zip_city].filter(Boolean).join(' · ')}</div>
    </>
  )
}

export function LetterFooter({ a = {}, lang = 'de' }) {
  const en = lang === 'en'
  return (
    <div className="pq-footer-wrap">
      <div className="pq-footer">
        <div>{a.company_name}<br />{a.street}<br />{a.zip_city}{a.seat && <><br />{en ? 'Registered office' : 'Sitz'}: {a.seat}</>}</div>
        <div>{a.phone && <>Tel. {a.phone}<br /></>}{a.fax && <>Fax {a.fax}<br /></>}{a.email}{a.website && <><br />{a.website}</>}</div>
        <div>{a.register}{a.vat_id && <><br />{en ? 'VAT ID' : 'USt-IdNr.'} {a.vat_id}</>}{a.tax_no && <><br />{en ? 'Tax no.' : 'St.-Nr.'} {a.tax_no}</>}
          {a.managing_directors && <><br />{en ? 'Managing directors' : 'Geschäftsführung'}: {a.managing_directors}</>}</div>
        <div>{a.bank_name}{a.iban && <><br />IBAN {a.iban}</>}{a.bic && <><br />BIC {a.bic}</>}
          {a.iban2 && <><br /><span className="pq-bank2">{a.bank2_name}<br />IBAN {a.iban2}{a.bic2 && <><br />BIC {a.bic2}</>}</span></>}</div>
      </div>
      {(a.certifications || a.footer_note) && <div className="pq-footnote">{[a.certifications, a.footer_note].filter(Boolean).join(' · ')}</div>}
    </div>
  )
}
