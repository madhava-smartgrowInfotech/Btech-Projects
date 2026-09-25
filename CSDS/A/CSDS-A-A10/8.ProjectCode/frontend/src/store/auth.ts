import { create } from 'zustand'

import type { User } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  setSession: (user: User, token: string) => void
  logout: () => void
}

const storedUser = localStorage.getItem('medflow_user')

export const useAuth = create<AuthState>((set) => ({
  user: storedUser ? (JSON.parse(storedUser) as User) : null,
  token: localStorage.getItem('medflow_token'),
  setSession: (user, token) => {
    localStorage.setItem('medflow_user', JSON.stringify(user))
    localStorage.setItem('medflow_token', token)
    set({ user, token })
  },
  logout: () => {
    localStorage.removeItem('medflow_user')
    localStorage.removeItem('medflow_token')
    set({ user: null, token: null })
  },
}))

export const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrator',
  doctor: 'Doctor',
  nurse: 'Nurse',
  lab_tech: 'Lab Technician',
  reception: 'Reception',
}

export const ROLE_HOME: Record<string, string> = {
  admin: '/app/admin',
  doctor: '/app/doctor',
  nurse: '/app/nurse',
  lab_tech: '/app/lab',
  reception: '/app/reception',
}
