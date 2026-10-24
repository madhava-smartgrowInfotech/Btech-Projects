import { useId, useRef } from 'react'
import { Area, AreaChart } from 'recharts'
import { useReducedMotion, useSize } from '../../lib/reduced'
import { useTheme } from '../../lib/theme'

// Measures its box (charts render only with a real width) and draws a crosshair that follows the pointer.
export function ChartFrame({ height = 220, children, crosshair = true, label, className = '' }) {
  const ref = useRef(null)
  const hl = useRef(null)
  const vl = useRef(null)
  const { width } = useSize(ref)
  function move(e) {
    const r = ref.current.getBoundingClientRect()
    hl.current.style.transform = `translateY(${e.clientY - r.top}px)`
    vl.current.style.transform = `translateX(${e.clientX - r.left}px)`
    hl.current.style.opacity = vl.current.style.opacity = '1'
  }
  function leave() {
    hl.current.style.opacity = vl.current.style.opacity = '0'
  }
  return (
    <div ref={ref} className={`relative w-full ${crosshair ? 'cursor-crosshair' : ''} ${className}`} style={{ height }}
      role="figure" aria-label={label} onPointerMove={crosshair ? move : undefined} onPointerLeave={crosshair ? leave : undefined}>
      {width > 0 && children({ width, height })}
      {crosshair && (
        <>
          <div ref={hl} className="pointer-events-none absolute left-0 top-0 w-full border-t border-dashed border-muted/40 opacity-0 transition-opacity" />
          <div ref={vl} className="pointer-events-none absolute left-0 top-0 h-full border-l border-dashed border-muted/40 opacity-0 transition-opacity" />
        </>
      )}
    </div>
  )
}

// Shared axis / grid styling: thin strokes, monospace labels.
export function useChartTheme() {
  const { tokens } = useTheme()
  const reduced = useReducedMotion()
  const tick = { fill: tokens.muted, fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }
  return {
    tokens,
    animate: !reduced,
    axis: { stroke: tokens.lineStrong, tick, tickLine: false, axisLine: { stroke: tokens.lineStrong } },
    grid: { stroke: tokens.grid, strokeDasharray: '0' },
  }
}

export function MonoTooltip({ active, payload, label, labelFormat, valueFormat }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-[6px] border border-line-strong bg-panel px-2.5 py-2 font-mono text-[11px] shadow-xl">
      <div className="mb-1 text-muted">{labelFormat ? labelFormat(label, payload) : label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <i className="inline-block h-2 w-2 rounded-[2px]" style={{ background: p.color || p.stroke || p.fill }} />
          <span className="text-muted">{p.name}</span>
          <span className="ml-auto pl-3 tabular-nums text-fg">{valueFormat ? valueFormat(p.value, p) : p.value}</span>
        </div>
      ))}
    </div>
  )
}

export function ChartLegend({ items }) {
  return (
    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[10px] uppercase tracking-wider text-muted">
      {items.map((i) => (
        <span key={i.label} className="inline-flex items-center gap-1.5">
          {i.line ? <i className="inline-block w-4 border-t-2" style={{ borderColor: i.color, borderStyle: i.dashed ? 'dashed' : 'solid' }} />
            : <i className="inline-block h-2 w-2 rounded-[2px]" style={{ background: i.color }} />}
          {i.label}
        </span>
      ))}
    </div>
  )
}

// Thin phosphor sparkline for KPI tiles.
export function Sparkline({ data, dataKey, tone = 'ok', height = 36, label }) {
  const { tokens, animate } = useChartTheme()
  const gid = `sp${useId().replace(/[^a-zA-Z0-9]/g, '')}`
  const color = tokens[tone] || tokens.ok
  if (!data?.length) return <div style={{ height }} />
  return (
    <ChartFrame height={height} crosshair={false} label={label}>
      {({ width, height: h }) => (
        <AreaChart width={width} height={h} data={data} margin={{ top: 3, right: 1, bottom: 1, left: 1 }}>
          <defs>
            <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.28} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={1.25} fill={`url(#${gid})`} dot={false}
            isAnimationActive={animate} animationDuration={1100} />
        </AreaChart>
      )}
    </ChartFrame>
  )
}
