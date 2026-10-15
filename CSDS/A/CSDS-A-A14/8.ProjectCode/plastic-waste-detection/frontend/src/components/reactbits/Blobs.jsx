import { motion } from 'framer-motion'

// Soft decorative blobs. preset: 'hero' | 'cta' | 'empty'. Purely decorative (aria-hidden).
const PRESETS = {
  hero: [
    { c: 'var(--lavender)', s: 380, x: '-6%', y: '-14%', d: 14 },
    { c: 'var(--mint)', s: 300, x: '72%', y: '8%', d: 17 },
    { c: 'var(--peach)', s: 240, x: '46%', y: '68%', d: 19 },
    { c: 'var(--sky)', s: 200, x: '8%', y: '66%', d: 16 },
  ],
  cta: [
    { c: 'var(--mint)', s: 260, x: '-5%', y: '-30%', d: 15 },
    { c: 'var(--sky)', s: 220, x: '78%', y: '40%', d: 18 },
    { c: 'var(--lavender)', s: 180, x: '60%', y: '-25%', d: 13 },
  ],
  empty: [
    { c: 'var(--lavender)', s: 160, x: '-8%', y: '-20%', d: 12 },
    { c: 'var(--mint)', s: 130, x: '80%', y: '60%', d: 15 },
  ],
}

const BLOB = 'M44.7,-52.9C57.1,-43.1,66,-28.6,68.6,-12.9C71.2,2.8,67.5,19.6,58.2,32.4C48.9,45.2,34,54,18.1,59.6C2.2,65.2,-14.7,67.6,-29.5,62C-44.3,56.4,-57,42.8,-63.1,27.2C-69.2,11.6,-68.7,-6,-62.1,-20.5C-55.5,-35,-42.8,-46.4,-29.2,-55.8C-15.6,-65.2,-1,-72.6,12.3,-70.2C25.6,-67.8,32.3,-62.7,44.7,-52.9Z'

export default function Blobs({ preset = 'hero' }) {
  return (
    <div className="blobs" aria-hidden="true">
      {(PRESETS[preset] || PRESETS.hero).map((b, i) => (
        <motion.svg
          key={i}
          viewBox="-100 -100 200 200"
          width={b.s}
          height={b.s}
          style={{ left: b.x, top: b.y }}
          animate={{ y: [0, -18, 0], rotate: [0, 8, 0] }}
          transition={{ duration: b.d, repeat: Infinity, ease: 'easeInOut' }}
        >
          <path d={BLOB} fill={b.c} />
        </motion.svg>
      ))}
    </div>
  )
}
