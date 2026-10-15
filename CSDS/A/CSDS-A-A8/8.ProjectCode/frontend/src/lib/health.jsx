import { createContext, useContext } from 'react'
import { api } from './api'
import { useAsync } from './useAsync'

const HealthCtx = createContext({ online: undefined })

// One shared poll of /api/health - drives the "API online / offline" badges.
export function HealthProvider({ children }) {
  const { data, error } = useAsync(() => api.get('/health', { auth: false }), [], { poll: 30000 })
  const online = error ? false : data ? true : undefined
  return <HealthCtx.Provider value={{ online }}>{children}</HealthCtx.Provider>
}

export const useHealth = () => useContext(HealthCtx)
