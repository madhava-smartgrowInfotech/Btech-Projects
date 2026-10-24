export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(d))
export const fmtInt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString())
export const fmtPct = (v, d = 0) => (v === null || v === undefined ? '—' : `${(Number(v) * 100).toFixed(d)}%`)
export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`
export const STATUS_LABEL = { live: 'Live', pass: 'Pass', blocked: 'Blocked' }

export const PRIORITY_NAME = { 1: 'Critical', 2: 'Emergent', 3: 'Urgent', 4: 'Less urgent', 5: 'Non-urgent' }
// hard-edged colour per priority (kit palette): coral, amber, sky, lime, paper
export const PRIORITY_COLOR = { 1: '#FF5C39', 2: '#FFD23F', 3: '#7CC6FF', 4: '#C8FF2E', 5: '#FAF7F0' }

export function fmtDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function timeAgo(iso) {
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000))
  if (s < 60) return `${s}s ago`
  if (s < 3600) return `${Math.round(s / 60)} min ago`
  if (s < 86400) return `${Math.round(s / 3600)} h ago`
  return `${Math.round(s / 86400)} d ago`
}
