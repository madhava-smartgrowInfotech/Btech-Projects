export const pct = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? '-' : `${(v * 100).toFixed(d)}%`)
export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString('en-US'))
export const clock = (t) => new Date(t).toLocaleTimeString('en-GB', { hour12: false })

// 0..1 risk/confidence -> token colour
export const riskVar = (r) => (r >= 0.85 ? 'var(--alert)' : r >= 0.7 ? 'var(--hot)' : r >= 0.5 ? 'var(--warn)' : 'var(--ok)')

export const SEVERITY_TONE = { critical: 'alert', high: 'hot', medium: 'warn', low: 'ok' }

export function severityOf(label, conf) {
  if (label !== 'attack') return 'low'
  return conf >= 0.85 ? 'critical' : conf >= 0.7 ? 'high' : 'medium'
}

export function bytes(n) {
  if (n === null || n === undefined) return '-'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(2)} MB`
}
