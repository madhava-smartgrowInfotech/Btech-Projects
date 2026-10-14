import { createContext, useContext, useState } from 'react'
import { logEvent } from './activity'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function readUser() {
  try {
    return JSON.parse(localStorage.getItem('ts_user'))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => (localStorage.getItem('ts_token') ? readUser() : null))
  const auth = {
    user,
    signIn(token, u) {
      localStorage.setItem('ts_token', token)
      localStorage.setItem('ts_user', JSON.stringify(u))
      logEvent('auth', `session opened for ${u.email}`)
      setUser(u)
    },
    signOut() {
      localStorage.removeItem('ts_token')
      localStorage.removeItem('ts_user')
      setUser(null)
    },
  }
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}
