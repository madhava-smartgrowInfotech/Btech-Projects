import { createContext, useContext, useEffect, useState } from 'react'
import api from './api'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [email, setEmail] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('apisentry_token')
    if (!token) { setReady(true); return }
    api.get('/auth/me')
      .then((r) => setEmail(r.data.email))
      .catch(() => localStorage.removeItem('apisentry_token'))
      .finally(() => setReady(true))
  }, [])

  const login = async (e, password, register = false) => {
    const path = register ? '/auth/register' : '/auth/login'
    const r = await api.post(path, { email: e, password })
    localStorage.setItem('apisentry_token', r.data.token)
    setEmail(r.data.email)
  }

  const logout = () => {
    localStorage.removeItem('apisentry_token')
    setEmail(null)
    window.location.href = '/'
  }

  return (
    <AuthCtx.Provider value={{ email, ready, login, logout }}>
      {children}
    </AuthCtx.Provider>
  )
}

export const useAuth = () => useContext(AuthCtx)
