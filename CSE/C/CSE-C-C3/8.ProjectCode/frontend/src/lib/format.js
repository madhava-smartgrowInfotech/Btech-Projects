export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())
export const money = (v) => (v === null || v === undefined ? '-' : `$${Number(v).toFixed(2)}`)
export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export function when(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function ago(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const s = Math.round((Date.now() - d.getTime()) / 1000)
  if (Number.isNaN(s)) return iso
  if (s < 45) return 'just now'
  const m = Math.round(s / 60)
  if (m < 60) return `${m} min ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h} h ago`
  const days = Math.round(h / 24)
  if (days < 30) return `${days} d ago`
  return d.toLocaleDateString()
}

// "2026-10-19T14:30" for <input type="datetime-local">, in the viewer's local time.
export function toLocalInput(d) {
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}
export const fromLocalInput = (v) => new Date(v).toISOString()

export function defaultWindow() {
  const start = new Date(Date.now() + 3600e3)
  start.setMinutes(Math.ceil(start.getMinutes() / 15) * 15, 0, 0)
  return { start: toLocalInput(start), end: toLocalInput(new Date(start.getTime() + 2 * 3600e3)) }
}

export function duration(startIso, endIso) {
  const h = (new Date(endIso) - new Date(startIso)) / 3600e3
  if (!(h > 0)) return '-'
  if (h < 1) return `${Math.round(h * 60)} min`
  return h % 1 === 0 ? `${h} h` : `${h.toFixed(1)} h`
}

export const STATUS = {
  reserved: { label: 'Reserved', tone: 'info' },
  active: { label: 'Parked', tone: 'safe' },
  completed: { label: 'Completed', tone: 'neutral' },
  cancelled: { label: 'Cancelled', tone: 'neutral' },
  failed: { label: 'Unable to park', tone: 'danger' },
  declined: { label: 'Declined', tone: 'warn' },
}

export const PAYMENT = {
  paid: { label: 'Paid', tone: 'safe' },
  pending: { label: 'Payment due', tone: 'warn' },
  refunded: { label: 'Refunded', tone: 'neutral' },
}

export const TRUST_EVENT = {
  benefit: { label: 'On-time checkout', tone: 'safe' },
  reward: { label: 'Trust reward', tone: 'safe' },
  warning: { label: 'Late checkout', tone: 'danger' },
  penalty: { label: 'Trust penalty', tone: 'danger' },
}

export const STRATEGY_LABEL = { fixed_0: 'No buffer (0)', fixed_1: 'Fixed buffer (1)', fixed_3: 'Fixed buffer (3)', dynamic: 'Dynamic policy' }
