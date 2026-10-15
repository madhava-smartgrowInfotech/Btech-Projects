export const num = (v, digits) => {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '-'
  return Number(v).toLocaleString(undefined, digits === undefined ? undefined : { maximumFractionDigits: digits, minimumFractionDigits: digits })
}
export const fixed = (v, digits = 3) => (v === null || v === undefined || Number.isNaN(Number(v)) ? '-' : Number(v).toFixed(digits))
export const pct = (v, digits = 1) => (v === null || v === undefined ? '-' : `${(v * 100).toFixed(digits)}%`)
export const titleize = (s = '') => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export function when(iso) {
  if (!iso) return '-'
  // the API returns naive UTC timestamps (no zone suffix)
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export const KIND = {
  mri: { label: 'MRI', tone: 'info' },
  dna: { label: 'DNA', tone: 'safe' },
  str: { label: 'STR', tone: 'warn' },
}
