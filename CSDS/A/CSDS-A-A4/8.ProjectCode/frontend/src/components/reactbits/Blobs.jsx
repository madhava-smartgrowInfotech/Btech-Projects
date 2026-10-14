import { motion, useReducedMotion } from 'framer-motion'

// Soft organic blob outlines (vendored in the spirit of React Bits' blob backgrounds).
const PATHS = [
  'M421 302Q390 404 284 434Q178 464 113 372Q48 280 104 178Q160 76 268 70Q376 64 414 132Q452 200 421 302Z',
  'M440 290Q402 380 310 417Q218 454 140 393Q62 332 73 236Q84 140 168 90Q252 40 343 86Q434 132 456 211Q478 290 440 290Z',
  'M408 318Q372 436 250 440Q128 444 86 342Q44 240 108 152Q172 64 280 78Q388 92 416 196Q444 300 408 318Z',
  'M429 287Q405 374 323 421Q241 468 166 410Q91 352 76 260Q61 168 140 106Q219 44 312 76Q405 108 429 197Q453 286 429 287Z',
]

const PRESETS = {
  hero: [
    { color: 'var(--lavender)', size: 520, top: '-12%', left: '-8%', d: 0 },
    { color: 'var(--mint)', size: 420, top: '38%', left: '62%', d: 1 },
    { color: 'var(--peach)', size: 340, top: '64%', left: '4%', d: 2 },
    { color: 'var(--sky)', size: 380, top: '-16%', left: '70%', d: 3 },
  ],
  empty: [
    { color: 'var(--lavender)', size: 260, top: '-30%', left: '-10%', d: 0 },
    { color: 'var(--mint)', size: 220, top: '40%', left: '70%', d: 1 },
    { color: 'var(--peach)', size: 180, top: '55%', left: '-4%', d: 2 },
  ],
  cta: [
    { color: 'var(--lavender)', size: 360, top: '-40%', left: '-8%', d: 0 },
    { color: 'var(--sky)', size: 320, top: '30%', left: '75%', d: 3 },
  ],
}

export default function Blobs({ preset = 'hero', opacity }) {
  const reduce = useReducedMotion()
  return (
    <div className="blobs" aria-hidden="true">
      {PRESETS[preset].map((b, i) => (
        <motion.svg
          key={i}
          viewBox="0 0 500 500"
          width={b.size}
          height={b.size}
          style={{ top: b.top, left: b.left, opacity }}
          animate={
            reduce
              ? undefined
              : { x: [0, 30, -20, 0], y: [0, -24, 18, 0], rotate: [0, 12, -8, 0], scale: [1, 1.06, 0.97, 1] }
          }
          transition={{ duration: 22 + i * 5, repeat: Infinity, ease: 'easeInOut' }}
        >
          <path d={PATHS[b.d % PATHS.length]} style={{ fill: b.color }} />
        </motion.svg>
      ))}
    </div>
  )
}
