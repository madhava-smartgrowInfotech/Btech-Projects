import { useEffect, useState } from 'react'
import { api } from './api'

let cache = null
let inflight = null

/** Public backend settings (thresholds, challenges, manual-location flag…), fetched once. */
export function loadConfig(force = false) {
  if (cache && !force) return Promise.resolve(cache)
  if (!inflight || force) {
    inflight = api('/api/config', { auth: false })
      .then((c) => {
        cache = c
        return c
      })
      .finally(() => {
        inflight = null
      })
  }
  return inflight
}

export function useConfig() {
  const [config, setConfig] = useState(cache)
  const [error, setError] = useState(null)
  useEffect(() => {
    let live = true
    loadConfig(true)
      .then((c) => live && setConfig(c))
      .catch((e) => live && setError(e))
    return () => {
      live = false
    }
  }, [])
  return { config, error }
}
