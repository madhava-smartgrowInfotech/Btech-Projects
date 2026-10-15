export const sci = (v, d = 3) => (v == null ? '–' : Number(v).toExponential(d))
export const short = (h, n = 16) => (h ? `${h.slice(0, n)}…` : '–')
export const utc = (iso) => (iso ? iso.replace('T', ' ').replace('+00:00', ' UTC') : '–')
