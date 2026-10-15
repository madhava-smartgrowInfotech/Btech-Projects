import { useSyncExternalStore } from 'react'

const MAX = 300
let events = []
let seq = 0
const subs = new Set()
const emit = () => subs.forEach((f) => f())

/** kind: api | sign | speech | auth | error | health | history | ui */
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
  return useSyncExternalStore((f) => { subs.add(f); return () => subs.delete(f) }, () => events)
}
