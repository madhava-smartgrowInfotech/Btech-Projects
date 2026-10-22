import { useEffect, useState } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'
export const prefersReduced = () => typeof window !== 'undefined' && window.matchMedia(QUERY).matches

export function useReducedMotion() {
  const [reduced, setReduced] = useState(prefersReduced)
  useEffect(() => {
    const mq = window.matchMedia(QUERY)
    const on = () => setReduced(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return reduced
}

// Element size via ResizeObserver (charts render only once they have a real width)
export function useSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 })
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => {
      const { width, height } = e.contentRect
      setSize((s) => (s.width === Math.round(width) && s.height === Math.round(height) ? s : { width: Math.round(width), height: Math.round(height) }))
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [ref])
  return size
}
