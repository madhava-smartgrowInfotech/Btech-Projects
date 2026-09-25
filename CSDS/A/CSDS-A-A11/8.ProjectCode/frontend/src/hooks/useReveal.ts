import { useLayoutEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

type RevealOptions = {
  selector?: string
  y?: number
  stagger?: number
  duration?: number
  delay?: number
  start?: string
  once?: boolean
  enabled?: boolean
}

/**
 * Scroll-driven reveal. Children matching `selector` (default `[data-reveal]`)
 * fade + rise on a staggered timeline as the container enters the viewport.
 */
export function useReveal<T extends HTMLElement = HTMLDivElement>(options: RevealOptions = {}) {
  const {
    selector = '[data-reveal]',
    y = 26,
    stagger = 0.075,
    duration = 0.95,
    delay = 0,
    start = 'top 82%',
    once = true,
    enabled = true,
  } = options
  const ref = useRef<T | null>(null)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el || !enabled) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const ctx = gsap.context(() => {
      const targets = gsap.utils.toArray<HTMLElement>(selector, el)
      const nodes = targets.length ? targets : [el]
      gsap.set(nodes, { opacity: 0, y })
      gsap.to(nodes, {
        opacity: 1,
        y: 0,
        duration,
        delay,
        stagger,
        ease: 'expo.out',
        scrollTrigger: {
          trigger: el,
          start,
          once,
        },
      })
    }, el)

    return () => ctx.revert()
  }, [selector, y, stagger, duration, delay, start, once, enabled])

  return ref
}

/** Refresh ScrollTrigger once async content has settled into the layout. */
export function refreshScrollTriggers() {
  requestAnimationFrame(() => ScrollTrigger.refresh())
}
