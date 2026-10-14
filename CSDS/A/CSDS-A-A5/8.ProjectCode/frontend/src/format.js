export function inr(x) {
  if (x === null || x === undefined) return '-'
  const v = Number(x)
  if (Math.abs(v) >= 1e7) return `₹${(v / 1e7).toFixed(2)} Cr`
  if (Math.abs(v) >= 1e5) return `₹${(v / 1e5).toFixed(2)} L`
  return `₹${Math.round(v).toLocaleString('en-IN')}`
}
export const pct = (x, d = 0) => (x === null || x === undefined ? '-' : `${(x * 100).toFixed(d)}%`)
export const num = (x) => (x === null || x === undefined ? '-' : Math.round(Number(x)).toLocaleString('en-IN'))
export const fixed = (x, d = 2) => (x === null || x === undefined ? '-' : Number(x).toFixed(d))
export const monthLabel = (m) => {
  const [y, mo] = m.split('-')
  return new Date(Number(y), Number(mo) - 1, 1).toLocaleString('en', { month: 'short' }) + ' ' + y.slice(2)
}
export const clock = (t) => new Date(t).toLocaleTimeString('en-GB', { hour12: false })
export const stamp = (t) => (t ? new Date(t).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : '-')

// Risk bands -> token names (CSS var or theme token key)
export const riskTone = (r) => (r >= 0.7 ? 'alert' : r >= 0.5 ? 'hot' : r >= 0.3 ? 'warn' : 'ok')
export const riskVar = (r) => `var(--${riskTone(r)})`

export const SECTORS = {
  raw_material: 'Raw material', manufacturer: 'Manufacturer', wholesaler: 'Wholesaler',
  retailer: 'Retailer', services: 'Services',
}
export const PATTERN_LABELS = {
  circular_trading: 'Circular trading', shell_entity: 'Shell entity', fake_invoices: 'Fake invoices',
  itc_spike: 'ITC spike', behaviour_anomaly: 'Unusual behaviour',
}
export const PATTERN_TONE = {
  circular_trading: 'info', shell_entity: 'alert', fake_invoices: 'hot', itc_spike: 'warn', behaviour_anomaly: 'cyan',
}
// Relative change of the last point vs the one before it
export function lastDelta(series, key) {
  if (!series || series.length < 2) return null
  const a = series[series.length - 2][key], b = series[series.length - 1][key]
  if (!a) return null
  return (b - a) / a
}
