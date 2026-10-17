import { useSyncExternalStore } from 'react'

// Records scored in this browser session (single scores + the first rows of each batch).
// Lives at module level so it survives route changes; the backend only keeps attack alerts.
const MAX = 200
let log = []
let seq = 0
const listeners = new Set()

function emit() {
  log = [...log]
  listeners.forEach((l) => l())
}

export function pushScored(entries) {
  const list = Array.isArray(entries) ? entries : [entries]
  const stamped = list.map((e) => ({ ...e, id: ++seq, time: e.time || Date.now() }))
  log = [...stamped.reverse(), ...log].slice(0, MAX)
  listeners.forEach((l) => l())
}

export function clearScored() {
  log = []
  emit()
}

export function useScored() {
  return useSyncExternalStore(
    (cb) => { listeners.add(cb); return () => listeners.delete(cb) },
    () => log,
  )
}
