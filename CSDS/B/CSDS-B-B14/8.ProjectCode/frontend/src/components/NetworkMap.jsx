import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { ZONE_COLORS, pressureColor } from '../lib/aqua'

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
      let color = colorBy === 'flow' ? '#1F6AAE' : ZONE_COLORS[l.zone] || '#4E5566'
      let weight = l.type === 'Pipe' ? 2 + ((l.diameter_mm || 150) / 450) * 5 : 4
      if (colorBy === 'flow') weight = 2 + (Math.abs(l.flow_lps || 0) / maxFlow) * 8
      if (r) {
        color = r === 1 ? '#B13A55' : r <= 3 ? '#A9541A' : '#8A6D00'
        weight = r === 1 ? 9 : 7
      }
      if (isSel) {
        color = '#14171F'
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
          color: n.sensor ? '#14171F' : '#ffffff',
          weight: n.sensor ? 2 : 1,
          fillColor: pressureColor(n.pressure),
          fillOpacity: 1,
        })
          .bindTooltip(
            `<b>${n.id}</b> - ${n.zone}${n.sensor ? ' (pressure logger)' : ''}<br/>Elevation ${n.elevation} m<br/>Pressure ${n.pressure ?? '-'} m (08:00)`,
          )
          .addTo(g)
      } else {
        const label = n.type === 'Tank' ? 'Tank' : 'Plant'
        L.marker([n.lat, n.lon], {
          icon: L.divIcon({
            className: '',
            html: `<div style="background:#14171F;color:white;border-radius:6px;padding:2px 6px;font-size:11px;font-weight:700;white-space:nowrap">${label}</div>`,
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

  return (
    <div
      ref={el}
      role="region"
      aria-label="Water network map"
      style={{ height, position: 'relative', zIndex: 0, borderRadius: 'var(--r)', overflow: 'hidden', border: '1px solid var(--border)' }}
    />
  )
}

export function MapLegend({ colorBy = 'zone', zones = [] }) {
  return (
    <div className="legend map-legend" style={{ marginTop: 12 }} aria-label="Map legend">
      {colorBy === 'zone' &&
        zones.map((z) => (
          <span key={z.id}>
            <i style={{ background: ZONE_COLORS[z.id] }} />
            {z.name}
          </span>
        ))}
      <span>
        <i style={{ background: '#B13A55' }} />
        below 20 m
      </span>
      <span>
        <i style={{ background: '#B7791F' }} />
        20–28 m
      </span>
      <span>
        <i style={{ background: '#1C7A50' }} />
        28–45 m
      </span>
      <span>
        <i style={{ background: '#1F6AAE' }} />
        above 45 m
      </span>
      <span>
        <i style={{ background: 'var(--surface)', border: '2px solid #14171F' }} />
        pressure logger
      </span>
    </div>
  )
}
