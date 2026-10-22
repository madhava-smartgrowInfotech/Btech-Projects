import { useCallback, useEffect, useState } from 'react'
import api, { describeError } from '../api'

// GET `url` once (and again on reload()). { data, error: {message, hint} | null, loading }
export default function useFetch(url, config) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const [tick, setTick] = useState(0)
  const reload = useCallback(() => setTick((t) => t + 1), [])
  useEffect(() => {
    let live = true
    setState((s) => ({ ...s, loading: true, error: null }))
    api.get(url, config)
      .then((r) => live && setState({ data: r.data, error: null, loading: false }))
      .catch((e) => live && setState({ data: null, error: describeError(e), loading: false }))
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, tick])
  return { ...state, reload }
}
