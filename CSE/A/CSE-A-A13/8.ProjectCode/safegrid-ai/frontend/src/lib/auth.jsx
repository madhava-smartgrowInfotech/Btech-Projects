import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

// Demo access gate. The SafeGrid-AI API has no user accounts, so sign-in is handled in the browser:
// it keeps the console behind a login screen for demos, it is not a security boundary.
export const DEMO_ACCOUNT = { email: 'operator@safegrid.ai', password: 'SafeGrid@2026', name: 'Grid Operator', role: 'Control room operator' }

const KEY = 'sg-session'
const AuthCtx = createContext(null)

function read() {
  try {
    const raw = localStorage.getItem(KEY)
    const s = raw ? JSON.parse(raw) : null
    return s && s.email ? s : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(read)

  const login = useCallback((email, password) => {
    const ok = email.trim().toLowerCase() === DEMO_ACCOUNT.email && password === DEMO_ACCOUNT.password
    if (!ok) return { ok: false, error: 'That email and password do not match the demo account.' }
    const next = { email: DEMO_ACCOUNT.email, name: DEMO_ACCOUNT.name, role: DEMO_ACCOUNT.role }
    try {
      localStorage.setItem(KEY, JSON.stringify(next))
    } catch {
      /* storage blocked - the session lasts until the page is closed */
    }
    setUser(next)
    return { ok: true }
  }, [])

  const logout = useCallback(() => {
    try {
      localStorage.removeItem(KEY)
    } catch {
      /* ignore */
    }
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

export function RequireAuth({ children }) {
  const { user } = useAuth()
  const loc = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return children
}
