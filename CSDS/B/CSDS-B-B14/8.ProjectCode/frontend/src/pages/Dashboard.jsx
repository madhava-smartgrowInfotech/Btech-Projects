import { Link } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, Droplets, FlaskConical, Gauge, LayoutDashboard, RefreshCw, Scale, ShieldAlert, Users } from 'lucide-react'
import useApi from '../useApi'
import { Button, Card, EmptyState, ErrorState, PageHeader, PageSkeleton, Skeleton, StatCard, Timeline } from '../components/ui'
import { AreaTrend, GroupedBars, LineCompare } from '../components/charts'
import NetworkMap, { MapLegend } from '../components/NetworkMap.jsx'
import { fmtInt, fmtNum, timeAgo } from '../lib/format'
import { dayLabel } from '../lib/aqua'
import { useChartTheme } from '../lib/palette'

const HOURS = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`)

export default function Dashboard() {
  const t = useChartTheme()
  const { data, loading, error, reload } = useApi('/dashboard')
  const net = useApi('/network')
  const alerts = useApi('/alerts')
  const refreshing = loading && !!data

  function refresh() {
    reload()
    net.reload()
    alerts.reload()
  }

  return (
    <>
      <PageHeader
        eyebrow="Operations"
        icon={LayoutDashboard}
        title="Operations dashboard"
        lead="Live state of the network twin, forecasts and alerts."
        actions={
          <Button variant="secondary" icon={RefreshCw} loading={refreshing} onClick={refresh}>
            Refresh
          </Button>
        }
      />

      {loading && !data && <PageSkeleton kpis={6} blocks={2} />}
      {error && !data && <ErrorState title="The dashboard did not load" error={error} onRetry={reload} />}

      {data && (
        <div className="stack" style={{ '--gap': '24px' }}>
          <div className="grid-kpi">
            <StatCard
              label="Non-revenue water"
              display={`${fmtNum(data.kpis.nrw_pct, 1)}%`}
              icon={Droplets}
              tone={data.kpis.nrw_pct > 15 ? 'rose' : 'sky'}
              foot={`${fmtInt(data.kpis.system_input_m3)} m³ in · ${fmtInt(data.kpis.billed_m3)} m³ billed`}
            />
            <StatCard
              label="Average pressure"
              display={`${fmtNum(data.kpis.avg_pressure, 1)} m`}
              icon={Gauge}
              tone="mint"
              foot={`minimum ${fmtNum(data.kpis.min_pressure, 1)} m`}
            />
            <StatCard
              label="Water quality"
              display={data.kpis.quality_potable_pct == null ? '–' : `${fmtNum(data.kpis.quality_potable_pct, 0)}% potable`}
              icon={FlaskConical}
              tone="lavender"
              foot={`${data.kpis.quality_checks} lab sample(s) checked`}
            />
            <StatCard
              label="Equity score"
              display={`${fmtNum(data.kpis.equity_score, 1)} / 100`}
              icon={Scale}
              tone={data.kpis.equity_score < 90 ? 'peach' : 'mint'}
              foot="worst vs best zone service"
            />
            <StatCard
              label="Active leaks"
              display={fmtInt(data.kpis.active_leaks)}
              icon={ShieldAlert}
              tone={data.kpis.active_leaks ? 'rose' : 'mint'}
              foot={`${data.kpis.open_alerts} open alert(s)`}
            />
            <StatCard
              label="Flagged meters"
              display={fmtInt(data.kpis.flagged_meters)}
              icon={Users}
              tone="peach"
              foot="abnormal use, last 7 days"
            />
          </div>

          <div className="grid-2 wide-left">
            <Card
              title="Network map"
              subtitle="Pipes coloured by zone, pressures at 08:00"
              actions={
                <Link className="btn secondary sm" to="/network">
                  Open full map
                </Link>
              }
            >
              {net.error && <ErrorState compact title="Map unavailable" error={net.error} onRetry={net.reload} />}
              {net.data ? (
                <>
                  <NetworkMap nodes={net.data.nodes} links={net.data.links} suspects={net.data.suspects} activeLeaks={net.data.active_leaks} height={340} />
                  <MapLegend zones={net.data.zones} />
                </>
              ) : (
                !net.error && <Skeleton height={340} radius={18} />
              )}
            </Card>

            <Card title="Open alerts" subtitle="Newest first: leaks, failed quality checks, abnormal meters">
              {alerts.error && <ErrorState compact title="Alerts did not load" error={alerts.error} onRetry={alerts.reload} />}
              {alerts.loading && !alerts.data && <Skeleton height={160} />}
              {alerts.data && alerts.data.length === 0 && (
                <EmptyState
                  compact
                  icon={CheckCircle2}
                  tone="mint"
                  title="All clear"
                  message="No open alerts. New leaks, failed quality checks and abnormal meters appear here."
                  action={
                    <Button variant="secondary" size="sm" to="/quality">
                      Run a quality check
                    </Button>
                  }
                />
              )}
              {alerts.data?.length > 0 && (
                <div style={{ maxHeight: 420, overflowY: 'auto', paddingRight: 4 }}>
                  <Timeline
                    items={alerts.data.slice(0, 12).map((a) => ({
                      id: a.id,
                      title: a.title,
                      meta: `${a.detail} · ${timeAgo(a.created_at)}${a.zone ? ` · ${a.zone}` : ''}`,
                      icon: AlertTriangle,
                      tone: a.severity === 'high' ? 'rose' : a.severity === 'medium' ? 'peach' : 'sky',
                    }))}
                  />
                </div>
              )}
            </Card>
          </div>

          <div className="grid-2">
            <Card title="System supply, next 24 hours" subtitle="Zone inflow from the twin, in litres per second">
              <AreaTrend
                label="Hourly system supply in litres per second"
                data={HOURS.map((x, i) => ({ x, y: data.hourly_supply_lps?.[i] ?? null }))}
                color={t.sky}
                name="Supply (L/s)"
                yFormat={(v) => fmtInt(v)}
                valueFormat={(v) => `${fmtNum(v, 1)} L/s`}
                height={260}
              />
            </Card>
            <Card title="Average pressure, next 24 hours" subtitle="Network average in metres of head">
              <LineCompare
                label="Hourly average network pressure in metres"
                data={HOURS.map((x, i) => ({ x, pressure: data.hourly_pressure?.[i] ?? null }))}
                series={[{ key: 'pressure', name: 'Avg pressure (m)', color: t.mint }]}
                yFormat={(v) => fmtNum(v, 0)}
                valueFormat={(v) => `${fmtNum(v, 1)} m`}
                height={260}
              />
            </Card>
            <Card title="Supply vs demand by zone" subtitle="m³/day. Delivered falls short of demand where pressure is low">
              <GroupedBars
                label="Demand, supply and losses per zone in cubic metres per day"
                data={data.zones.map((z) => ({ x: z.name || z.zone, demand: z.demand_m3, supply: z.supply_m3, losses: z.losses_m3 }))}
                series={[
                  { key: 'demand', name: 'Demand', color: t.lavender },
                  { key: 'supply', name: 'Supply', color: t.sky },
                  { key: 'losses', name: 'Losses', color: t.rose },
                ]}
                valueFormat={(v) => fmtInt(v)}
                height={260}
              />
            </Card>
            <Card
              title="Demand forecast, next 7 days"
              subtitle={`${fmtInt(data.kpis.forecast_week_m3)} m³ forecast against ${fmtInt(data.kpis.last_week_m3)} m³ last week · weather: ${data.weather_source}`}
            >
              <AreaTrend
                label="Forecast total demand per day for the next seven days"
                data={data.forecast_week.map((d) => ({ x: dayLabel(d.date), y: d.forecast_m3 }))}
                color={t.lavender}
                name="Forecast (m³)"
                yFormat={(v) => fmtInt(v)}
                valueFormat={(v) => `${fmtInt(v)} m³`}
                height={260}
              />
            </Card>
          </div>
        </div>
      )}
    </>
  )
}
