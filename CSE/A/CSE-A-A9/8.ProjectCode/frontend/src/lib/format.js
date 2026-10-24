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

export const fmtScore = (v) => (v == null ? '–' : `${Math.round(v * 100)}%`)
export const fmtMetric = (v, d = 3) => (v == null ? '–' : Number(v).toFixed(d))
export const fmtSeconds = (v) => (v == null ? '–' : v < 1 ? `${(v * 1000).toFixed(0)} ms` : `${v.toFixed(2)} s`)
export const fmtHour = (h) => `${String(h).padStart(2, '0')}:00`
export const fmtDays = (d) => {
  if (d == null) return '–'
  if (d < 60) return `${d} days`
  if (d < 730) return `${Math.round(d / 30)} months`
  return `${(d / 365).toFixed(1)} years`
}
export function fmtDateTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}
