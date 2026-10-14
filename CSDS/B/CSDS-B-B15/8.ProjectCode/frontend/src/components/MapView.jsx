import { useEffect, useRef } from 'react'
import L from 'leaflet'

const HYDERABAD = [17.385, 78.4867]

/**
 * Leaflet + OpenStreetMap map, styled with the kit tokens (tiles darken in dark mode via .mq-map in index.css).
 * markers: [{ id, lat, lon, color, label, permanentLabel, popup, radius }]
 */
export default function MapView({ markers = [], user, height = 320, onSelect }) {
  const el = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)

  useEffect(() => {
    map.current = L.map(el.current, { scrollWheelZoom: false }).setView(HYDERABAD, 11)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map.current)
    layer.current = L.layerGroup().addTo(map.current)
    return () => map.current.remove()
  }, [])

  useEffect(() => {
    const g = layer.current
    g.clearLayers()
    const pts = []
    markers.forEach((m) => {
      const c = L.circleMarker([m.lat, m.lon], {
        radius: m.radius || 9,
        color: '#0d0d0f',
        weight: 1.5,
        fillColor: m.color || '#4ade80',
        fillOpacity: 0.9,
      }).addTo(g)
      if (m.label) c.bindTooltip(String(m.label), { permanent: !!m.permanentLabel, direction: 'top', className: 'mq-tip' })
      if (m.popup) c.bindPopup(m.popup)
      if (onSelect) c.on('click', () => onSelect(m.id))
      pts.push([m.lat, m.lon])
    })
    if (user) {
      L.circleMarker([user.lat, user.lon], { radius: 7, color: '#0d0d0f', weight: 2, fillColor: '#67e8f9', fillOpacity: 1 })
        .bindTooltip('You', { permanent: true, direction: 'bottom', className: 'mq-tip' })
        .addTo(g)
      pts.push([user.lat, user.lon])
    }
    if (pts.length > 1) map.current.fitBounds(pts, { padding: [30, 30], maxZoom: 14 })
    else if (pts.length === 1) map.current.setView(pts[0], 13)
  }, [markers, user, onSelect])

  return <div ref={el} style={{ height }} className="mq-map w-full overflow-hidden rounded-[6px] border border-line z-0" />
}
