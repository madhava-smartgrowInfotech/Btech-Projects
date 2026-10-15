import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { api, setUnauthorizedHandler, tokenStore } from './api'
import { homeFor } from '../components/ui/layout'
import { Skeleton } from '../components/ui/feedback'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(() => !!tokenStore.get())

  const logout = useCallback(() => {
    tokenStore.set(null)
    setUser(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
  }, [logout])

  // restore the session from a saved token
  useEffect(() => {
    if (!tokenStore.get()) return
    api
      .get('/auth/me')
      .then((r) => setUser(r.user))
      .catch((e) => {
        // only a rejected token ends the session; an offline backend keeps it for the next visit
        if (e.status === 401) tokenStore.set(null)
      })
      .finally(() => setBooting(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const r = await api.post('/auth/login', { email, password })
    tokenStore.set(r.token)
    setUser(r.user)
    return r.user
  }, [])

  const value = useMemo(() => ({ user, booting, login, logout }), [user, booting, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

// Route guard: sends signed-out visitors to /login and wrong-role visitors to their own home screen.
export function RequireAuth({ roles, children }) {
  const { user, booting } = useAuth()
  const loc = useLocation()
  if (booting) {
    return (
      <div className="container" style={{ paddingTop: 80 }} aria-busy="true" aria-label="Loading">
        <Skeleton height={28} width={240} />
        <Skeleton height={160} style={{ marginTop: 24 }} />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  if (roles && !roles.includes(user.role)) return <Navigate to={homeFor(user.role)} replace />
  return children
}
