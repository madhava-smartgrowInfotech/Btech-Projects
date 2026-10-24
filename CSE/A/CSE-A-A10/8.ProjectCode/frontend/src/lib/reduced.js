import { useEffect, useState } from 'react'

const Q = '(prefers-reduced-motion: reduce)'

// Follows the OS "reduce motion" setting live.
export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => (typeof window !== 'undefined' && window.matchMedia ? window.matchMedia(Q).matches : false))
  useEffect(() => {
    const mq = window.matchMedia(Q)
    const on = (e) => setReduced(e.matches)
    setReduced(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return reduced
}

// Observes an element's box so charts only render once they have a real width.
export function useSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 })
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const read = () => setSize({ width: Math.floor(el.clientWidth), height: Math.floor(el.clientHeight) })
    read()
    if (typeof ResizeObserver === 'undefined') return undefined
    const ro = new ResizeObserver(read)
    ro.observe(el)
    return () => ro.disconnect()
  }, [ref])
  return size
}
