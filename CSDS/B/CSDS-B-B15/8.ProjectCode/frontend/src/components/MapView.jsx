import { useEffect, useRef } from 'react'
import L from 'leaflet'

const HYDERABAD = [17.385, 78.4867]

/** Leaflet + OpenStreetMap map. markers: [{id, lat, lon, color, label, popup, radius}] */
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
        color: '#fff',
        weight: 2,
        fillColor: m.color || '#0f766e',
        fillOpacity: 0.9,
      }).addTo(g)
      if (m.label) c.bindTooltip(String(m.label), { permanent: !!m.permanentLabel, direction: 'top' })
      if (m.popup) c.bindPopup(m.popup)
      if (onSelect) c.on('click', () => onSelect(m.id))
      pts.push([m.lat, m.lon])
    })
    if (user) {
      L.circleMarker([user.lat, user.lon], { radius: 7, color: '#1d4ed8', weight: 3, fillColor: '#60a5fa', fillOpacity: 1 })
        .bindTooltip('You', { permanent: true, direction: 'bottom' })
        .addTo(g)
      pts.push([user.lat, user.lon])
    }
    if (pts.length > 1) map.current.fitBounds(pts, { padding: [30, 30], maxZoom: 14 })
    else if (pts.length === 1) map.current.setView(pts[0], 13)
  }, [markers, user, onSelect])

  return <div ref={el} style={{ height }} className="w-full rounded-xl border border-slate-200 z-0" />
}
