import { useEffect, useState } from 'react'
import { api } from './api'

// Public settings (disclaimer text, accepted formats, LLM availability) - fetched once, shared by every screen.
let cached = null
let pending = null

function load() {
  if (cached) return Promise.resolve(cached)
  if (!pending) {
    pending = api
      .config()
      .then((c) => (cached = c))
      .finally(() => {
        pending = null
      })
  }
  return pending
}

export function useConfig() {
  const [config, setConfig] = useState(cached)
  const [error, setError] = useState(null)
  useEffect(() => {
    if (cached) return undefined
    let live = true
    load()
      .then((c) => live && setConfig(c))
      .catch((e) => live && setError(e))
    return () => {
      live = false
    }
  }, [])
  return { config, error }
}
