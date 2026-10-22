import { lazy, Suspense, useCallback, useState } from 'react'
import { useReducedMotion } from '../../lib/reduced'
import { useTheme } from '../../lib/theme'

const WireGrid = lazy(() => import('./WireGrid'))

// three.js wireframe grid, lazy-loaded; a pure CSS grid when reduced motion is set or WebGL is missing.
export default function Backdrop({ intensity = 1, className = '' }) {
  const reduced = useReducedMotion()
  const { tokens, theme } = useTheme()
  const [failed, setFailed] = useState(false)
  const fail = useCallback(() => setFailed(true), [])
  const css = <div className="grid-bg absolute inset-0" />
  return (
    <div className={`pointer-events-none overflow-hidden ${className}`} aria-hidden="true">
      {reduced || failed ? css : (
        <Suspense fallback={css}>
          <WireGrid className="absolute inset-0" color={tokens.ok} opacity={(theme === 'dark' ? 0.2 : 0.26) * intensity} onFail={fail} />
        </Suspense>
      )}
    </div>
  )
}
