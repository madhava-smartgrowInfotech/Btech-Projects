export const pct = (v, digits = 1) => (v === null || v === undefined ? '-' : `${(v * 100).toFixed(digits)}%`)
export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())
export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
export const humanize = (s = '') => s.replace(/_/g, ' ')

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

// 0-100 match score -> badge tone (same thresholds the backend uses for match_strength)
export const scoreTone = (score) => (score >= 65 ? 'safe' : score >= 45 ? 'info' : 'warn')

export const num1 = (v, d = 2) => (v === null || v === undefined || Number.isNaN(Number(v)) ? '-' : Number(v).toFixed(d))

export const fileSize = (bytes) => (bytes >= 1048576 ? `${(bytes / 1048576).toFixed(2)} MB` : `${(bytes / 1024).toFixed(1)} KB`)
