import { createContext, useContext, useEffect, useState } from 'react'
import api from './api'

const AuthContext = createContext(null)
const TOKEN = 'av_token'
const USER = 'av_user'

function hasToken() {
  try {
    return !!localStorage.getItem(TOKEN)
  } catch {
    return false
  }
}

function cachedUser() {
  try {
    return JSON.parse(localStorage.getItem(USER))
  } catch {
    return null
  }
}

function remember(token, user) {
  try {
    if (token) localStorage.setItem(TOKEN, token)
    localStorage.setItem(USER, JSON.stringify(user))
  } catch {
    /* storage blocked: the session lasts until the tab closes */
  }
}

function forget() {
  try {
    localStorage.removeItem(TOKEN)
    localStorage.removeItem(USER)
  } catch {
    /* nothing stored */
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(cachedUser)
  // A stored token is checked once with the server before protected pages render.
  const [ready, setReady] = useState(() => !hasToken())

  useEffect(() => {
    if (!hasToken()) return undefined
    let alive = true
    api
      .get('/auth/me')
      .then(({ data }) => {
        if (!alive) return
        setUser(data)
        remember(null, data)
      })
      .catch((err) => {
        // 401 means the token is no longer valid. Any other error keeps the cached user (for example, API offline).
        if (alive && err.response?.status === 401) setUser(null)
      })
      .finally(() => {
        if (alive) setReady(true)
      })
    return () => {
      alive = false
    }
  }, [])

  async function login(email, password) {
    const { data } = await api.post('/auth/login', { email, password })
    remember(data.token, data.user)
    setUser(data.user)
    return data.user
  }

  function logout() {
    forget()
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, ready, login, logout }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
