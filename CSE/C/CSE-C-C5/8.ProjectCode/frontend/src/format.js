// Shared formatting helpers.
export const pct = (p, digits = 1) => `${(p * 100).toFixed(digits)}%`
export const lpa = (v) => `${Number(v).toFixed(1)} LPA`
export const num = (v, d = 0) => Number(v).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d })

export function clock(t) {
  const d = new Date(t)
  return [d.getHours(), d.getMinutes(), d.getSeconds()].map((n) => String(n).padStart(2, '0')).join(':')
}

// Placement probability -> theme colour token.
export function probVar(p) {
  if (p >= 0.7) return 'var(--ok)'
  if (p >= 0.5) return 'var(--warn)'
  if (p >= 0.3) return 'var(--hot)'
  return 'var(--alert)'
}
export const probTone = (p) => (p >= 0.7 ? 'ok' : p >= 0.5 ? 'warn' : p >= 0.3 ? 'hot' : 'alert')

export const TIER_TONE = { 1: 'info', 2: 'cyan', 3: 'neutral' }

export const MODEL_LABELS = {
  logreg: 'Logistic Reg.', tree: 'Decision Tree', rf: 'Random Forest', svm: 'SVM', knn: 'kNN', xgb: 'XGBoost',
  xgb_calibrated: 'XGB + Platt', hybrid_xgb_knn: 'Hybrid XGB+kNN', hybrid_xgb_svm: 'Hybrid XGB+SVM',
}
export const modelLabel = (k) => MODEL_LABELS[k] || k
