// localStorage that never throws (private windows, blocked storage). Keys are namespaced "athena.".
const NS = 'athena.'

export function readStore(key) {
  try {
    return window.localStorage.getItem(key.replace(/^am\./, NS))
  } catch {
    return null
  }
}

export function writeStore(key, value) {
  try {
    const k = key.replace(/^am\./, NS)
    if (value === null || value === undefined) window.localStorage.removeItem(k)
    else window.localStorage.setItem(k, value)
  } catch {
    /* storage unavailable: the app still works, the choice just isn't remembered */
  }
}
