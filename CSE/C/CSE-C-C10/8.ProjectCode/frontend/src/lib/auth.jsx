import { createContext, useContext, useEffect, useState } from 'react'
import api from '../api'
import { logEvent } from './activity'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function readUser() {
  try {
    return JSON.parse(localStorage.getItem('vp_user'))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => (localStorage.getItem('vp_token') ? readUser() : null))

  // A stored session is re-checked once on load; an expired token signs the user out quietly.
  useEffect(() => {
    if (!localStorage.getItem('vp_token')) return
    api.get('/auth/me', { silent: true }).catch((e) => {
      if (e.response?.status === 401) {
        localStorage.removeItem('vp_token')
        localStorage.removeItem('vp_user')
        setUser(null)
      }
    })
  }, [])

  const auth = {
    user,
    signIn(token, u) {
      localStorage.setItem('vp_token', token)
      localStorage.setItem('vp_user', JSON.stringify(u))
      logEvent('auth', `session opened for ${u.email}`)
      setUser(u)
    },
    signOut() {
      localStorage.removeItem('vp_token')
      localStorage.removeItem('vp_user')
      setUser(null)
    },
  }
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}
