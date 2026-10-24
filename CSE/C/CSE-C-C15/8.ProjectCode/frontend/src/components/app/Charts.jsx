import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, Tooltip, XAxis, YAxis } from 'recharts'
import { SEVERITIES, bytes, clock, fmt, sevVar } from '../../format'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../ui/charts'

const M = { top: 8, right: 8, bottom: 0, left: 0 }

// Packet rate per monitoring window; attack windows are drawn as red markers.
export function RateChart({ rows, height = 240 }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  return (
    <>
      <ChartFrame height={height} label="Packet rate per monitoring window">
        {({ width, height: h }) => (
          <AreaChart width={width} height={h} data={rows} margin={M}>
            <defs>
              <linearGradient id="rateFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={tokens.ok} stopOpacity={0.3} />
                <stop offset="100%" stopColor={tokens.ok} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid {...grid} vertical={false} />
            <XAxis dataKey="t" {...axis} tickFormatter={clock} minTickGap={36} />
            <YAxis {...axis} width={46} tickFormatter={(v) => fmt(v)} />
            <Tooltip content={<MonoTooltip labelFormat={(l) => clock(l)} valueFormat={(v) => `${fmt(v)} pkt/s`} />} />
            <Area type="monotone" dataKey="rate" name="Packet rate" stroke={tokens.ok} strokeWidth={1.5} fill="url(#rateFill)" isAnimationActive={animate}
              dot={(p) => (p.payload.attack
                ? <circle key={p.index} cx={p.cx} cy={p.cy} r={3.5} fill={tokens.alert} stroke={tokens.panel} />
                : <g key={p.index} />)} />
          </AreaChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'Packet rate', color: tokens.ok, line: true }, { label: 'Attack window', color: tokens.alert }]} />
    </>
  )
}

export function ConfidenceChart({ rows, height = 220 }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  return (
    <>
      <ChartFrame height={height} label="Model confidence and distributed risk per window">
        {({ width, height: h }) => (
          <LineChart width={width} height={h} data={rows} margin={M}>
            <CartesianGrid {...grid} vertical={false} />
            <XAxis dataKey="t" {...axis} tickFormatter={clock} minTickGap={36} />
            <YAxis {...axis} width={40} domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} />
            <Tooltip content={<MonoTooltip labelFormat={(l) => clock(l)} valueFormat={(v) => v.toFixed(2)} />} />
            <Line type="monotone" dataKey="confidence" name="Confidence" stroke={tokens.cyan} strokeWidth={1.5} dot={false} isAnimationActive={animate} />
            <Line type="monotone" dataKey="risk" name="Distributed risk" stroke={tokens.hot} strokeWidth={1.5} dot={false} isAnimationActive={animate} />
          </LineChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'Model confidence', color: tokens.cyan, line: true }, { label: 'Distributed risk', color: tokens.hot, line: true }]} />
    </>
  )
}

export function PredictionDonut({ benign, attack, height = 220 }) {
  const { tokens, animate } = useChartTheme()
  const data = [{ name: 'Benign', value: benign, fill: tokens.ok }, { name: 'Attack', value: attack, fill: tokens.alert }]
  const total = benign + attack
  return (
    <>
      <ChartFrame height={height} crosshair={false} label={`Benign ${benign}, attack ${attack}`}>
        {({ width, height: h }) => (
          <div className="relative">
            <PieChart width={width} height={h}>
              <Pie data={data} dataKey="value" nameKey="name" innerRadius={h * 0.27} outerRadius={h * 0.4} stroke={tokens.panel} strokeWidth={2} isAnimationActive={animate}>
                {data.map((d) => <Cell key={d.name} fill={d.fill} />)}
              </Pie>
              <Tooltip content={<MonoTooltip valueFormat={(v) => `${v} windows`} />} />
            </PieChart>
            <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
              <div><div className="font-mono text-2xl font-semibold tabular-nums text-fg">{fmt(total)}</div><div className="font-mono text-[10px] uppercase tracking-wider text-dim">windows</div></div>
            </div>
          </div>
        )}
      </ChartFrame>
      <ChartLegend items={data.map((d) => ({ label: `${d.name} ${d.value}`, color: d.fill }))} />
    </>
  )
}

