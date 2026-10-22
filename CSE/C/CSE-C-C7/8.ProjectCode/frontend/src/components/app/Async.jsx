import { ErrorState, SkeletonBlock } from '../ui'

/** Renders skeleton -> error (with retry) -> content for a useApi() result. */
export function Async({ q, skeleton, title, children }) {
  if (q.loading && !q.data) return skeleton || <SkeletonBlock rows={5} />
  if (q.error && !q.data) return <ErrorState title={title} error={q.error} onRetry={q.reload} />
  return children(q.data)
}

export function CardSkeletons({ n = 4 }) {
  return (
    <div className="course-grid" role="status" aria-label="Loading courses">
      {Array.from({ length: n }, (_, i) => (
        <div key={i} className="card">
          <SkeletonBlock rows={4} label="Loading course" />
        </div>
      ))}
    </div>
  )
}
