// localStorage can throw (private windows, blocked site data) - never let that break the UI.
export function readStore(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function writeStore(key, value) {
  try {
    if (value === null || value === undefined) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    /* ignore */
  }
}
