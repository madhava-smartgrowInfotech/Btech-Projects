import { memo } from 'react'

// Soft decorative blobs behind hero / empty-state / CTA surfaces. Purely visual (aria-hidden).
const PRESETS = {
  hero: [
    { c: 'var(--lavender)', x: '-6%', y: '-10%', s: 420 },
    { c: 'var(--mint)', x: '62%', y: '48%', s: 360 },
    { c: 'var(--peach)', x: '78%', y: '-14%', s: 300 },
  ],
  empty: [
    { c: 'var(--lavender)', x: '-8%', y: '-30%', s: 180 },
    { c: 'var(--mint)', x: '72%', y: '40%', s: 170 },
  ],
  cta: [
    { c: 'var(--mint)', x: '-6%', y: '-30%', s: 300 },
    { c: 'var(--sky)', x: '78%', y: '30%', s: 280 },
  ],
}

function Blobs({ preset = 'hero' }) {
  const list = PRESETS[preset] || PRESETS.hero
  return (
    <div className="blobs" aria-hidden="true">
      {list.map((b, i) => (
        <svg key={i} width={b.s} height={b.s} viewBox="0 0 200 200" style={{ left: b.x, top: b.y }}>
          <path
            fill={b.c}
            d="M44.7,-58.6C57.2,-49.7,66.1,-35.3,70.6,-19.5C75.1,-3.7,75.2,13.6,68.4,27.6C61.6,41.6,47.9,52.3,33,59.9C18.1,67.5,2,72,-14.7,70.1C-31.4,68.2,-48.7,59.9,-59.4,46.5C-70.1,33.1,-74.2,14.6,-71.9,-2.4C-69.6,-19.4,-61,-34.9,-48.8,-43.9C-36.6,-52.9,-20.8,-55.4,-3.4,-51.6C14,-47.8,32.2,-67.5,44.7,-58.6Z"
            transform="translate(100 100)"
          />
        </svg>
      ))}
    </div>
  )
}

export default memo(Blobs)
