import { lazy, Suspense, useState } from 'react'
import { CalendarRange, Percent, TrendingUp, Waves } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { fmtNum, fmtSigned, monthLabel } from '../lib/format'
import { Badge, Card, EmptyState, PageHeader, Skeleton, StatCard, Table, Tabs } from '../components/ui'
import { Stagger } from '../components/motion'
import { ChartLegend } from '../components/charts'
import Async from '../components/Async'
import { Disclaimer } from '../components/Common'

const ForecastChart = lazy(() => import('../components/charts/ForecastChart'))

const RANGES = [
  { id: 'all', label: 'Full history', since: undefined },
  { id: '5y', label: 'Last 5 years', since: 2021 },
  { id: '2y', label: 'Last 2 years', since: 2024 },
]

export default function Forecast() {
  const state = useAsync(api.forecast)
  const [range, setRange] = useState('all')
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Forecast"
        icon={TrendingUp}
        title="Economic forecast"
        lead="A Holt-Winters projection of the Household Financial Conditions Index with a 95% interval. It extrapolates past patterns and cannot predict personal outcomes."
      />
      <Async state={state} title="Could not load the forecast">
        {(f) =>
          !f.available ? (
            <EmptyState icon={TrendingUp} tone="peach" title="Forecast data is unavailable" message={f.interpretation} />
          ) : (
            <>
              <Stagger className="grid-kpi">
                <Stagger.Item><StatCard label="Horizon" value={f.horizon_months} format={(v) => `${Math.round(v)} months`} icon={CalendarRange} tone="lavender" foot={`${monthLabel(f.forecast[0].date)} – ${monthLabel(f.forecast[f.forecast.length - 1].date)}`} /></Stagger.Item>
                <Stagger.Item><StatCard label="Trend" display={f.trend_direction[0].toUpperCase() + f.trend_direction.slice(1)} icon={TrendingUp} tone="mint" foot="Direction of the index" /></Stagger.Item>
                <Stagger.Item><StatCard label="Projected change" display={fmtSigned(f.forecast_pct_change, 2)} icon={Percent} tone="sky" foot="Last observed → end of horizon" /></Stagger.Item>
                <Stagger.Item><StatCard label="Residual std" value={f.residual_std} format={(v) => v.toFixed(3)} icon={Waves} tone="peach" foot="Interval = ±1.96 × this" /></Stagger.Item>
              </Stagger>

              <Card hover={false} title="Index history and forecast" subtitle={f.method} actions={<Tabs tabs={RANGES} value={range} onChange={setRange} label="History range" name="forecast-range" />}>
                <ChartLegend items={[{ label: 'History', color: 'var(--lavender)' }, { label: 'Forecast', color: 'var(--mint)' }, { label: '95% interval', color: 'var(--mint)' }]} />
                <Suspense fallback={<Skeleton height={380} radius={18} style={{ marginTop: 12 }} />}>
                  <ForecastChart history={f.history} forecast={f.forecast} height={380} sinceYear={RANGES.find((r) => r.id === range).since} />
                </Suspense>
              </Card>

              <div className="grid-2">
                <Card hover={false} tint="sky" title="Interpretation" actions={<Badge tone="mint">Trend: {f.trend_direction}</Badge>}>
                  <div className="stack" style={{ '--gap': '12px' }}>
                    <p>{f.interpretation}</p>
                    <p className="small muted">Shaded band: approximate 95% interval (±1.96 × residual std of {f.residual_std}). Statistical extrapolation of past patterns - not a guarantee.</p>
                    {f.source_note && <p className="small muted">Data: {f.source_note}</p>}
                  </div>
                </Card>
                <Card hover={false} title="Forecast values">
                  <Table
                    caption="Monthly forecast with 95% interval"
                    rows={f.forecast}
                    rowKey={(r) => r.date}
                    pageSize={6}
                    columns={[
                      { key: 'date', label: 'Month', render: (r) => monthLabel(r.date, true) },
                      { key: 'value', label: 'Forecast', numeric: true, render: (r) => fmtNum(r.value, 2) },
                      { key: 'lower', label: 'Lower', numeric: true, render: (r) => fmtNum(r.lower, 2) },
                      { key: 'upper', label: 'Upper', numeric: true, render: (r) => fmtNum(r.upper, 2) },
                    ]}
                    cardTitle={(r) => monthLabel(r.date, true)}
                  />
                </Card>
              </div>
              <Disclaimer />
            </>
          )
        }
      </Async>
    </div>
  )
}
