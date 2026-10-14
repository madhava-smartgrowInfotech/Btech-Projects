// Display helpers. Every value is formatted from real API data; a missing value shows an em dash.
const dash = '—'

export const isNum = (v) => typeof v === 'number' && Number.isFinite(v)

export function num(v, digits = 2) {
  if (v === 'inf') return '∞'
  return isNum(v) ? v.toFixed(digits) : dash
}

export const pct = (v, digits = 2) => (isNum(v) ? `${v.toFixed(digits)}%` : dash)
export const ms = (v) => (isNum(v) ? `${v.toFixed(1)} ms` : dash)
export const db = (v) => (v === 'inf' ? '∞ dB' : isNum(v) ? `${v.toFixed(2)} dB` : dash)

export function bytes(n) {
  if (!isNum(n)) return dash
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(2)} MB`
}

export function clock(t) {
  return new Date(t).toLocaleTimeString('en-GB', { hour12: false })
}

export function when(iso) {
  if (!iso) return dash
  return new Date(iso).toLocaleString('en-GB', { hour12: false, dateStyle: 'short', timeStyle: 'short' })
}

// Hex key validation: 256-bit key = 64 hex characters.
export const HEX64 = /^[0-9a-fA-F]{64}$/
export const HEX32 = /^[0-9a-fA-F]{32}$/

// Flip the lowest bit of the first key byte (the same 1-bit change the lab uses).
export function flipBit(hex) {
  const first = parseInt(hex.slice(0, 2), 16) ^ 1
  return first.toString(16).padStart(2, '0') + hex.slice(2)
}
