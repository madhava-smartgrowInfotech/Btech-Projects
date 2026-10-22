import { createContext, useContext, useMemo } from 'react'
import useFetch from './useFetch'

// Reference data every screen needs (dropdown options, company list, dataset totals), fetched once.
const DataContext = createContext({ meta: null, companies: null, stats: null, error: null, loading: true, reload: () => {} })
export const useData = () => useContext(DataContext)

export function DataProvider({ children }) {
  const meta = useFetch('/meta')
  const companies = useFetch('/companies')
  const stats = useFetch('/stats')
  const value = useMemo(() => ({
    meta: meta.data,
    companies: companies.data,
    stats: stats.data,
    error: meta.error || companies.error || stats.error,
    loading: meta.loading || companies.loading || stats.loading,
    reload: () => { meta.reload(); companies.reload(); stats.reload() },
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [meta.data, companies.data, stats.data, meta.error, companies.error, stats.error, meta.loading, companies.loading, stats.loading])
  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}
