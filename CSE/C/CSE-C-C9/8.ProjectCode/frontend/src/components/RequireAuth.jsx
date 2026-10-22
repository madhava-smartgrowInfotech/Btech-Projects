import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'

/** Sends signed-out visitors to /login and returns them to the page they asked for. */
export default function RequireAuth({ children }) {
  const { user } = useAuth()
  const loc = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname + loc.search }} />
  return children
}
