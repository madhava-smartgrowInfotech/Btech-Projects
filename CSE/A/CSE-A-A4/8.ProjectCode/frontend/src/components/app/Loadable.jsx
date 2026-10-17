import { ErrorState, PageSkeleton } from '../ui'

/** Skeleton while loading, an actionable error if it failed, otherwise the children. */
export default function Loadable({ state, kpis = 4, blocks = 2, title, children }) {
  if (state.loading && !state.data) return <PageSkeleton kpis={kpis} blocks={blocks} />
  if (state.error) return <ErrorState title={title || 'Could not load this screen'} error={state.error} onRetry={state.reload} />
  return children
}
