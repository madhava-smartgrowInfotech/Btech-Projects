import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from './api'

/** Pipeline progress flags from /api/state - the React twin of Streamlit's st.session_state checks. */
const Ctx = createContext(null)

export function PipelineProvider({ children }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const s = await api('/api/state')
      setState(s)
      setError(null)
      return s
    } catch (e) {
      setError(e)
      return null
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const value = useMemo(() => ({ state, error, refresh }), [state, error, refresh])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const usePipeline = () => useContext(Ctx)
