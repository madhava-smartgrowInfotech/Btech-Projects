const nf = new Intl.NumberFormat('en-US')

export const fmtInt = (v) => (v == null || Number.isNaN(v) ? '–' : nf.format(Math.round(v)))
export const fmtNum = (v, d = 2) =>
  v == null || Number.isNaN(v) ? '–' : Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })
export const fmtPct = (v, d = 1) => (v == null ? '–' : `${(v * 100).toFixed(d)}%`)
export const fmtSigned = (v, d = 2, suffix = '%') =>
  v == null ? '–' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(d)}${suffix}`

/** US dollars, e.g. $368.16 */
export const fmtUSD = (v, d = 2) => (v == null || Number.isNaN(v) ? '–' : `$${fmtNum(v, d)}`)

export function fmtCompact(v) {
  if (v == null) return '–'
  const a = Math.abs(v)
  if (a >= 1e9) return `${(v / 1e9).toFixed(2)}B`
  if (a >= 1e6) return `${(v / 1e6).toFixed(2)}M`
  if (a >= 1e3) return `${(v / 1e3).toFixed(1)}K`
  return String(Math.round(v))
}

/** 2026-10-19 -> "19 Oct" (long: "19 Oct 2026") */
export function dateLabel(iso, long = false) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', long ? { day: 'numeric', month: 'short', year: 'numeric' } : { day: 'numeric', month: 'short' })
}

/** Next `n` business days after an ISO date (same calendar the backend uses for its forecast overlay). */
export function nextBusinessDays(iso, n) {
  const [y, m, d] = iso.split('-').map(Number)
  const cur = new Date(Date.UTC(y, m - 1, d))
  const out = []
  while (out.length < n) {
    cur.setUTCDate(cur.getUTCDate() + 1)
    const dow = cur.getUTCDay()
    if (dow !== 0 && dow !== 6) out.push(cur.toISOString().slice(0, 10))
  }
  return out
}

export function timeAgo(iso) {
  if (!iso) return ''
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.round(s / 60)} min ago`
  if (s < 86400) return `${Math.round(s / 3600)} h ago`
  return `${Math.round(s / 86400)} days ago`
}
