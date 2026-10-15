export const pct = (v, d = 1) => (v == null ? '-' : `${(v * 100).toFixed(d)}%`)
export const ms = (v) => (v == null ? '-' : `${Number(v).toFixed(v < 10 ? 2 : 1)} ms`)
export const label = (g) => String(g ?? '').replaceAll('_', ' ')
export const clock = (t) => new Date(t).toLocaleTimeString('en-GB', { hour12: false })
export const stamp = (iso) => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export function transcriptText(title, messages) {
  const lines = messages.map((m) => `[${new Date(m.created_at || m.at).toLocaleTimeString()}] ${m.side === 'signer' ? 'Signer' : 'Speaker'}: ${m.text}`)
  return `${title}\n${'='.repeat(title.length)}\n\n${lines.join('\n')}\n`
}

export function downloadText(name, text) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain' }))
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}
