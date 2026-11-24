const BASE = '/api'

export function getToken() {
  return localStorage.getItem('crm_token')
}

export function setSession(token, user) {
  if (token) {
    localStorage.setItem('crm_token', token)
    localStorage.setItem('crm_user', JSON.stringify(user))
  } else {
    localStorage.removeItem('crm_token')
    localStorage.removeItem('crm_user')
  }
}

export function storedUser() {
  try { return JSON.parse(localStorage.getItem('crm_user')) } catch { return null }
}

// REV02-07: Freischaltung des Protokolls (nur dieser Tab, 30 Minuten)
export function setAuditToken(token, minutes) {
  try { sessionStorage.setItem('crm_audit', JSON.stringify({ token, until: Date.now() + minutes * 60000 })) } catch { /* ohne Speicher */ }
}
function auditToken() {
  try { const a = JSON.parse(sessionStorage.getItem('crm_audit')); return a && a.until > Date.now() ? a.token : null } catch { return null }
}
export const auditUnlocked = () => !!auditToken()

async function request(method, path, body) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (path.startsWith('/audit') && auditToken()) headers['X-Audit-Token'] = auditToken()
  let payload
  if (body instanceof FormData) {
    payload = body
  } else if (body instanceof URLSearchParams) {
    payload = body
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  const res = await fetch(BASE + path, { method, headers, body: payload })
  if (res.status === 401 && !path.startsWith('/auth/login')) {
    setSession(null)
    window.location.href = '/login'
    throw new Error('Sitzung abgelaufen')
  }
  if (res.status === 423) { try { sessionStorage.removeItem('crm_audit') } catch { /* egal */ } }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    let msg = data?.detail || `Fehler ${res.status}`
    if (Array.isArray(msg)) msg = msg.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join(', ')
    throw new Error(msg)
  }
  return data
}

export function qs(params = {}) {
  const p = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') p.set(k, v)
  })
  const s = p.toString()
  return s ? `?${s}` : ''
}

/** Datei mit Anmeldung herunterladen und im Browser speichern. */
export async function downloadFile(path, filename) {
  const res = await fetch(BASE + path, { headers: { Authorization: `Bearer ${getToken()}` } })
  if (!res.ok) throw new Error(`Download fehlgeschlagen (${res.status})`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b) => request('POST', p, b),
  patch: (p, b) => request('PATCH', p, b),
  put: (p, b) => request('PUT', p, b),
  upload: (p, formData) => request('POST', p, formData),
  del: (p) => request('DELETE', p),
  login: (email, password) =>
    request('POST', '/auth/login', new URLSearchParams({ username: email, password })),
}
