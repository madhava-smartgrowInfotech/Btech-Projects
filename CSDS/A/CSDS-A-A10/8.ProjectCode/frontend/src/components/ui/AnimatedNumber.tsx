import { useEffect, useRef } from 'react'
import { animate, useMotionValue, useTransform } from 'framer-motion'

export function AnimatedNumber({
  value,
  decimals = 0,
  suffix = '',
}: {
  value: number
  decimals?: number
  suffix?: string
}) {
  const motionValue = useMotionValue(0)
  const rounded = useTransform(motionValue, (v) => v.toFixed(decimals))
  const spanRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const controls = animate(motionValue, value, { duration: 0.9, ease: [0.16, 1, 0.3, 1] })
    return controls.stop
  }, [value, motionValue])

  useEffect(() => rounded.on('change', (v) => {
    if (spanRef.current) spanRef.current.textContent = `${v}${suffix}`
  }), [rounded, suffix])

  return <span ref={spanRef}>0{suffix}</span>
}
