import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import confetti from 'canvas-confetti'
import { api } from './api'
import { useAuth } from './auth'

const Ctx = createContext(null)

/** Mirrors GET /api/state (dataset, active model, thresholds) and refreshes it after every mutation. */
export function AppStateProvider({ children }) {
  const { user } = useAuth()
  const [state, setState] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const s = await api.state()
      setState(s)
      setError(null)
      return s
    } catch (e) {
      setError(e)
      return null
    }
  }, [])

  useEffect(() => {
    if (!user) {
      setState(null)
      return
    }
    setLoading(true)
    refresh().finally(() => setLoading(false))
  }, [user, refresh])

  const value = useMemo(
    () => ({
      state,
      error,
      loading,
      refresh,
      hasData: Boolean(state?.dataset?.prepared),
      hasModel: Boolean(state?.model),
      hasTrial: Boolean(state?.trained_models?.length),
    }),
    [state, error, loading, refresh],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const useAppState = () => useContext(Ctx)

/** A short celebration; skipped under prefers-reduced-motion. */
export function celebrate() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  confetti({ particleCount: 90, spread: 70, origin: { y: 0.7 }, colors: ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF', '#FFB8C6'], disableForReducedMotion: true })
}

/** Changes whenever the dataset or the active model changes; use as a dependency to refetch. */
export function useStateKey() {
  const { state } = useAppState()
  return [state?.dataset?.name, state?.dataset?.prepared_rows, state?.model?.name, state?.model?.saved_at, JSON.stringify(state?.thresholds)].join('|')
}
