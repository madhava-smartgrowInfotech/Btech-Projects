export const clock = (t) => new Date(t).toLocaleTimeString('en-GB', { hour12: false })
export const n0 = (v) => (v === null || v === undefined ? '-' : Math.round(v).toLocaleString('en-IN'))
export const n1 = (v) => (v === null || v === undefined ? '-' : Number(v).toFixed(1))
export const pct = (v) => (v === null || v === undefined ? '-' : `${Math.round(v)}%`)

// Controllers keep one colour on every chart.
export const CTRL_VAR = { fixed: 'var(--dim)', adaptive: 'var(--cyan)', emergency: 'var(--warn)', advanced: 'var(--ok)' }
export const CTRL_SHORT = { fixed: 'Fixed-time', adaptive: 'Adaptive', emergency: 'Emergency-aware', advanced: 'Advanced AI' }
export const CTRL_KEYS = ['fixed', 'adaptive', 'emergency', 'advanced']

// Vehicle classes on the map and in tables.
export const VEHICLE = {
  car: { color: 'var(--cyan)', size: 0.42, label: 'Car' },
  bike: { color: 'var(--hot)', size: 0.3, label: 'Bike' },
  bus: { color: 'var(--ok)', size: 0.6, label: 'Bus' },
  truck: { color: 'var(--info)', size: 0.5, label: 'Truck' },
  ambulance: { color: 'var(--alert)', size: 0.9, label: 'Ambulance' },
}

export const LEVEL_TONE = { LOW: 'ok', MEDIUM: 'cyan', HIGH: 'warn', JAMMED: 'alert' }
export const SIGNAL_VAR = { green: 'var(--ok)', clearing: 'var(--warn)', red: 'var(--alert)' }
