/* Recharts wrappers in the Neo Brutal style: flat colour blocks, thick axes, accent fills,
   no gradients, no soft shadows. Lazy-loaded with the pages that use them. */
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTheme } from '../../lib/theme'
import { useReducedMotion } from '../../lib/motion'

export const PALETTE = { lime: '#C8FF2E', coral: '#FF5C39', sky: '#7CC6FF', amber: '#FFD23F', ink: '#111111', paper: '#FAF7F0' }

function useChartTheme() {
  const { theme } = useTheme()
  const reduced = useReducedMotion()
  const fg = theme === 'dark' ? PALETTE.paper : PALETTE.ink
  const narrow = typeof window !== 'undefined' && window.innerWidth < 640
  return { fg, grid: theme === 'dark' ? '#3a3a3a' : '#d9d3c4', animate: !reduced, narrow }
}

function BrutalTip({ active, payload, label, labelKey }) {
  if (!active || !payload?.length) return null
  const title = labelKey ? payload[0]?.payload?.[labelKey] : label
  return (
    <div className="chart-tip">
      <div className="t">{title}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="row" style={{ '--gap': '6px' }}>
          <i style={{ width: 10, height: 10, background: p.color || p.fill, border: '2px solid currentColor', display: 'inline-block' }} />
          {p.name}: <strong>{p.value}</strong>
        </div>
      ))}
    </div>
  )
}

function axes(fg, xKey, { angle } = {}) {
  const tick = { fill: fg, fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fontWeight: 600 }
  return [
    <CartesianGrid key="g" stroke="transparent" vertical={false} />,
    <XAxis
      key="x"
      dataKey={xKey}
      stroke={fg}
      strokeWidth={3}
      tick={tick}
      tickLine={{ stroke: fg, strokeWidth: 2 }}
      interval={0}
      angle={angle}
      textAnchor={angle ? 'end' : 'middle'}
      height={angle ? 60 : 30}
    />,
    <YAxis key="y" stroke={fg} strokeWidth={3} tick={tick} tickLine={{ stroke: fg, strokeWidth: 2 }} allowDecimals={false} width={36} />,
  ]
}

/** Single-series bar chart. data: [{[xKey], [yKey]}] */
export function BarBlocks({ data, xKey, yKey, name, color = PALETTE.lime, colorFn, height = 280, labelKey }) {
  const { fg, animate, narrow } = useChartTheme()
  return (
    <div className="chart-box" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 12, right: 8, left: -8, bottom: 4 }} barCategoryGap="22%">
          {axes(fg, xKey, { angle: data.length > 6 || (narrow && data.length > 3) ? -35 : 0 })}
          <Tooltip content={<BrutalTip labelKey={labelKey} />} cursor={{ fill: fg, fillOpacity: 0.08 }} />
          <Bar dataKey={yKey} name={name} fill={color} stroke={PALETTE.ink} strokeWidth={3} isAnimationActive={animate} animationDuration={700}>
            {colorFn && data.map((d, i) => <Cell key={i} fill={colorFn(d)} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Stacked bars. series: [{key, name, color}] */
export function StackedBlocks({ data, xKey, series, height = 280 }) {
  const { fg, animate, narrow } = useChartTheme()
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="chart-box" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 12, right: 8, left: -8, bottom: 4 }} barCategoryGap="22%">
            {axes(fg, xKey, { angle: narrow && data.length > 3 ? -35 : 0 })}
            <Tooltip content={<BrutalTip />} cursor={{ fill: fg, fillOpacity: 0.08 }} />
            {series.map((s) => (
              <Bar key={s.key} dataKey={s.key} name={s.name} stackId="a" fill={s.color} stroke={PALETTE.ink} strokeWidth={3} isAnimationActive={animate} animationDuration={700} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="legend" aria-hidden="true">
        {series.map((s) => (
          <span key={s.key}>
            <i style={{ background: s.color }} />
            {s.name}
          </span>
        ))}
      </div>
    </div>
  )
}
