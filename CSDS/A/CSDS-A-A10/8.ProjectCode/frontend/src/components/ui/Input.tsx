import { type InputHTMLAttributes, type LabelHTMLAttributes, type SelectHTMLAttributes, forwardRef } from 'react'

import { cn } from '@/lib/utils'

export const Label = ({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) => (
  <label className={cn('mb-1.5 block text-xs font-medium text-ink-300', className)} {...props} />
)

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'h-10 w-full rounded-lg border border-white/10 bg-ink-900/60 px-3 text-sm text-ink-50 placeholder:text-ink-400',
        'outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      'w-full rounded-lg border border-white/10 bg-ink-900/60 px-3 py-2 text-sm text-ink-50 placeholder:text-ink-400',
      'outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20',
      className,
    )}
    {...props}
  />
))
Textarea.displayName = 'Textarea'

export const NativeSelect = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'h-10 w-full rounded-lg border border-white/10 bg-ink-900/60 px-3 text-sm text-ink-50',
        'outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20',
        className,
      )}
      {...props}
    >
      {children}
    </select>
  ),
)
NativeSelect.displayName = 'NativeSelect'
