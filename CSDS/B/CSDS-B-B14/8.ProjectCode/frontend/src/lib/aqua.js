// AquaVision helpers shared by the screens: zone colours, pressure bands, day labels, status tones.

// Zone colours in the same ink tones as the chart palette (readable on the map and in bars).
export const ZONE_COLORS = { Z1: '#1F6AAE', Z2: '#5B45C9', Z3: '#A9541A', Z4: '#1C7A50', Z5: '#B13A55', SRC: '#4E5566' }

// Pressure bands on the map, in metres of head.
export function pressureColor(p) {
  if (p == null) return '#9AA1B2'
  if (p < 20) return '#B13A55'
  if (p < 28) return '#B7791F'
  if (p < 45) return '#1C7A50'
  return '#1F6AAE'
}

/** "Mon, 5 Oct" from a YYYY-MM-DD string. */
export function dayLabel(iso) {
  if (!iso) return '–'
  const d = new Date(`${iso}T00:00:00`)
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
}

export const SEVERITY_TONE = { high: 'rose', medium: 'peach', low: 'sky' }
export const TYPE_TONE = { night_flow: 'peach', burst: 'rose', suspected_theft: 'lavender', unusual_pattern: 'neutral' }
export const STATUS_TONE = { 'under-supplied': 'rose', 'high losses': 'peach', 'excess pressure': 'sky', balanced: 'mint' }
