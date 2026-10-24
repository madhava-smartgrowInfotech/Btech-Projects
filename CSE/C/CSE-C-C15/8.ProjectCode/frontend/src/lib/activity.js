import { useSyncExternalStore } from 'react'

// Tiny external store behind the terminal-style activity log (API calls, detections, session changes).
const MAX = 200
let events = []
let seq = 0
const subs = new Set()

export function logEvent(kind, text) {
  seq += 1
  events = [...events.slice(-(MAX - 1)), { id: seq, t: Date.now(), kind, text }]
  subs.forEach((fn) => fn())
}
export function clearActivity() {
  events = []
  subs.forEach((fn) => fn())
}
const subscribe = (fn) => {
  subs.add(fn)
  return () => subs.delete(fn)
}
export const useActivity = () => useSyncExternalStore(subscribe, () => events)
