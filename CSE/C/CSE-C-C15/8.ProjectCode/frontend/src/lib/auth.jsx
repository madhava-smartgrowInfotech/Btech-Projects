import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { logEvent } from './activity'

// SentinelFlow is a localhost-only tool with no user database, so sign-in is a demo gate in the browser.
export const DEMO_USER = { email: 'demo@sentinelflow.com', password: 'Demo@1234', name: 'Demo Analyst' }
const KEY = 'sf_session'
const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function load() {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(load)
  const signIn = useCallback((email, password) => {
    if (email.trim().toLowerCase() !== DEMO_USER.email || password !== DEMO_USER.password) {
      logEvent('auth', `sign-in rejected for ${email.trim() || 'empty email'}`)
      return { ok: false, error: 'Email or password is not correct. Use the demo credentials shown on this page.' }
    }
    const u = { email: DEMO_USER.email, name: DEMO_USER.name }
    try { localStorage.setItem(KEY, JSON.stringify(u)) } catch { /* private mode: session lasts until reload */ }
    setUser(u)
    logEvent('auth', `signed in as ${u.email}`)
    return { ok: true }
  }, [])
  const signOut = useCallback(() => {
    try { localStorage.removeItem(KEY) } catch { /* ignore */ }
    logEvent('auth', 'signed out')
    setUser(null)
  }, [])
  const value = useMemo(() => ({ user, signIn, signOut }), [user, signIn, signOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function RequireAuth({ children }) {
  const { user } = useAuth()
  const loc = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return children
}
