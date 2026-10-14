import { useSyncExternalStore } from 'react'

// Small in-memory event log: API calls, sign-ins and errors. Shown by the terminal log panel.
const MAX = 200
let events = []
let seq = 0
const subs = new Set()
const emit = () => subs.forEach((f) => f())

export function logEvent(kind, text) {
  events = [...events.slice(-(MAX - 1)), { id: ++seq, t: Date.now(), kind, text }]
  emit()
}

export function clearActivity() {
  events = []
  emit()
}

export function useActivity() {
  return useSyncExternalStore(
    (cb) => {
      subs.add(cb)
      return () => subs.delete(cb)
    },
    () => events,
  )
}
