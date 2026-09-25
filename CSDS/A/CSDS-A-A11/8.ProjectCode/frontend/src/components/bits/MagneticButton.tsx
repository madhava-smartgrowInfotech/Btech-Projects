import { useRef, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { cn } from '@/lib/utils'

type Props = {
  children: ReactNode
  className?: string
  strength?: number
  onClick?: () => void
}

/**
 * Cursor-magnetic wrapper: the element leans toward the pointer and releases on exit.
 * Pointer tracking is skipped on coarse pointers so touch stays predictable.
 */
export function MagneticButton({ children, className, strength = 0.3, onClick }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const sx = useSpring(x, { stiffness: 220, damping: 18, mass: 0.35 })
  const sy = useSpring(y, { stiffness: 220, damping: 18, mass: 0.35 })
  const rotate = useTransform(sx, [-40, 40], [-2, 2])

  const handleMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.pointerType !== 'mouse') return
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    x.set((event.clientX - (rect.left + rect.width / 2)) * strength)
    y.set((event.clientY - (rect.top + rect.height / 2)) * strength)
  }

  const reset = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      ref={ref}
      onPointerMove={handleMove}
      onPointerLeave={reset}
      onClick={onClick}
      style={{ x: sx, y: sy, rotate }}
      className={cn('inline-flex will-change-transform', className)}
    >
      {children}
    </motion.div>
  )
}
