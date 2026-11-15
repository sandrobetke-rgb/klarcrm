import { useEffect, useRef, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { ErrorBox } from '../components/ui'
import { LetterFooter, LetterHead } from '../components/Letterhead'

const GROUPS = [
  ['Firma (Briefkopf)', [['company_name', 'Firmenname'], ['street', 'Straße'], ['zip_city', 'PLZ und Ort'], ['country', 'Land'],
    ['phone', 'Telefon'], ['fax', 'Fax'], ['email', 'E-Mail'], ['website', 'Website'],
    ['locations', 'Weitere Standorte (z. B. „Werk Krupka (CZ)“)', true]]],
  ['Rechtliches (Fußzeile)', [['register', 'Handelsregister (z. B. HRB 1234, AG Detmold)'], ['seat', 'Sitz der Gesellschaft'],
    ['vat_id', 'USt-IdNr.'], ['tax_no', 'Steuernummer'], ['managing_directors', 'Geschäftsführung', true],
    ['certifications', 'Zertifizierungen (z. B. IATF 16949 · ISO 9001 · ISO 14001)', true], ['footer_note', 'Zusatz Fußzeile (optional)', true]]],
  ['Bankverbindungen (Fußzeile)', [['bank_name', 'Bank 1'], ['iban', 'IBAN 1'], ['bic', 'BIC 1'], ['bank2_name', 'Bank 2 (optional)'],
    ['iban2', 'IBAN 2'], ['bic2', 'BIC 2']]],
]
const TEXTS = [['intro_de', 'Einleitung (Deutsch)'], ['intro_en', 'Einleitung (Englisch)'], ['terms_de', 'Bedingungen / AGB-Hinweis (Deutsch)'],
  ['terms_en', 'Bedingungen / AGB-Hinweis (Englisch)'], ['closing_de', 'Grußformel (Deutsch)'], ['closing_en', 'Grußformel (Englisch)']]

export default function CompanySettings() {
  const { isAdmin } = useAuth()
  const [v, setV] = useState(null)
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const [logoTs, setLogoTs] = useState(Date.now())
  const file = useRef()
  useEffect(() => { api.get('/app-settings').then(setV) }, [])
  if (!isAdmin) return <Navigate to="/" />
  if (!v) return <div className="loading">Lade…</div>
  const set = (k, x) => { setMsg(null); setV({ ...v, [k]: x }) }
  async function save() {
    setErr(null)
    try { setV(await api.put('/app-settings', v)); setMsg('Gespeichert – gilt für Angebote und Anfragen (Druck/PDF).') } catch (e) { setErr(e) }
  }
  async function uploadLogo(f) {
    setErr(null)
    try {
      const fd = new FormData()
      fd.append('entity', 'app'); fd.append('entity_id', '1'); fd.append('doc_type', 'logo'); fd.append('file', f)
      const a = await api.upload('/attachments', fd)
      setV(await api.put('/app-settings', { ...v, logo_attachment_id: a.id })); setLogoTs(Date.now()); setMsg('Logo gespeichert.')
    } catch (e) { setErr(e) }
  }
  return (
    <div className="page">
      <header className="page-head">
        <div><h1>Firma &amp; Layout</h1><p className="muted">Briefkopf, Logo, Bankverbindung, Fußzeile und Standardtexte – gilt für Angebote und Werkzeug-/Anlagenanfragen</p></div>
        <button className="btn btn-primary" onClick={save}>Speichern</button>
      </header>
      {msg && <div className="ok-box">{msg}</div>}<ErrorBox error={err} />
      <div className="grid-2">
        {GROUPS.map(([t, fields]) => (
          <div key={t} className="card"><h3>{t}</h3>
            <div className="form-grid">{fields.map(([k, l, wide]) => (
              <div key={k} className={`field ${wide ? 'span-2' : ''}`}><label>{l}</label><input value={v[k] || ''} onChange={(e) => set(k, e.target.value)} /></div>))}</div>
          </div>
        ))}
        <div className="card"><h3>Logo &amp; Farbe</h3>
          <div className="logo-row">
            {v.logo_attachment_id ? <img src={`/api/public/logo?t=${logoTs}`} alt="Logo" className="logo-preview" /> : <div className="logo-preview empty small">kein Logo</div>}
            <div className="stack">
              <input ref={file} type="file" accept="image/png,image/jpeg,image/svg+xml" hidden onChange={(e) => e.target.files[0] && uploadLogo(e.target.files[0])} />
              <button className="btn btn-ghost" onClick={() => file.current.click()}>Logo hochladen (PNG, JPG, SVG)</button>
              <label className="inline-label">Akzentfarbe <input type="color" value={v.accent_color || '#1f4b99'} onChange={(e) => set('accent_color', e.target.value)} style={{ width: 60, padding: 2 }} /></label>
              <label className="inline-label">Logogröße <select value={v.logo_size || 'mittel'} onChange={(e) => set('logo_size', e.target.value)} style={{ width: 'auto' }}>
                <option value="klein">klein</option><option value="mittel">mittel</option><option value="gross">groß</option></select></label>
              {v.logo_attachment_id && <button className="btn btn-ghost btn-sm" onClick={() => set('logo_attachment_id', null)}>Logo entfernen</button>}
            </div>
          </div>
        </div>
        <div className="card"><h3>Vorschau Briefkopf</h3>
          <p className="muted small" style={{ marginTop: 0 }}>So sehen Kopf und Fußzeile im Druck aus (verkleinert). Änderungen erst mit „Speichern“ übernehmen.</p>
          <div className="letter-preview-wrap">
            <div className="letter-preview" style={{ '--accent': v.accent_color || '#1f4b99' }}>
              <LetterHead a={{ ...v, logo_src: `/api/public/logo?t=${logoTs}` }} />
              <div className="pq-title">Angebot AN-{new Date().getFullYear()}-0001</div>
              <div className="muted-lines"><span style={{ width: '70%' }} /><span /><span style={{ width: '85%' }} /><span style={{ width: '60%' }} /></div>
              <LetterFooter a={v} />
            </div>
          </div>
        </div>
        <div className="card"><h3>Standardtexte</h3>
          <div className="form-grid">{TEXTS.map(([k, l]) => (
            <div key={k} className="field span-2"><label>{l}</label><textarea rows={2} value={v[k] || ''} onChange={(e) => set(k, e.target.value)} /></div>))}</div>
        </div>
      </div>
    </div>
  )
}
