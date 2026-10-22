import { useSyncExternalStore } from 'react'

// Tiny event store behind the terminal-style activity log: API calls, health changes, UI actions.
const MAX = 200
let events = []
let seq = 0
const listeners = new Set()

function emit() {
  listeners.forEach((l) => l())
}

export function logEvent(kind, text) {
  seq += 1
  events = [...events.slice(-(MAX - 1)), { id: seq, t: Date.now(), kind, text }]
  emit()
}

export function clearActivity() {
  events = []
  emit()
}

export function useActivity() {
  return useSyncExternalStore(
    (cb) => { listeners.add(cb); return () => listeners.delete(cb) },
    () => events,
  )
}
