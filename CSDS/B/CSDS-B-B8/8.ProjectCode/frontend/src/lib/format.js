export const pct = (v, digits = 1) => (v === null || v === undefined ? '-' : `${(v * 100).toFixed(digits)}%`)
export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())
export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
export const humanize = (s = '') => s.replace(/_/g, ' ')

export const seconds = (v, digits = 2) => (v === null || v === undefined ? '-' : `${Number(v).toFixed(digits)} s`)

export function ms(v) {
  if (v === null || v === undefined) return '-'
  return v >= 1000 ? `${(v / 1000).toFixed(1)} s` : `${Math.round(v)} ms`
}

export function duration(s) {
  s = Math.round(s || 0)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h) return `${h}h ${m}m`
  if (m) return `${m}m ${sec}s`
  return `${sec}s`
}

export function when(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function clock(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
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

// Colours chosen to stay legible on both the dark and the light theme.
export const ACTIVITY_COLORS = {
  walking: '#0ea5e9',
  standing: '#22c55e',
  sitting: '#a855f7',
  lying: '#f97316',
  drinking: '#14b8a6',
  picking_up: '#eab308',
  away: '#94a3b8',
}
export const activityColor = (a) => ACTIVITY_COLORS[a] || '#94a3b8'
export const CLIP_LABELS = ['walking', 'standing', 'sitting', 'lying', 'drinking', 'picking_up', 'fall']

export const ALERT_STATUS = {
  pending: { label: 'Pending', tone: 'warn' },
  sending: { label: 'Sending', tone: 'info' },
  sent: { label: 'Sent', tone: 'danger' },
  undelivered: { label: 'Undelivered', tone: 'neutral' },
  failed: { label: 'Failed', tone: 'danger' },
  cancelled: { label: "I'm OK - cancelled", tone: 'safe' },
}

export const localDay = (d = new Date()) => d.toLocaleDateString('en-CA')
