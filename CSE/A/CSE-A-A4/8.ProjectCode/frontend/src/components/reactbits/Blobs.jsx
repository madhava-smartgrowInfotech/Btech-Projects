import { useReducedMotion } from 'framer-motion'

const PRESETS = {
  hero: [
    { c: 'var(--lavender)', s: 420, x: '-6%', y: '-14%', d: 18 },
    { c: 'var(--mint)', s: 340, x: '68%', y: '-8%', d: 22 },
    { c: 'var(--peach)', s: 300, x: '38%', y: '62%', d: 26 },
  ],
  empty: [
    { c: 'var(--lavender-soft)', s: 220, x: '-8%', y: '-30%', d: 16 },
    { c: 'var(--sky-soft)', s: 200, x: '70%', y: '40%', d: 20 },
  ],
  cta: [
    { c: 'var(--mint)', s: 300, x: '-6%', y: '-30%', d: 20 },
    { c: 'var(--sky)', s: 280, x: '76%', y: '30%', d: 24 },
  ],
}

/** Soft drifting colour blobs behind a section. Static under reduced motion. */
export default function Blobs({ preset = 'hero' }) {
  const reduce = useReducedMotion()
  return (
    <div className="blobs" aria-hidden="true">
      {(PRESETS[preset] || PRESETS.hero).map((b, i) => (
        <svg
          key={i}
          width={b.s}
          height={b.s}
          viewBox="0 0 200 200"
          style={{
            left: b.x,
            top: b.y,
            animation: reduce ? 'none' : `blob-drift ${b.d}s ease-in-out ${i * -4}s infinite alternate`,
          }}
        >
          <path fill={b.c} d="M43.6,-58.2C56.5,-48.6,67.2,-35.6,71.6,-20.6C76,-5.6,74.1,11.3,66.2,24.5C58.3,37.7,44.4,47.2,29.6,54.9C14.8,62.6,-0.9,68.5,-16.5,65.8C-32.1,63.1,-47.6,51.8,-57.5,37.4C-67.4,23,-71.7,5.5,-68.2,-10C-64.7,-25.5,-53.4,-39,-40,-48.4C-26.6,-57.8,-13.3,-63.1,0.9,-64.2C15.1,-65.3,30.7,-67.8,43.6,-58.2Z" transform="translate(100 100)" />
        </svg>
      ))}
      <style>{'@keyframes blob-drift{from{transform:translate(0,0) rotate(0deg) scale(1)}to{transform:translate(28px,22px) rotate(14deg) scale(1.08)}}'}</style>
    </div>
  )
}
