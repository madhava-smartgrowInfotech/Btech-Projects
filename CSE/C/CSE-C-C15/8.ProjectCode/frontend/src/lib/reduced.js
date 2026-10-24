import { useEffect, useState } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

export function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia?.(QUERY).matches
}

// Follows the OS "reduce motion" setting live.
export function useReducedMotion() {
  const [reduced, setReduced] = useState(prefersReducedMotion)
  useEffect(() => {
    const mq = window.matchMedia(QUERY)
    const on = (e) => setReduced(e.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return reduced
}

// Width/height of an element (ResizeObserver); charts only render once they have a real width.
export function useSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 })
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const measure = () => setSize({ width: Math.floor(el.clientWidth), height: Math.floor(el.clientHeight) })
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [ref])
  return size
}
