import type { ReactNode } from 'react'
import { PlugZap, RefreshCw, SearchX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api'
import { cn } from '@/lib/utils'

export function ErrorState({
  error,
  onRetry,
  compact = false,
  title,
  className,
}: {
  error?: unknown
  onRetry?: () => void
  compact?: boolean
  title?: string
  className?: string
}) {
  const offline = error instanceof ApiError && error.offline
  const message =
    error instanceof Error ? error.message : 'Something went wrong loading this section.'

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-white/[0.09] bg-white/[0.015] px-6 text-center',
        compact ? 'py-8' : 'py-14',
        className,
      )}
    >
      <span className="grid h-10 w-10 place-items-center rounded-full border border-white/[0.08] bg-white/[0.03] text-amber-300">
        <PlugZap className="h-4 w-4" />
      </span>
      <div>
        <p className="text-sm font-medium text-ink-200">
          {title ?? (offline ? 'Service unreachable' : 'Could not load')}
        </p>
        <p className="mx-auto mt-1 max-w-sm text-[13px] leading-relaxed text-ink-400">
          {offline
            ? 'The Nuvara service is not responding right now. Everything else on the page keeps working.'
            : message}
        </p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} className="mt-1">
          <RefreshCw className="h-3.5 w-3.5" />
          Try again
        </Button>
      )}
    </div>
  )
}

export function EmptyState({
  title,
  description,
  action,
  icon,
  className,
}: {
  title: string
  description?: string
  action?: ReactNode
  icon?: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-white/[0.09] bg-white/[0.015] px-6 py-14 text-center',
        className,
      )}
    >
      <span className="grid h-10 w-10 place-items-center rounded-full border border-white/[0.08] bg-white/[0.03] text-ink-400">
        {icon ?? <SearchX className="h-4 w-4" />}
      </span>
      <div>
        <p className="text-sm font-medium text-ink-200">{title}</p>
        {description && (
          <p className="mx-auto mt-1 max-w-sm text-[13px] leading-relaxed text-ink-400">
            {description}
          </p>
        )}
      </div>
      {action}
    </div>
  )
}
