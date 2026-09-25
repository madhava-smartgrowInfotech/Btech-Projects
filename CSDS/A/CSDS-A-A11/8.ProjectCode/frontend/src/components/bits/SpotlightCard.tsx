import { useRef, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

/**
 * Card shell with a pointer-tracked radial highlight and a hairline border that
 * lights up on hover. Pure CSS custom properties — no per-frame React state.
 */
export function SpotlightCard({
  children,
  className,
  glowColor = 'rgba(229,165,75,0.16)',
}: {
  children: ReactNode
  className?: string
  glowColor?: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [active, setActive] = useState(false)

  const onMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty('--mx', `${event.clientX - rect.left}px`)
    el.style.setProperty('--my', `${event.clientY - rect.top}px`)
  }

  return (
    <div
      ref={ref}
      onPointerMove={onMove}
      onPointerEnter={() => setActive(true)}
      onPointerLeave={() => setActive(false)}
      className={cn(
        'group/spot relative overflow-hidden rounded-2xl border border-white/[0.07] bg-ink-900/60 transition-[border-color,transform,box-shadow] duration-500 ease-expo hover:border-white/[0.14]',
        className,
      )}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 ease-expo"
        style={{
          opacity: active ? 1 : 0,
          background: `radial-gradient(420px circle at var(--mx, 50%) var(--my, 50%), ${glowColor}, transparent 62%)`,
        }}
      />
      <div className="relative">{children}</div>
    </div>
  )
}
