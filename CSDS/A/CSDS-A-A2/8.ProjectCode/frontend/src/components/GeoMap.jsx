/* Leaflet map (lazy-loaded): geo-fence centre + radius, tolerance ring, and check-in points. */
import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const square = (fill, size = 16) =>
  L.divIcon({
    className: '',
    html: `<span style="display:block;width:${size}px;height:${size}px;background:${fill};border:3px solid #111;box-shadow:2px 2px 0 #111"></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })

export default function GeoMap({ center, radius, tolerance = 0, points = [], tall, label = 'Geo-fence map' }) {
  const el = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)

  useEffect(() => {
    const m = L.map(el.current, { scrollWheelZoom: false, attributionControl: true })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(m)
    layer.current = L.layerGroup().addTo(m)
    map.current = m
    return () => {
      m.remove()
      map.current = null
    }
  }, [])

  useEffect(() => {
    const m = map.current
    if (!m || !center) return
    const g = layer.current
    g.clearLayers()
    const c = [center.lat, center.lon]
    if (tolerance > 0) {
      L.circle(c, { radius: radius + tolerance, color: '#111', weight: 2, dashArray: '6 6', fill: false }).addTo(g)
    }
    L.circle(c, { radius, color: '#111', weight: 3, fillColor: '#C8FF2E', fillOpacity: 0.35 }).addTo(g)
    L.marker(c, { icon: square('#FF5C39', 18), title: 'Geo-fence centre', keyboard: false }).addTo(g).bindTooltip('Geo-fence centre')
    // circle.getBounds() needs a projected map; derive the box from the radius instead.
    const bounds = L.latLng(c).toBounds(2 * (radius + tolerance))
    points.forEach((p) => {
      L.marker([p.lat, p.lon], { icon: square(p.color || '#7CC6FF', 14), title: p.label, keyboard: false })
        .addTo(g)
        .bindTooltip(p.label || '')
      bounds.extend([p.lat, p.lon])
    })
    m.fitBounds(bounds.pad(0.25), { maxZoom: 18 })
  }, [center?.lat, center?.lon, radius, tolerance, JSON.stringify(points)]) // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={el} className={`map ${tall ? 'tall' : ''}`} role="img" aria-label={label} />
}
