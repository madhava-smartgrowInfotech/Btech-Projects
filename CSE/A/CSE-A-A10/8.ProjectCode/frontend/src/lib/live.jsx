import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import api, { describeError } from '../api'
import { logEvent } from './activity'

// The one shared live simulation (server side). Every screen that needs it reads it from here, so a
// change made on Live control shows up on Prediction and Violations without refetching blindly.
const LiveContext = createContext(null)
export const useLive = () => useContext(LiveContext)

export function LiveProvider({ children }) {
  const [snap, setSnap] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [version, setVersion] = useState(0) // bumps whenever the sim was restarted or changed by a non-live screen
  const gate = useRef(Promise.resolve())

  const refresh = useCallback(async () => {
    try {
      const r = await api.get('/live', { silent: true })
      setSnap(r.data)
      setError(null)
    } catch (e) {
      setError(describeError(e))
    }
  }, [])
  useEffect(() => { refresh() }, [refresh])

  // Requests are serialised so quick clicks never race each other.
  const run = useCallback((fn, { quiet = false } = {}) => {
    const next = gate.current.then(async () => {
      if (!quiet) setBusy(true)
      try {
        const r = await fn()
        setSnap(r.data)
        setError(null)
        return r.data
      } catch (e) {
        const d = describeError(e)
        if (!quiet) setError(d)
        throw d
      } finally {
        if (!quiet) setBusy(false)
      }
    })
    gate.current = next.catch(() => {})
    return next
  }, [])

  const actions = useMemo(() => ({
    refresh,
    configure: (patch) => run(() => api.put('/live/config', patch)).then((d) => { if (patch.grid) setVersion((v) => v + 1); return d }),
    step: (seconds, opts) => run(() => api.post('/live/step', { seconds }, opts?.quiet ? { silent: true } : undefined), opts),
    ambulance: () => run(() => api.post('/live/ambulance')).then((d) => { logEvent('ui', `ambulance sent into J${d.entry.junction} ${d.entry.approach}`); return d }),
    reset: () => run(() => api.post('/live/reset')).then((d) => { setVersion((v) => v + 1); return d }),
    simulate: () => run(() => api.post('/prediction/simulate')),
  }), [refresh, run])

  const value = useMemo(() => ({ snap, error, busy, version, ...actions }), [snap, error, busy, version, actions])
  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>
}
