// localStorage can throw (private mode, blocked storage) — every access is guarded.
export function readStore(key, fallback = null) {
  try {
    const v = window.localStorage.getItem(key)
    return v === null ? fallback : v
  } catch {
    return fallback
  }
}

export function writeStore(key, value) {
  try {
    if (value === null || value === undefined) window.localStorage.removeItem(key)
    else window.localStorage.setItem(key, value)
  } catch {
    /* storage unavailable: keep working in memory */
  }
}
