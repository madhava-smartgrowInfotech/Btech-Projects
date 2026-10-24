import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import api, { getToken, setToken } from '../api'
import { logEvent } from './activity'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(!getToken())
  // set when the user chose to leave, so RequireAuth does not bounce them from "/" to "/login"
  const [leftOnPurpose, setLeft] = useState(false)

  useEffect(() => {
    if (!getToken()) return
    api.get('/auth/me', { silent: true }).then((r) => setUser(r.data)).catch(() => setToken(null)).finally(() => setReady(true))
  }, [])

  useEffect(() => {
    const on = () => { setUser(null); logEvent('auth', 'session expired - sign in again') }
    window.addEventListener('fs:unauthorized', on)
    return () => window.removeEventListener('fs:unauthorized', on)
  }, [])

  const signIn = useCallback(async (email, password) => {
    const r = await api.post('/auth/login', { email, password })
    setToken(r.data.token)
    setUser(r.data.user)
    setLeft(false)
    logEvent('auth', `signed in as ${r.data.user.email}`)
    return r.data.user
  }, [])

  const signOut = useCallback(() => {
    setToken(null)
    setUser(null)
    setLeft(true)
    logEvent('auth', 'signed out')
  }, [])

  const value = useMemo(() => ({ user, ready, signIn, signOut, leftOnPurpose }), [user, ready, signIn, signOut, leftOnPurpose])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function RequireAuth({ children }) {
  const { user, ready, leftOnPurpose } = useAuth()
  const loc = useLocation()
  if (!ready) return <div className="grid min-h-screen place-items-center font-mono text-sm text-muted" aria-busy="true">authenticating…</div>
  if (!user) return <Navigate to={leftOnPurpose ? '/' : '/login'} state={{ from: loc.pathname }} replace />
  return children
}
