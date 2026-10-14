import { api } from './api'
import { useApi } from './useApi'

// Regions and form options rarely change - fetch once per session and share.
let regionsP = null
let optionsP = null

export const getRegions = () => {
  regionsP = regionsP || api.regions().catch((e) => ((regionsP = null), Promise.reject(e)))
  return regionsP
}
export const getOptions = () => {
  optionsP = optionsP || api.options().catch((e) => ((optionsP = null), Promise.reject(e)))
  return optionsP
}

export const useRegions = () => useApi(() => getRegions(), [])
export const useOptions = () => useApi(() => getOptions(), [])

/** city -> index (model order) */
export const cityIndex = (regions) => Object.fromEntries(regions.map((r, i) => [r.city, i]))
