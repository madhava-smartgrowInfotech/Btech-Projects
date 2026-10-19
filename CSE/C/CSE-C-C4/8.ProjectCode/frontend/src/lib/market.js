// Display names and small derivations over the API's per-ticker metrics object.
import { nextBusinessDays } from './format'

// Company names for the default universe (README table). Unknown tickers fall back to the symbol.
export const COMPANIES = {
  TSLA: 'Tesla',
  AAPL: 'Apple',
  AMZN: 'Amazon',
  MSFT: 'Microsoft',
  GOOGL: 'Alphabet (Google)',
  NVDA: 'Nvidia',
  META: 'Meta Platforms',
  FDX: 'FedEx',
  IBM: 'IBM',
  ORCL: 'Oracle',
}
export const companyOf = (t) => COMPANIES[t] || t

export const MODEL_LABELS = {
  arima: 'ARIMA',
  sarimax: 'SARIMAX',
  prophet: 'Prophet',
  random_forest: 'Random Forest',
  svr: 'SVR',
  lstm: 'LSTM',
  lstm_attention: 'LSTM + Attention',
  lstm_attention_sentiment: 'LSTM + Attention + Sentiment',
  hybrid_federated: 'Full Hybrid (FedAvg)',
}
export const DEEP_ORDER = ['lstm', 'lstm_attention', 'lstm_attention_sentiment', 'hybrid_federated']
export const modelLabel = (k) => MODEL_LABELS[k] || k

/** Flat list of every scored model for one ticker's metrics object. */
export function allModels(m) {
  if (!m) return []
  const base = Object.entries(m.baselines || {})
    .filter(([, v]) => v?.metrics)
    .map(([key, v]) => ({ key, kind: 'baseline', label: modelLabel(key), ...v.metrics }))
  const deep = DEEP_ORDER.filter((k) => m.deep?.[k]?.mae != null).map((key) => ({ key, kind: 'deep', label: modelLabel(key), ...m.deep[key] }))
  return [...base, ...deep]
}

export function bestBy(models, field, lowest = true) {
  const ok = models.filter((x) => x[field] != null && !Number.isNaN(x[field]))
  if (!ok.length) return null
  return ok.reduce((a, b) => ((lowest ? b[field] < a[field] : b[field] > a[field]) ? b : a))
}

/** Percentage move from the last close to the final day of a forecast list. */
export function forecastMove(m, which = 'forecast_short') {
  const f = m?.[which]
  if (!f?.length || !m.last_close) return null
  return (f[f.length - 1].predicted_close / m.last_close - 1) * 100
}

/**
 * Lines a forecast up with the price history.
 * The models are trained up to a cut-off close (`baseClose`, the API's last_close) which can be older than the
 * live history the API serves now, so the forecast is anchored on the history row with that close.
 * Returns chart rows [{x, close?, forecast?, band?}], table rows with the actual close where it is already known,
 * and the cut-off/latest dates.
 */
export function buildSeries(history, forecast, baseClose, shown) {
  const last = history.length - 1
  let anchor = -1
  history.forEach((r, i) => {
    if (Math.abs(r.close - baseClose) < 0.01) anchor = i
  })
  const anchored = anchor >= 0
  const startDate = history[anchored ? anchor : last].date
  const dates = nextBusinessDays(startDate, forecast.length)
  let from = Math.max(0, history.length - shown)
  if (anchored) from = Math.min(from, Math.max(0, anchor - 10))

  const byDate = new Map()
  history.slice(from).forEach((r) => byDate.set(r.date, { x: r.date, close: r.close }))
  if (anchored) byDate.set(startDate, { ...byDate.get(startDate), forecast: baseClose, band: [baseClose, baseClose] })
  forecast.forEach((f, i) => byDate.set(dates[i], { ...(byDate.get(dates[i]) || { x: dates[i] }), forecast: f.predicted_close, band: [f.lower, f.upper] }))

  const actual = new Map(history.map((r) => [r.date, r.close]))
  const rows = forecast.map((f, i) => {
    const a = actual.get(dates[i]) ?? null
    return { ...f, date: dates[i], actual: a, miss: a == null ? null : (f.predicted_close / a - 1) * 100, change: (f.predicted_close / baseClose - 1) * 100 }
  })
  return {
    data: [...byDate.values()].sort((a, b) => (a.x < b.x ? -1 : 1)),
    rows,
    anchored,
    cutoff: startDate,
    latest: history[last],
    stale: anchored ? anchor < last : Math.abs(history[last].close - baseClose) > 0.01,
  }
}

export const tone = (score) => (score > 0.15 ? 'mint' : score < -0.15 ? 'rose' : 'neutral')
export const toneLabel = (score) => (score > 0.15 ? 'Positive' : score < -0.15 ? 'Negative' : 'Neutral')
