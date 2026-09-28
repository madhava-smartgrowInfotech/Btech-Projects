import { createContext, useContext, useState } from 'react'
import api from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('ns_user')) } catch { return null }
  })

  const save = (token, u) => {
    localStorage.setItem('ns_token', token)
    localStorage.setItem('ns_user', JSON.stringify(u))
    setUser(u)
  }
  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    save(data.token, data.user)
    return data.user
  }
  const register = async (name, email, password) => {
    const { data } = await api.post('/auth/register', { name, email, password })
    save(data.token, data.user)
    return data.user
  }
  const markProfile = () => {
    const u = { ...user, has_profile: true }
    localStorage.setItem('ns_user', JSON.stringify(u))
    setUser(u)
  }
  const logout = () => {
    localStorage.removeItem('ns_token')
    localStorage.removeItem('ns_user')
    setUser(null)
  }
  return <AuthContext.Provider value={{ user, login, register, logout, markProfile }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
