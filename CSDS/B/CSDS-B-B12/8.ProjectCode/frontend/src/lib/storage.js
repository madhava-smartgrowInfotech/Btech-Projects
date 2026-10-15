// localStorage wrappers: private windows and blocked site data make these throw, so never let them crash the app.
export function readStore(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function writeStore(key, value) {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* storage unavailable - the preference simply is not remembered */
  }
}
