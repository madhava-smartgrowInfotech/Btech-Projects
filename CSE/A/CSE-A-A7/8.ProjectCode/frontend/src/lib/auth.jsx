import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { api, getToken, setToken } from './api'
import { SkeletonBlock } from '../components/ui'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(getToken()))
  const [leftOnPurpose, setLeft] = useState(false)

  useEffect(() => {
    if (!getToken()) return undefined
    let live = true
    api
      .me()
      .then((u) => live && setUser(u))
      .catch(() => setToken(null))
      .finally(() => live && setLoading(false))
    return () => {
      live = false
    }
  }, [])

  useEffect(() => {
    const on = () => {
      setToken(null)
      setUser(null)
    }
    window.addEventListener('athena:unauthorized', on)
    return () => window.removeEventListener('athena:unauthorized', on)
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await api.login(email, password)
    setToken(res.access_token)
    setLeft(false)
    setUser(res.user)
    return res.user
  }, [])

  const logout = useCallback(() => {
    setLeft(true)
    setToken(null)
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, loading, login, logout, leftOnPurpose }), [user, loading, login, logout, leftOnPurpose])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

export function RequireAuth({ children }) {
  const { user, loading, leftOnPurpose } = useAuth()
  const loc = useLocation()
  if (loading)
    return (
      <div className="container" style={{ padding: '48px 16px' }}>
        <SkeletonBlock rows={4} label="Checking your session" />
      </div>
    )
  if (!user) return leftOnPurpose ? <Navigate to="/" replace /> : <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return children
}
