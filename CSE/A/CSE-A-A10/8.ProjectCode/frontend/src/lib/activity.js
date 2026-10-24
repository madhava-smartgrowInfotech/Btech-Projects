import { useSyncExternalStore } from 'react'

// In-memory event log that backs the terminal-style activity drawer: real API calls, sign-in, simulator actions.
const MAX = 200
let events = []
let seq = 0
const listeners = new Set()

export function logEvent(kind, text) {
  seq += 1
  events = [...events.slice(-(MAX - 1)), { id: seq, t: Date.now(), kind, text }]
  listeners.forEach((l) => l())
}

export function clearActivity() {
  events = []
  listeners.forEach((l) => l())
}

const subscribe = (cb) => {
  listeners.add(cb)
  return () => listeners.delete(cb)
}
export const useActivity = () => useSyncExternalStore(subscribe, () => events)
