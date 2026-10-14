export const pct = (v, digits = 1) => (v === null || v === undefined ? '-' : `${(v * 100).toFixed(digits)}%`)
export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())
export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
export const humanize = (s = '') => s.replace(/_/g, ' ')

export const MODEL_LABEL = {
  xgboost: 'XGBoost',
  random_forest: 'Random Forest',
  logistic_regression: 'Logistic Regression',
}
export const modelLabel = (k) => MODEL_LABEL[k] || titleize(k || '')

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

export const VERDICT = {
  phishing: { label: 'Phishing', tone: 'danger' },
  suspicious: { label: 'Suspicious', tone: 'warn' },
  safe: { label: 'Looks safe', tone: 'safe' },
  unknown: { label: 'Unknown', tone: 'neutral' },
}

export const STATUS = {
  pending: { label: 'Pending', tone: 'warn' },
  confirmed_phishing: { label: 'Confirmed phishing', tone: 'danger' },
  confirmed_safe: { label: 'Confirmed safe', tone: 'safe' },
}

export const DECIDED_BY = {
  ml: { label: 'ML model', tone: 'info' },
  community: { label: 'Community', tone: 'info' },
  none: { label: 'No model', tone: 'neutral' },
}

// Split a pasted / uploaded blob into candidate URLs (one per line; first CSV column).
export function parseUrlList(text) {
  const out = []
  for (const raw of text.split(/\r?\n/)) {
    let line = raw.trim()
    if (!line || line.startsWith('#')) continue
    if (line.includes(',')) line = line.split(',')[0].trim().replace(/^"+|"+$/g, '')
    if (/^url$/i.test(line)) continue
    if (line.includes('.') || line.includes('://')) out.push(line)
  }
  return out
}
