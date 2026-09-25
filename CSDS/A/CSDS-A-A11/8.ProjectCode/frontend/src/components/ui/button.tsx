import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'relative inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-full font-medium tracking-tight transition-[background-color,color,border-color,box-shadow,transform] duration-300 ease-expo disabled:pointer-events-none disabled:opacity-45 active:scale-[0.985]',
  {
    variants: {
      variant: {
        primary:
          'bg-amber-400 text-ink-950 hover:bg-amber-300 shadow-[0_10px_30px_-12px_rgba(229,165,75,0.8)]',
        secondary:
          'bg-white/[0.06] text-ink-100 hover:bg-white/[0.1] border border-white/[0.08]',
        outline:
          'border border-white/15 text-ink-100 hover:border-white/30 hover:bg-white/[0.04]',
        ghost: 'text-ink-300 hover:text-ink-100 hover:bg-white/[0.06]',
        danger: 'bg-rose-500/90 text-white hover:bg-rose-500',
        link: 'text-amber-300 underline-offset-4 hover:underline px-0',
      },
      size: {
        sm: 'h-9 px-4 text-[13px]',
        md: 'h-11 px-6 text-sm',
        lg: 'h-13 px-8 text-[15px] py-3.5',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
    )
  },
)
Button.displayName = 'Button'

export { buttonVariants }
