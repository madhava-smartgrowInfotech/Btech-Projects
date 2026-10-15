import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api'
import { logEvent } from './activity'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function stored() {
  try { return JSON.parse(localStorage.getItem('sb_user')) } catch { return null }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(stored)

  const save = useCallback(({ token, user }) => {
    try { localStorage.setItem('sb_token', token); localStorage.setItem('sb_user', JSON.stringify(user)) } catch { /* ignore */ }
    setUser(user)
    logEvent('auth', `signed in as ${user.email}`)
    return user
  }, [])
  const signIn = useCallback(async (email, password) => save((await api.post('/auth/login', { email, password })).data), [save])
  const register = useCallback(async (name, email, password) => save((await api.post('/auth/register', { name, email, password })).data), [save])
  const signOut = useCallback(() => {
    try { localStorage.removeItem('sb_token'); localStorage.removeItem('sb_user') } catch { /* ignore */ }
    setUser(null)
    logEvent('auth', 'signed out')
  }, [])

  // a 401 from any request ends the session
  useEffect(() => {
    const on = () => setUser(null)
    window.addEventListener('sb:unauthorized', on)
    return () => window.removeEventListener('sb:unauthorized', on)
  }, [])

  const value = useMemo(() => ({ user, signIn, register, signOut }), [user, signIn, register, signOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
