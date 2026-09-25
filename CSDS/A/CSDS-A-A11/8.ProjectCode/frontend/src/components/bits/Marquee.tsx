import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

/** Seamless horizontal ticker — the track is duplicated and translated by 50%. */
export function Marquee({
  children,
  className,
  speed = 38,
  pauseOnHover = true,
}: {
  children: ReactNode
  className?: string
  speed?: number
  pauseOnHover?: boolean
}) {
  return (
    <div className={cn('group relative overflow-hidden mask-fade-x', className)}>
      <div
        className={cn(
          'flex w-max animate-marquee items-center gap-12',
          pauseOnHover && 'group-hover:[animation-play-state:paused]',
        )}
        style={{ animationDuration: `${speed}s` }}
      >
        <div className="flex shrink-0 items-center gap-12">{children}</div>
        <div className="flex shrink-0 items-center gap-12" aria-hidden>
          {children}
        </div>
      </div>
    </div>
  )
}
