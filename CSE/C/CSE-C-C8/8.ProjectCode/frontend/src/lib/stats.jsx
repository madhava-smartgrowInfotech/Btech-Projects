import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api } from './api'

const StatsCtx = createContext({ health: null, metrics: null, error: null, refresh: () => {} })

// Backend health + model metrics shared by the shell (sidebar footer, topbar) and the dashboard.
export function StatsProvider({ children }) {
  const [state, setState] = useState({ health: null, metrics: null, error: null })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let alive = true
    const load = async () => {
      try {
        const [health, metrics] = await Promise.all([api.health(), api.metrics().catch(() => null)])
        if (alive) setState({ health, metrics, error: null })
      } catch (error) {
        if (alive) setState((s) => ({ ...s, error }))
      }
    }
    load()
    const t = setInterval(load, 30000)
    return () => {
      alive = false
      clearInterval(t)
    }
  }, [tick])

  const value = useMemo(() => ({ ...state, refresh: () => setTick((n) => n + 1) }), [state])
  return <StatsCtx.Provider value={value}>{children}</StatsCtx.Provider>
}

export const useStats = () => useContext(StatsCtx)
