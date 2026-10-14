import { Component, lazy, Suspense } from 'react'
import { Skeleton } from './ui'

const GeoMap = lazy(() => import('./GeoMap'))

class MapBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    if (this.state.failed) {
      const { center, radius } = this.props
      return (
        <div className="state">
          <h3>Map unavailable</h3>
          <p>
            The map could not load. Centre {center?.lat?.toFixed(5)}, {center?.lon?.toFixed(5)} · radius {Math.round(radius)} m.
          </p>
        </div>
      )
    }
    return this.props.children
  }
}

/** Leaflet is heavy, so the map is code-split and only loaded where it is shown. */
export function LazyMap(props) {
  return (
    <MapBoundary {...props}>
      <Suspense fallback={<Skeleton height={props.tall ? 420 : 340} />}>
        <GeoMap {...props} />
      </Suspense>
    </MapBoundary>
  )
}
