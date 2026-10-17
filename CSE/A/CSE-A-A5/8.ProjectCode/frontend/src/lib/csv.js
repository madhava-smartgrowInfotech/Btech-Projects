function splitLine(line) {
  const out = []
  let cur = ''
  let q = false
  for (let i = 0; i < line.length; i++) {
    const c = line[i]
    if (c === '"') {
      if (q && line[i + 1] === '"') { cur += '"'; i++ } else q = !q
    } else if (c === ',' && !q) { out.push(cur); cur = '' } else cur += c
  }
  out.push(cur)
  return out
}

// Reads proto / service / state (and the ground-truth `label`, if present) for the first `max` rows,
// so batch results can show them next to the API's per-row verdicts. The API scores; this only labels rows.
export function readFlowMeta(text, max = 1000) {
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '')
  if (lines.length < 2) return []
  const head = splitLine(lines[0]).map((h) => h.trim().toLowerCase().replace(/ /g, '_'))
  const at = (name) => head.indexOf(name)
  const ip = at('proto'), is = at('service'), ist = at('state'), il = at('label')
  return lines.slice(1, max + 1).map((l) => {
    const c = splitLine(l)
    const label = il >= 0 ? c[il]?.trim() : undefined
    return {
      proto: ip >= 0 ? c[ip]?.trim() || '-' : '-',
      service: is >= 0 ? c[is]?.trim() || '-' : '-',
      state: ist >= 0 ? c[ist]?.trim() || '-' : '-',
      truth: label === '1' ? 'attack' : label === '0' ? 'normal' : undefined,
    }
  })
}
