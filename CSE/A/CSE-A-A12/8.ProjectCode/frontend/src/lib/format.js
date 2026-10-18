export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(d))
export const fmtInt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString())
export const fmtPct = (v, d = 1) => (v === null || v === undefined ? '—' : `${(Number(v) * 100).toFixed(d)}%`)
export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

const DATE = { year: 'numeric', month: 'short', day: '2-digit' }
const TIME = { hour: '2-digit', minute: '2-digit' }
export const fmtDate = (iso) => (iso ? new Date(iso).toLocaleDateString(undefined, DATE) : '—')
export const fmtDateTime = (iso) =>
  iso ? `${new Date(iso).toLocaleDateString(undefined, DATE)} · ${new Date(iso).toLocaleTimeString(undefined, TIME)}` : '—'

export const STATUS_LABEL = { live: 'Live', upcoming: 'Upcoming', expired: 'Expired', closed: 'Closed' }

/** Class name -> badge tone / chart colour (green, red, yellow in the original UI). */
export const CLASS_TONE = { Normal: 'pass', 'Bacterial Pneumonia': 'blocked', 'Viral Pneumonia': 'upcoming' }
export const CLASS_COLOR = { Normal: '#C8FF2E', 'Bacterial Pneumonia': '#FF5C39', 'Viral Pneumonia': '#FFD23F' }
export const CLASS_SHORT = { Normal: 'Normal', 'Bacterial Pneumonia': 'Bacterial', 'Viral Pneumonia': 'Viral' }
