import { useCallback, useEffect, useRef, useState } from 'react'
import api, { describeError } from '../api'

// GET helper with the three states every screen needs: loading, error ({message, hint}) and data.
export function useGet(url, { params, enabled = true, deps = [], retryOn503 = 0 } = {}) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(enabled)
  const tries = useRef(0)
  const timer = useRef(null)

  const load = useCallback(() => {
    if (!enabled) return undefined
    let live = true
    setLoading(true)
    api.get(url, { params })
      .then((r) => { if (live) { setData(r.data); setError(null) } })
      .catch((e) => {
        if (!live) return
        const d = describeError(e)
        // the prediction model trains in the background right after start-up: retry quietly a few times
        if (d.status === 503 && tries.current < retryOn503) {
          tries.current += 1
          timer.current = setTimeout(load, 2500)
          return
        }
        setError(d)
      })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, enabled, JSON.stringify(params), retryOn503, ...deps])

  useEffect(() => {
    tries.current = 0
    const cancel = load()
    return () => { cancel?.(); clearTimeout(timer.current) }
  }, [load])

  const reload = useCallback(() => { tries.current = 0; load() }, [load])
  return { data, error, loading, reload, setData }
}
