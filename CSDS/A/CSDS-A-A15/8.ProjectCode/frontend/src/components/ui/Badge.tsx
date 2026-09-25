import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  color?: 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose' | 'slate'
}

const colorStyles: Record<NonNullable<BadgeProps['color']>, string> = {
  cyan: 'bg-cyan-400/10 text-cyan-300 ring-cyan-400/30',
  violet: 'bg-violet-400/10 text-violet-300 ring-violet-400/30',
  emerald: 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/30',
  amber: 'bg-amber-400/10 text-amber-300 ring-amber-400/30',
  rose: 'bg-rose-400/10 text-rose-300 ring-rose-400/30',
  slate: 'bg-white/5 text-slate-300 ring-white/10',
}

export function Badge({ className, color = 'slate', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1',
        colorStyles[color],
        className,
      )}
      {...props}
    />
  )
}
