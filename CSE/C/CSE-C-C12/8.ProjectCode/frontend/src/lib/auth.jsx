import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { authApi } from './api'
import { readStore, writeStore } from './storage'

const AuthCtx = createContext(null)
const HINT = 'cl.session'

export const DEMO_ACCOUNT = { email: 'demo@carelens.ai', password: 'Demo@1234' }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  // The session cookie is httponly, so a local hint records whether a session may exist.
  // Without it we skip /auth/me (an expected 401 would otherwise be logged in the console).
  useEffect(() => {
    let alive = true
    if (readStore(HINT) !== '1') {
      setReady(true)
      return undefined
    }
    authApi
      .me()
      .then((u) => alive && setUser(u))
      .catch(() => {
        writeStore(HINT, '0')
        if (alive) setUser(null)
      })
      .finally(() => alive && setReady(true))
    return () => {
      alive = false
    }
  }, [])

  // Any protected API call that comes back 401 means the session is gone: drop it so routes redirect to sign-in.
  useEffect(() => {
    const on = () => {
      writeStore(HINT, '0')
      setUser(null)
    }
    window.addEventListener('cl:unauthorized', on)
    return () => window.removeEventListener('cl:unauthorized', on)
  }, [])

  const login = useCallback(async (email, password) => {
    await authApi.login(email, password)
    setUser(await authApi.me())
    writeStore(HINT, '1')
  }, [])
  const register = useCallback(async (email, password) => {
    await authApi.register(email, password)
    setUser(await authApi.me())
    writeStore(HINT, '1')
  }, [])
  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      writeStore(HINT, '0')
      setUser(null)
    }
  }, [])

  const value = useMemo(() => ({ user, ready, login, register, logout, meta: null }), [user, ready, login, register, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
