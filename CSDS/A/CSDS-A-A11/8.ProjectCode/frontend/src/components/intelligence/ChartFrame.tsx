import type { ReactNode } from 'react'
import { useReveal } from '@/hooks/useReveal'
import { cn } from '@/lib/utils'

export const CHART_COLORS = {
  amber: '#E5A54B',
  cobalt: '#6B93FF',
  teal: '#4FD1C5',
  rose: '#F08A8A',
  slate: '#6B7684',
  grid: 'rgba(255,255,255,0.055)',
  axis: '#6B7684',
}

export const AGENT_COLORS: Record<string, string> = {
  collaborative: CHART_COLORS.amber,
  content: CHART_COLORS.cobalt,
  trending: CHART_COLORS.teal,
  diversity: CHART_COLORS.rose,
}

export const axisProps = {
  stroke: CHART_COLORS.axis,
  tick: { fill: CHART_COLORS.axis, fontSize: 11 },
  tickLine: false,
  axisLine: { stroke: 'rgba(255,255,255,0.08)' },
} as const

type TooltipEntry = {
  name?: string | number
  value?: number | string
  color?: string
  dataKey?: string | number
}

/** Shared tooltip so every chart in the console reads as one system. */
export function ChartTooltip({
  active,
  payload,
  label,
  formatter,
  labelFormatter,
}: {
  active?: boolean
  payload?: TooltipEntry[]
  label?: string | number
  formatter?: (value: number, name: string) => string
  labelFormatter?: (label: string | number) => string
}) {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="rounded-xl border border-white/10 bg-ink-875/95 px-3 py-2.5 shadow-lift backdrop-blur-xl">
      {label !== undefined && (
        <p className="mb-1.5 text-[10.5px] uppercase tracking-[0.16em] text-ink-500">
          {labelFormatter ? labelFormatter(label) : label}
        </p>
      )}
      <ul className="space-y-1">
        {payload.map((entry, i) => (
          <li key={i} className="flex items-center gap-2 text-[12px]">
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full"
              style={{ background: entry.color ?? CHART_COLORS.slate }}
            />
            <span className="capitalize text-ink-400">
              {String(entry.name ?? entry.dataKey ?? '').replace(/_/g, ' ')}
            </span>
            <span className="num ml-auto text-ink-100">
              {formatter
                ? formatter(Number(entry.value), String(entry.name ?? ''))
                : typeof entry.value === 'number'
                  ? entry.value.toFixed(3)
                  : String(entry.value)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Panel shell with a GSAP reveal so charts never appear as raw recharts output. */
export function ChartFrame({
  eyebrow,
  title,
  description,
  action,
  children,
  className,
  bodyClassName,
}: {
  eyebrow?: string
  title: string
  description?: string
  action?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
}) {
  const ref = useReveal<HTMLDivElement>({ stagger: 0.06, y: 16 })

  return (
    <section ref={ref} className={cn('panel overflow-hidden', className)}>
      <header
        data-reveal
        className="flex flex-wrap items-start justify-between gap-4 border-b border-white/[0.06] px-5 py-4 sm:px-6"
      >
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h3 className="mt-1.5 text-[15px] font-medium tracking-tight text-ink-100">{title}</h3>
          {description && (
            <p className="mt-1 max-w-xl text-[12.5px] leading-relaxed text-ink-500">
              {description}
            </p>
          )}
        </div>
        {action}
      </header>
      <div data-reveal className={cn('p-5 sm:p-6', bodyClassName)}>
        {children}
      </div>
    </section>
  )
}
