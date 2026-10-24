export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())
export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

// Drop float noise (e.g. 0.30000000000000004) without hiding real precision.
export const value = (v) => (v === null || v === undefined ? '-' : Number(Number(v).toFixed(2)).toLocaleString(undefined, { maximumFractionDigits: 2 }))

export function when(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function day(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export function shortDay(iso) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

export function bytes(n) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

// Result status -> badge tone + label (colour is never the only cue: the label always shows).
export const STATUS = {
  NORMAL: { label: 'Normal', tone: 'safe' },
  LOW: { label: 'Low', tone: 'warn' },
  HIGH: { label: 'High', tone: 'danger' },
  UNKNOWN: { label: 'Unknown', tone: 'neutral' },
}

export const REPORT_STATUS = {
  Completed: { label: 'Completed', tone: 'safe' },
  Failed: { label: 'Failed', tone: 'danger' },
  Processing: { label: 'Processing', tone: 'info' },
  Pending: { label: 'Pending', tone: 'warn' },
}
