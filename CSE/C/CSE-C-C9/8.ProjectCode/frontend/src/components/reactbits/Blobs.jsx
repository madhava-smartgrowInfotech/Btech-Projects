import { useReducedMotion } from 'framer-motion'

const PRESETS = {
  empty: [
    { c: 'var(--lavender)', x: '-8%', y: '-30%', s: 180 },
    { c: 'var(--mint)', x: '82%', y: '60%', s: 150 },
  ],
  hero: [
    { c: 'var(--lavender)', x: '-6%', y: '-10%', s: 360 },
    { c: 'var(--mint)', x: '68%', y: '6%', s: 300 },
    { c: 'var(--peach)', x: '40%', y: '72%', s: 280 },
    { c: 'var(--sky)', x: '-4%', y: '70%', s: 220 },
  ],
  cta: [
    { c: 'var(--mint)', x: '-6%', y: '-20%', s: 260 },
    { c: 'var(--sky)', x: '86%', y: '50%', s: 240 },
  ],
}

/** Soft drifting pastel blobs. Static under reduced motion. */
export default function Blobs({ preset = 'hero' }) {
  const reduce = useReducedMotion()
  const items = PRESETS[preset] || PRESETS.hero
  return (
    <div className="blobs" aria-hidden="true">
      {items.map((b, i) => (
        <svg
          key={i}
          viewBox="0 0 200 200"
          width={b.s}
          height={b.s}
          style={{ left: b.x, top: b.y, animation: reduce ? 'none' : `blob-drift ${14 + i * 3}s ease-in-out ${i * -3}s infinite alternate` }}
        >
          <path fill={b.c} d="M43.7,-58.3C56.4,-49.3,66.2,-36.1,70.6,-21.2C75,-6.3,74,10.2,67.5,23.6C61,37,49,47.3,35.6,55.6C22.2,63.9,7.4,70.1,-8.4,70.7C-24.2,71.3,-41,66.3,-52.6,55.7C-64.2,45.1,-70.6,28.9,-72.1,12.5C-73.6,-3.9,-70.2,-20.5,-61.2,-32.4C-52.2,-44.3,-37.6,-51.4,-23.4,-59.7C-9.2,-68,4.6,-77.5,18.3,-75.6C32,-73.7,31,-67.3,43.7,-58.3Z" transform="translate(100 100)" />
        </svg>
      ))}
      <style>{'@keyframes blob-drift{from{transform:translate(0,0) rotate(0deg) scale(1)}to{transform:translate(18px,-14px) rotate(14deg) scale(1.06)}}'}</style>
    </div>
  )
}
