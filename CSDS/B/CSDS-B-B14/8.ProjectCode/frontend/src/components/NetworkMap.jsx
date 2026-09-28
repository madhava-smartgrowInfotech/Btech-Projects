import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { ZONE_COLORS, pressureColor } from './ui.jsx'

// Leaflet map of the twin: pipes coloured by zone (or flow), nodes by pressure, ranked leak suspects highlighted.
export default function NetworkMap({ nodes, links, suspects = [], activeLeaks = [], onPipeClick, selectedPipe, height = 480, colorBy = 'zone' }) {
  const el = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)
  const fitted = useRef(false)

  useEffect(() => {
    map.current = L.map(el.current, { zoomControl: true, scrollWheelZoom: false })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map.current)
    layer.current = L.layerGroup().addTo(map.current)
    return () => {
      map.current.remove()
      fitted.current = false
    }
  }, [])

  useEffect(() => {
    if (!nodes?.length) return
    const g = layer.current
    g.clearLayers()
    const rank = Object.fromEntries(suspects.map((s, i) => [s.pipe, i + 1]))
    const leakPipes = new Set(activeLeaks.map((e) => e.pipe))
    const maxFlow = Math.max(...links.map((l) => Math.abs(l.flow_lps || 0)), 1)
    links.forEach((l) => {
      const r = rank[l.id]
      const isSel = selectedPipe === l.id
      let color = colorBy === 'flow' ? '#0369a1' : ZONE_COLORS[l.zone] || '#475569'
      let weight = l.type === 'Pipe' ? 2 + ((l.diameter_mm || 150) / 450) * 5 : 4
      if (colorBy === 'flow') weight = 2 + (Math.abs(l.flow_lps || 0) / maxFlow) * 8
      if (r) {
        color = r === 1 ? '#e11d48' : r <= 3 ? '#f97316' : '#facc15'
        weight = r === 1 ? 9 : 7
      }
      if (isSel) {
        color = '#0f172a'
        weight = 8
      }
      const line = L.polyline(l.coords, { color, weight, opacity: r || isSel ? 1 : 0.8, dashArray: l.type === 'Pump' ? '6 4' : null })
      const info = [
        `<b>${l.id}</b> (${l.type}) - ${l.zone}`,
        l.diameter_mm ? `${l.diameter_mm} mm, ${l.length_m} m` : '',
        l.flow_lps != null ? `Flow ${l.flow_lps.toFixed(1)} L/s (08:00)` : '',
        r ? `<b>Leak suspect #${r}</b>` : '',
        leakPipes.has(l.id) ? 'Injected leak (twin)' : '',
      ].filter(Boolean)
      line.bindTooltip(info.join('<br/>'), { sticky: true })
      if (onPipeClick && l.type === 'Pipe') line.on('click', () => onPipeClick(l.id))
      line.addTo(g)
      if (r) {
        const mid = [(l.coords[0][0] + l.coords[1][0]) / 2, (l.coords[0][1] + l.coords[1][1]) / 2]
        L.marker(mid, {
          icon: L.divIcon({
            className: '',
            html: `<div style="background:${color};color:white;border-radius:9999px;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.4)">${r}</div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11],
          }),
        }).addTo(g)
      }
    })
    nodes.forEach((n) => {
      if (n.type === 'Junction') {
        L.circleMarker([n.lat, n.lon], {
          radius: n.sensor ? 6 : 4,
          color: n.sensor ? '#0f172a' : '#ffffff',
          weight: n.sensor ? 2 : 1,
          fillColor: pressureColor(n.pressure),
          fillOpacity: 1,
        })
          .bindTooltip(
            `<b>${n.id}</b> - ${n.zone}${n.sensor ? ' (pressure logger)' : ''}<br/>Elevation ${n.elevation} m<br/>Pressure ${n.pressure ?? '-'} m (08:00)`
          )
          .addTo(g)
      } else {
        const label = n.type === 'Tank' ? 'Tank' : 'Plant'
        L.marker([n.lat, n.lon], {
          icon: L.divIcon({
            className: '',
            html: `<div style="background:#0f172a;color:white;border-radius:6px;padding:2px 6px;font-size:11px;font-weight:700;white-space:nowrap">${label}</div>`,
            iconAnchor: [20, 10],
          }),
        })
          .bindTooltip(`${n.type} ${n.id}${n.pressure != null && n.type === 'Tank' ? `<br/>Level ${n.pressure} m (08:00)` : ''}`)
          .addTo(g)
      }
    })
    if (!fitted.current) {
      map.current.fitBounds(L.latLngBounds(nodes.map((n) => [n.lat, n.lon])).pad(0.12))
      fitted.current = true
    }
  }, [nodes, links, suspects, activeLeaks, selectedPipe, colorBy, onPipeClick])

  return <div ref={el} style={{ height }} className="w-full rounded-xl overflow-hidden border border-slate-200 z-0" />
}

export function MapLegend({ colorBy = 'zone', zones = [] }) {
  const dot = (cls, text) => (
    <span className="flex items-center gap-1.5">
      <span className={`w-2.5 h-2.5 rounded-full inline-block ${cls}`} /> {text}
    </span>
  )
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600 mt-2">
      {colorBy === 'zone' &&
        zones.map((z) => (
          <span key={z.id} className="flex items-center gap-1.5">
            <span className="w-3 h-1.5 rounded inline-block" style={{ background: ZONE_COLORS[z.id] }} /> {z.name}
          </span>
        ))}
      {dot('bg-rose-600', 'below 20 m')}
      {dot('bg-amber-500', '20-28 m')}
      {dot('bg-emerald-500', '28-45 m')}
      {dot('bg-sky-600', 'above 45 m')}
      {dot('border-2 border-slate-900', 'pressure logger')}
    </div>
  )
}
