import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../services/api'
import { connectSimulationSocket } from '../services/ws'
import { useToast } from '../components/ui/feedback'

const Ctx = createContext(null)
export const useSimulation = () => useContext(Ctx)

const MAX_LIVE_EVENTS = 300
const REFRESH_ON = ['grid_update', 'simulation_complete', 'simulation_stopped', 'simulation_started', 'simulation_error']

/**
 * Single source of truth for the console: REST snapshot (status, grid, metrics, agents, safety log) refreshed whenever
 * the WebSocket reports a change, plus the live event feed. Screens only read from here and call the actions.
 */
export function SimulationProvider({ children }) {
  const toast = useToast()
  const [status, setStatus] = useState(null)
  const [grid, setGrid] = useState(null)
  const [topology, setTopology] = useState(null)
  const [series, setSeries] = useState([])
  const [summary, setSummary] = useState(null)
  const [agents, setAgents] = useState([])
  const [safety, setSafety] = useState({ events: [], chain_valid: null, total: 0 })
  const [scenarios, setScenarios] = useState([])
  const [events, setEvents] = useState([])
  const [socket, setSocket] = useState('connecting')
  const [error, setError] = useState(null)
  const [ready, setReady] = useState(false)
  const [busy, setBusy] = useState(null)
  const refreshTimer = useRef(null)

  const refresh = useCallback(async () => {
    try {
      const [st, g, m, a, s] = await Promise.all([api.status(), api.gridState(), api.metrics(), api.agents(), api.safetyEvents()])
      setStatus(st)
      setGrid(g)
      setSeries(m.series)
      setSummary(m.summary)
      setAgents(a)
      setSafety(s)
      setError(null)
    } catch (e) {
      setError(`The SafeGrid API is not reachable (${e.message}). Check that the backend is running, then retry.`)
    } finally {
      setReady(true)
    }
  }, [])

  const scheduleRefresh = useCallback(() => {
    clearTimeout(refreshTimer.current)
    refreshTimer.current = setTimeout(refresh, 200)
  }, [refresh])

  const loadStatic = useCallback(() => {
    api.topology().then(setTopology).catch(() => {})
    api.scenarios().then(setScenarios).catch(() => {})
    api.events().then((r) => setEvents(r.events)).catch(() => {})
  }, [])

  useEffect(() => {
    refresh()
    loadStatic()
    const close = connectSimulationSocket({
      onState: setSocket,
      onEvent: (ev) => {
        if (ev.type === 'connected') return
        setEvents((prev) => [ev, ...prev].slice(0, MAX_LIVE_EVENTS))
        if (REFRESH_ON.includes(ev.type)) scheduleRefresh()
        if (ev.type === 'simulation_error') toast({ tone: 'error', title: 'Simulation error', message: ev.data?.error })
        if (ev.type === 'simulation_complete') toast({ tone: 'success', title: 'Simulation complete', message: 'All steps have been run.' })
      },
    })
    return () => {
      clearTimeout(refreshTimer.current)
      close()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refresh, scheduleRefresh, loadStatic])

  const act = useCallback(
    async (name, fn, success) => {
      setBusy(name)
      try {
        const r = await fn()
        setError(null)
        await refresh()
        if (success) toast({ tone: 'success', title: success.title, message: success.message?.(r) })
        return r
      } catch (e) {
        toast({ tone: 'error', title: `Could not ${name}`, message: e.message })
        return null
      } finally {
        setBusy(null)
      }
    },
    [refresh, toast],
  )

  const actions = useMemo(
    () => ({
      start: (cfg, resume = false) => act('start the run', () => api.start(cfg, resume), { title: resume ? 'Run resumed' : 'Run started', message: () => 'Live playback is streaming to the console.' }),
      stop: () => act('stop the run', api.stop, { title: 'Run stopped' }),
      reset: (cfg) =>
        act('reset the run', () => api.reset(cfg), { title: 'Run reset', message: () => 'The grid is back at step 0.' }).then((r) => {
          if (r) setEvents([])
          return r
        }),
      step: () => act('advance one step', api.step, { title: 'Step complete' }),
      runScenario: (id, cfg) => act('run the scenario', () => api.runScenario(id, cfg), { title: 'Scenario finished', message: (r) => `${r?.summary?.proposals ?? 0} proposals checked by the shield.` }),
      refresh,
    }),
    [act, refresh],
  )

  const value = { status, grid, topology, series, summary, agents, safety, scenarios, events, socket, error, ready, busy, ...actions }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
