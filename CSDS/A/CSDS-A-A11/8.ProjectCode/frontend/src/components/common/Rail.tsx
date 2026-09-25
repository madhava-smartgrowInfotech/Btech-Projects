import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

/** Horizontal snap scroller with edge-aware arrow affordances. */
export function Rail({
  children,
  className,
  itemClassName,
}: {
  children: ReactNode[]
  className?: string
  itemClassName?: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [edges, setEdges] = useState({ start: true, end: false })

  const measure = useCallback(() => {
    const el = ref.current
    if (!el) return
    setEdges({
      start: el.scrollLeft <= 4,
      end: el.scrollLeft + el.clientWidth >= el.scrollWidth - 4,
    })
  }, [])

  useEffect(() => {
    measure()
    const el = ref.current
    if (!el) return
    el.addEventListener('scroll', measure, { passive: true })
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => {
      el.removeEventListener('scroll', measure)
      ro.disconnect()
    }
  }, [measure, children.length])

  const scrollBy = (dir: 1 | -1) => {
    const el = ref.current
    if (!el) return
    el.scrollBy({ left: dir * Math.max(280, el.clientWidth * 0.72), behavior: 'smooth' })
  }

  return (
    <div className={cn('relative', className)}>
      <div
        ref={ref}
        data-lenis-prevent
        className="no-scrollbar -mx-5 flex snap-x snap-mandatory gap-5 overflow-x-auto scroll-smooth px-5 pb-1 sm:mx-0 sm:px-0"
      >
        {children.map((child, i) => (
          <div
            key={i}
            className={cn(
              'w-[74vw] shrink-0 snap-start sm:w-[44vw] lg:w-[calc((100%-3rem)/3)] xl:w-[calc((100%-4.5rem)/4)]',
              itemClassName,
            )}
          >
            {child}
          </div>
        ))}
      </div>

      <div className="pointer-events-none absolute -top-14 right-0 hidden gap-2 sm:flex">
        <button
          type="button"
          onClick={() => scrollBy(-1)}
          disabled={edges.start}
          aria-label="Scroll left"
          className="pointer-events-auto grid h-9 w-9 place-items-center rounded-full border border-white/[0.09] bg-white/[0.02] text-ink-300 transition-all duration-300 ease-expo hover:border-white/25 hover:text-ink-100 disabled:opacity-30"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => scrollBy(1)}
          disabled={edges.end}
          aria-label="Scroll right"
          className="pointer-events-auto grid h-9 w-9 place-items-center rounded-full border border-white/[0.09] bg-white/[0.02] text-ink-300 transition-all duration-300 ease-expo hover:border-white/25 hover:text-ink-100 disabled:opacity-30"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
