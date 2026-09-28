export function inr(x) {
  if (x === null || x === undefined) return '-'
  const v = Number(x)
  if (Math.abs(v) >= 1e7) return `₹${(v / 1e7).toFixed(2)} Cr`
  if (Math.abs(v) >= 1e5) return `₹${(v / 1e5).toFixed(2)} L`
  return `₹${Math.round(v).toLocaleString('en-IN')}`
}
export const pct = (x, d = 0) => (x === null || x === undefined ? '-' : `${(x * 100).toFixed(d)}%`)
export const num = (x) => Number(x).toLocaleString('en-IN')
export const monthLabel = (m) => {
  const [y, mo] = m.split('-')
  return new Date(Number(y), Number(mo) - 1, 1).toLocaleString('en', { month: 'short' }) + ' ' + y.slice(2)
}
export function riskColor(r) {
  if (r >= 0.7) return '#dc2626'
  if (r >= 0.5) return '#ea580c'
  if (r >= 0.3) return '#ca8a04'
  return '#16a34a'
}
export const SECTORS = {
  raw_material: 'Raw material', manufacturer: 'Manufacturer', wholesaler: 'Wholesaler',
  retailer: 'Retailer', services: 'Services',
}
