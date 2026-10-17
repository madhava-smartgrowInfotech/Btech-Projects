import { useSyncExternalStore } from 'react'

// Tiny event store behind the terminal-style activity log: real API calls and UI actions only.
const MAX = 200
let events = []
let seq = 0
const listeners = new Set()

function emit() {
  events = [...events]
  listeners.forEach((l) => l())
}

export function logEvent(kind, text) {
  seq += 1
  events.push({ id: seq, t: Date.now(), kind, text })
  if (events.length > MAX) events.splice(0, events.length - MAX)
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
