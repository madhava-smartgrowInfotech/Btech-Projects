/* Forecast line with a 90% band and a capacity line, in the kit's chart style (flat blocks, thick axes, no gradients).
   Lazy-loaded with the pages that use it. data: [{label, mean, lower?, upper?}] */
import { Area, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTheme } from '../../lib/theme'
import { useReducedMotion } from '../../lib/motion'
import { PALETTE } from '../ui/Charts'

function Tip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <div className="chart-tip">
      <div className="t">{label}</div>
      <div>
        Expected: <strong>{row.mean}</strong>
      </div>
      {row.lower !== undefined && (
        <div>
          90% band: {row.lower} to {row.upper}
        </div>
      )}
    </div>
  )
}

export default function ForecastBand({ data, capacity, height = 240, name = 'Expected', capacityLabel = 'capacity' }) {
  const { theme } = useTheme()
  const reduced = useReducedMotion()
  const fg = theme === 'dark' ? PALETTE.paper : PALETTE.ink
  const hasBand = data.some((d) => d.lower !== undefined)
  // Stacked areas: a transparent base at the lower bound, then the band height on top.
  const rows = data.map((d) => ({
    ...d,
    base: d.lower ?? d.mean,
    span: d.lower !== undefined ? Math.max(0, d.upper - d.lower) : 0,
  }))
  const tick = { fill: fg, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fontWeight: 600 }

  return (
    <div className="chart-box" style={{ height }} role="img" aria-label={`${name} forecast${capacity != null ? `, ${capacityLabel} ${capacity}` : ''}`}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={{ top: 12, right: 12, left: -8, bottom: 4 }}>
          <CartesianGrid vertical={false} stroke="transparent" />
          <XAxis dataKey="label" stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} interval="preserveStartEnd" minTickGap={18} />
          <YAxis stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} allowDecimals={false} width={40} />
          <Tooltip content={<Tip />} cursor={{ stroke: fg, strokeWidth: 2 }} />
          {hasBand && <Area type="linear" dataKey="base" stackId="band" stroke="none" fill="transparent" isAnimationActive={false} legendType="none" />}
          {hasBand && (
            <Area type="linear" dataKey="span" name="90% band" stackId="band" stroke={PALETTE.ink} strokeWidth={2} fill={PALETTE.sky} fillOpacity={1} isAnimationActive={!reduced} />
          )}
          <Line
            type="linear"
            dataKey="mean"
            name={name}
            stroke={fg}
            strokeWidth={3}
            dot={{ r: 4, fill: PALETTE.lime, stroke: fg, strokeWidth: 2 }}
            activeDot={{ r: 6, fill: PALETTE.lime, stroke: fg, strokeWidth: 2 }}
            isAnimationActive={!reduced}
          />
          {capacity != null && (
            <ReferenceLine
              y={capacity}
              stroke={PALETTE.coral}
              strokeWidth={3}
              strokeDasharray="8 6"
              label={{ value: `${capacityLabel} ${capacity}`, position: 'insideTopRight', fill: fg, fontSize: 11, fontWeight: 600 }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
