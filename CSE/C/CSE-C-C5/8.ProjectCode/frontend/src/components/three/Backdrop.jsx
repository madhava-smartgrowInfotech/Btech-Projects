import { lazy, Suspense, useCallback, useState } from 'react'
import { useReducedMotion } from '../../lib/reduced'

const GridScene = lazy(() => import('./GridScene'))

// three.js wire-grid background. Reduced motion, missing WebGL and the loading moment all fall back to the CSS grid.
export default function Backdrop({ intensity = 1, className = '' }) {
  const reduced = useReducedMotion()
  const [failed, setFailed] = useState(false)
  const fail = useCallback(() => setFailed(true), [])
  const fallback = <div className="grid-bg fade-mask absolute inset-0" aria-hidden="true" />
  return (
    <div className={`pointer-events-none overflow-hidden ${className}`} aria-hidden="true">
      {reduced || failed ? fallback : (
        <Suspense fallback={fallback}>
          <GridScene intensity={intensity} onFail={fail} />
        </Suspense>
      )}
    </div>
  )
}
