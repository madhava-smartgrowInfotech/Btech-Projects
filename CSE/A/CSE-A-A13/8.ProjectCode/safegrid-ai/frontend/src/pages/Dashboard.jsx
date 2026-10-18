import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Activity, ArrowDownUp, Gauge, Leaf, ShieldAlert, ShieldCheck, Sun, Zap } from 'lucide-react'
import { useSimulation } from '../hooks/useSimulation'
import { NODE_IDS, num, pct, pu } from '../lib/format'
import { PageHeader } from '../components/ui/layout'
import { Badge, Card, CardHeader, StatCard } from '../components/ui/display'
import { EmptyState } from '../components/ui/feedback'
import { MultiLineChart, StackedBars, useChartColors } from '../components/charts'
import { SlideUp, Stagger } from '../components/motion'
import ChartPanel from '../components/safegrid/ChartPanel'
import ActionLane from '../components/safegrid/ActionLane'
import EventFeed from '../components/safegrid/EventFeed'

const kwFmt = (d = 1) => (v) => `${num(v, d)} kW`

export default function Dashboard() {
  const { ready, grid, series, summary, events, agents, safety } = useSimulation()
  const c = useChartColors()
  const t = grid?.totals || {}
  const loading = !ready

  const data = useMemo(
    () =>
      series.map((s) => ({
        time: s.time,
        generation: s.generation_kw,
        load: s.load_kw,
        exchange: s.ext_grid_kw,
        approved: s.counts?.approved ?? 0,
        projected: s.counts?.projected ?? 0,
        rejected: s.counts?.rejected ?? 0,
        ...Object.fromEntries(NODE_IDS.map((n) => [`soc_${n}`, s.nodes?.[n]?.soc])),
      })),
    [series],
  )

  const intervened = agents.map((a) => a.latest).filter(Boolean).find((r) => r.shield.status !== 'approved')
  const anyDecision = agents.some((a) => a.latest)
  const caused = summary?.violations_caused_by_actions ?? 0
  const interventions = summary ? summary.projected + summary.rejected : 0

  return (
    <div className="stack">
      <PageHeader
        title="Dashboard"
        description="Live state of the feeder. Agents propose actions; only what the Symbolic Safety Shield validates is ever applied to the grid."
        actions={
          safety.chain_valid === null ? null : (
            <Badge tone={safety.chain_valid ? 'safe' : 'danger'} dot>
              Audit chain {safety.chain_valid ? 'valid' : 'broken'} · {safety.total || 0} events
            </Badge>
          )
        }
      />

      <Stagger className="stat-grid">
        <StatCard loading={loading} icon={Sun} tone="info" label="Generation" value={t.generation_kw ?? 0} format={kwFmt(1)} />
        <StatCard loading={loading} icon={Zap} tone="warn" label="Load" value={t.load_kw ?? 0} format={kwFmt(1)} />
        <StatCard loading={loading} icon={ArrowDownUp} label="Grid import / export" value={t.ext_grid_kw ?? 0} format={kwFmt(1)} delta="positive = import" />
        <StatCard loading={loading} icon={Gauge} tone="info" label="Voltage range" value={t.min_voltage_pu == null ? '-' : `${pu(t.min_voltage_pu)} - ${pu(t.max_voltage_pu)}`} delta="limits 0.95 - 1.05 pu" />
        <StatCard loading={loading} icon={Activity} tone={t.max_line_loading_pct > 100 ? 'danger' : t.max_line_loading_pct > 80 ? 'warn' : undefined} label="Worst line loading" value={t.max_line_loading_pct ?? 0} format={(v) => `${num(v, 0)}%`} />
        <StatCard loading={loading} icon={ShieldAlert} tone="warn" label="Shield interventions" value={interventions} delta={summary ? `of ${summary.proposals} proposals` : undefined} />
        <StatCard loading={loading} icon={ShieldCheck} tone={caused ? 'danger' : undefined} label="Violations caused by actions" value={caused} delta={caused === 0 && summary?.proposals ? 'all executed actions safe' : 'vs. all-idle grid'} deltaTone={caused === 0 ? 'up' : 'down'} />
        <StatCard loading={loading} icon={Leaf} label="Renewable utilisation" value={summary?.renewable_utilization == null ? '-' : pct(summary.renewable_utilization, 1)} delta="share of PV output used" />
      </Stagger>

      <div className="grid grid-2">
        <SlideUp inView>
          <ChartPanel cta title="Generation, load and grid exchange" subtitle="Total across the feeder, kW" legend={[{ label: 'Generation', color: c.accent }, { label: 'Load', color: c.danger }, { label: 'Grid exchange', color: c.info }]}>
            <MultiLineChart data={data} valueFormat={(v) => num(v, 1)} series={[{ key: 'generation', label: 'Generation', color: c.accent, area: true }, { key: 'load', label: 'Load', color: c.danger }, { key: 'exchange', label: 'Grid exchange', color: c.info }]} />
          </ChartPanel>
        </SlideUp>
        <SlideUp inView delay={0.08}>
          <ChartPanel title="Battery state of charge" subtitle="Per node" legend={NODE_IDS.map((n) => ({ label: n, color: c.node[n] }))}>
            <MultiLineChart data={data} yDomain={[0, 1]} valueFormat={(v) => pct(v)} series={NODE_IDS.map((n) => ({ key: `soc_${n}`, label: n, color: c.node[n] }))} />
          </ChartPanel>
        </SlideUp>
      </div>

      <div className="grid grid-2">
        <SlideUp inView>
          <ChartPanel title="Shield outcome per step" subtitle="How each proposal was decided" legend={[{ label: 'Approved', color: c.status.approved }, { label: 'Projected', color: c.status.projected }, { label: 'Rejected', color: c.status.rejected }]}>
            <StackedBars data={data} series={[{ key: 'approved', label: 'Approved', color: c.status.approved }, { key: 'projected', label: 'Projected', color: c.status.projected }, { key: 'rejected', label: 'Rejected', color: c.status.rejected }]} />
          </ChartPanel>
        </SlideUp>
        <SlideUp inView delay={0.08}>
          <Card className="chart-card">
            <CardHeader title="Latest shield intervention" subtitle="Most recent proposal the shield changed or blocked" />
            <div className="card-body">
              {intervened ? (
                <ActionLane record={intervened} showChecks={false} />
              ) : (
                <EmptyState icon={ShieldCheck} title={anyDecision ? 'No intervention in the latest step' : 'No decisions yet'} actions={<Link className="btn" to="/app/shield">Try an action on the shield</Link>}>
                  {anyDecision ? 'Every agent proposal in the latest step passed the shield as requested.' : 'Step or start the simulation, or test any proposal yourself on the Safety shield screen.'}
                </EmptyState>
              )}
            </div>
          </Card>
        </SlideUp>
      </div>

      <SlideUp inView>
        <Card>
          <CardHeader title="Event timeline" subtitle="Agent actions, shield interventions and conflicts, newest first" />
          <div className="card-body">
            <EventFeed events={events} />
          </div>
        </Card>
      </SlideUp>
    </div>
  )
}
