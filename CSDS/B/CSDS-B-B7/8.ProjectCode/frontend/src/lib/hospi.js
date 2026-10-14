/* Formatting and shared constants for the HospiSense screens. */
export const FACILITIES = ['A', 'B', 'C', 'D', 'E']

export const pct = (x, d = 0) => (x === null || x === undefined ? '—' : `${(x * 100).toFixed(d)}%`)

export const num = (x, d = 2) => (x === null || x === undefined || Number.isNaN(Number(x)) ? '—' : Number(x).toFixed(d))

export const shortDate = (iso) => {
  const d = new Date(`${iso}T00:00:00`)
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

/** Warning tone for a ratio of demand to capacity: critical at 100%+, watch at 90%+. */
export const loadTone = (ratio) => (ratio >= 1 ? 'critical' : ratio >= 0.9 ? 'watch' : 'ok')

/** Colour used for a delta badge (a CSS value from the kit tokens). */
export const TONE_COLOR = {
  critical: 'var(--coral)',
  watch: 'var(--amber)',
  ok: 'var(--lime)',
}
