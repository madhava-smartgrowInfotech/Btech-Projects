import { LocateFixed } from 'lucide-react'
import { useEffect, useState } from 'react'
import { CircleMarker, MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet'

export const CITY_CENTER = [12.9716, 77.5946] // sample city: Bengaluru
const TILES = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const ATTRIBUTION = '&copy; OpenStreetMap contributors'

export function BaseTiles() {
  return <TileLayer url={TILES} attribution={ATTRIBUTION} />
}

function ClickHandler({ onPick }) {
  useMapEvents({ click: (e) => onPick({ lat: e.latlng.lat, lng: e.latlng.lng }) })
  return null
}

function FlyTo({ point }) {
  const map = useMap()
  useEffect(() => {
    if (point) map.flyTo([point.lat, point.lng], Math.max(map.getZoom(), 15), { duration: 0.5 })
  }, [point, map])
  return null
}

export default function MapPicker({ value, onChange }) {
  const [locating, setLocating] = useState(false)
  const [geoError, setGeoError] = useState('')
  const [flyTarget, setFlyTarget] = useState(null)

  function locate() {
    if (!navigator.geolocation) return setGeoError('Location is not available in this browser - tap the map instead.')
    setLocating(true)
    setGeoError('')
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const pt = { lat: p.coords.latitude, lng: p.coords.longitude }
        onChange(pt)
        setFlyTarget(pt)
        setLocating(false)
      },
      () => {
        setGeoError('Could not get your location - tap the map instead.')
        setLocating(false)
      },
      { timeout: 10000 },
    )
  }

  return (
    <div>
      <div className="h-72 overflow-hidden rounded-lg border border-slate-300">
        <MapContainer center={CITY_CENTER} zoom={12} className="h-full w-full" scrollWheelZoom>
          <BaseTiles />
          <ClickHandler onPick={onChange} />
          <FlyTo point={flyTarget} />
          {value && <CircleMarker center={[value.lat, value.lng]} radius={9} pathOptions={{ color: '#fff', weight: 2, fillColor: '#d03b3b', fillOpacity: 1 }} />}
        </MapContainer>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-600">
        <button type="button" className="btn-secondary px-2.5 py-1 text-xs" onClick={locate} disabled={locating}>
          <LocateFixed className="h-3.5 w-3.5" /> {locating ? 'Locating...' : 'Use my location'}
        </button>
        {value ? (
          <span>
            Pinned at {value.lat.toFixed(5)}, {value.lng.toFixed(5)}
          </span>
        ) : (
          <span>Tap the map to pin where the problem is.</span>
        )}
        {geoError && <span className="text-red-700">{geoError}</span>}
      </div>
    </div>
  )
}
