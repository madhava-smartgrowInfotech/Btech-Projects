import { useCallback, useEffect, useRef, useState } from 'react'

/** Fetch with loading / error / reload. `fn` receives {signal}. */
export function useApi(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const ctrl = useRef(null)
  const load = useCallback(({ quiet = false } = {}) => {
    ctrl.current?.abort()
    const c = new AbortController()
    ctrl.current = c
    if (!quiet) setState((s) => ({ ...s, loading: true, error: null }))
    return fn({ signal: c.signal })
      .then((data) => {
        if (!c.signal.aborted) setState({ data, error: null, loading: false })
      })
      .catch((error) => {
        if (error.name !== 'AbortError' && !c.signal.aborted) setState({ data: null, error, loading: false })
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => {
    load()
    return () => ctrl.current?.abort()
  }, [load])
  return { ...state, reload: load }
}

/** Poll /api/jobs-style status while `active`; calls onDone(status) when the job stops. */
export function usePoll(fn, active, onDone, ms = 2000) {
  const done = useRef(onDone)
  done.current = onDone
  useEffect(() => {
    if (!active) return undefined
    let stop = false
    const tick = async () => {
      try {
        const r = await fn()
        if (stop) return
        if (r && !r.running) {
          done.current?.(r)
          return
        }
      } catch {
        /* transient - keep polling */
      }
      if (!stop) t = setTimeout(tick, ms)
    }
    let t = setTimeout(tick, ms)
    return () => {
      stop = true
      clearTimeout(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, ms])
}
