export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())
export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
export const humanize = (s = '') => s.replace(/_/g, ' ')

export function bytes(n) {
  if (n === null || n === undefined) return '-'
  if (n < 1024) return `${n} B`
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`
  if (n < 1073741824) return `${(n / 1048576).toFixed(2)} MB`
  return `${(n / 1073741824).toFixed(2)} GB`
}

// Backend timestamps are naive UTC strings (SQLite drops the offset) - treat them as UTC.
function parse(iso) {
  if (!iso) return null
  const s = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`
  const d = new Date(s)
  return Number.isNaN(d.getTime()) ? null : d
}

export function when(iso) {
  const d = parse(iso)
  return d ? d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '-'
}

export function ago(iso) {
  const d = parse(iso)
  if (!d) return '-'
  const s = Math.round((Date.now() - d.getTime()) / 1000)
  if (s < 45) return 'just now'
  const m = Math.round(s / 60)
  if (m < 60) return `${m} min ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h} h ago`
  const days = Math.round(h / 24)
  if (days < 30) return `${days} d ago`
  return d.toLocaleDateString()
}

export const dayKey = (iso) => {
  const d = parse(iso)
  return d ? d.toISOString().slice(0, 10) : null
}

export const ROLE = {
  owner: { label: 'Owner', tone: 'safe' },
  editor: { label: 'Editor', tone: 'info' },
  viewer: { label: 'Viewer', tone: 'neutral' },
}

const ACTION_LABELS = {
  register: 'Account registered',
  login_success: 'Signed in',
  login_failure: 'Sign-in failed',
  logout: 'Signed out',
  keys_updated: 'Keys updated',
  upload: 'File uploaded',
  download: 'File downloaded',
  file_update: 'Content replaced',
  delete: 'File deleted',
  share: 'Access granted',
  permission_change: 'Role changed',
  access_revocation: 'Access revoked',
  unauthorized_access: 'Access denied',
  integrity_verification: 'Chain verified',
  failed_integrity_verification: 'Chain verification failed',
}
export const actionLabel = (a) => ACTION_LABELS[a] || titleize(a)

export const shortHash = (h) => (h && h.length > 16 ? `${h.slice(0, 8)}…${h.slice(-6)}` : h || '-')
