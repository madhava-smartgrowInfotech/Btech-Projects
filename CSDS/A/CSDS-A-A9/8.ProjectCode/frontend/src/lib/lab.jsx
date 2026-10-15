import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from './api'

const LabCtx = createContext(null)

/** Single source of truth for the server-side lab session (GET /api/state). */
export function LabProvider({ children }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const s = await api.state()
      setState(s)
      setError(null)
      return s
    } catch (e) {
      setError(e)
      throw e
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh().catch(() => {})
  }, [refresh])

  const value = useMemo(() => ({ state, error, loading, refresh }), [state, error, loading, refresh])
  return <LabCtx.Provider value={value}>{children}</LabCtx.Provider>
}

export const useLab = () => useContext(LabCtx)
