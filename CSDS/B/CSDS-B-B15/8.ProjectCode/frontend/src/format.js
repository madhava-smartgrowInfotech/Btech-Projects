// MediQueue display helpers shared by the kit components and the screens.

export const SEVERITIES = ['critical', 'severe', 'moderate', 'mild']

/** Badge tone per triage level (kit tones: ok, warn, hot, alert) */
export const SEVERITY_TONE = { mild: 'ok', moderate: 'warn', severe: 'hot', critical: 'alert' }

/** CSS colour per triage level, for bars and charts */
export const SEVERITY_VAR = { mild: 'var(--ok)', moderate: 'var(--warn)', severe: 'var(--hot)', critical: 'var(--alert)' }

/** Badge tone per booking / referral status */
export const STATUS_TONE = {
  waiting: 'info', called: 'ok', done: 'neutral', no_show: 'alert', referred: 'cyan',
  pending_consent: 'warn', sent: 'info', accepted: 'ok', completed: 'ok', declined: 'alert',
}

export const statusLabel = (s) => s.replace('_', ' ')

/** Hex colour for a hospital load percentage (Leaflet markers and charts) */
export const loadHex = (pct) => (pct >= 90 ? '#f87171' : pct >= 70 ? '#fb923c' : pct >= 40 ? '#fbbf24' : '#4ade80')

/** CSS colour for a 0-1 score (used by the kit's score components) */
export const riskVar = (v) => (v >= 0.66 ? 'var(--alert)' : v >= 0.33 ? 'var(--warn)' : 'var(--ok)')

export const clock = (t) => new Date(t).toLocaleTimeString('en-GB', { hour12: false })

// kit display helpers that are unused in MediQueue; present so the kit copy stays importable
export const PATTERN_LABELS = {}
export const PATTERN_TONE = {}
