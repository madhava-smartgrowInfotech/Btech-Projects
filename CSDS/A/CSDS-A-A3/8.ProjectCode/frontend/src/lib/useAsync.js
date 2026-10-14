import { useCallback, useEffect, useRef, useState } from 'react'

// Runs an async loader and tracks loading / error / data. Changing `deps` re-runs it.
export function useAsync(loader, deps = [], { poll = 0, enabled = true } = {}) {
  const [state, setState] = useState({ data: undefined, error: null, loading: enabled })
  const ref = useRef(loader)
  ref.current = loader
  const seq = useRef(0)

  const run = useCallback(async ({ quiet = false } = {}) => {
    const id = ++seq.current
    if (!quiet) setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await ref.current()
      if (id === seq.current) setState({ data, error: null, loading: false })
      return data
    } catch (error) {
      if (error?.name === 'AbortError') return undefined
      // a failed background refresh keeps the last good data on screen
      if (id === seq.current) setState((s) => ({ data: quiet ? s.data : undefined, error: quiet ? s.error : error, loading: false }))
      return undefined
    }
  }, [])

  useEffect(() => {
    if (!enabled) return undefined
    run()
    if (!poll) return undefined
    const t = setInterval(() => run({ quiet: true }), poll)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, enabled, poll])

  return { ...state, reload: run }
}
