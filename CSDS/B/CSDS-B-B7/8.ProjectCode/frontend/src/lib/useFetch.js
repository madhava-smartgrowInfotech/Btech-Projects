import { useCallback, useEffect, useRef, useState } from 'react'
import api, { errorMessage } from '../api'

/**
 * GET helper for a screen. Keeps the last good data on error, and ignores answers
 * that arrive after a newer request has started (for example after changing a facility).
 */
export default function useFetch(url, params = {}, { enabled = true } = {}) {
  const [state, setState] = useState({ data: null, error: '', loading: true })
  const key = JSON.stringify(params)
  const latest = useRef(0)

  const load = useCallback(async () => {
    const id = ++latest.current
    setState((s) => ({ ...s, loading: true, error: '' }))
    try {
      const { data } = await api.get(url, { params: JSON.parse(key) })
      if (id === latest.current) setState({ data, error: '', loading: false })
    } catch (err) {
      if (id === latest.current) setState((s) => ({ data: s.data, error: errorMessage(err), loading: false }))
    }
  }, [url, key])

  useEffect(() => {
    if (enabled) load()
  }, [load, enabled])

  return { ...state, reload: load }
}
