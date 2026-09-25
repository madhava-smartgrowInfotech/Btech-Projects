import { type ReactNode, useRef } from 'react'
import { motion, useMotionTemplate, useMotionValue } from 'framer-motion'

export function SpotlightCard({
  icon,
  title,
  description,
  accent = '#3b82f6',
}: {
  icon: ReactNode
  title: string
  description: string
  accent?: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return
    mouseX.set(e.clientX - rect.left)
    mouseY.set(e.clientY - rect.top)
  }

  const background = useMotionTemplate`radial-gradient(280px circle at ${mouseX}px ${mouseY}px, ${accent}22, transparent 75%)`

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      whileHover={{ y: -4 }}
      transition={{ type: 'spring', stiffness: 300, damping: 22 }}
      className="group relative overflow-hidden rounded-2xl border border-white/8 bg-ink-850/70 p-6"
    >
      <motion.div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" style={{ background }} />
      <div
        className="relative mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
        style={{ background: `${accent}1a`, color: accent }}
      >
        {icon}
      </div>
      <h3 className="relative font-display text-base font-semibold text-white">{title}</h3>
      <p className="relative mt-2 text-sm leading-relaxed text-ink-400">{description}</p>
    </motion.div>
  )
}
