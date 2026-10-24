import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { api, token } from './api'

const AuthCtx = createContext({ user: null, ready: false, login: async () => {}, logout: () => {} })

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(() => !token.get())

  // restore the session from a saved token
  useEffect(() => {
    if (!token.get()) return undefined
    let live = true
    api
      .me()
      .then((u) => live && setUser(u))
      .catch(() => token.set(null))
      .finally(() => live && setReady(true))
    return () => {
      live = false
    }
  }, [])

  // any 401 from the API signs the user out
  useEffect(() => {
    const on = () => setUser(null)
    window.addEventListener('ll-unauthorized', on)
    return () => window.removeEventListener('ll-unauthorized', on)
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await api.login(email, password)
    token.set(res.token)
    setUser(res.user)
    return res.user
  }, [])

  const logout = useCallback(() => {
    token.set(null)
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, ready, login, logout }), [user, ready, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

export function RequireAuth({ children }) {
  const { user, ready } = useAuth()
  const loc = useLocation()
  if (!ready) return <div className="container" aria-busy="true" aria-label="Checking session" />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname + loc.search }} />
  return children
}
