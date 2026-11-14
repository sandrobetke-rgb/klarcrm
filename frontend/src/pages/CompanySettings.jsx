import { useEffect, useRef, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { ErrorBox } from '../components/ui'

const GROUPS = [
  ['Firma', [['company_name', 'Firmenname'], ['street', 'Straße'], ['zip_city', 'PLZ und Ort'], ['country', 'Land'],
    ['phone', 'Telefon'], ['email', 'E-Mail'], ['website', 'Website']]],
  ['Rechtliches & Bank (Fußzeile)', [['register', 'Handelsregister (z. B. HRB 1234, AG Detmold)'], ['vat_id', 'USt-IdNr.'],
    ['managing_directors', 'Geschäftsführung'], ['bank_name', 'Bank'], ['iban', 'IBAN'], ['bic', 'BIC']]],
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
    try { setV(await api.put('/app-settings', v)); setMsg('Gespeichert – gilt für alle Angebote (Druck/PDF).') } catch (e) { setErr(e) }
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
        <div><h1>Firma &amp; Angebotslayout</h1><p className="muted">Briefkopf, Logo, Fußzeile und Standardtexte für Angebote (Deutsch/Englisch)</p></div>
        <button className="btn btn-primary" onClick={save}>Speichern</button>
      </header>
      {msg && <div className="ok-box">{msg}</div>}<ErrorBox error={err} />
      <div className="grid-2">
        {GROUPS.map(([t, fields]) => (
          <div key={t} className="card"><h3>{t}</h3>
            <div className="form-grid">{fields.map(([k, l]) => (
              <div key={k} className="field"><label>{l}</label><input value={v[k] || ''} onChange={(e) => set(k, e.target.value)} /></div>))}</div>
          </div>
        ))}
        <div className="card"><h3>Logo &amp; Farbe</h3>
          <div className="logo-row">
            {v.logo_attachment_id ? <img src={`/api/public/logo?t=${logoTs}`} alt="Logo" className="logo-preview" /> : <div className="logo-preview empty small">kein Logo</div>}
            <div className="stack">
              <input ref={file} type="file" accept="image/png,image/jpeg,image/svg+xml" hidden onChange={(e) => e.target.files[0] && uploadLogo(e.target.files[0])} />
              <button className="btn btn-ghost" onClick={() => file.current.click()}>Logo hochladen (PNG, JPG, SVG)</button>
              <label className="inline-label">Akzentfarbe <input type="color" value={v.accent_color || '#1f4b99'} onChange={(e) => set('accent_color', e.target.value)} style={{ width: 60, padding: 2 }} /></label>
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
