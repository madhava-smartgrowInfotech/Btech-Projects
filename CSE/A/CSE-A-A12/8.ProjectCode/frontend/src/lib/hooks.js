import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'

/** Run an async loader on mount (and when deps change); exposes {data, error, loading, reload}. */
export function useAsync(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const seq = useRef(0)
  const run = useCallback(() => {
    const id = ++seq.current
    setState((s) => ({ ...s, loading: true, error: null }))
    loader().then(
      (data) => id === seq.current && setState({ data, error: null, loading: false }),
      (error) => id === seq.current && setState({ data: null, error, loading: false }),
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => {
    run()
    return () => {
      seq.current++
    }
  }, [run])
  return { ...state, reload: run }
}

let healthCache = null
/** Public model/API status, cached for the session. */
export function useHealth() {
  const [health, setHealth] = useState(healthCache)
  useEffect(() => {
    let alive = true
    const poll = (tries) =>
      api.health().then(
        (h) => {
          healthCache = h
          if (alive) setHealth(h)
          // the model warms up in the background; re-check until it is ready
          if (!h.model_ready && tries < 20) setTimeout(() => alive && poll(tries + 1), 1500)
        },
        () => {},
      )
    if (!healthCache?.model_ready) poll(0)
    return () => {
      alive = false
    }
  }, [])
  return health
}

export function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} · PneumoDetect` : 'PneumoDetect - Pneumonia Detection Using Deep Learning'
  }, [title])
}
