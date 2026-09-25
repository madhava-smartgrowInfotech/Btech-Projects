import { useEffect, useRef } from 'react'
import Lenis from 'lenis'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

let lenisInstance: Lenis | null = null

export function getLenis() {
  return lenisInstance
}

/**
 * Site-wide inertial scrolling, driven by the GSAP ticker so ScrollTrigger
 * timelines stay perfectly in sync with the smoothed scroll position.
 */
export function useSmoothScroll() {
  const rafRef = useRef<((time: number) => void) | null>(null)

  useEffect(() => {
    const prefersReduced =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReduced) return

    const lenis = new Lenis({
      duration: 1.1,
      easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      wheelMultiplier: 0.95,
      touchMultiplier: 1.4,
      lerp: 0.1,
    })
    lenisInstance = lenis

    const onScroll = () => ScrollTrigger.update()
    lenis.on('scroll', onScroll)

    const tick = (time: number) => lenis.raf(time * 1000)
    rafRef.current = tick
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)

    return () => {
      if (rafRef.current) gsap.ticker.remove(rafRef.current)
      lenis.off('scroll', onScroll)
      lenis.destroy()
      lenisInstance = null
    }
  }, [])
}

/** Jump to top on route change without fighting the smooth scroller. */
export function scrollToTop(immediate = true) {
  const lenis = getLenis()
  if (lenis) lenis.scrollTo(0, { immediate })
  else window.scrollTo({ top: 0, behavior: immediate ? 'auto' : 'smooth' })
}
