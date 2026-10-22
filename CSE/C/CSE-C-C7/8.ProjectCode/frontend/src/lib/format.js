export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(d))
export const fmtInt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString())
export const fmtPct = (v, d = 0) => (v === null || v === undefined || Number.isNaN(Number(v)) ? '—' : `${(Number(v) * 100).toFixed(d)}%`)
export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

/** The API stores naive UTC timestamps; show them in the viewer's local time. */
export function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export const splitList = (s) =>
  String(s || '')
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)

export const EVENT_LABEL = {
  view: 'Viewed',
  open: 'Opened',
  start: 'Started',
  quiz: 'Quiz',
  content: 'Content reviewed',
  forum: 'Discussion',
  complete: 'Completed',
  dismiss: 'Dismissed',
  save: 'Saved',
}
export const EVENT_TONE = { complete: 'pass', dismiss: 'blocked', start: 'info', save: 'info', quiz: 'upcoming' }

export const ACTION_LABEL = {
  quiz: 'Complete a quiz',
  content: 'Review learning content',
  forum: 'Engage with discussion',
  homepage: 'Visit course resources',
  continue_course: 'Continue your learning path',
}
export const ACTION_COUNT = Object.keys(ACTION_LABEL).length

/** Highest-benefit action from an {action: benefit} map. */
export function bestAction(uplift) {
  const entries = Object.entries(uplift || {}).filter(([, v]) => typeof v === 'number')
  if (!entries.length) return null
  const [key, value] = entries.sort((a, b) => b[1] - a[1])[0]
  return { key, value, label: ACTION_LABEL[key] || key }
}
