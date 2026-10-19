import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Api, getToken, setToken, setUnauthorizedHandler } from './api'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(() => !!getToken())

  // `leftOnPurpose` lets RequireAuth send a deliberate log out to the landing page instead of /login
  const [leftOnPurpose, setLeftOnPurpose] = useState(false)
  const logout = useCallback((opts) => {
    setToken(null)
    setUser(null)
    setLeftOnPurpose(!!opts?.home)
  }, [])

  const refresh = useCallback(async () => {
    const u = await Api.me()
    setUser(u)
    return u
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
  }, [logout])

  useEffect(() => {
    if (!getToken()) return
    Api.me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setBooting(false))
  }, [])

  const signIn = useCallback(async (fn) => {
    const r = await fn()
    setToken(r.token)
    setUser(r.user)
    setLeftOnPurpose(false)
    return r.user
  }, [])

  const value = useMemo(
    () => ({
      user,
      booting,
      leftOnPurpose,
      logout,
      refresh,
      login: (email, pw) => signIn(() => Api.login(email, pw)),
      register: (name, email, pw) => signIn(() => Api.register(name, email, pw)),
    }),
    [user, booting, leftOnPurpose, logout, refresh, signIn],
  )
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
