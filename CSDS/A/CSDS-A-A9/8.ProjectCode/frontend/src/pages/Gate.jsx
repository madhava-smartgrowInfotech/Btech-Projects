import { ErrorState, PageSkeleton } from '../components/ui'
import { useLab } from '../lib/lab'

/** Shows a skeleton while loading and an error state (with retry) if the API is unreachable. */
export default function Gate({ children, kpis = 4, blocks = 2 }) {
  const { state, error, loading, refresh } = useLab()
  if (loading && !state) return <PageSkeleton kpis={kpis} blocks={blocks} />
  if (!state) {
    return <ErrorState title="Could not load the lab" error={error} onRetry={() => refresh().catch(() => {})} />
  }
  return children(state)
}
