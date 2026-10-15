import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import api from '../api.js'

// Session state for the whole app. Token and user live in localStorage under the keys api.js already reads.
const AuthCtx = createContext(null)

function readUser() {
  try {
    return JSON.parse(localStorage.getItem('pv_user'))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readUser)

  const login = useCallback(async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('pv_token', data.token)
    localStorage.setItem('pv_user', JSON.stringify(data.user))
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(async () => {
    localStorage.removeItem('pv_token')
    localStorage.removeItem('pv_user')
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
