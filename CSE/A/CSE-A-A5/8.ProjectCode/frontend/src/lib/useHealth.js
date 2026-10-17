import { useEffect, useState } from 'react'
import api from '../api'
import { logEvent } from './activity'

// Polls /api/health. state: null (first check pending) | 'ok' (engine loaded) | 'loading' (API up, engine not loaded) | 'down'
export default function useHealth(interval = 10000) {
  const [state, setState] = useState(null)
  const [info, setInfo] = useState(null)
  useEffect(() => {
    let prev = null
    let live = true
    const check = () => api.get('/health', { silent: true })
      .then((r) => {
        if (!live) return
        const s = r.data.engine_loaded ? 'ok' : 'loading'
        if (s !== prev) logEvent('health', `api online - ThreatSense engine ${r.data.engine_loaded ? 'loaded' : 'not loaded yet'}`)
        prev = s
        setInfo(r.data)
        setState(s)
      })
      .catch(() => {
        if (!live) return
        if (prev !== 'down') logEvent('error', 'api unreachable on /api/health')
        prev = 'down'
        setState('down')
      })
    check()
    const id = setInterval(check, interval)
    return () => { live = false; clearInterval(id) }
  }, [interval])
  return { state, info }
}
