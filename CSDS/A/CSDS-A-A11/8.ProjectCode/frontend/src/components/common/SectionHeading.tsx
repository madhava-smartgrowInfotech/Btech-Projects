import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Reveal } from '@/components/bits/Reveal'

export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
  className,
}: {
  eyebrow?: string
  title: ReactNode
  description?: ReactNode
  action?: ReactNode
  className?: string
}) {
  return (
    <Reveal>
      <div
        className={cn(
          'flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between',
          className,
        )}
      >
        <div className="max-w-2xl">
          {eyebrow && <p className="eyebrow mb-3">{eyebrow}</p>}
          <h2 className="text-[28px] font-medium leading-[1.1] tracking-tighter text-ink-100 sm:text-[34px]">
            {title}
          </h2>
          {description && (
            <p className="mt-3 text-[15px] leading-relaxed text-ink-400">{description}</p>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
    </Reveal>
  )
}
