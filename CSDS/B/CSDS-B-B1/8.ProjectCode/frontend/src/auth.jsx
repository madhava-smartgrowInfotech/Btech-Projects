import { createContext, useContext, useState } from 'react'
import api from './api.js'

const AuthContext = createContext(null)

function stored() {
  try {
    return JSON.parse(localStorage.getItem('cp_user'))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(stored)

  function save({ token, user }) {
    localStorage.setItem('cp_token', token)
    localStorage.setItem('cp_user', JSON.stringify(user))
    setUser(user)
    return user
  }

  const value = {
    user,
    login: async (email, password) => save((await api.post('/auth/login', { email, password })).data),
    register: async (name, email, password) => save((await api.post('/auth/register', { name, email, password })).data),
    logout: () => {
      localStorage.removeItem('cp_token')
      localStorage.removeItem('cp_user')
      setUser(null)
    },
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)

export function homeFor(user) {
  if (!user) return '/login'
  return user.role === 'citizen' ? '/track' : '/queue'
}
