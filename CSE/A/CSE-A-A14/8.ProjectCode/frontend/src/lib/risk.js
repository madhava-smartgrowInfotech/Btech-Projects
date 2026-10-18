// Risk-band presentation shared by tables, badges and charts.
export const RISK_ORDER = ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk']
export const RISK_TONE = { 'Low Risk': 'mint', 'Medium Risk': 'butter', 'High Risk': 'peach', 'Critical Risk': 'rose' }
export const RISK_COLOR = {
  'Low Risk': 'var(--mint)',
  'Medium Risk': 'var(--butter)',
  'High Risk': 'var(--peach)',
  'Critical Risk': 'var(--rose)',
}
export const RISK_HEX = { 'Low Risk': '#A7E8C8', 'Medium Risk': '#FFE7A3', 'High Risk': '#FFC9A3', 'Critical Risk': '#FFB8C6' }
export const shortBand = (b) => (b ? b.replace(' Risk', '') : '')
