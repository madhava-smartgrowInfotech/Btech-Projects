import { useCallback, useEffect, useRef, useState } from 'react'

/** Run an async loader on mount / when deps change. Returns {data, error, loading, reload}. */
export function useApi(loader, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const seq = useRef(0)
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  const run = useCallback(() => {
    const id = ++seq.current
    setState((s) => ({ ...s, loading: true, error: null }))
    loaderRef.current().then(
      (data) => id === seq.current && setState({ data, error: null, loading: false }),
      (error) => id === seq.current && setState((s) => ({ data: s.data, error, loading: false })),
    )
  }, [])

  useEffect(() => {
    run()
    return () => {
      seq.current++
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { ...state, reload: run }
}
