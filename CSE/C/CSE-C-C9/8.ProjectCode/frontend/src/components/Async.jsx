import { ErrorState, PageSkeleton } from './ui'

/** Skeleton while loading, an error state with retry, otherwise render children(data). */
export default function Async({ state, skeleton, children, title }) {
  if (state.loading) return skeleton || <PageSkeleton />
  if (state.error) return <ErrorState title={title || 'Could not load this screen'} error={state.error} onRetry={state.reload} />
  return children(state.data)
}
