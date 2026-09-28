import { useCallback, useEffect, useState } from 'react'
import api, { errorText } from './api'

// GET `path` on mount (and when it changes); returns data, loading, error and a reload function.
export default function useApi(path) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const load = useCallback(async () => {
    if (!path) return
    setLoading(true)
    setError('')
    try {
      const r = await api.get(path)
      setData(r.data)
    } catch (e) {
      setError(errorText(e))
    } finally {
      setLoading(false)
    }
  }, [path])
  useEffect(() => {
    load()
  }, [load])
  return { data, loading, error, reload: load, setData }
}
