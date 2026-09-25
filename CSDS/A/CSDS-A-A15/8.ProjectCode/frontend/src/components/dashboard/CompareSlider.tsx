import { GripVertical } from 'lucide-react'
import { useRef, useState } from 'react'

export function CompareSlider({
  beforeSrc,
  afterSrc,
  beforeLabel = 'Original',
  afterLabel = 'Explainable Heatmap',
}: {
  beforeSrc: string
  afterSrc: string
  beforeLabel?: string
  afterLabel?: string
}) {
  const [percent, setPercent] = useState(50)
  const containerRef = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)

  function updateFromClientX(clientX: number) {
    const el = containerRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const pct = ((clientX - rect.left) / rect.width) * 100
    setPercent(Math.min(100, Math.max(0, pct)))
  }

  return (
    <div
      ref={containerRef}
      className="relative aspect-video w-full overflow-hidden rounded-xl ring-1 ring-white/10 select-none cursor-ew-resize"
      onMouseDown={(e) => {
        dragging.current = true
        updateFromClientX(e.clientX)
      }}
      onMouseMove={(e) => {
        if (dragging.current) updateFromClientX(e.clientX)
      }}
      onMouseUp={() => (dragging.current = false)}
      onMouseLeave={() => (dragging.current = false)}
      onTouchStart={(e) => updateFromClientX(e.touches[0].clientX)}
      onTouchMove={(e) => updateFromClientX(e.touches[0].clientX)}
    >
      <img src={afterSrc} alt={afterLabel} className="absolute inset-0 h-full w-full object-cover" draggable={false} />
      <img
        src={beforeSrc}
        alt={beforeLabel}
        className="absolute inset-0 h-full w-full object-cover"
        style={{ clipPath: `inset(0 ${100 - percent}% 0 0)` }}
        draggable={false}
      />

      <div
        className="absolute inset-y-0 w-0.5 bg-white/80"
        style={{ left: `${percent}%` }}
      >
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-8 w-8 rounded-full bg-white flex items-center justify-center shadow-lg">
          <GripVertical className="h-4 w-4 text-slate-900" />
        </div>
      </div>

      <span className="absolute top-3 left-3 rounded-full bg-black/50 backdrop-blur px-2.5 py-1 text-xs text-white">
        {beforeLabel}
      </span>
      <span className="absolute top-3 right-3 rounded-full bg-black/50 backdrop-blur px-2.5 py-1 text-xs text-white">
        {afterLabel}
      </span>
    </div>
  )
}
