export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' ? '—' : Number(v).toFixed(d))
export const fmtInt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString())
export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`
export const STATUS_LABEL = { live: 'Live', upcoming: 'Upcoming', expired: 'Expired', closed: 'Closed' }
export const STAGE_LABEL = {
  eligibility: 'Eligibility',
  location: 'Location',
  liveness: 'Liveness',
  face: 'Face match',
  success: 'Recorded',
}
