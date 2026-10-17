const nf = new Intl.NumberFormat('en-IN')

export const fmtInt = (v) => (v == null || Number.isNaN(v) ? '–' : nf.format(Math.round(v)))
export const fmtNum = (v, d = 1) =>
  v == null ? '–' : Number(v).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d })
export const fmtPct = (v, d = 1) => (v == null ? '–' : `${(v * 100).toFixed(d)}%`)
export const fmtSigned = (v, d = 2, suffix = '%') =>
  v == null ? '–' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(d)}${suffix}`

/** ₹ in millions (as the README reports), e.g. ₹62.2M */
export function fmtINR(v, compact = true) {
  if (v == null) return '–'
  if (!compact) return `₹${nf.format(Math.round(v))}`
  const a = Math.abs(v)
  if (a >= 1e7) return `₹${(v / 1e6).toFixed(1)}M`
  if (a >= 1e5) return `₹${(v / 1e6).toFixed(2)}M`
  if (a >= 1e3) return `₹${(v / 1e3).toFixed(1)}K`
  return `₹${Number(v).toFixed(2)}`
}

export function fmtCompact(v) {
  if (v == null) return '–'
  const a = Math.abs(v)
  if (a >= 1e6) return `${(v / 1e6).toFixed(a >= 1e7 ? 1 : 2)}M`
  if (a >= 1e3) return `${(v / 1e3).toFixed(a >= 1e4 ? 0 : 1)}K`
  return String(Math.round(v))
}

export function monthLabel(p, long = false) {
  if (!p) return ''
  const [y, m] = p.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('en-GB', { month: long ? 'long' : 'short', year: 'numeric' })
}

export function timeAgo(iso) {
  if (!iso) return ''
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.round(s / 60)} min ago`
  if (s < 86400) return `${Math.round(s / 3600)} h ago`
  return `${Math.round(s / 86400)} days ago`
}

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })
export const fmtUSD = (v) => (v == null || Number.isNaN(Number(v)) ? '–' : usd.format(v))
/** value already in 0-100 (as /api/comparison returns it) */
export const fmtPoints = (v, d = 1) => (v == null ? '–' : `${Number(v).toFixed(d)}%`)
