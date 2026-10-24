import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import api, { describeError, errorMessage } from '../api'
import { mitLabel, pct } from '../format'
import { logEvent } from './activity'

// One shared poller for the whole console: session status, detections, host health and mitigations.
const LiveContext = createContext(null)
export const useLive = () => useContext(LiveContext)

const POLL_MS = 3000

export function LiveProvider({ children }) {
  const [status, setStatus] = useState(null)
  const [det, setDet] = useState(null) // { detections, by_prediction, by_severity }
  const [health, setHealth] = useState(null)
  const [mit, setMit] = useState(null)
  const [error, setError] = useState(null)
  const [loaded, setLoaded] = useState(false)
  const [updatedAt, setUpdatedAt] = useState(null)
  const lastId = useRef(null)
  const lastMode = useRef(null)
  const alive = useRef(true)

  const refresh = useCallback(async () => {
    const q = { silent: true }
    const [s, d, h, m] = await Promise.allSettled([
      api.get('/status', q), api.get('/detections', { ...q, params: { limit: 100 } }), api.get('/health', q), api.get('/mitigations', q),
    ])
    if (!alive.current) return
    if (s.status === 'fulfilled' && d.status === 'fulfilled') {
      setError(null)
      setUpdatedAt(Date.now())
    } else {
      const bad = s.status === 'rejected' ? s : d
      if (bad.status === 'rejected') setError(describeError(bad.reason))
    }
    if (s.status === 'fulfilled') {
      setStatus(s.value.data)
      const mode = s.value.data.mode
      if (lastMode.current !== mode) {
        logEvent('health', lastMode.current === null ? `api online · mode ${mode}` : `session mode: ${lastMode.current} -> ${mode}`)
        lastMode.current = mode
      }
    }
    if (d.status === 'fulfilled') {
      setDet(d.value.data)
      const rows = d.value.data.detections || []
      if (rows.length) {
        const newest = rows[0].id
        if (lastId.current !== null && newest !== lastId.current) {
          rows.filter((r) => r.id > lastId.current).reverse().forEach((r) => {
            logEvent(r.prediction === 'Attack' ? 'error' : 'pipeline',
              `window #${r.id} ${r.prediction} ${pct(r.confidence)} · sev ${r.severity} · ${Math.round(r.packet_rate)} pkt/s · ${mitLabel(r.mitigation_status)}`)
          })
        }
        lastId.current = newest
      } else if (lastId.current === null) {
        lastId.current = 0
      }
    }
    if (h.status === 'fulfilled') setHealth(h.value.data)
    if (m.status === 'fulfilled') setMit(m.value.data)
    setLoaded(true)
  }, [])

  useEffect(() => {
    alive.current = true
    refresh()
    const id = setInterval(() => { if (!document.hidden) refresh() }, POLL_MS)
    const vis = () => { if (!document.hidden) refresh() }
    document.addEventListener('visibilitychange', vis)
    return () => { alive.current = false; clearInterval(id); document.removeEventListener('visibilitychange', vis) }
  }, [refresh])

  const [busy, setBusy] = useState(null) // 'live' | 'sim' | 'stop' | null

  // Session control. Resolves { ok, error }.
  const run = useCallback(async (kind, fn) => {
    setBusy(kind)
    try {
      const r = await fn()
      await refresh()
      return { ok: true, data: r.data }
    } catch (e) {
      await refresh()
      return { ok: false, error: errorMessage(e), hint: describeError(e).hint }
    } finally {
      setBusy(null)
    }
  }, [refresh])

  const startLive = useCallback((iface, windowSeconds) => run('live', () => api.post('/monitor/start', { interface: iface, window_seconds: windowSeconds })), [run])
  const startSim = useCallback((windowSeconds = 5) => run('sim', () => api.post('/demo/start', { window_seconds: windowSeconds })), [run])
  const stop = useCallback(() => run('stop', async () => {
    await api.post('/monitor/stop')
    return api.post('/demo/stop')
  }), [run])

  const value = useMemo(() => ({
    status, detections: det?.detections || [], byPrediction: det?.by_prediction || {}, bySeverity: det?.by_severity || {},
    health, mitigations: mit, error, loaded, updatedAt, refresh, busy, startLive, startSim, stop,
  }), [status, det, health, mit, error, loaded, updatedAt, refresh, busy, startLive, startSim, stop])

  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>
}
