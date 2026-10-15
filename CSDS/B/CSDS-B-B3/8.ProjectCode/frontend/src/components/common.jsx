import { useCallback, useState } from 'react'
import { Badge, Card, ErrorState, Skeleton, useToast } from './ui'

// loading -> skeleton, error -> ErrorState with retry, otherwise render children(data)
export function AsyncView({ state, skeleton, children }) {
  if (state.loading && state.data === undefined) return skeleton || <PageSkeleton />
  if (state.error) return <ErrorState title="Couldn't load this screen" error={state.error} onRetry={state.reload} />
  if (state.data === undefined) return null
  return children(state.data)
}

export function PageSkeleton({ stats = 4, cards = 2 }) {
  return (
    <div aria-busy="true" aria-label="Loading">
      <div className="grid grid-4">
        {Array.from({ length: stats }).map((_, i) => (
          <Card key={i} pad spotlight={false}>
            <Skeleton width="55%" height={12} />
            <Skeleton width="40%" height={30} style={{ marginTop: 14 }} />
          </Card>
        ))}
      </div>
      <div className="grid grid-2 mt">
        {Array.from({ length: cards }).map((_, i) => (
          <Card key={i} pad spotlight={false}>
            <Skeleton width="45%" height={18} />
            {Array.from({ length: 4 }).map((__, j) => (
              <Skeleton key={j} height={14} style={{ marginTop: 14 }} />
            ))}
          </Card>
        ))}
      </div>
    </div>
  )
}

export function CardSkeleton({ rows = 5 }) {
  return (
    <Card pad spotlight={false} aria-busy="true" aria-label="Loading">
      <Skeleton width="40%" height={18} />
      {Array.from({ length: rows }).map((_, j) => (
        <Skeleton key={j} height={14} style={{ marginTop: 14 }} />
      ))}
    </Card>
  )
}

export function StatusBadge({ map, value }) {
  const s = map[value] || { label: value, tone: 'neutral' }
  return (
    <Badge tone={s.tone} dot>
      {s.label}
    </Badge>
  )
}

// Wraps a mutating API call: tracks `busy`, toasts success, toasts the real error message on failure.
export function useAction() {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const run = useCallback(
    async (fn, success) => {
      setBusy(true)
      try {
        const r = await fn()
        const msg = typeof success === 'function' ? success(r) : success
        if (msg) toast(typeof msg === 'string' ? { title: msg } : msg)
        return { ok: true, data: r }
      } catch (e) {
        toast({ tone: 'error', title: 'That did not work', message: e.message, duration: 8000 })
        return { ok: false, error: e }
      } finally {
        setBusy(false)
      }
    },
    [toast],
  )
  return { busy, run }
}

export const Muted = ({ children }) => <span className="faint">{children}</span>
