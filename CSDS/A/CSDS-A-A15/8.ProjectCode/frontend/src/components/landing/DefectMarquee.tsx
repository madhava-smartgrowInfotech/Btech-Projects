import gsap from 'gsap'
import { useEffect, useRef } from 'react'

const DEFECTS = [
  'Crazing',
  'Inclusion',
  'Patches',
  'Pitted Surface',
  'Rolled-in Scale',
  'Scratches',
]

/** GSAP-driven infinite marquee of the defect classes the model recognizes. */
export function DefectMarquee() {
  const trackRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const track = trackRef.current
    if (!track) return

    const ctx = gsap.context(() => {
      const width = track.scrollWidth / 2
      gsap.to(track, {
        x: -width,
        duration: 24,
        ease: 'none',
        repeat: -1,
      })
    }, track)

    return () => ctx.revert()
  }, [])

  const items = [...DEFECTS, ...DEFECTS]

  return (
    <div className="relative border-y border-white/5 py-5 overflow-hidden bg-white/[0.02]">
      <div className="absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-[#05070c] to-transparent z-10" />
      <div className="absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-[#05070c] to-transparent z-10" />
      <div ref={trackRef} className="flex gap-12 w-max">
        {items.map((label, i) => (
          <span key={i} className="flex items-center gap-3 text-sm font-medium text-slate-500 whitespace-nowrap">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400/60" />
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}
