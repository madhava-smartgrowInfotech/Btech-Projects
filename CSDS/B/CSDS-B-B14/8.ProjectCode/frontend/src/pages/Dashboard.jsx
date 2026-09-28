import { Link } from 'react-router-dom'
import { AlertTriangle, Droplets, FlaskConical, Gauge, RefreshCw, Scale, ShieldAlert, Users } from 'lucide-react'
import useApi from '../useApi'
import { Badge, ErrorBox, Kpi, Loading, PageHeader, ZONE_COLORS, dayLabel, fmt, severityTone, timeAgo } from '../components/ui.jsx'
import { BarChart, LineChart } from '../components/Charts.jsx'
import NetworkMap, { MapLegend } from '../components/NetworkMap.jsx'

const HOURS = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`)

export function AlertList({ alerts }) {
  if (!alerts?.length) return <div className="text-sm text-slate-500 py-4">No alerts.</div>
  return (
    <ul className="divide-y divide-slate-100">
      {alerts.map((a) => (
        <li key={a.id} className="py-3 flex gap-3">
          <AlertTriangle className={`w-4 h-4 mt-0.5 shrink-0 ${a.severity === 'high' ? 'text-rose-600' : 'text-amber-500'}`} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-slate-800">{a.title}</span>
              <Badge tone={severityTone(a.severity)}>{a.kind}</Badge>
              {!a.open && <Badge>resolved</Badge>}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">{a.detail}</div>
            <div className="text-xs text-slate-400 mt-0.5">
              {timeAgo(a.created_at)}
              {a.zone ? ` - ${a.zone}` : ''}
            </div>
          </div>
        </li>
      ))}
    </ul>
  )
}

export default function Dashboard() {
  const { data, loading, error, reload } = useApi('/dashboard')
  const net = useApi('/network')
  return (
    <div>
      <PageHeader title="Operations dashboard" subtitle="Live state of the network twin, forecasts and alerts">
        <button className="btn-secondary" onClick={() => { reload(); net.reload() }} disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </PageHeader>
      <ErrorBox error={error} onRetry={reload} />
      {loading && !data && <Loading text="Simulating the network and loading KPIs..." />}
      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            <Kpi icon={Droplets} label="Non-revenue water" value={fmt(data.kpis.nrw_pct, 1)} unit="%" tone={data.kpis.nrw_pct > 15 ? 'rose' : 'sky'}
              hint={`${fmt(data.kpis.system_input_m3)} m3 in / ${fmt(data.kpis.billed_m3)} m3 billed`} />
            <Kpi icon={Gauge} label="Avg pressure" value={fmt(data.kpis.avg_pressure, 1)} unit="m" tone="emerald" hint={`minimum ${fmt(data.kpis.min_pressure, 1)} m`} />
            <Kpi icon={FlaskConical} label="Quality" value={data.kpis.quality_potable_pct == null ? '-' : fmt(data.kpis.quality_potable_pct, 0)} unit={data.kpis.quality_potable_pct == null ? '' : '% potable'}
              tone="violet" hint={`${data.kpis.quality_checks} lab sample(s) checked`} />
            <Kpi icon={Scale} label="Equity score" value={fmt(data.kpis.equity_score, 1)} unit="/ 100" tone={data.kpis.equity_score < 90 ? 'amber' : 'emerald'} hint="worst vs best zone service" />
            <Kpi icon={ShieldAlert} label="Active leaks" value={data.kpis.active_leaks} tone={data.kpis.active_leaks ? 'rose' : 'emerald'} hint={`${data.kpis.open_alerts} open alerts`} />
            <Kpi icon={Users} label="Flagged meters" value={data.kpis.flagged_meters} tone="amber" hint="abnormal consumption, last 7 days" />
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            <div className="card p-4 lg:col-span-2">
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-semibold text-slate-800">Network map</h2>
                <Link to="/network" className="text-sm text-sky-700 hover:underline">Open full map</Link>
              </div>
              <ErrorBox error={net.error} onRetry={net.reload} />
              {net.data ? (
                <>
                  <NetworkMap nodes={net.data.nodes} links={net.data.links} suspects={net.data.suspects} activeLeaks={net.data.active_leaks} height={340} />
                  <MapLegend zones={net.data.zones} />
                </>
              ) : (
                !net.error && <Loading />
              )}
            </div>
            <div className="card p-4">
              <h2 className="font-semibold text-slate-800 mb-1">Alerts</h2>
              <div className="max-h-[400px] overflow-y-auto">
                <AlertList alerts={data.alerts} />
              </div>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <div className="card p-4">
              <h2 className="font-semibold text-slate-800">System supply and pressure - next 24 h (twin)</h2>
              <p className="text-xs text-slate-500 mb-2">Zone inflow (L/s) with average network pressure (m, dashed)</p>
              <LineChart labels={HOURS} series={[{ name: 'Supply (L/s)', color: '#0284c7', values: data.hourly_supply_lps }]}
                right={[{ name: 'Avg pressure (m)', color: '#10b981', values: data.hourly_pressure }]} yUnit="L/s" rightUnit="m" />
            </div>
            <div className="card p-4">
              <h2 className="font-semibold text-slate-800">Supply vs demand by zone (m3/day)</h2>
              <p className="text-xs text-slate-500 mb-2">Supply includes losses; delivered is below demand where pressure is short</p>
              <BarChart categories={data.zones.map((z) => z.zone)} yUnit="m3"
                series={[
                  { name: 'Demand', color: '#94a3b8', values: data.zones.map((z) => z.demand_m3) },
                  { name: 'Supply', color: '#0284c7', colors: data.zones.map((z) => ZONE_COLORS[z.zone]), values: data.zones.map((z) => z.supply_m3) },
                  { name: 'Losses', color: '#e11d48', values: data.zones.map((z) => z.losses_m3) },
                ]} />
            </div>
          </div>

          <div className="card p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-semibold text-slate-800">Demand forecast - all zones, next 7 days</h2>
              <span className="text-xs text-slate-500">
                {fmt(data.kpis.forecast_week_m3)} m3 forecast vs {fmt(data.kpis.last_week_m3)} m3 last week - weather: {data.weather_source}
              </span>
            </div>
            <BarChart categories={data.forecast_week.map((d) => dayLabel(d.date))} series={[{ name: 'Forecast demand', color: '#0284c7', values: data.forecast_week.map((d) => d.forecast_m3) }]} yUnit="m3" height={200} />
          </div>
        </div>
      )}
    </div>
  )
}
