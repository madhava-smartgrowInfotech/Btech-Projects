import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { api, getToken, setToken, setUnauthorizedHandler } from './api'
import { PageSkeleton } from '../components/ui/Feedback'

const AuthCtx = createContext(null)

/** Demo sign-in. The token lives in localStorage; /api/auth/me validates it on boot. */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(Boolean(getToken()))

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    if (!getToken()) return undefined
    let alive = true
    api
      .me()
      .then((u) => alive && setUser(u))
      .catch((e) => {
        if (!alive) return
        // Only a rejected token ends the session; if the API is simply offline keep it so the app can show its error state.
        if (e.status === 401) setToken(null)
        else setUser({ email: '', name: 'Offline' })
      })
      .finally(() => alive && setBooting(false))
    return () => {
      alive = false
    }
  }, [logout])

  const login = useCallback(async (email, password) => {
    const res = await api.login(email, password)
    setToken(res.token)
    setUser(res.user)
    return res.user
  }, [])

  const value = useMemo(() => ({ user, booting, login, logout }), [user, booting, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

/** Wraps protected routes: redirects to /login (remembering where the user was heading). */
export function RequireAuth({ children }) {
  const { user, booting } = useAuth()
  const loc = useLocation()
  if (booting) {
    return (
      <div className="container" style={{ paddingTop: 48 }}>
        <PageSkeleton />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname + loc.search }} />
  return children
}
