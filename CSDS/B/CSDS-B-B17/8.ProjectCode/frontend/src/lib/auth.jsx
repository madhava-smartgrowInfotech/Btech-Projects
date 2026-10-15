import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import api from '../api'
import { readStore, writeStore } from './storage'

const AuthCtx = createContext({ user: null, signedOut: false, login: async () => {}, logout: () => {} })

function storedUser() {
  try {
    return readStore('cs_token') ? JSON.parse(readStore('cs_user') || 'null') : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(storedUser)
  const [signedOut, setSignedOut] = useState(false) // true after an explicit sign-out, so the guard sends people home, not to /login

  const login = useCallback(async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    writeStore('cs_token', data.token)
    writeStore('cs_user', JSON.stringify(data.user))
    setSignedOut(false)
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(() => {
    writeStore('cs_token', null)
    writeStore('cs_user', null)
    setSignedOut(true)
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, signedOut, login, logout }), [user, signedOut, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
