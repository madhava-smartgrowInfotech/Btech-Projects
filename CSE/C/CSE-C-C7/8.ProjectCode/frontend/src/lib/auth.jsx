import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { get, post } from './api'

const AuthCtx = createContext({ user: null, loading: true })

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore the session from the cookie.
  useEffect(() => {
    let alive = true
    get('/api/me')
      .then((r) => alive && setUser(r.user))
      .catch(() => alive && setUser(null))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [])

  // Any 401 from a protected call means the session is gone.
  useEffect(() => {
    const on = () => setUser(null)
    window.addEventListener('lpq:unauthorized', on)
    return () => window.removeEventListener('lpq:unauthorized', on)
  }, [])

  const login = useCallback(async (email, password) => {
    const r = await post('/api/auth/login', { email, password })
    setUser(r.user)
    return r.user
  }, [])

  const register = useCallback(async (form) => {
    const r = await post('/api/auth/register', form)
    setUser(r.user)
    return r.user
  }, [])

  const logout = useCallback(async () => {
    try {
      await post('/api/auth/logout')
    } finally {
      setUser(null)
    }
  }, [])

  const value = useMemo(() => ({ user, loading, login, register, logout }), [user, loading, login, register, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
