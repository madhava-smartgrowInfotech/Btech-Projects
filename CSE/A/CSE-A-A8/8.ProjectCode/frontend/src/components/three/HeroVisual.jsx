import { Component, Suspense, lazy, useMemo } from 'react'
import { hasWebGL, useReducedMotion } from '../../lib/motion'
import { useChartColors } from '../charts/colors'

const HeroScene = lazy(() => import('./HeroScene'))

function Fallback() {
  return <img className="hero-fallback" src="/hero-fallback.svg" alt="" aria-hidden="true" />
}

// If WebGL initialisation throws, show the static image instead of a broken canvas.
class SceneBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  componentDidCatch() {}
  render() {
    return this.state.failed ? <Fallback /> : this.props.children
  }
}

export default function HeroVisual() {
  const reduced = useReducedMotion()
  const webgl = useMemo(() => hasWebGL(), [])
  const colors = useChartColors()
  if (reduced || !webgl) return <Fallback />
  return (
    <SceneBoundary>
      <Suspense fallback={<Fallback />}>
        <HeroScene colors={colors} />
      </Suspense>
    </SceneBoundary>
  )
}
