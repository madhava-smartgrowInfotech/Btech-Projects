import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { api } from './api'

const HealthCtx = createContext({ data: null, error: null, refresh: () => {} })

/** Polls /api/health: every 30 s normally, every 2 s while the model is still loading. */
export function HealthProvider({ children }) {
  const [state, setState] = useState({ data: null, error: null })
  const timer = useRef(null)
  const alive = useRef(true)

  const check = useCallback(async () => {
    clearTimeout(timer.current)
    let next = 30000
    try {
      const data = await api.health()
      if (!alive.current) return
      setState({ data, error: null })
      if (data.model?.status === 'loading' || data.model?.status === 'idle') next = 2000
    } catch (error) {
      if (!alive.current) return
      setState({ data: null, error })
      next = 5000
    }
    timer.current = setTimeout(check, next)
  }, [])

  useEffect(() => {
    alive.current = true
    check()
    return () => {
      alive.current = false
      clearTimeout(timer.current)
    }
  }, [check])

  return <HealthCtx.Provider value={{ ...state, refresh: check }}>{children}</HealthCtx.Provider>
}

export const useHealth = () => useContext(HealthCtx)
