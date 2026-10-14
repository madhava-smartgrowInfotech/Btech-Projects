import { lazy, Suspense } from 'react'
import { useReducedMotion } from '../../lib/reduced'

// three.js is loaded only when the page mounts it. Reduced motion or a slow load shows the CSS grid instead.
const WireGrid = lazy(() => import('../three/WireGrid'))

export default function Backdrop({ intensity = 0.5, className = '' }) {
  const reduced = useReducedMotion()
  const fallback = <div className="grid-bg h-full w-full opacity-60" />
  return (
    <div aria-hidden="true" className={`pointer-events-none ${className}`}>
      {reduced ? fallback : <Suspense fallback={fallback}><WireGrid intensity={intensity} /></Suspense>}
    </div>
  )
}
