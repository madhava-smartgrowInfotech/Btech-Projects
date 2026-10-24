import { motion } from 'framer-motion'

// Soft floating pastel blobs for hero, CTA and empty-state backgrounds.
// MotionConfig reducedMotion="user" (see main.jsx) turns the drift off for people who prefer less motion.
const BLOB = 'M44.7,-52.4C57.6,-41.7,67.3,-26.8,69.9,-10.7C72.5,5.4,68,22.6,58.1,35.6C48.2,48.6,32.9,57.4,16.4,62.2C-0.1,67,-17.8,67.8,-32.4,61C-47,54.2,-58.5,39.8,-64.1,23.6C-69.7,7.4,-69.4,-10.6,-62.3,-25C-55.2,-39.4,-41.3,-50.2,-26.7,-60.3C-12.1,-70.4,3.2,-79.8,17.4,-76.2C31.6,-72.6,31.8,-63.1,44.7,-52.4Z'

const PRESETS = {
  hero: [
    { color: 'var(--lavender)', size: 460, x: '-8%', y: '-18%', dur: 16 },
    { color: 'var(--mint)', size: 380, x: '68%', y: '38%', dur: 19 },
    { color: 'var(--peach)', size: 300, x: '38%', y: '-26%', dur: 22 },
  ],
  cta: [
    { color: 'var(--mint)', size: 340, x: '-6%', y: '-30%', dur: 18 },
    { color: 'var(--sky)', size: 300, x: '78%', y: '40%', dur: 21 },
  ],
  empty: [
    { color: 'var(--lavender)', size: 220, x: '-8%', y: '-18%', dur: 14 },
    { color: 'var(--mint)', size: 180, x: '78%', y: '58%', dur: 17 },
  ],
  auth: [
    { color: 'var(--lavender)', size: 420, x: '-10%', y: '-14%', dur: 17 },
    { color: 'var(--rose)', size: 320, x: '60%', y: '60%', dur: 20 },
    { color: 'var(--butter)', size: 240, x: '70%', y: '-10%', dur: 23 },
  ],
}

export default function Blobs({ preset = 'hero' }) {
  const items = PRESETS[preset] || PRESETS.hero
  return (
    <div className="blobs" aria-hidden="true">
      {items.map((b, i) => (
        <motion.svg
          key={i}
          viewBox="-100 -100 200 200"
          width={b.size}
          height={b.size}
          style={{ left: b.x, top: b.y }}
          animate={{ y: [0, 18, -10, 0], x: [0, -12, 10, 0], rotate: [0, 8, -6, 0] }}
          transition={{ duration: b.dur, repeat: Infinity, ease: 'easeInOut' }}
        >
          <path d={BLOB} style={{ fill: b.color }} />
        </motion.svg>
      ))}
    </div>
  )
}
