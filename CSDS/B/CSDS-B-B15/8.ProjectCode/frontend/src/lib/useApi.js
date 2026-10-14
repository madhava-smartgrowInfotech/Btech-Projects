import { useCallback, useEffect, useRef, useState } from 'react'
import { describeError } from '../api'

/**
 * Runs `fetcher()` on mount and whenever `deps` change.
 * Returns { data, error, loading, reload, setData }. A failed reload keeps the last good data.
 */
export default function useApi(fetcher, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const seq = useRef(0)

  const run = useCallback(() => {
    const id = ++seq.current
    setState((s) => ({ ...s, loading: true, error: null }))
    return fetcher()
      .then((data) => {
        if (id === seq.current) setState({ data, error: null, loading: false })
        return data
      })
      .catch((e) => {
        if (id === seq.current) setState((s) => ({ ...s, error: describeError(e), loading: false }))
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    run()
  }, [run])

  const setData = useCallback((d) => setState((s) => ({ ...s, data: typeof d === 'function' ? d(s.data) : d })), [])
  return { ...state, reload: run, setData }
}
