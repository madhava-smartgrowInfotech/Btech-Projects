import { type ReactNode, useEffect } from 'react'
import Lenis from '@studio-freight/lenis'

export function SmoothScroll({ children }: { children: ReactNode }) {
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.15,
      easing: (t) => 1 - Math.pow(1 - t, 3),
      smoothWheel: true,
    })

    function raf(time: number) {
      lenis.raf(time)
      requestAnimationFrame(raf)
    }
    const raf_id = requestAnimationFrame(raf)

    return () => {
      cancelAnimationFrame(raf_id)
      lenis.destroy()
    }
  }, [])

  return <>{children}</>
}
