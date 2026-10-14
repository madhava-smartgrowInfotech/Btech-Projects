// Display helpers for APISentry scan data.

export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export function when(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

// Badge tones from the kit (danger, warn, safe, info, neutral).
export const GRADE_TONE = { A: 'safe', B: 'safe', C: 'warn', D: 'danger', F: 'danger' }
export const SEVERITY_TONE = { critical: 'danger', high: 'danger', medium: 'warn', low: 'info', info: 'neutral' }
