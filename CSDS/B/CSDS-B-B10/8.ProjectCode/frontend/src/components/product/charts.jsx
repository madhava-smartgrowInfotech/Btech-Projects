import { Area, AreaChart, Bar, BarChart, CartesianGrid, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../ui/charts'

const HIST_TONE = { gray: 'info', r: 'alert', g: 'ok', b: 'cyan' }
const TICKS = [0, 64, 128, 192, 255]

// Pixel-value histogram. `hist` = { gray: [256] } or { r: [256], g: [256], b: [256] } from the API.
export function HistogramChart({ hist, label }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  const keys = Object.keys(hist || {})
  const rows = Array.from({ length: 256 }, (_, v) => {
    const row = { v }
    keys.forEach((k) => { row[k] = hist[k][v] })
    return row
  })
  return (
    <div>
      <ChartFrame height={170} label={label}>
        {({ width, height }) => (
          <AreaChart width={width} height={height} data={rows} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <CartesianGrid {...grid} vertical={false} />
            <XAxis dataKey="v" type="number" domain={[0, 255]} ticks={TICKS} {...axis} />
            <YAxis hide />
            <Tooltip cursor={false} content={<MonoTooltip labelFormat={(v) => `value ${v}`} />} />
            {keys.map((k) => (
              <Area key={k} type="monotone" dataKey={k} name={k} stroke={tokens[HIST_TONE[k]]} fill={tokens[HIST_TONE[k]]}
                fillOpacity={0.12} strokeWidth={1.25} dot={false} isAnimationActive={animate} />
            ))}
          </AreaChart>
        )}
      </ChartFrame>
      <ChartLegend items={keys.map((k) => ({ label: k, color: tokens[HIST_TONE[k]], line: true }))} />
    </div>
  )
}

// Neighbouring-pixel scatter: each dot is (pixel, right or down neighbour). Original = a line, cipher = a cloud.
export function CorrelationScatter({ plain, cipher, label }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  const toRows = (pts) => (pts || []).map(([x, y]) => ({ x, y }))
  return (
    <div>
      <ChartFrame height={260} crosshair={false} label={label}>
        {({ width, height }) => (
          <ScatterChart width={width} height={height} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
            <CartesianGrid {...grid} />
            <XAxis type="number" dataKey="x" domain={[0, 255]} ticks={TICKS} {...axis} />
            <YAxis type="number" dataKey="y" domain={[0, 255]} ticks={TICKS} width={36} {...axis} />
            <Scatter data={toRows(plain)} fill={tokens.cyan} fillOpacity={0.45} isAnimationActive={animate} />
            <Scatter data={toRows(cipher)} fill={tokens.ok} fillOpacity={0.6} isAnimationActive={animate} />
          </ScatterChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'original', color: tokens.cyan }, { label: 'cipher', color: tokens.ok }]} />
    </div>
  )
}

// Encrypt and decrypt time per algorithm. `rows` = [{ algorithm, enc_ms, dec_ms }] from /bench/run.
export function BenchChart({ rows, label }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  return (
    <div>
      <ChartFrame height={260} crosshair={false} label={label}>
        {({ width, height }) => (
          <BarChart width={width} height={height} data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid {...grid} vertical={false} />
            <XAxis dataKey="algorithm" {...axis} />
            <YAxis width={44} {...axis} />
            <Tooltip cursor={false} content={<MonoTooltip valueFormat={(v) => `${Number(v).toFixed(2)} ms`} />} />
            <Bar dataKey="enc_ms" name="encrypt" fill={tokens.ok} isAnimationActive={animate} radius={[2, 2, 0, 0]} />
            <Bar dataKey="dec_ms" name="decrypt" fill={tokens.cyan} isAnimationActive={animate} radius={[2, 2, 0, 0]} />
          </BarChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'encrypt', color: tokens.ok }, { label: 'decrypt', color: tokens.cyan }]} />
    </div>
  )
}
