// Number / time / colour helpers shared by every screen.
const num = (n, d = 0) => (n === null || n === undefined || Number.isNaN(Number(n)) ? '-' : Number(n).toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: 0 }))

export const fmt = num
export const pct = (v, d = 1) => (v === null || v === undefined ? '-' : `${(v * 100).toFixed(d)}%`)
export const pctRaw = (v, d = 1) => (v === null || v === undefined ? '-' : `${Number(v).toFixed(d)}%`)

export function bytes(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '-'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = Number(n)
  let i = 0
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i += 1 }
  return `${v.toFixed(v >= 100 || i === 0 ? 0 : 1)} ${u[i]}`
}
export const rate = (n, unit) => `${num(n, 0)} ${unit}`

// Server timestamps are unix seconds.
export const clock = (t) => {
  const d = new Date(t > 1e12 ? t : t * 1000)
  return Number.isNaN(d.getTime()) ? '-' : d.toLocaleTimeString('en-GB', { hour12: false })
}
export const dateTime = (t) => {
  if (!t) return '-'
  const d = new Date(t * 1000)
  return Number.isNaN(d.getTime()) ? '-' : `${d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })} ${d.toLocaleTimeString('en-GB', { hour12: false })}`
}

export const SEVERITIES = ['Low', 'Medium', 'High', 'Critical']
export const SEVERITY_TONE = { Low: 'ok', Medium: 'warn', High: 'hot', Critical: 'alert' }
export const sevVar = (s) => `var(--${SEVERITY_TONE[s] || 'dim'})`
export const predTone = (p) => (p === 'Attack' ? 'alert' : 'ok')

// 0..1 risk -> token colour
export const riskVar = (r) => (r >= 0.7 ? 'var(--alert)' : r >= 0.4 ? 'var(--warn)' : 'var(--ok)')

export const MIT_LABEL = {
  monitor: 'monitor',
  quarantine: 'quarantine',
  rate_limit_recommended: 'rate limit advised',
}
export const mitLabel = (m) => MIT_LABEL[m] || m || '-'
export const mitTone = (m) => (m === 'quarantine' ? 'alert' : m === 'rate_limit_recommended' ? 'warn' : 'neutral')

export const FEATURE_LABEL = {
  received_packets: 'Received packets',
  received_bytes: 'Received bytes',
  received_packets_per_second: 'Received pkt/s',
  received_bytes_per_second: 'Received bytes/s',
  average_received_packet_size: 'Avg received pkt size',
  sent_packets: 'Sent packets',
  sent_bytes: 'Sent bytes',
  sent_packets_per_second: 'Sent pkt/s',
  sent_bytes_per_second: 'Sent bytes/s',
  average_sent_packet_size: 'Avg sent pkt size',
}
