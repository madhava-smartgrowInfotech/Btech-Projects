import type { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  tone?: 'emerald' | 'amber' | 'danger' | 'neutral'
  className?: string
}

const tones: Record<string, string> = {
  emerald: 'bg-emerald-500/12 text-emerald-300 border-emerald-500/25',
  amber: 'bg-amber-500/12 text-amber-300 border-amber-500/25',
  danger: 'bg-red-500/12 text-red-300 border-red-500/25',
  neutral: 'bg-white/5 text-[var(--color-text-muted)] border-white/10',
}

export function Badge({ children, tone = 'neutral', className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  )
}
