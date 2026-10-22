import { useSyncExternalStore } from 'react'

// In-memory event stream for the terminal activity log: API calls, pipeline stages, auth, run history.
let events = []
let seq = 0
const subs = new Set()
const emit = () => subs.forEach((f) => f())

export function logEvent(kind, text) {
  events = [...events.slice(-299), { id: ++seq, t: Date.now(), kind, text }]
  emit()
}
export function clearActivity() {
  events = []
  emit()
}
const subscribe = (f) => {
  subs.add(f)
  return () => subs.delete(f)
}
export const useActivity = () => useSyncExternalStore(subscribe, () => events)
