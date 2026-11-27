import { useEffect, useMemo, useState } from 'react'
import { marked } from 'marked'
import { api, downloadFile } from '../api'
import { ErrorBox } from '../components/ui'
import Version from '../components/Version'

// Dokumentation im Programm (REV01-X02): Lastenheft und Benutzerbeschreibung lesen, Inhaltsverzeichnis, Suche, Word-Download
const slug = (t) => t.toLowerCase().replace(/<[^>]+>/g, '').replace(/[^a-z0-9äöüß]+/g, '-').replace(/^-|-$/g, '')

export default function Docs() {
  const [list, setList] = useState([])
  const [key, setKey] = useState('beschreibung')
  const [doc, setDoc] = useState(null)
  const [q, setQ] = useState('')
  const [err, setErr] = useState(null)
  useEffect(() => { api.get('/docs').then((l) => { setList(l); if (l.length && !l.find((d) => d.key === key)) setKey(l[0].key) }).catch(setErr) }, [])
  useEffect(() => { setDoc(null); api.get(`/docs/${key}`).then(setDoc).catch(setErr) }, [key])
  const { html, toc } = useMemo(() => {
    if (!doc) return { html: '', toc: [] }
    const toc = []
    const renderer = new marked.Renderer()
    renderer.heading = ({ tokens, depth }) => {
      const text = marked.Parser.parseInline(tokens)
      const id = slug(text)
      if (depth <= 3) toc.push({ depth, text: text.replace(/<[^>]+>/g, ''), id })
      return `<h${depth} id="${id}">${text}</h${depth}>`
    }
    let html = marked.parse(doc.markdown, { renderer, gfm: true })
    if (q.trim().length > 1) {
      const re = new RegExp(`(${q.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})(?![^<]*>)`, 'gi')
      html = html.replace(re, '<mark>$1</mark>')
    }
    return { html, toc }
  }, [doc, q])
  const meta = list.find((d) => d.key === key)
  return (
    <div className="page page-wide">
      <header className="page-head">
        <div><h1>Dokumentation</h1><p className="muted">Benutzerbeschreibung und Lastenheft – immer auf dem Stand der installierten Version · Softwarestand <Version /></p></div>
        <div className="toolbar">
          <div className="seg">{list.map((d) => <button key={d.key} className={key === d.key ? 'on' : ''} onClick={() => setKey(d.key)}>{d.title}</button>)}</div>
          <input className="search" type="search" placeholder="Im Dokument suchen…" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="btn btn-primary" onClick={() => downloadFile(`/docs/${key}/docx`, `KlarCRM_${meta?.title || key}.docx`).catch(setErr)}>Als Word herunterladen</button>
        </div>
      </header>
      <ErrorBox error={err} />
      {!doc ? <div className="loading">Lade…</div> : (
        <div className="docs-layout">
          <nav className="docs-toc card">
            <strong>Inhalt</strong>{meta?.version && <small className="muted"> · Version {meta.version}</small>}
            {toc.map((t) => <a key={t.id + t.depth} href={`#${t.id}`} className={`toc-${t.depth}`}
              onClick={(e) => { e.preventDefault(); document.getElementById(t.id)?.scrollIntoView({ behavior: 'smooth' }) }}>{t.text}</a>)}
          </nav>
          <article className="card markdown" dangerouslySetInnerHTML={{ __html: html }} />
        </div>
      )}
    </div>
  )
}
