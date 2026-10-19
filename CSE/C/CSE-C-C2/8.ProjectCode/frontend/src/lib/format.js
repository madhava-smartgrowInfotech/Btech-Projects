export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(d))
export const fmtInt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString())
export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

// Labels used by the kit's StatusBadge.
export const STATUS_LABEL = { ok: 'Ready', pending: 'Pending', failed: 'Failed', live: 'Live' }

/** Seconds -> "1m 24s" / "38s" / "0.4s". */
export function fmtDuration(sec) {
  const s = Number(sec)
  if (!Number.isFinite(s)) return '—'
  if (s < 10) return `${s.toFixed(1)}s`
  if (s < 60) return `${Math.round(s)}s`
  return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`
}

/** Minutes (float) -> "~2 min" / "<1 min". */
export function fmtMinutes(min) {
  const m = Number(min)
  if (!Number.isFinite(m) || m <= 0) return '—'
  if (m < 1) return '<1 min'
  return `~${Math.round(m)} min`
}

export function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}
