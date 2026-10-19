import { motion, useReducedMotion } from 'framer-motion'

// Soft floating blobs behind hero / empty states. preset: hero | cta | empty
const PRESETS = {
  hero: [
    { c: 'var(--lavender)', s: 420, x: '-6%', y: '-18%', d: 16 },
    { c: 'var(--mint)', s: 340, x: '68%', y: '48%', d: 19 },
    { c: 'var(--peach)', s: 260, x: '42%', y: '-12%', d: 22 },
  ],
  cta: [
    { c: 'var(--mint)', s: 320, x: '-8%', y: '-30%', d: 18 },
    { c: 'var(--sky)', s: 280, x: '78%', y: '40%', d: 21 },
  ],
  empty: [
    { c: 'var(--lavender)', s: 200, x: '-10%', y: '-20%', d: 18 },
    { c: 'var(--mint)', s: 170, x: '80%', y: '55%', d: 22 },
  ],
}

export default function Blobs({ preset = 'hero' }) {
  const reduce = useReducedMotion()
  return (
    <div className="blobs" aria-hidden="true">
      {(PRESETS[preset] || PRESETS.hero).map((b, i) => (
        <motion.svg
          key={i}
          width={b.s}
          height={b.s}
          viewBox="0 0 200 200"
          style={{ left: b.x, top: b.y }}
          animate={reduce ? undefined : { x: [0, 18, -10, 0], y: [0, -14, 12, 0], rotate: [0, 8, -6, 0] }}
          transition={{ duration: b.d, repeat: Infinity, ease: 'easeInOut' }}
        >
          <path
            fill={b.c}
            d="M44.7,-58.4C57.9,-48.8,68.5,-34.6,72.6,-18.7C76.7,-2.8,74.3,14.7,66.1,28.7C57.9,42.7,43.9,53.2,28.4,60.4C12.9,67.6,-4,71.5,-20.1,67.8C-36.2,64.1,-51.5,52.8,-61.1,37.9C-70.7,23,-74.6,4.5,-70.4,-11.6C-66.2,-27.7,-53.9,-41.4,-40,-50.9C-26.1,-60.4,-13,-65.7,1.3,-67.2C15.6,-68.7,31.5,-68,44.7,-58.4Z"
            transform="translate(100 100)"
          />
        </motion.svg>
      ))}
    </div>
  )
}
