import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, clearSession, getUser, setSession } from './api'

const AuthCtx = createContext({ user: null, login: async () => {}, register: async () => {}, logout: () => {}, expired: false })

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getUser())
  const [expired, setExpired] = useState(false)

  useEffect(() => {
    const on = () => {
      setUser(null)
      setExpired(true)
    }
    window.addEventListener('bs-unauthorized', on)
    return () => window.removeEventListener('bs-unauthorized', on)
  }, [])

  const finish = useCallback((data) => {
    setSession(data)
    setUser(data.user)
    setExpired(false)
    return data.user
  }, [])

  const login = useCallback(async (email, password) => finish(await api.post('/auth/login', { email, password }, { auth: false })), [finish])
  const register = useCallback(
    async (name, email, password) => finish(await api.post('/auth/register', { name, email, password }, { auth: false })),
    [finish],
  )
  const logout = useCallback(() => {
    clearSession()
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, login, register, logout, expired }), [user, login, register, logout, expired])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
