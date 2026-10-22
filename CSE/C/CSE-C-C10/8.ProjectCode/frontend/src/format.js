export const pct = (x, d = 1) => (x === null || x === undefined ? '-' : `${(x * 100).toFixed(d)}%`)
export const num = (x) => (x === null || x === undefined ? '-' : Math.round(Number(x)).toLocaleString('en-US'))
export const fixed = (x, d = 3) => (x === null || x === undefined ? '-' : Number(x).toFixed(d))
export const usd = (x) => {
  if (x === null || x === undefined) return '-'
  const v = Number(x)
  if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(2)}M`
  if (Math.abs(v) >= 1e3) return `$${(v / 1e3).toFixed(0)}K`
  return `$${Math.round(v)}`
}
export const meanStd = (m) => (m ? `${m.mean.toFixed(3)} ± ${m.std.toFixed(3)}` : '-')
export const clock = (t) => new Date(t).toLocaleTimeString('en-GB', { hour12: false })

// Probability / score -> token name. Success is green, failure is red, in-between is amber.
export const successTone = (p) => (p >= 0.6 ? 'ok' : p >= 0.4 ? 'warn' : 'alert')
export const outcomeTone = (o) => (o === 'SUCCESS' ? 'ok' : 'alert')

export const FIELD_LABELS = {
  funding_total_usd: 'Total funding (USD)',
  funding_rounds: 'Funding rounds',
  relationships: 'Relationships',
  milestones: 'Milestones',
  avg_participants: 'Avg. participants',
  age_first_funding_year: 'Age at first funding (yrs)',
  age_last_funding_year: 'Age at last funding (yrs)',
  age_first_milestone_year: 'Age at first milestone (yrs)',
  age_last_milestone_year: 'Age at last milestone (yrs)',
}
export const FLAG_LABELS = {
  has_VC: 'Has VC', has_angel: 'Has angel', has_roundA: 'Round A', has_roundB: 'Round B',
  has_roundC: 'Round C', has_roundD: 'Round D', is_top500: 'Top-500 ranked',
}
// "has_roundC" -> "Round C", "industry_type_AI" -> "Industry: AI"
export function featureLabel(name) {
  if (FLAG_LABELS[name]) return FLAG_LABELS[name]
  if (name.startsWith('industry_type_')) return `Industry: ${name.slice(14)}`
  if (name.startsWith('state_')) return `State: ${name.slice(6)}`
  if (name === 'log_funding_total_usd') return 'log(funding)'
  return FIELD_LABELS[name] || name.replace(/_/g, ' ')
}
