import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, getToken, setToken, setUnauthorizedHandler } from './api'

const AuthCtx = createContext(null)
export const useAuth = () => useContext(AuthCtx)

/** Session state. status: 'loading' (checking a saved token) | 'in' | 'out'. */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(getToken() ? 'loading' : 'out')
  const [leftOnPurpose, setLeftOnPurpose] = useState(false) // true after the user pressed Sign out

  const signOut = useCallback((onPurpose = false) => {
    setToken(null)
    setUser(null)
    setLeftOnPurpose(onPurpose === true)
    setStatus('out')
  }, [])

  // An expired or rejected token (401) signs out without the "on purpose" flag, so the user lands on the login form.
  useEffect(() => {
    setUnauthorizedHandler(() => signOut(false))
  }, [signOut])

  // Validate a saved token once on load.
  useEffect(() => {
    if (!getToken()) return undefined
    let alive = true
    api
      .me()
      .then((d) => {
        if (!alive) return
        setUser(d.user)
        setStatus('in')
      })
      .catch((e) => {
        if (!alive) return
        // Offline API: keep the token so a refresh after restart still works, but show signed-out.
        if (e.status !== 0) setToken(null)
        setStatus('out')
      })
    return () => {
      alive = false
    }
  }, [])

  const finish = useCallback((d) => {
    setToken(d.token)
    setUser(d.user)
    setLeftOnPurpose(false)
    setStatus('in')
    return d.user
  }, [])

  const login = useCallback(async (email, password) => finish(await api.login(email, password)), [finish])
  const register = useCallback(async (name, email, password) => finish(await api.register(name, email, password)), [finish])

  const value = useMemo(() => ({ user, status, leftOnPurpose, login, register, signOut }), [user, status, leftOnPurpose, login, register, signOut])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}
