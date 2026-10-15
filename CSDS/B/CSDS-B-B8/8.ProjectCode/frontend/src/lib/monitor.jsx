import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api } from './api'

const MonitorCtx = createContext(null)

/**
 * One shared poller for /monitor/state. Every protected screen reads it (sidebar status, fall
 * countdown). The Live monitor screen asks for a faster rate while it is open.
 */
export function MonitorProvider({ children }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState(null)
  const fast = useRef(0)
  const [rate, setRate] = useState(1000)

  const refresh = useCallback(async () => {
    try {
      const data = await api.get('/monitor/state')
      setState(data)
      setError(null)
      return data
    } catch (e) {
      setError(e)
      return null
    }
  }, [])

  useEffect(() => {
    let alive = true
    let timer
    const tick = async () => {
      await refresh()
      if (alive) timer = setTimeout(tick, rate)
    }
    tick()
    return () => {
      alive = false
      clearTimeout(timer)
    }
  }, [refresh, rate])

  const requestFast = useCallback(() => {
    fast.current += 1
    setRate(250)
    return () => {
      fast.current -= 1
      if (fast.current <= 0) setRate(1000)
    }
  }, [])

  const value = useMemo(() => ({ state, error, refresh, requestFast }), [state, error, refresh, requestFast])
  return <MonitorCtx.Provider value={value}>{children}</MonitorCtx.Provider>
}

export const useMonitor = () => useContext(MonitorCtx)

// The Live monitor screen calls this to poll at 4 Hz while it is mounted.
export function useFastMonitor() {
  const ctx = useContext(MonitorCtx)
  useEffect(() => ctx.requestFast(), [ctx.requestFast]) // eslint-disable-line react-hooks/exhaustive-deps
  return ctx
}
