import { useLayoutEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { cn } from '@/lib/utils'

gsap.registerPlugin(ScrollTrigger)

type Props = {
  text: string
  className?: string
  /** Reveal immediately on mount instead of waiting for the scroll trigger. */
  immediate?: boolean
  delay?: number
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span'
}

/**
 * Word-by-word masked rise. Each word sits in an overflow-hidden sleeve and is
 * lifted into place on a staggered expo curve.
 */
export function TextReveal({ text, className, immediate = false, delay = 0, as = 'h2' }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const Tag = as

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      gsap.set(el.querySelectorAll('[data-word]'), { yPercent: 0, opacity: 1 })
      return
    }

    const ctx = gsap.context(() => {
      const words = el.querySelectorAll('[data-word]')
      gsap.set(words, { yPercent: 118, opacity: 0 })
      gsap.to(words, {
        yPercent: 0,
        opacity: 1,
        duration: 1.05,
        delay,
        stagger: 0.055,
        ease: 'expo.out',
        ...(immediate
          ? {}
          : { scrollTrigger: { trigger: el, start: 'top 86%', once: true } }),
      })
    }, el)

    return () => ctx.revert()
  }, [text, immediate, delay])

  return (
    <div ref={ref}>
      <Tag className={cn('flex flex-wrap', className)}>
        {text.split(' ').map((word, i) => (
          <span key={`${word}-${i}`} className="overflow-hidden pb-[0.12em] pr-[0.26em]">
            <span data-word className="inline-block will-change-transform">
              {word}
            </span>
          </span>
        ))}
      </Tag>
    </div>
  )
}
