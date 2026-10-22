import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ReferenceLine, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from 'recharts'
import { Tooltip as RTooltip } from 'recharts'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../ui/charts'

// Vertical or horizontal bars. `series` = [{ key, label, color }]; `colorBy(row)` tints single-series bars.
export function Bars({ data, xKey, series, layout = 'vertical', height = 260, valueFormat = (v) => v, domain, colorBy, label, legend = true, refLine, xWidth = 96 }) {
  const { axis, grid, animate, tokens } = useChartTheme()
  const horizontal = layout === 'horizontal' // horizontal bars: categories on the Y axis
  return (
    <div>
      <ChartFrame height={height} label={label} crosshair={false}>
        {({ width, height: h }) => (
          <BarChart width={width} height={h} data={data} layout={horizontal ? 'vertical' : 'horizontal'}
            margin={{ top: 8, right: 16, bottom: 4, left: horizontal ? 4 : -8 }} barCategoryGap="22%">
            <CartesianGrid {...grid} horizontal={!horizontal} vertical={horizontal} />
            {horizontal ? (
              <>
                <XAxis type="number" {...axis} domain={domain || [0, 'auto']} tickFormatter={valueFormat} />
                <YAxis type="category" dataKey={xKey} {...axis} width={xWidth} interval={0} />
              </>
            ) : (
              <>
                <XAxis dataKey={xKey} {...axis} interval={0} />
                <YAxis {...axis} domain={domain || [0, 'auto']} tickFormatter={valueFormat} width={44} />
              </>
            )}
            <RTooltip cursor={{ fill: tokens.line }} content={<MonoTooltip valueFormat={valueFormat} />} />
            {refLine !== undefined && (horizontal
              ? <ReferenceLine x={refLine} stroke={tokens.muted} strokeDasharray="4 4" />
              : <ReferenceLine y={refLine} stroke={tokens.muted} strokeDasharray="4 4" />)}
            {series.map((s) => (
              <Bar key={s.key} dataKey={s.key} name={s.label} fill={s.color || tokens.ok} radius={[2, 2, 0, 0]} isAnimationActive={animate} animationDuration={900}>
                {colorBy && series.length === 1 && data.map((row, i) => <Cell key={i} fill={colorBy(row)} />)}
              </Bar>
            ))}
          </BarChart>
        )}
      </ChartFrame>
      {legend && series.length > 1 && <ChartLegend items={series.map((s) => ({ label: s.label, color: s.color }))} />}
    </div>
  )
}

// Ring chart with a centre readout.
export function Donut({ data, height = 220, label, center }) {
  const { animate, tokens } = useChartTheme()
  return (
    <div>
      <ChartFrame height={height} label={label} crosshair={false}>
        {({ width, height: h }) => (
          <div className="relative" style={{ width, height: h }}>
            <PieChart width={width} height={h}>
              <Pie data={data} dataKey="value" nameKey="name" innerRadius="62%" outerRadius="88%" paddingAngle={2} stroke={tokens.panel}
                startAngle={90} endAngle={-270} isAnimationActive={animate} animationDuration={900}>
                {data.map((d) => <Cell key={d.name} fill={d.color} />)}
              </Pie>
              <RTooltip content={<MonoTooltip />} />
            </PieChart>
            {center && <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">{center}</div>}
          </div>
        )}
      </ChartFrame>
      <ChartLegend items={data.map((d) => ({ label: `${d.name} · ${d.value.toLocaleString('en-US')}`, color: d.color }))} />
    </div>
  )
}

// Precision (x) vs recall (y) of every model.
export function PrecisionRecall({ points, height = 260, label, best }) {
  const { axis, grid, animate, tokens } = useChartTheme()
  return (
    <ChartFrame height={height} label={label} crosshair={false}>
      {({ width, height: h }) => (
        <ScatterChart width={width} height={h} margin={{ top: 12, right: 24, bottom: 20, left: 12 }}>
          <CartesianGrid {...grid} />
          <XAxis type="number" dataKey="precision" name="Precision" {...axis} domain={[0.4, 0.85]} tickFormatter={(v) => v.toFixed(2)}
            label={{ value: 'precision', position: 'insideBottom', offset: -10, fill: tokens.muted, fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} />
          <YAxis type="number" dataKey="recall" name="Recall" {...axis} domain={[0.4, 0.85]} tickFormatter={(v) => v.toFixed(2)} width={52}
            label={{ value: 'recall', angle: -90, position: 'insideLeft', offset: -2, fill: tokens.muted, fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} />
          <ZAxis range={[110, 110]} />
          <RTooltip cursor={{ strokeDasharray: '3 3', stroke: tokens.muted }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const p = payload[0].payload
              return (
                <div className="rounded-[6px] border border-line-strong bg-panel px-2.5 py-2 font-mono text-[11px] shadow-xl">
                  <div className="mb-1 text-fg">{p.name}</div>
                  <div className="text-muted">precision {p.precision.toFixed(3)}</div>
                  <div className="text-muted">recall {p.recall.toFixed(3)}</div>
                </div>
              )
            }} />
          <Scatter data={points} isAnimationActive={animate}>
            {points.map((p) => <Cell key={p.name} fill={p.name === best ? tokens.ok : tokens.info} stroke={tokens.panel} />)}
          </Scatter>
        </ScatterChart>
      )}
    </ChartFrame>
  )
}

// 2x2 confusion matrix as a heat grid. matrix = [[TN, FP], [FN, TP]]; labels: failure=0, success=1.
export function ConfusionMatrix({ matrix, decimals = 0 }) {
  const total = matrix.flat().reduce((a, b) => a + b, 0) || 1
  const cell = (v, good, r, c) => {
    const share = v / total
    const tone = good ? 'var(--ok)' : 'var(--alert)'
    return (
      <div key={`${r}${c}`} className="relative grid min-h-[84px] place-items-center rounded-[4px] border border-line text-center"
        style={{ background: `color-mix(in oklab, ${tone} ${Math.round(12 + share * 120)}%, transparent)` }}>
        <div>
          <div className="font-mono text-xl font-semibold tabular-nums text-fg">{v.toFixed(decimals)}</div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted">{(share * 100).toFixed(1)}%</div>
        </div>
      </div>
    )
  }
  const head = 'font-mono text-[10px] uppercase tracking-[0.12em] text-dim'
  return (
    <div role="table" aria-label="Confusion matrix" className="grid grid-cols-[auto_1fr_1fr] gap-1.5">
      <div />
      <div className={`${head} text-center`}>pred. failure</div>
      <div className={`${head} text-center`}>pred. success</div>
      <div className={`${head} flex items-center`}>actual failure</div>
      {cell(matrix[0][0], true, 0, 0)}
      {cell(matrix[0][1], false, 0, 1)}
      <div className={`${head} flex items-center`}>actual success</div>
      {cell(matrix[1][0], false, 1, 0)}
      {cell(matrix[1][1], true, 1, 1)}
    </div>
  )
}
