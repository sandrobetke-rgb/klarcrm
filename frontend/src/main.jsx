import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Navigate, NavLink, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import './styles.css'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Accounts from './pages/Accounts'
import AccountDetail from './pages/AccountDetail'
import Contacts from './pages/Contacts'
import Pipeline from './pages/Pipeline'
import Activities from './pages/Activities'
import Quotes from './pages/Quotes'
import QuoteEditor from './pages/QuoteEditor'
import Users from './pages/Users'
import Profile from './pages/Profile'
import Calculations from './pages/Calculations'
import CalculationEditor from './pages/CalculationEditor'
import MasterData from './pages/MasterData'
import Utilization from './pages/Utilization'
import Reports from './pages/Reports'
import ProcurementList, { ProcurementDetail } from './pages/Procurement'
import PageHelp from './components/PageHelp'
import AuditLog from './pages/AuditLog'
import CompanySettings from './pages/CompanySettings'
import NotificationBell from './components/NotificationBell'
import { ROLES } from './constants'
import Footer from './components/Footer'
import Changes from './pages/Changes'
import Inquiries, { InquiryDetail } from './pages/Inquiries'
import PriceList, { PriceChangeDetail } from './pages/PriceList'
import Docs from './pages/Docs'
import MonthlyReport from './pages/MonthlyReport'

function Layout() {
  const { user, logout, isAdmin } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  // Menü in Arbeitsreihenfolge (Anfrage → Kalkulation → Angebot → Verfolgung), Gruppen als Zwischenüberschrift
  const nav = [
    ['/', 'Dashboard', '▦'],
    ['#', 'Vertrieb'],
    ['/anfragen', 'Anfragen', '✉'],
    ['/pipeline', 'Pipeline', '⇶'],
    ['/kalkulationen', 'Kalkulationen', '∑'],
    ['/angebote', 'Angebote', '€'],
    ['/aktivitaeten', 'Aktivitäten', '✓'],
    ['/preisliste', 'Preisliste', '₤'],
    ['#', 'Kunden'],
    ['/firmen', 'Firmen', '▣'],
    ['/kontakte', 'Kontakte', '☺'],
    ['#', 'Planung & Analyse'],
    ['/auslastung', 'Auslastung', '▤'],
    ['/auswertungen', 'Auswertungen', '◔'],
    ['/monatsbericht', 'Monatsbericht', '▦'],
    ['/beschaffung', 'Beschaffung', '⚒'],
    ['#', 'System'],
    ['/stammdaten', 'Stammdaten', '≡'],
    ['/aenderungen', 'Änderungswünsche', '✎'],
    ['/dokumentation', 'Dokumentation', '📖'],
  ]
  if (user.is_superuser) nav.push(['/protokoll', 'Protokoll 🔒', '⎙'])   // REV02-07: nur SuperUser
  if (isAdmin) nav.push(['/benutzer', 'Benutzer', '⚙'], ['/einstellungen', 'Firma & Layout', '✎'])
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand"><span className="logo">K</span> KlarCRM</div>
        <nav>
          {nav.map(([to, label, icon], i) => to === '#' ? <div key={`g${i}`} className="nav-group">{label}</div> : (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
              <span className="nav-icon" aria-hidden>{icon}</span>{label}
            </NavLink>
          ))}
        </nav>
        <NotificationBell />
        <div className="sidebar-foot">
          <NavLink to="/profil" className="user-chip">
            <span className="avatar">{user.name.split(' ').map((p) => p[0]).slice(0, 2).join('')}</span>
            <span>
              <strong>{user.name}</strong>
              <small>{ROLES.find((r) => r.value === user.role)?.label}</small>
            </span>
          </NavLink>
          <button className="btn btn-ghost btn-sm logout" onClick={logout}>Abmelden</button>
        </div>
      </aside>
      <main className="content">
        <PageHelp />
        <Outlet />
        <Footer />
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/anfragen" element={<Inquiries />} />
            <Route path="/preisliste" element={<PriceList />} />
            <Route path="/preisliste/aenderungen/:id" element={<PriceChangeDetail />} />
            <Route path="/anfragen/:id" element={<InquiryDetail />} />
            <Route path="/firmen" element={<Accounts />} />
            <Route path="/firmen/:id" element={<AccountDetail />} />
            <Route path="/kontakte" element={<Contacts />} />
            <Route path="/aktivitaeten" element={<Activities />} />
            <Route path="/angebote" element={<Quotes />} />
            <Route path="/angebote/:id" element={<QuoteEditor />} />
            <Route path="/kalkulationen" element={<Calculations />} />
            <Route path="/kalkulationen/:id" element={<CalculationEditor />} />
            <Route path="/stammdaten" element={<MasterData />} />
            <Route path="/auslastung" element={<Utilization />} />
            <Route path="/auswertungen" element={<Reports />} />
            <Route path="/monatsbericht" element={<MonthlyReport />} />
            <Route path="/beschaffung" element={<ProcurementList />} />
            <Route path="/beschaffung/:id" element={<ProcurementDetail />} />
            <Route path="/protokoll" element={<AuditLog />} />
            <Route path="/aenderungen" element={<Changes />} />
            <Route path="/dokumentation" element={<Docs />} />
            <Route path="/einstellungen" element={<CompanySettings />} />
            <Route path="/benutzer" element={<Users />} />
            <Route path="/profil" element={<Profile />} />
          </Route>
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
