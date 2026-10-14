/* Browser storage with a guard: private windows and blocked site data can throw or return nothing. */
export function readStore(key) {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

export function writeStore(key, value) {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    /* storage unavailable: the app still works, the preference just is not kept */
  }
}

export function removeStore(key) {
  try {
    window.localStorage.removeItem(key)
  } catch {
    /* see writeStore */
  }
}
