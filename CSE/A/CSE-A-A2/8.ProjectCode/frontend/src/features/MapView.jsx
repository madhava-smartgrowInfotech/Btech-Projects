import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Hard-edged square pins (no image assets, so nothing 404s and they match the brutal style).
const pin = (bg, label) =>
  L.divIcon({
    className: '',
    html: `<div style="width:26px;height:26px;display:grid;place-items:center;background:${bg};color:#111;border:3px solid #111;box-shadow:3px 3px 0 #111;font:700 13px 'IBM Plex Mono',monospace">${label}</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14],
  })

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])

/**
 * Leaflet map. `hospitals` are plotted as lime "H" pins (the first one highlighted when `accident` is set),
 * `accident` as a coral "!" pin.
 */
export default function MapView({ center, hospitals = [], accident, tall = false }) {
  const el = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)

  useEffect(() => {
    map.current = L.map(el.current, { scrollWheelZoom: false }).setView([center.lat, center.lon], 12)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(map.current)
    layer.current = L.layerGroup().addTo(map.current)
    return () => {
      map.current.remove()
      map.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!map.current) return
    layer.current.clearLayers()
    const pts = []
    hospitals.forEach((h, i) => {
      const mk = L.marker([h.lat, h.lon], { icon: pin(accident && i === 0 ? '#c8ff2e' : '#7cc6ff', 'H'), title: h.name, keyboard: true })
        .bindPopup(`<strong>${esc(h.name)}</strong><br>${esc(h.distance_km)} km - ${esc(h.phone)}`)
        .addTo(layer.current)
      if (accident && i === 0) mk.openPopup()
      pts.push([h.lat, h.lon])
    })
    if (accident) {
      L.marker([accident.lat, accident.lon], { icon: pin('#ff5c39', '!'), title: 'Accident location', zIndexOffset: 500 })
        .bindPopup('<strong>Accident location</strong>')
        .addTo(layer.current)
      pts.push([accident.lat, accident.lon])
    }
    if (pts.length > 1) map.current.fitBounds(pts, { padding: [32, 32], maxZoom: 14 })
    else map.current.setView([center.lat, center.lon], 12)
  }, [hospitals, accident, center.lat, center.lon])

  return <div ref={el} className={`map ${tall ? 'tall' : ''}`} role="region" aria-label="Map of the accident location and nearby hospitals" />
}
