import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, getToken, setToken, setUnauthorizedHandler } from './api'
import { readStore, writeStore } from './storage'
import { useToast } from '../components/ui/Toast'

const AuthCtx = createContext(null)

function cachedUser() {
  try {
    return JSON.parse(readStore('am.user') || 'null')
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const toast = useToast()
  const [user, setUser] = useState(() => (getToken() ? cachedUser() : null))
  const [meta, setMeta] = useState(null) // device + token expiry from /me
  const [checking, setChecking] = useState(Boolean(getToken()))

  const clear = useCallback(() => {
    setToken(null)
    writeStore('am.user', null)
    setUser(null)
    setMeta(null)
  }, [])

  // The JWT is device-bound and verified server-side on every call, like Streamlit's per-rerun check.
  useEffect(() => {
    setUnauthorizedHandler((msg) => {
      clear()
      toast.warning(msg)
    })
    if (!getToken()) return
    api('/api/auth/me')
      .then((d) => {
        setUser(d.user)
        setMeta(d)
        writeStore('am.user', JSON.stringify(d.user))
      })
      .catch(() => {})
      .finally(() => setChecking(false))
  }, [clear, toast])

  const login = useCallback(async (username, password, role) => {
    const d = await api('/api/auth/login', { method: 'POST', body: { username, password, role }, auth: false })
    setToken(d.token)
    writeStore('am.user', JSON.stringify(d.user))
    setUser(d.user)
    setMeta({ expires_local: d.expires_local })
    api('/api/auth/me').then(setMeta).catch(() => {})
    return d
  }, [])

  const logout = useCallback(async () => {
    try {
      await api('/api/auth/logout', { method: 'POST' })
    } catch {
      /* token may already be invalid */
    }
    clear()
  }, [clear])

  const value = useMemo(() => ({ user, meta, checking, login, logout }), [user, meta, checking, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
