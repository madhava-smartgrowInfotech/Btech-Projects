import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api'
import { logEvent } from './activity'

const HealthContext = createContext({ health: null, state: 'checking' })
export const useHealth = () => useContext(HealthContext)

/** Polls /api/health. state: ok | loading (models or speech still loading) | down */
export function HealthProvider({ children }) {
  const [health, setHealth] = useState(null)
  const [state, setState] = useState('checking')
  useEffect(() => {
    let alive = true
    let prev = null
    const check = () => api.get('/health', { silent: true })
      .then((r) => {
        if (!alive) return
        const s = r.data.models_loaded && r.data.speech_ready ? 'ok' : 'loading'
        if (s !== prev) logEvent('health', `api online · models ${r.data.models_loaded ? 'ready' : 'loading'} · speech ${r.data.speech_ready ? 'ready' : 'loading'} · ${r.data.online ? 'online' : 'offline'}`)
        prev = s
        setHealth(r.data)
        setState(s)
      })
      .catch(() => {
        if (!alive) return
        if (prev !== 'down') logEvent('error', 'api unreachable on /api/health')
        prev = 'down'
        setHealth(null)
        setState('down')
      })
    check()
    const id = setInterval(check, 15000)
    return () => { alive = false; clearInterval(id) }
  }, [])
  const value = useMemo(() => ({ health, state }), [health, state])
  return <HealthContext.Provider value={value}>{children}</HealthContext.Provider>
}
