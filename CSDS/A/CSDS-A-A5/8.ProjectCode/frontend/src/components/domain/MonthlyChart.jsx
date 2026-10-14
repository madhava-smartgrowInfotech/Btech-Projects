import { Bar, CartesianGrid, Cell, ComposedChart, Line, Tooltip, XAxis, YAxis } from 'recharts'
import { inr, monthLabel } from '../../format'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../ui/charts'

// Per month: ITC available in GSTR-2B vs ITC claimed in GSTR-3B (bars) and the JEPA deviation (dashed line).
export default function MonthlyChart({ monthly, height = 260 }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  const rows = monthly.map((r) => ({
    month: r.month, avail: r.present ? r.avail || 0 : null, claimed: r.present ? r.claimed || 0 : null,
    deviation: r.deviation ?? null, over: r.present && (r.claimed || 0) > 1.2 * (r.avail || 0) + 50000, present: r.present,
  }))
  return (
    <>
      <ChartFrame height={height} label="Monthly ITC available vs claimed, with JEPA deviation">
        {({ width, height: h }) => (
          <ComposedChart width={width} height={h} data={rows} margin={{ top: 8, right: 4, bottom: 0, left: 4 }} barGap={2}>
            <CartesianGrid {...grid} vertical={false} />
            <XAxis dataKey="month" tickFormatter={monthLabel} {...axis} interval="preserveStartEnd" minTickGap={8} />
            <YAxis yAxisId="v" tickFormatter={inr} {...axis} width={68} />
            <YAxis yAxisId="d" orientation="right" {...axis} width={34} tickFormatter={(v) => `${v}x`} />
            <Tooltip cursor={false} isAnimationActive={false}
              content={<MonoTooltip labelFormat={(m, p) => `${monthLabel(m)}${p?.[0]?.payload?.present === false ? ' · no return' : ''}`}
                valueFormat={(v, p) => (p.dataKey === 'deviation' ? `${Number(v).toFixed(2)}x` : inr(v))} />} />
            <Bar yAxisId="v" dataKey="avail" name="GSTR-2B available" fill={tokens.dim} radius={[2, 2, 0, 0]} isAnimationActive={animate} maxBarSize={18} />
            <Bar yAxisId="v" dataKey="claimed" name="GSTR-3B claimed" radius={[2, 2, 0, 0]} isAnimationActive={animate} maxBarSize={18}>
              {rows.map((r) => <Cell key={r.month} fill={r.over ? tokens.alert : tokens.ok} />)}
            </Bar>
            <Line yAxisId="d" dataKey="deviation" name="JEPA deviation" stroke={tokens.info} strokeWidth={1.4} strokeDasharray="4 3"
              dot={{ r: 2, fill: tokens.info, strokeWidth: 0 }} connectNulls isAnimationActive={animate} />
          </ComposedChart>
        )}
      </ChartFrame>
      <ChartLegend items={[
        { label: 'ITC available (2B)', color: 'var(--dim)' }, { label: 'ITC claimed (3B)', color: 'var(--ok)' },
        { label: 'claimed well above 2B', color: 'var(--alert)' }, { label: 'JEPA deviation (x typical)', color: 'var(--info)', line: true, dashed: true },
      ]} />
    </>
  )
}
