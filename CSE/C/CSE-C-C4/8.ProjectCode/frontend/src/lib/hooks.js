import { useCallback, useEffect, useRef, useState } from 'react'
import { useToast } from '../components/ui'

/** Wraps an async state's reload so a manual refresh ends in a visible success toast. */
export function useRefresh(state, title) {
  const toast = useToast()
  const asked = useRef(false)
  useEffect(() => {
    if (!asked.current || state.loading) return
    asked.current = false
    if (!state.error) toast({ kind: 'success', title, message: 'Fresh data loaded from the API.' })
  }, [state.loading, state.error, title, toast])
  return useCallback(() => {
    asked.current = true
    state.reload()
  }, [state])
}

/** Runs `fn(signal)` on mount and whenever `deps` change; exposes loading / error / reload. */
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const [nonce, setNonce] = useState(0)
  const fnRef = useRef(fn)
  fnRef.current = fn
  useEffect(() => {
    const ctl = new AbortController()
    setState((s) => ({ data: s.data, error: null, loading: true }))
    Promise.resolve(fnRef.current(ctl.signal))
      .then((data) => !ctl.signal.aborted && setState({ data, error: null, loading: false }))
      .catch((error) => !ctl.signal.aborted && setState({ data: null, error, loading: false }))
    return () => ctl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce])
  const reload = useCallback(() => setNonce((n) => n + 1), [])
  return { ...state, reload }
}
