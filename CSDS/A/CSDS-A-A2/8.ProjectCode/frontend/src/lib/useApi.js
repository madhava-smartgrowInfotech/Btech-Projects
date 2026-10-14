import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'

/** Load data from a GET endpoint with loading / error / reload (+ optional silent polling). */
export function useApi(path, { enabled = true, interval = 0 } = {}) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(Boolean(enabled && path))
  const ctrl = useRef(null)

  const load = useCallback(
    async (silent = false) => {
      if (!path || !enabled) return
      ctrl.current?.abort()
      const c = new AbortController()
      ctrl.current = c
      if (!silent) setLoading(true)
      try {
        const d = await api(path, { signal: c.signal })
        setData(d)
        setError(null)
      } catch (e) {
        if (e.name !== 'AbortError') setError(e)
      } finally {
        if (ctrl.current === c) setLoading(false)
      }
    },
    [path, enabled],
  )

  useEffect(() => {
    load()
    return () => ctrl.current?.abort()
  }, [load])

  useEffect(() => {
    if (!interval || !enabled) return undefined
    const id = setInterval(() => load(true), interval)
    return () => clearInterval(id)
  }, [interval, enabled, load])

  return { data, error, loading, reload: load, setData }
}
