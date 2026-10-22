import { useCallback, useEffect, useRef, useState } from 'react'

/** Loads data from `fn(signal)` on mount; exposes {data, error, loading, reload}. */
export function useLoad(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const [tick, setTick] = useState(0)
  const ref = useRef(fn)
  ref.current = fn
  useEffect(() => {
    const ac = new AbortController()
    setState((s) => ({ ...s, loading: true, error: null }))
    ref.current(ac.signal)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ data: null, error, loading: false })
      })
    return () => ac.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])
  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { ...state, reload }
}

export function useDocTitle(title) {
  useEffect(() => {
    document.title = title
  }, [title])
}
