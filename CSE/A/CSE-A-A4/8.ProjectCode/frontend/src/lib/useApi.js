import { useCallback, useEffect, useRef, useState } from 'react'

/** Run an async loader on mount; returns {data, error, loading, reload}. */
export function useApi(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const alive = useRef(true)
  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }))
    return loader()
      .then((data) => alive.current && setState({ data, error: null, loading: false }))
      .catch((error) => alive.current && setState({ data: null, error, loading: false }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => {
    alive.current = true
    run()
    return () => {
      alive.current = false
    }
  }, [run])
  return { ...state, reload: run }
}
