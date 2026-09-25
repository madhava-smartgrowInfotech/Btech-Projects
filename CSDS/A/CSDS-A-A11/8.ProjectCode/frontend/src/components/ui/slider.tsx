import * as React from 'react'
import * as SliderPrimitive from '@radix-ui/react-slider'
import { cn } from '@/lib/utils'

export const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn('relative flex w-full touch-none select-none items-center py-2', className)}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-[3px] w-full grow overflow-hidden rounded-full bg-white/[0.09]">
      <SliderPrimitive.Range className="absolute h-full rounded-full bg-gradient-to-r from-amber-500 to-amber-300" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb
      className="block h-4 w-4 rounded-full border border-amber-200/70 bg-ink-950 shadow-[0_0_0_4px_rgba(229,165,75,0.14)] transition-[box-shadow,transform] duration-300 ease-expo hover:scale-110 hover:shadow-[0_0_0_7px_rgba(229,165,75,0.18)] focus-visible:ring-2 focus-visible:ring-amber-300 disabled:pointer-events-none"
      aria-label="Weight"
    />
  </SliderPrimitive.Root>
))
Slider.displayName = 'Slider'
