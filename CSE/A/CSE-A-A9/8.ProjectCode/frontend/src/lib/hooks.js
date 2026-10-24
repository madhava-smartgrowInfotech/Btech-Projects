import { useCallback, useEffect, useRef, useState } from 'react'

/** Run an async loader, tracking loading/error; reload() re-runs it. Stale responses are ignored. */
export function useAsync(loader, deps = [], { enabled = true } = {}) {
  const [s, setS] = useState({ data: null, loading: enabled, error: null })
  const seq = useRef(0)
  const run = useCallback(() => {
    const id = ++seq.current
    setS((p) => ({ ...p, loading: true, error: null }))
    return Promise.resolve()
      .then(loader)
      .then((data) => {
        if (id === seq.current) setS({ data, loading: false, error: null })
        return data
      })
      .catch((error) => {
        if (id === seq.current) setS((p) => ({ data: p.data, loading: false, error }))
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => {
    if (enabled) run()
  }, [run, enabled])
  return { ...s, reload: run }
}

export function useDebounced(value, ms = 350) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}
