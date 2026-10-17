import { lazy, Suspense } from 'react'
import { useReducedMotion } from '../../lib/reduced'

const Backdrop = lazy(() => import('./Backdrop'))

// three.js is lazy-loaded; with reduced motion (or while it loads / without WebGL) the static CSS grid is shown.
export default function LazyBackdrop({ intensity = 1, className = '' }) {
  const reduced = useReducedMotion()
  return (
    <div className={`grid-bg fade-mask ${className}`} aria-hidden="true">
      {!reduced && (
        <Suspense fallback={null}>
          <Backdrop intensity={intensity} className="h-full w-full" />
        </Suspense>
      )}
    </div>
  )
}
