import { useReducedMotion } from 'framer-motion'

const PRESETS = {
  empty: [
    { c: 'var(--lavender)', s: 140, x: '-30px', y: '-30px' },
    { c: 'var(--mint)', s: 110, x: 'auto', y: 'auto', r: '-20px', b: '-24px' },
  ],
  hero: [
    { c: 'var(--lavender)', s: 380, x: '-90px', y: '-80px' },
    { c: 'var(--mint)', s: 300, x: 'auto', y: '40px', r: '-60px' },
    { c: 'var(--peach)', s: 240, x: '38%', y: 'auto', b: '-90px' },
  ],
  cta: [
    { c: 'var(--sky)', s: 260, x: '-60px', y: '-60px' },
    { c: 'var(--lavender)', s: 220, x: 'auto', y: 'auto', r: '-40px', b: '-60px' },
  ],
}

/** Decorative soft blobs; static (no motion) so it is safe for reduced-motion users. */
export default function Blobs({ preset = 'hero' }) {
  useReducedMotion()
  return (
    <div className="blobs" aria-hidden="true">
      {PRESETS[preset].map((b, i) => (
        <svg key={i} width={b.s} height={b.s} viewBox="0 0 200 200" style={{ left: b.x === 'auto' ? undefined : b.x, top: b.y === 'auto' ? undefined : b.y, right: b.r, bottom: b.b }}>
          <path fill={b.c} d="M44.7,-58.3C57.6,-48.6,67.4,-34.2,71.7,-18.2C76,-2.2,74.8,15.5,66.6,29.4C58.4,43.3,43.2,53.4,27.2,60.4C11.2,67.4,-5.6,71.3,-21.6,67.4C-37.6,63.5,-52.8,51.8,-62.1,36.6C-71.4,21.4,-74.8,2.7,-70.6,-13.7C-66.4,-30.1,-54.6,-44.2,-40.8,-53.8C-27,-63.4,-11.2,-68.5,2.9,-72C17,-75.5,31.8,-68,44.7,-58.3Z" transform="translate(100 100)" />
        </svg>
      ))}
    </div>
  )
}
