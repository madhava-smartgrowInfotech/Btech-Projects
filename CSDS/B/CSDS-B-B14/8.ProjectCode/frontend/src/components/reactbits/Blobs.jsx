// Soft decorative shapes behind the hero, empty states and the call-to-action block.
// Purely decorative: hidden from assistive technology, no motion cost.
export default function Blobs({ preset = 'empty' }) {
  const big = preset === 'landing'
  return (
    <div className="blobs" aria-hidden="true">
      <svg viewBox="0 0 200 200" style={{ width: big ? 460 : 220, top: big ? -120 : -60, left: big ? -120 : -40 }}>
        <circle cx="100" cy="100" r="95" fill="var(--lavender)" />
      </svg>
      <svg viewBox="0 0 200 200" style={{ width: big ? 380 : 180, bottom: big ? -90 : -50, right: big ? -80 : -30 }}>
        <circle cx="100" cy="100" r="95" fill="var(--mint)" />
      </svg>
    </div>
  )
}
