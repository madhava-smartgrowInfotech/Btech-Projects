import { createContext, useContext, useState } from 'react'
import { Navigate } from 'react-router-dom'
import api from './api'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('mq_user'))
    } catch {
      return null
    }
  })

  const save = ({ token, user }) => {
    localStorage.setItem('mq_token', token)
    localStorage.setItem('mq_user', JSON.stringify(user))
    setUser(user)
    return user
  }
  const login = async (email, password) => save((await api.post('/auth/login', { email, password })).data)
  const register = async (body) => save((await api.post('/auth/register', body)).data)
  const logout = () => {
    localStorage.removeItem('mq_token')
    localStorage.removeItem('mq_user')
    setUser(null)
  }
  return <AuthCtx.Provider value={{ user, login, register, logout }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

export function homeFor(user) {
  if (!user) return '/login'
  return { patient: '/book', staff: '/console', admin: '/dashboard' }[user.role] || '/'
}

export function RequireRole({ roles, children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (!roles.includes(user.role)) return <Navigate to={homeFor(user)} replace />
  return children
}
