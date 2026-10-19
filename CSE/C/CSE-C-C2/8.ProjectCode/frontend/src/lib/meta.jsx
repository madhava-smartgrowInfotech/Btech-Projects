import { createContext, useContext } from 'react'
import { api } from './api'
import { useAsync } from './useAsync'

const MetaCtx = createContext({ loading: true, error: null, languages: [], styles: [], lengths: [], meta: null, health: null, reload: () => {} })

/** Languages, styles/lengths and server health, loaded once for the whole app. */
export function MetaProvider({ children }) {
  const { loading, error, data, reload } = useAsync(async () => {
    const [languages, meta, health] = await Promise.all([api.languages(), api.meta(), api.health()])
    return { languages, meta, health }
  }, [])
  const value = {
    loading,
    error,
    reload,
    languages: data?.languages || [],
    styles: data?.meta?.styles || [],
    lengths: data?.meta?.lengths || [],
    meta: data?.meta || null,
    health: data?.health || null,
  }
  return <MetaCtx.Provider value={value}>{children}</MetaCtx.Provider>
}

export const useMeta = () => useContext(MetaCtx)
