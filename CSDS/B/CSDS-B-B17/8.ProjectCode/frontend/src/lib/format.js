export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(d))
export const fmtInt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString())
export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`
export const pct = (v, d = 1) => (v === null || v === undefined ? '—' : `${(v * 100).toFixed(d)}%`)

export const fmtTime = (t) => {
  if (t == null) return '—'
  const s = Math.max(0, Math.round(t))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}
export const fmtDate = (iso) => (iso ? new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) : '—')
export const label = (s) => (s ? String(s).replaceAll('_', ' ') : '—')
export const cleanTitle = (t) => (t || '').replace('[Sample] ', '')
export const signed = (v, d = 2) => (v == null ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(d)}`)

export const STATUS_LABEL = { done: 'Analysed', failed: 'Failed', processing: 'Processing', queued: 'Queued' }

// Emotion palette (flat accent blocks, dark text on every one for contrast).
export const EMOTION_COLOR = {
  angry: '#ff5c39',
  frustrated: '#ff9f1c',
  concerned: '#ffd23f',
  neutral: '#cfc9b8',
  satisfied: '#c8ff2e',
  relieved: '#7cc6ff',
}
