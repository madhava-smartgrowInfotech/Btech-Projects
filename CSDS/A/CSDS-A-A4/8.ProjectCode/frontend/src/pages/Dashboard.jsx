import {
  ArrowRight,
  BarChart3,
  Boxes,
  CalendarRange,
  Database,
  LayoutDashboard,
  MapPinned,
  Package,
  RefreshCcw,
  Target,
  TrendingUp,
} from 'lucide-react'
import { AreaTrend } from '../components/charts'
import { Stagger } from '../components/motion'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, PageSkeleton, ProgressBar, StatCard, Table, Timeline } from '../components/ui'
import { api } from '../lib/api'
import { fmtCompact, fmtINR, fmtInt, fmtPct, fmtSigned, monthLabel, timeAgo } from '../lib/format'
import { useApi } from '../lib/useApi'

export default function Dashboard() {
  const { data, error, loading, reload } = useApi((o) => api.summary(o))

  if (loading) return <PageSkeleton />
  if (error) return <ErrorState title="Could not load the dashboard" error={error} onRetry={reload} />

  const ds = data.dataset
  const months = Object.keys(ds.monthly_total)
  const vols = Object.values(ds.monthly_total)
  const lastDelta = vols.length > 1 ? ((vols.at(-1) - vols.at(-2)) / vols.at(-2)) * 100 : null
  const rf = data.forecaster.random_forest
  const cmp = data.comparison
  const ro = data.rolling
  const maxTop = Math.max(...ds.top_regions.map((r) => r.avg_orders))

  const pipeline = [
    { title: <>Historical data <Badge tone="mint" dot>ready</Badge></>, meta: `data/demand_history.csv · ${ds.regions} regions × ${ds.periods} months`, icon: Database, tone: 'mint' },
    {
      title: <>Random Forest forecaster {data.forecaster.trained ? <Badge tone="mint" dot>trained</Badge> : <Badge tone="peach" dot>not trained</Badge>}</>,
      meta: data.forecaster.trained ? `Trained ${timeAgo(data.forecaster.trained_at)} · ${data.forecaster.trained_at?.slice(0, 16).replace('T', ' ')} UTC` : 'Train it on the Forecast page',
      icon: TrendingUp,
      tone: data.forecaster.trained ? 'lavender' : 'peach',
    },
    {
      title: <>Hub location matheuristic <Badge tone="mint" dot>available</Badge></>,
      meta: data.has_pulp ? 'Exact sub-problems via CBC (PuLP)' : 'Greedy allocation fallback - install pulp',
      icon: Boxes,
      tone: 'peach',
    },
    {
      title: <>Rolling re-optimisation {ro ? <Badge tone="mint" dot>{ro.months} months evaluated</Badge> : <Badge tone="peach" dot>not run</Badge>}</>,
      meta: ro ? `Adaptive ${fmtPct(ro.adaptive_avg.fulfilment_rate)} vs static ${fmtPct(ro.static_avg.fulfilment_rate)} fulfilment` : 'Run it on the Re-optimise page',
      icon: RefreshCcw,
      tone: 'rose',
    },
    {
      title: <>Method comparison {cmp ? <Badge tone="mint" dot>{Object.keys(cmp.methods).length} methods</Badge> : <Badge tone="peach" dot>not run</Badge>}</>,
      meta: cmp ? `Proposed hubs: ${cmp.methods.proposed?.hub_cities.join(', ')}` : 'Run it on the Compare page',
      icon: BarChart3,
      tone: 'sky',
    },
  ]

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Overview"
        icon={LayoutDashboard}
        title="Your logistics network at a glance"
        lead={`Historical orders from ${ds.regions} regions over ${ds.periods} months feed a Random Forest that forecasts next-month demand; the forecast drives a capacitated hub-location model solved by a matheuristic.`}
        actions={
          <Button to="/app/plan" icon={Boxes} size="lg">
            Plan hubs
          </Button>
        }
      />

      <Stagger className="grid-kpi">
        <Stagger.Item>
          <StatCard label="Demand regions" value={ds.regions} icon={MapPinned} tone="lavender" foot="cities + satellite districts" />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="Months of history" value={ds.periods} icon={CalendarRange} tone="sky" foot={`${monthLabel(ds.first_period)} – ${monthLabel(ds.last_period)}`} />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard
            label="Orders in the dataset"
            value={ds.total_orders}
            format={fmtCompact}
            icon={Package}
            tone="mint"
            spark={vols}
            delta={lastDelta != null ? { value: lastDelta, text: fmtSigned(lastDelta, 1), label: 'last month' } : null}
          />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard
            label="Random Forest MAPE"
            value={rf?.mape}
            format={(v) => `${v.toFixed(2)}%`}
            display={rf ? undefined : '–'}
            icon={Target}
            tone="peach"
            foot={rf ? `held-out months · R² ${rf.r2}` : 'forecaster not trained'}
          />
        </Stagger.Item>
      </Stagger>

      <Card title="Monthly order volume across the network" subtitle={`${monthLabel(ds.first_period)} to ${monthLabel(ds.last_period)} · festival peaks in Oct–Nov`}>
        <AreaTrend
          data={months.map((m, i) => ({ x: m, y: vols[i] }))}
          name="Orders"
          valueFormat={fmtInt}
          xFormat={monthLabel}
          yFormat={fmtCompact}
          label="Area chart of monthly order volume"
        />
      </Card>

      <div className="grid-2">
        <Card title="Pipeline status" subtitle="Predict-then-optimise, step by step">
          <Timeline items={pipeline} />
        </Card>
        <Card title="Largest markets" subtitle="Average monthly orders">
          <div className="stack" style={{ '--gap': '16px' }}>
            {ds.top_regions.map((r, i) => (
              <div key={r.region_id}>
                <div className="row between" style={{ marginBottom: 7 }}>
                  <span style={{ fontWeight: 600 }}>
                    <span className="muted num" style={{ marginRight: 8 }}>
                      {i + 1}
                    </span>
                    {r.city}
                  </span>
                  <span className="num" style={{ fontWeight: 600 }}>
                    {fmtInt(r.avg_orders)}
                  </span>
                </div>
                <ProgressBar value={r.avg_orders} max={maxTop} tone={['lavender', 'mint', 'peach', 'sky', 'rose'][i % 5]} label={`${r.city} share of the largest market`} />
              </div>
            ))}
          </div>
          {ro && (
            <div className="card tint-mint" style={{ marginTop: 22, padding: 18 }}>
              <strong style={{ display: 'block' }}>Re-optimising monthly pays off</strong>
              <span className="small" style={{ color: 'var(--text-2)' }}>
                Adaptive plan: {fmtPct(ro.adaptive_avg.fulfilment_rate)} fulfilment vs {fmtPct(ro.static_avg.fulfilment_rate)} for a static plan, at{' '}
                {fmtSigned(((ro.adaptive_avg.total_cost - ro.static_avg.total_cost) / ro.static_avg.total_cost) * 100, 1)} operating cost.
              </span>
            </div>
          )}
        </Card>
      </div>

      <Card
        title="Latest method comparison"
        subtitle={cmp ? `Proposed hubs: ${cmp.methods.proposed?.hub_cities.join(', ')}` : undefined}
        actions={
          <Button to="/app/compare" variant="secondary" size="sm" iconRight={ArrowRight}>
            Details
          </Button>
        }
        hover={false}
      >
        {cmp ? (
          <Table
            caption="Latest method comparison"
            rows={Object.entries(cmp.methods).map(([k, m]) => ({ key: k, ...m }))}
            rowKey={(r) => r.key}
            pageSize={0}
            highlight={(r) => r.key === 'proposed'}
            columns={[
              { key: 'label', label: 'Method', wrap: true },
              { key: 'total_cost', label: 'Operating cost', numeric: true, render: (r) => fmtINR(r.total_cost) },
              {
                key: 'cost_vs_proposed_pct',
                label: 'vs proposed',
                numeric: true,
                render: (r) => <Badge tone={r.cost_vs_proposed_pct > 0.005 ? 'rose' : r.cost_vs_proposed_pct < -0.005 ? 'mint' : 'neutral'}>{fmtSigned(r.cost_vs_proposed_pct)}</Badge>,
              },
              { key: 'avg_delivery_hours', label: 'Avg delivery', numeric: true, render: (r) => `${r.avg_delivery_hours} h` },
              { key: 'fulfilment_rate', label: 'Fulfilment', numeric: true, render: (r) => fmtPct(r.fulfilment_rate) },
              { key: 'reliability_sla', label: 'Reliability', numeric: true, render: (r) => fmtPct(r.reliability_sla) },
            ]}
          />
        ) : (
          <EmptyState icon={BarChart3} title="No comparison yet" message="Run the proposed method against the traditional ones to see how they stack up." action={<Button to="/app/compare">Run a comparison</Button>} />
        )}
      </Card>
    </div>
  )
}
