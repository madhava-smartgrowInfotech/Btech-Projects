import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../lib/api'
import { fmtPct, fmtTime } from '../lib/format'
import { useToast } from '../components/ui'

const Ctx = createContext(null)
export const useMonitor = () => useContext(Ctx)

export const COUNTDOWN_SECONDS = 15
const LIVE_INTERVAL_MS = 1500
const MAX_POINTS = 40
const MAX_EVENTS = 25

function locate() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => resolve(null),
      { timeout: 3000 },
    )
  })
}

/** Shared app state: sensor pipeline, event log, 15 s confirmation countdown and emergency dispatch. */
export function MonitorProvider({ children }) {
  const toast = useToast()
  const [health, setHealth] = useState({ status: 'loading' })
  const [history, setHistory] = useState([])
  const [events, setEvents] = useState([])
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [live, setLive] = useState(false)
  const [pending, setPending] = useState(null)
  const [countdown, setCountdown] = useState(COUNTDOWN_SECONDS)
  const [dispatching, setDispatching] = useState(false)
  const [dispatch, setDispatch] = useState(null)
  const [dispatchOpen, setDispatchOpen] = useState(false)
  const pendingRef = useRef(null)
  const liveRef = useRef(false)
  liveRef.current = live
  const eventId = useRef(0)

  const refreshHealth = useCallback(async () => {
    setHealth((h) => (h.status === 'ok' ? h : { status: 'loading' }))
    try {
      const h = await api.health()
      setHealth({ status: 'ok', ...h })
    } catch (e) {
      setHealth({ status: 'error', message: e.message })
    }
  }, [])
  useEffect(() => {
    refreshHealth()
  }, [refreshHealth])

  const logEvent = useCallback((text, level = 'None') => {
    setEvents((xs) => [{ id: ++eventId.current, at: fmtTime(), text, level }, ...xs].slice(0, MAX_EVENTS))
  }, [])

  const runReading = useCallback(
    async (reading, source = 'manual') => {
      setBusy(true)
      try {
        const r = await api.predict(reading)
        const f = r.features_used
        setHistory((h) => [...h, { t: fmtTime(), acc: +f.acc_magnitude.toFixed(2), gyro: +f.gyro_magnitude.toFixed(2) }].slice(-MAX_POINTS))
        setResult({ ...r, source, at: fmtTime() })
        setError(null)
        logEvent(
          `${r.accident_detected ? 'ACCIDENT' : 'Normal reading'}: severity ${r.severity_label}, confidence ${fmtPct(r.confidence)}`,
          r.severity_label,
        )
        if ((r.severity_label === 'Moderate' || r.severity_label === 'Severe') && !pendingRef.current) {
          pendingRef.current = r
          setPending(r)
          setCountdown(COUNTDOWN_SECONDS)
          // Do not stream new readings under an open confirmation; the user restarts live monitoring afterwards.
          if (liveRef.current) logEvent('Live monitoring paused while the alert awaits confirmation.')
          setLive(false)
        }
        return r
      } catch (e) {
        setError(e)
        logEvent(`Prediction failed: ${e.message}`, 'Severe')
        return null
      } finally {
        setBusy(false)
      }
    },
    [logEvent],
  )

  const runScenario = useCallback(
    async (scenario) => {
      setBusy(true)
      try {
        const reading = await api.simulate(scenario)
        return await runReading(reading, scenario)
      } catch (e) {
        setError(e)
        logEvent(`Sensor simulation failed: ${e.message}`, 'Severe')
        toast.error(e.message)
        return null
      } finally {
        setBusy(false)
      }
    },
    [runReading, logEvent, toast],
  )

  // Live monitoring: one random reading every 1.5 s, never two requests in flight.
  const inflight = useRef(false)
  useEffect(() => {
    if (!live) return undefined
    const id = setInterval(async () => {
      if (inflight.current) return
      inflight.current = true
      try {
        const reading = await api.simulate('random')
        await runReading(reading, reading.scenario)
      } catch (e) {
        setError(e)
        setLive(false)
        logEvent(`Live monitoring stopped: ${e.message}`, 'Severe')
        toast.error(`Live monitoring stopped: ${e.message}`)
      } finally {
        inflight.current = false
      }
    }, LIVE_INTERVAL_MS)
    return () => clearInterval(id)
  }, [live, runReading, logEvent, toast])

  const sendAlert = useCallback(async () => {
    const r = pendingRef.current
    if (!r) return
    pendingRef.current = null
    setPending(null)
    setDispatching(true)
    try {
      const pos = await locate()
      const data = await api.emergency({ severity_label: r.severity_label, confidence: r.confidence, ...(pos || {}) })
      setDispatch({ ...data, located: Boolean(pos), severity_label: r.severity_label, at: fmtTime() })
      setDispatchOpen(true)
      logEvent(`Emergency alert dispatched (ID ${data.alert_id}).`, 'Severe')
      toast.success(`Alert ${data.alert_id} dispatched.`)
    } catch (e) {
      logEvent(`Alert failed: ${e.message}`, 'Severe')
      toast.error(`Could not dispatch the alert: ${e.message}`, 9000)
    } finally {
      setDispatching(false)
    }
  }, [logEvent, toast])

  const cancelAlert = useCallback(() => {
    pendingRef.current = null
    setPending(null)
    logEvent('User confirmed they are OK. Alert cancelled.')
    toast.info('Alert cancelled. Glad you are safe.')
  }, [logEvent, toast])

  // Countdown ticks while an alert is pending; auto-sends at zero.
  useEffect(() => {
    if (!pending) return undefined
    const id = setInterval(() => setCountdown((c) => c - 1), 1000)
    return () => clearInterval(id)
  }, [pending])
  useEffect(() => {
    if (pending && countdown <= 0) sendAlert()
  }, [pending, countdown, sendAlert])

  const value = useMemo(
    () => ({
      health, refreshHealth, history, events, result, busy, error, live, setLive, pending, countdown, dispatching, dispatch, dispatchOpen,
      setDispatchOpen, runReading, runScenario, sendAlert, cancelAlert, clearError: () => setError(null),
    }),
    [health, refreshHealth, history, events, result, busy, error, live, pending, countdown, dispatching, dispatch, dispatchOpen, runReading, runScenario, sendAlert, cancelAlert],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
