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
import AuditLog from './pages/AuditLog'
import CompanySettings from './pages/CompanySettings'
import NotificationBell from './components/NotificationBell'
import { ROLES } from './constants'
import Footer from './components/Footer'

function Layout() {
  const { user, logout, isAdmin } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  const nav = [
    ['/', 'Dashboard', '▦'],
    ['/pipeline', 'Pipeline', '⇶'],
    ['/firmen', 'Firmen', '▣'],
    ['/kontakte', 'Kontakte', '☺'],
    ['/aktivitaeten', 'Aktivitäten', '✓'],
    ['/kalkulationen', 'Kalkulation', '∑'],
    ['/auslastung', 'Auslastung', '▤'],
    ['/angebote', 'Angebote', '€'],
    ['/stammdaten', 'Stammdaten', '≡'],
  ]
  if (isAdmin || user.role === 'gesellschafter' || user.can_approve) nav.push(['/protokoll', 'Protokoll', '⎙'])
  if (isAdmin) nav.push(['/benutzer', 'Benutzer', '⚙'], ['/einstellungen', 'Firma & Layout', '✉'])
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand"><span className="logo">K</span> KlarCRM</div>
        <nav>
          {nav.map(([to, label, icon]) => (
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
            <Route path="/protokoll" element={<AuditLog />} />
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
