import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { EASE_EXPO, cn } from '@/lib/utils'

/** Lightweight viewport reveal for single blocks (GSAP handles the staggered groups). */
export function Reveal({
  children,
  className,
  delay = 0,
  y = 22,
}: {
  children: ReactNode
  className?: string
  delay?: number
  y?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.9, ease: EASE_EXPO, delay }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  )
}
