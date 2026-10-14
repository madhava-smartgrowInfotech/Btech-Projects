import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { logEvent } from './activity'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function stored() {
  try {
    const token = localStorage.getItem('sc_token')
    const user = JSON.parse(localStorage.getItem('sc_user') || 'null')
    return token && user ? { token, user } : null
  } catch {
    return null
  }
}

// Session = token + user, kept in localStorage so a reload stays signed in.
export function AuthProvider({ children }) {
  const [session, setSession] = useState(stored)
  const navigate = useNavigate()

  const signIn = useCallback((data) => {
    try {
      localStorage.setItem('sc_token', data.token)
      localStorage.setItem('sc_user', JSON.stringify(data.user))
    } catch {
      /* private mode: the session lasts until the tab closes */
    }
    setSession({ token: data.token, user: data.user })
    logEvent('auth', `signed in as ${data.user.email}`)
  }, [])

  const signOut = useCallback(() => {
    try {
      localStorage.removeItem('sc_token')
      localStorage.removeItem('sc_user')
    } catch {
      /* nothing stored */
    }
    setSession(null)
    logEvent('auth', 'signed out')
    navigate('/login')
  }, [navigate])

  // The API client fires this when the token is rejected (401): end the session here.
  useEffect(() => {
    const expired = () => {
      setSession(null)
      try {
        localStorage.removeItem('sc_token')
        localStorage.removeItem('sc_user')
      } catch {
        /* nothing stored */
      }
      logEvent('auth', 'session expired')
      navigate('/login')
    }
    window.addEventListener('sc:signed-out', expired)
    return () => window.removeEventListener('sc:signed-out', expired)
  }, [navigate])

  const value = useMemo(() => ({ user: session?.user ?? null, signIn, signOut }), [session, signIn, signOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
