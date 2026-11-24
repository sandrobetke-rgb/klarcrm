import { createContext, useContext, useEffect, useState } from 'react'
import { api, getToken, setSession, storedUser } from './api'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(storedUser())
  // Rechte (z. B. Freigabe, SuperUser) beim Start frisch vom Server holen – greifen ohne Neuanmeldung
  useEffect(() => {
    if (!getToken()) return
    api.get('/auth/me').then((u) => { setSession(getToken(), u); setUser(u) }).catch(() => {})
  }, [])

  async function login(email, password) {
    const res = await api.login(email, password)
    setSession(res.access_token, res.user)
    setUser(res.user)
  }
  function logout() {
    setSession(null)
    setUser(null)
  }
  const canWrite = user && ['admin', 'vertrieb'].includes(user.role)
  const isAdmin = user?.role === 'admin'
  return <AuthCtx.Provider value={{ user, login, logout, canWrite, isAdmin }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
