import { createContext, useCallback, useContext, useMemo, useState } from 'react'

// Sample login only: the product has no accounts, so this is a client-side demo gate
// (not real security). Credentials are shown on the login screen.
export const DEMO_USER = { email: 'demo@finsight.ai', password: 'finsight123', name: 'Demo User' }
const KEY = 'finsight-auth'

function read() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || 'null')
  } catch {
    return null
  }
}

const AuthCtx = createContext({ user: null, login: () => false, logout: () => {} })

export function AuthProvider({ children }) {
  const [user, setUser] = useState(read)
  const login = useCallback((email, password) => {
    if (email.trim().toLowerCase() === DEMO_USER.email && password === DEMO_USER.password) {
      const u = { email: DEMO_USER.email, name: DEMO_USER.name }
      try {
        localStorage.setItem(KEY, JSON.stringify(u))
      } catch {
        /* storage blocked: session lasts until reload */
      }
      setUser(u)
      return true
    }
    return false
  }, [])
  const logout = useCallback(() => {
    try {
      localStorage.removeItem(KEY)
      sessionStorage.removeItem('finsight-baseline')
      sessionStorage.removeItem('finsight-result')
    } catch {
      /* storage blocked */
    }
    setUser(null)
  }, [])
  const value = useMemo(() => ({ user, login, logout }), [user, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
