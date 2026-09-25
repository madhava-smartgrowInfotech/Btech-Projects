import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { ROLE_HOME, useAuth } from '@/store/auth'
import type { Role } from '@/types'

export function ProtectedRoute({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const user = useAuth((s) => s.user)

  if (!user) return <Navigate to="/login" replace />
  if (!roles.includes(user.role)) return <Navigate to={ROLE_HOME[user.role]} replace />

  return <>{children}</>
}
