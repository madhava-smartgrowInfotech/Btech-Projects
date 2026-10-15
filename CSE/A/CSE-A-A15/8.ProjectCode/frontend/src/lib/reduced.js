import { useEffect, useState } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

// Follows the OS setting live, so switching it while the page is open takes effect at once.
export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => !!window.matchMedia?.(QUERY)?.matches)
  useEffect(() => {
    const mq = window.matchMedia?.(QUERY)
    if (!mq) return undefined
    const on = () => setReduced(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return reduced
}

// Width and height of an element, updated by ResizeObserver. Charts need this: they draw nothing at 0 px.
export function useSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 })
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setSize({ width: Math.floor(width), height: Math.floor(height) })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [ref])
  return size
}
