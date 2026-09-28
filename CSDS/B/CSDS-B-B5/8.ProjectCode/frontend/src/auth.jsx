import { createContext, useContext, useState } from 'react'
import api from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('sb_user')) } catch { return null }
  })

  const save = ({ token, user }) => {
    localStorage.setItem('sb_token', token)
    localStorage.setItem('sb_user', JSON.stringify(user))
    setUser(user)
  }
  const login = async (email, password) => save((await api.post('/auth/login', { email, password })).data)
  const register = async (name, email, password) =>
    save((await api.post('/auth/register', { name, email, password })).data)
  const logout = () => {
    localStorage.removeItem('sb_token')
    localStorage.removeItem('sb_user')
    setUser(null)
  }
  return <AuthContext.Provider value={{ user, login, register, logout }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
