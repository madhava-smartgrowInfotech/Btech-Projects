export const pct = (v, digits = 1) => (v === null || v === undefined ? '-' : `${(v * 100).toFixed(digits)}%`)
export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())
export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
export const humanize = (s = '') => s.replace(/_/g, ' ')
export const inr = (v) => `₹${Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
export const score = (v) => (v === null || v === undefined ? '-' : `${Math.round(v)}`)

export function when(iso) {
  if (!iso) return '-'
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function day(iso) {
  if (!iso) return '-'
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, { dateStyle: 'medium' })
}

export function ago(iso) {
  if (!iso) return '-'
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
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

// Knowledge-state status -> badge tone / label (matches the Streamlit page's five statuses)
export const STATUS = {
  completed: { label: 'Completed', tone: 'safe' },
  strong: { label: 'Strong', tone: 'info' },
  weak: { label: 'Weak', tone: 'warn' },
  recommended: { label: 'Recommended', tone: 'neutral' },
  locked: { label: 'Locked', tone: 'neutral' },
}

export const REQUEST_STATUS = {
  pending: { label: 'Pending', tone: 'warn' },
  accepted: { label: 'Accepted', tone: 'safe' },
  rejected: { label: 'Rejected', tone: 'danger' },
}

export const SESSION_STATUS = {
  scheduled: { label: 'Scheduled', tone: 'info' },
  completed: { label: 'Completed', tone: 'safe' },
  cancelled: { label: 'Cancelled', tone: 'danger' },
}
