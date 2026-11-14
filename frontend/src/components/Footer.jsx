import { BRAND } from '../constants'

export default function Footer() {
  return (
    <footer className="app-footer">
      <span>© {BRAND.year} <strong className="brand-mark">SB<span>/</span>Thinkworks</strong></span>
      <span className="footer-sep">·</span>
      <span>KlarCRM</span>
      <span className="footer-sep">·</span>
      <span className="footer-claim">{BRAND.claim}</span>
    </footer>
  )
}

