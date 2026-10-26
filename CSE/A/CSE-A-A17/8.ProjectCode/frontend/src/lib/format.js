export const fmtNum = (v, d = 2) => (v === null || v === undefined || v === '' || Number.isNaN(Number(v)) ? '—' : Number(v).toFixed(d))
export const fmtInt = (v) => (v === null || v === undefined || Number.isNaN(Number(v)) ? '—' : Number(v).toLocaleString())
export const fmtPct = (v, d = 1) => (v === null || v === undefined || Number.isNaN(Number(v)) ? '—' : `${Number(v).toFixed(d)}%`)
export const fmtSigned = (v, d = 1) => (v === null || v === undefined || Number.isNaN(Number(v)) ? '—' : `${v > 0 ? '+' : ''}${Number(v).toFixed(d)}%`)
export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`
export const STATUS_LABEL = { done: 'Done', todo: 'To do' }
