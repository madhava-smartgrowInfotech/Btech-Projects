import * as React from 'react'
import { cn } from '@/lib/utils'

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'h-11 w-full rounded-full border border-white/[0.09] bg-white/[0.03] px-4 text-sm text-ink-100 placeholder:text-ink-500 transition-colors duration-300 ease-expo hover:border-white/15 focus:border-amber-400/50 focus:bg-white/[0.05] focus:outline-none focus:ring-0',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'

export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => (
  <div className="relative">
    <select
      ref={ref}
      className={cn(
        'h-11 w-full appearance-none rounded-full border border-white/[0.09] bg-white/[0.03] pl-4 pr-10 text-sm text-ink-100 transition-colors duration-300 ease-expo hover:border-white/15 focus:border-amber-400/50 focus:outline-none [&>option]:bg-ink-900 [&>option]:text-ink-100',
        className,
      )}
      {...props}
    >
      {children}
    </select>
    <svg
      aria-hidden
      viewBox="0 0 12 12"
      className="pointer-events-none absolute right-4 top-1/2 h-3 w-3 -translate-y-1/2 text-ink-400"
    >
      <path d="M2 4.5 6 8.5 10 4.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  </div>
))
Select.displayName = 'Select'
