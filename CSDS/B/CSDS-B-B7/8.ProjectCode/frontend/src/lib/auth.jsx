/* Signed-in user for the whole app. The token and user live in localStorage so a reload keeps the session. */
import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { readStore, removeStore, writeStore } from './storage'

const AuthCtx = createContext({ user: null, login: () => {}, logout: async () => {} })

function readUser() {
  try {
    return JSON.parse(readStore('hs_user'))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readUser)

  const login = useCallback(({ token, user: nextUser }) => {
    writeStore('hs_token', token)
    writeStore('hs_user', JSON.stringify(nextUser))
    setUser(nextUser)
  }, [])

  const logout = useCallback(async () => {
    removeStore('hs_token')
    removeStore('hs_user')
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
