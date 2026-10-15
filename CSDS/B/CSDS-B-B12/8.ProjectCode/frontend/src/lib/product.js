import { errorMessage } from '../api.js'

export const pct = (v) => (v === null || v === undefined ? '—' : `${(v * 100).toFixed(1)}%`)
export const fmtDate = (s) => (s ? new Date(s).toLocaleString() : '—')
export const LANGS = { en: 'English', hi: 'Hindi', te: 'Telugu' }
export const MODALITY_LABEL = { xray: 'Chest X-ray', ct: 'Chest CT' }

/** Turns an API error into the message to show plus its HTTP status (undefined when the server did not answer). */
export async function failure(err) {
  return { message: await errorMessage(err), status: err?.response?.status }
}
