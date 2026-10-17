export const pct = (v, digits = 1) => (v === null || v === undefined ? '-' : `${(v * 100).toFixed(digits)}%`)
export const num = (v) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())
export const titleize = (s = '') =>
  s
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())

export const DISEASE_NAME = { diabetes: 'Diabetes', heart: 'Heart disease', liver: 'Liver disease', kidney: 'Kidney disease' }

export const METRICS = [
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'precision', label: 'Precision' },
  { key: 'recall', label: 'Recall' },
  { key: 'f1', label: 'F1' },
]

export const RISK = {
  high: { label: 'High risk', tone: 'danger' },
  low: { label: 'Low risk', tone: 'safe' },
}
