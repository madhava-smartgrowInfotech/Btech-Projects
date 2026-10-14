import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { api } from './api'

// Shared /api/stats + /api/config snapshot: KPIs, model metrics and the retraining flag.
const StatsCtx = createContext(null)

export function StatsProvider({ children }) {
  const [stats, setStats] = useState(null)
  const [config, setConfig] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [watching, setWatching] = useState(false)
  const listeners = useRef(new Set())
  const wasRetraining = useRef(false)

  const refresh = useCallback(async () => {
    try {
      const s = await api.stats()
      if (wasRetraining.current && !s.retraining) listeners.current.forEach((fn) => fn(s))
      wasRetraining.current = !!s.retraining
      setStats(s)
      setError(null)
      return s
    } catch (e) {
      setError(e)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const loadConfig = useCallback(() => api.config().then(setConfig).catch(() => {}), [])

  useEffect(() => {
    refresh()
    loadConfig()
  }, [refresh, loadConfig])

  // reload config once the backend comes back after being unreachable
  useEffect(() => {
    if (stats && !config) loadConfig()
  }, [stats, config, loadConfig])

  // poll quickly while a retrain runs, slowly otherwise
  const fast = watching || !!stats?.retraining
  useEffect(() => {
    const t = setInterval(refresh, fast ? 3000 : 30000)
    return () => clearInterval(t)
  }, [fast, refresh])

  useEffect(() => {
    if (!watching) return undefined
    // stop the fast poll after 10 minutes even if the flag never flips
    const t = setTimeout(() => setWatching(false), 600000)
    return () => clearTimeout(t)
  }, [watching])

  const onRetrainDone = useCallback((fn) => {
    listeners.current.add(fn)
    return () => listeners.current.delete(fn)
  }, [])

  const watchRetrain = useCallback(() => {
    wasRetraining.current = true
    setWatching(true)
  }, [])

  useEffect(() => {
    if (watching && stats && !stats.retraining && !wasRetraining.current) setWatching(false)
  }, [watching, stats])

  const metrics = stats?.metrics && Object.keys(stats.metrics).length ? stats.metrics : null
  const value = {
    stats,
    config,
    error,
    loading,
    refresh,
    ti: stats?.threat_intel,
    metrics,
    retraining: !!stats?.retraining,
    watchRetrain,
    onRetrainDone,
  }
  return <StatsCtx.Provider value={value}>{children}</StatsCtx.Provider>
}

export const useStats = () => useContext(StatsCtx)
