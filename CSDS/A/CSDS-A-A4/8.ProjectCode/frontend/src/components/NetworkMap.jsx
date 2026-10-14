import { useMemo, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { fmtInt } from '../lib/format'
import { PASTEL, useChartTheme } from '../lib/palette'

const W = 600
const H = 640
const PAD = 34

/**
 * Hub network drawn from region coordinates.
 * regions: [{city, lat, lon}] in model order; hubs: [index]; assign: [hubIndex per region] (optional);
 * demand: [number per region] (optional, sizes the circles).
 */
export default function NetworkMap({ regions, hubs = [], assign, demand, label, height }) {
  const t = useChartTheme()
  const reduce = useReducedMotion()
  const [tip, setTip] = useState(null)

  const proj = useMemo(() => {
    const lats = regions.map((r) => r.lat)
    const lons = regions.map((r) => r.lon)
    const [la0, la1, lo0, lo1] = [Math.min(...lats), Math.max(...lats), Math.min(...lons), Math.max(...lons)]
    const k = Math.cos(((la0 + la1) / 2) * (Math.PI / 180))
    const sx = (W - 2 * PAD) / ((lo1 - lo0) * k || 1)
    const sy = (H - 2 * PAD) / (la1 - la0 || 1)
    const s = Math.min(sx, sy)
    const ox = (W - (lo1 - lo0) * k * s) / 2
    const oy = (H - (la1 - la0) * s) / 2
    return regions.map((r) => [ox + (r.lon - lo0) * k * s, oy + (la1 - r.lat) * s])
  }, [regions])

  const hubColor = useMemo(() => Object.fromEntries(hubs.map((h, i) => [h, PASTEL[i % PASTEL.length]])), [hubs])
  const maxD = demand ? Math.max(...demand) : 1
  const radius = (i) => (demand ? 2.5 + Math.sqrt(demand[i] / maxD) * 10 : 4)
  const hubSet = new Set(hubs)

  const show = (e, i) => {
    const box = e.currentTarget.ownerSVGElement.getBoundingClientRect()
    const [x, y] = proj[i]
    setTip({ i, w: box.width, left: (x / W) * box.width, top: (y / H) * box.height })
  }

  return (
    <div className="map-wrap" style={height ? { maxHeight: height } : undefined}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label || `Network map with ${hubs.length} hubs and ${regions.length} regions`}>
        <defs>
          <pattern id="mapgrid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M40 0H0V40" fill="none" stroke={t.dark ? 'rgba(255,255,255,.05)' : 'rgba(31,36,48,.05)'} strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={W} height={H} fill="url(#mapgrid)" />
        {assign &&
          regions.map((_, i) => {
            const h = assign[i]
            if (h == null || h === i) return null
            const [x1, y1] = proj[i]
            const [x2, y2] = proj[h]
            return (
              <motion.line
                key={`l${i}`}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={hubColor[h] || t.muted}
                strokeWidth={1.8}
                strokeLinecap="round"
                initial={reduce ? false : { pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 0.85 }}
                transition={{ duration: 0.8, delay: 0.15 + (i % 30) * 0.012, ease: 'easeOut' }}
              />
            )
          })}
        {regions.map((r, i) =>
          hubSet.has(i) ? null : (
            <motion.circle
              key={`c${i}`}
              cx={proj[i][0]}
              cy={proj[i][1]}
              r={radius(i)}
              fill={assign ? hubColor[assign[i]] || t.muted : t.sky}
              fillOpacity={0.9}
              stroke={t.surface}
              strokeWidth={1.5}
              initial={reduce ? false : { scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 300, damping: 18, delay: (i % 40) * 0.008 }}
              style={{ transformOrigin: `${proj[i][0]}px ${proj[i][1]}px`, cursor: 'pointer' }}
              onPointerEnter={(e) => show(e, i)}
              onPointerLeave={() => setTip(null)}
            />
          ),
        )}
        {hubs.map((h, k) => {
          const [x, y] = proj[h]
          return (
            <motion.g
              key={`h${h}`}
              initial={reduce ? false : { scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 380, damping: 14, delay: 0.5 + k * 0.08 }}
              style={{ transformOrigin: `${x}px ${y}px`, cursor: 'pointer' }}
              onPointerEnter={(e) => show(e, h)}
              onPointerLeave={() => setTip(null)}
            >
              <rect x={x - 11} y={y - 11} width={22} height={22} rx={7} fill={hubColor[h]} stroke={t.text} strokeWidth={2.4} />
              <text x={x} y={y - 18} textAnchor="middle" fontSize="13" fontWeight="700" fill={t.text} style={{ paintOrder: 'stroke', stroke: t.surface, strokeWidth: 4, fontFamily: 'Plus Jakarta Sans, Inter, sans-serif' }}>
                {regions[h].city}
              </text>
            </motion.g>
          )
        })}
      </svg>
      {tip && (
        <div className="map-tip" style={{ left: tip.left > tip.w - 180 ? tip.left - 172 : tip.left + 12, top: tip.top + 12 }}>
          <strong>{regions[tip.i].city}</strong>
          {hubSet.has(tip.i) && <span className="badge lavender" style={{ marginLeft: 6 }}>hub</span>}
          {assign && !hubSet.has(tip.i) && <div className="muted">served by {regions[assign[tip.i]]?.city}</div>}
          {demand && <div className="muted">{fmtInt(demand[tip.i])} orders</div>}
        </div>
      )}
    </div>
  )
}