export function SeverityBars({ counts, height = 220 }) {
  const { axis, grid, animate } = useChartTheme()
  const data = SEVERITIES.map((s) => ({ name: s, value: counts[s] || 0 }))
  return (
    <ChartFrame height={height} crosshair={false} label="Detections by severity">
      {({ width, height: h }) => (
        <BarChart width={width} height={h} data={data} margin={M}>
          <CartesianGrid {...grid} vertical={false} />
          <XAxis dataKey="name" {...axis} />
          <YAxis {...axis} width={34} allowDecimals={false} />
          <Tooltip cursor={{ fill: 'transparent' }} content={<MonoTooltip valueFormat={(v) => `${v} windows`} />} />
          <Bar dataKey="value" name="Windows" radius={[2, 2, 0, 0]} isAnimationActive={animate}>
            {data.map((d) => <Cell key={d.name} fill={sevVar(d.name)} />)}
          </Bar>
        </BarChart>
      )}
    </ChartFrame>
  )
}

export function ProtocolBars({ data, height = 200 }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  return (
    <ChartFrame height={height} crosshair={false} label="Packets by protocol in the latest window">
      {({ width, height: h }) => (
        <BarChart width={width} height={h} data={data} margin={M}>
          <CartesianGrid {...grid} vertical={false} />
          <XAxis dataKey="name" {...axis} />
          <YAxis {...axis} width={46} tickFormatter={(v) => fmt(v)} />
          <Tooltip cursor={{ fill: 'transparent' }} content={<MonoTooltip valueFormat={(v) => `${fmt(v)} packets`} />} />
          <Bar dataKey="value" name="Packets" fill={tokens.cyan} radius={[2, 2, 0, 0]} isAnimationActive={animate} />
        </BarChart>
      )}
    </ChartFrame>
  )
}

export function HealthChart({ rows, height = 220 }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  return (
    <>
      <ChartFrame height={height} label="CPU and memory utilisation">
        {({ width, height: h }) => (
          <LineChart width={width} height={h} data={rows} margin={M}>
            <CartesianGrid {...grid} vertical={false} />
            <XAxis dataKey="t" {...axis} tickFormatter={clock} minTickGap={36} />
            <YAxis {...axis} width={40} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
            <Tooltip content={<MonoTooltip labelFormat={(l) => clock(l)} valueFormat={(v) => `${v.toFixed(1)}%`} />} />
            <Line type="monotone" dataKey="cpu" name="CPU" stroke={tokens.ok} strokeWidth={1.5} dot={false} isAnimationActive={animate} />
            <Line type="monotone" dataKey="mem" name="Memory" stroke={tokens.info} strokeWidth={1.5} dot={false} isAnimationActive={animate} />
          </LineChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'CPU %', color: tokens.ok, line: true }, { label: 'Memory %', color: tokens.info, line: true }]} />
    </>
  )
}

// Throughput derived from the difference between consecutive cumulative byte counters.
export function ThroughputChart({ rows, height = 220 }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  return (
    <>
      <ChartFrame height={height} label="Network throughput in and out">
        {({ width, height: h }) => (
          <AreaChart width={width} height={h} data={rows} margin={M}>
            <CartesianGrid {...grid} vertical={false} />
            <XAxis dataKey="t" {...axis} tickFormatter={clock} minTickGap={36} />
            <YAxis {...axis} width={58} tickFormatter={(v) => `${bytes(v)}/s`} />
            <Tooltip content={<MonoTooltip labelFormat={(l) => clock(l)} valueFormat={(v) => `${bytes(v)}/s`} />} />
            <Area type="monotone" dataKey="inRate" name="In" stroke={tokens.cyan} fill={tokens.cyan} fillOpacity={0.12} strokeWidth={1.5} isAnimationActive={animate} />
            <Area type="monotone" dataKey="outRate" name="Out" stroke={tokens.warn} fill={tokens.warn} fillOpacity={0.12} strokeWidth={1.5} isAnimationActive={animate} />
          </AreaChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'Bytes in / s', color: tokens.cyan, line: true }, { label: 'Bytes out / s', color: tokens.warn, line: true }]} />
    </>
  )
}

export function ImportanceBars({ data, height = 320 }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  return (
    <ChartFrame height={height} crosshair={false} label="Feature importance">
      {({ width, height: h }) => (
        <BarChart width={width} height={h} data={data} layout="vertical" margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
          <CartesianGrid {...grid} horizontal={false} />
          <XAxis type="number" {...axis} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
          <YAxis type="category" dataKey="name" {...axis} width={width < 480 ? 96 : 150} />
          <Tooltip cursor={{ fill: 'transparent' }} content={<MonoTooltip valueFormat={(v) => `${(v * 100).toFixed(2)}%`} />} />
          <Bar dataKey="value" name="Importance" fill={tokens.ok} radius={[0, 2, 2, 0]} isAnimationActive={animate} />
        </BarChart>
      )}
    </ChartFrame>
  )
}
