import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium tracking-tight transition-colors',
  {
    variants: {
      variant: {
        default: 'border-white/10 bg-white/[0.05] text-ink-300',
        accent: 'border-amber-400/30 bg-amber-400/10 text-amber-200',
        cobalt: 'border-cobalt-400/30 bg-cobalt-500/10 text-cobalt-300',
        success: 'border-teal-400/30 bg-teal-400/10 text-teal-400',
        warning: 'border-amber-400/35 bg-amber-500/10 text-amber-300',
        danger: 'border-rose-400/30 bg-rose-500/10 text-rose-400',
        outline: 'border-white/15 bg-transparent text-ink-300',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

/** forwardRef so Radix primitives (tooltip/dropdown triggers) can compose it via asChild. */
export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, ...props }, ref) => (
    <span ref={ref} className={cn(badgeVariants({ variant }), className)} {...props} />
  ),
)
Badge.displayName = 'Badge'

export { badgeVariants }
