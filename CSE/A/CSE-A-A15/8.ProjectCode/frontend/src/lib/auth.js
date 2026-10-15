import { useNavigate } from 'react-router-dom'
import { clearSession, getUser } from '../api'
import { logEvent } from './activity'

// Session view for the shell. The token itself never leaves api.js.
export function useAuth() {
  const nav = useNavigate()
  const name = getUser()
  return {
    user: name ? { name } : null,
    signOut() {
      clearSession()
      logEvent('auth', 'signed out')
      nav('/login')
    },
  }
}
