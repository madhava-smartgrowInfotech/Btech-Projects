export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(d))
export const fmtPct = (v) => (v === null || v === undefined ? '—' : `${Math.round(v * 100)}%`)
export const fmtTime = (d = new Date()) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })

export const SCENARIOS = [
  { id: 'normal', label: 'Normal driving', tone: 'secondary' },
  { id: 'brake', label: 'Harsh brake', tone: 'secondary' },
  { id: 'minor', label: 'Minor crash', tone: 'secondary' },
  { id: 'moderate', label: 'Moderate crash', tone: 'secondary' },
  { id: 'severe', label: 'Severe crash', tone: 'danger' },
]

// Severity label -> badge tone / colour used across the UI.
export const SEVERITY = {
  None: { tone: 'pass', color: '#c8ff2e' },
  Minor: { tone: 'info', color: '#7cc6ff' },
  Moderate: { tone: 'upcoming', color: '#ffd23f' },
  Severe: { tone: 'blocked', color: '#ff5c39' },
}

export const EMERGENCY_CONTACTS = [
  { label: 'Ambulance', number: '108' },
  { label: 'National emergency', number: '112' },
  { label: 'Traffic police', number: '103' },
]

// Kept for the kit's StatusBadge.
export const STATUS_LABEL = { live: 'Live', upcoming: 'Upcoming', expired: 'Expired', closed: 'Closed' }
