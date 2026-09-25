import { useEffect, useRef, useState } from 'react'
import { useInView, useMotionValue, useSpring } from 'framer-motion'
import { cn } from '@/lib/utils'

type Props = {
  value: number
  decimals?: number
  prefix?: string
  suffix?: string
  className?: string
  /** Multiply the incoming value (e.g. 0.042 → 4.2 with 100). */
  scale?: number
  compact?: boolean
  startOnView?: boolean
}

/**
 * Spring-driven counter. Values ease into place instead of snapping, which makes
 * live metrics feel continuous rather than stroboscopic.
 */
export function AnimatedNumber({
  value,
  decimals = 0,
  prefix = '',
  suffix = '',
  className,
  scale = 1,
  compact = false,
  startOnView = false,
}: Props) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-40px' })
  const motionValue = useMotionValue(startOnView ? 0 : value * scale)
  const spring = useSpring(motionValue, { stiffness: 110, damping: 22, mass: 0.7 })
  const [display, setDisplay] = useState(() => (startOnView ? 0 : value * scale))

  useEffect(() => {
    if (startOnView && !inView) return
    motionValue.set(Number.isFinite(value) ? value * scale : 0)
  }, [value, scale, motionValue, startOnView, inView])

  useEffect(() => spring.on('change', (v) => setDisplay(v)), [spring])

  const formatted = compact
    ? new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(
        display,
      )
    : display.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })

  return (
    <span ref={ref} className={cn('num tabular-nums', className)}>
      {prefix}
      {formatted}
      {suffix}
    </span>
  )
}
