import { useCallback, useEffect, useRef, useState } from 'react'

/** Runs `fn` on mount (and on `reload`) and tracks loading / error / data. */
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ loading: true, error: null, data: null })
  const seq = useRef(0)
  const run = useCallback(() => {
    const id = ++seq.current
    setState((s) => ({ ...s, loading: true, error: null }))
    fn().then(
      (data) => id === seq.current && setState({ loading: false, error: null, data }),
      (error) => id === seq.current && setState({ loading: false, error, data: null }),
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => {
    run()
  }, [run])
  return { ...state, reload: run, setData: (data) => setState((s) => ({ ...s, data })) }
}
