import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { api, clearSession, getToken, saveSession, savedUser } from './api'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => (getToken() ? savedUser() : null))

  const signIn = useCallback(async (mode, form) => {
    const data = await api.post(mode === 'login' ? '/auth/login' : '/auth/register', form)
    saveSession(data.token, data.user)
    setUser(data.user)
    return data.user
  }, [])

  const signOut = useCallback(() => {
    clearSession()
    setUser(null)
  }, [])

  // a 401 from any call means the token expired
  useEffect(() => {
    window.addEventListener('cw:unauthorized', signOut)
    return () => window.removeEventListener('cw:unauthorized', signOut)
  }, [signOut])

  const value = useMemo(() => ({ user, signIn, signOut }), [user, signIn, signOut])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

export function RequireAuth({ children }) {
  const { user } = useAuth()
  const loc = useLocation()
  if (!user || !getToken()) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return children
}
