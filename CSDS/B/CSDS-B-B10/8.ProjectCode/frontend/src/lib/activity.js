import { useSyncExternalStore } from 'react'

// In-memory event log shown by the ActivityLog panel (API calls, sign-in, errors). Keeps the last 200 events.
const MAX = 200
let events = []
let seq = 0
const listeners = new Set()

function emit() {
  listeners.forEach((l) => l())
}

export function logEvent(kind, text) {
  events = [...events.slice(-(MAX - 1)), { id: ++seq, kind, text, t: Date.now() }]
  emit()
}

export function clearActivity() {
  events = []
  emit()
}

function subscribe(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useActivity() {
  return useSyncExternalStore(subscribe, () => events)
}
