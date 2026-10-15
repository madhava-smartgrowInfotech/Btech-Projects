import { useSyncExternalStore } from 'react'

// Client-side event feed for the activity drawer: API calls, auth and errors seen by this page.
// Kept in memory only. Nothing here is sent anywhere.
const MAX = 200
let events = []
let nextId = 1
const listeners = new Set()

function subscribe(cb) {
  listeners.add(cb)
  return () => listeners.delete(cb)
}
const emit = () => listeners.forEach((cb) => cb())

export function logEvent(kind, text) {
  events = [...events.slice(-(MAX - 1)), { id: nextId++, t: Date.now(), kind, text }]
  emit()
}

export function clearActivity() {
  events = []
  emit()
}

export function useActivity() {
  return useSyncExternalStore(subscribe, () => events)
}
