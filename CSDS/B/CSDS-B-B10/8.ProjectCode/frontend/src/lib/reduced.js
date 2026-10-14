import { useEffect, useLayoutEffect, useState } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

// True when the OS asks for less motion. Motion components collapse to plain fades when this is true.
export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => !!window.matchMedia?.(QUERY).matches)
  useEffect(() => {
    const mq = window.matchMedia?.(QUERY)
    if (!mq) return
    const on = () => setReduced(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return reduced
}

// Width/height of an element, kept current with ResizeObserver. Charts only render with a real width.
export function useSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 })
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setSize({ width: Math.floor(width), height: Math.floor(height) })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [ref])
  return size
}
