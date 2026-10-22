export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(d))
export const fmtInt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString())
export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`
export const pct = (v) => `${Math.round((Number(v) || 0) * 100)}%`

// Backend timestamps are naive UTC ISO strings; treat them as UTC.
export function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export const SAFETY_LABEL = { emergency: 'Emergency', caution: 'Caution', routine: 'Routine' }
export const SAFETY_TONE = { emergency: 'blocked', caution: 'upcoming', routine: 'pass' }

// Kit leftover, kept so Display.StatusBadge still resolves.
export const STATUS_LABEL = { live: 'Live', upcoming: 'Upcoming', expired: 'Expired', closed: 'Closed' }
