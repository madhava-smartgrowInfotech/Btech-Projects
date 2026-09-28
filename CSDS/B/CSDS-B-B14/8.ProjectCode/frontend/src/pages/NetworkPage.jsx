import { useState } from 'react'
import { Lightbulb, Loader2, Play, RefreshCw } from 'lucide-react'
import api, { errorText } from '../api'
import useApi from '../useApi'
import { Badge, ErrorBox, Kpi, Loading, PageHeader, ZONE_COLORS, fmt } from '../components/ui.jsx'
import NetworkMap, { MapLegend } from '../components/NetworkMap.jsx'
import { BarChart } from '../components/Charts.jsx'

const STATUS_TONE = { 'under-supplied': 'rose', 'high losses': 'amber', 'excess pressure': 'sky', balanced: 'emerald' }

function Imbalance() {
  const { data, loading, error, reload } = useApi('/imbalance')
  const [speed, setSpeed] = useState(1.0)
  const [throttle, setThrottle] = useState('')
  const [what, setWhat] = useState(null)
  const [busy, setBusy] = useState(false)
  const [werr, setWerr] = useState('')

  async function run(sp, th) {
    setBusy(true)
    setWerr('')
    try {
      const r = await api.post('/imbalance/whatif', { pump_speed: sp, throttle: th || null })
      setWhat(r.data)
    } catch (e) {
      setWerr(errorText(e))
    } finally {
      setBusy(false)
    }
  }

  if (loading && !data) return <div className="card p-5"><Loading text="Simulating supply and demand for each zone..." /></div>
  if (error) return <ErrorBox error={error} onRetry={reload} />
  const rec = data.suggestion.recommended
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Equity score" value={fmt(data.current.equity_score, 1)} unit="/ 100" tone={data.current.equity_score < 90 ? 'amber' : 'emerald'} hint="worst vs best zone service level" />
        <Kpi label="Non-revenue water" value={fmt(data.current.nrw_pct, 1)} unit="%" tone="rose" />
        <Kpi label="System input" value={fmt(data.current.system_input_m3)} unit="m3/day" />
        <Kpi label="Minimum pressure" value={fmt(data.current.min_pressure, 1)} unit="m" tone={data.current.min_pressure < 20 ? 'rose' : 'emerald'} />
      </div>
      <div className={`card p-5 border-l-4 ${data.suggestion.improves ? 'border-l-amber-500' : 'border-l-emerald-500'}`}>
        <div className="flex items-start gap-3">
          <Lightbulb className="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-slate-800">Rebalancing suggestion</h3>
            <p className="text-sm text-slate-600 mt-1">{data.suggestion.text}</p>
            {rec && (
              <button className="btn-primary mt-3" disabled={busy}
                onClick={() => {
                  setSpeed(rec.pump_speed)
                  setThrottle(rec.throttle ? Object.keys(rec.throttle)[0] : '')
                  run(rec.pump_speed, rec.throttle)
                }}>
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Test plan on the twin
              </button>
            )}
          </div>
        </div>
      </div>
      <div className="card overflow-x-auto">
        <div className="p-4 pb-2 flex items-center justify-between">
          <h3 className="font-semibold text-slate-800">Supply vs demand per zone (24 h simulation)</h3>
          <button className="btn-secondary !py-1.5" onClick={reload}><RefreshCw className="w-4 h-4" /></button>
        </div>
        <table className="w-full">
          <thead>
            <tr><th className="th">Zone</th><th className="th">Demand m3</th><th className="th">Supply m3</th><th className="th">Delivered</th><th className="th">Losses m3</th><th className="th">Pressure OK</th><th className="th">Avg / min m</th><th className="th">Status</th></tr>
          </thead>
          <tbody>
            {data.zones.map((z) => (
              <tr key={z.zone}>
                <td className="td"><span className="inline-block w-2.5 h-2.5 rounded-full mr-2" style={{ background: ZONE_COLORS[z.zone] }} />{z.name}</td>
                <td className="td">{fmt(z.demand_m3)}</td>
                <td className="td">{fmt(z.supply_m3)}</td>
                <td className="td">{fmt(z.service_ratio * 100, 1)}%</td>
                <td className="td">{fmt(z.losses_m3)}</td>
                <td className="td">{fmt(z.pressure_adequacy * 100, 0)}%</td>
                <td className="td">{fmt(z.avg_pressure, 1)} / {fmt(z.min_pressure, 1)}</td>
                <td className="td"><Badge tone={STATUS_TONE[z.status]}>{z.status}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card p-5">
        <h3 className="font-semibold text-slate-800">What-if on the twin</h3>
        <div className="grid md:grid-cols-3 gap-4 mt-3 items-end">
          <div>
            <label className="label">Pump speed: {Math.round(speed * 100)}%</label>
            <input type="range" min="0.85" max="1.25" step="0.05" value={speed} onChange={(e) => setSpeed(Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="label">Throttle a trunk main</label>
            <select className="input" value={throttle} onChange={(e) => setThrottle(e.target.value)}>
              <option value="">None</option>
              <option value="P01">Zone 1 trunk main (P01)</option>
              <option value="P02">Zone 4 trunk main (P02)</option>
            </select>
          </div>
          <button className="btn-secondary" disabled={busy} onClick={() => run(speed, throttle ? { [throttle]: 300 } : null)}>
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Simulate
          </button>
        </div>
        <ErrorBox error={werr} />
        {what && (
          <div className="mt-4">
            <div className="text-sm text-slate-600 mb-2">
              Scenario: <b>{what.action}</b> - equity {data.current.equity_score} to <b>{what.equity_score}</b>, NRW {data.current.nrw_pct}% to <b>{what.nrw_pct}%</b>, minimum pressure {data.current.min_pressure} m to <b>{what.min_pressure} m</b>
            </div>
            <BarChart categories={data.zones.map((z) => z.zone)} yUnit="%" height={200}
              series={[
                { name: 'Pressure OK - now', color: '#94a3b8', values: data.zones.map((z) => z.pressure_adequacy * 100) },
                { name: 'Pressure OK - scenario', color: '#0284c7', values: data.zones.map((z) => what.zones[z.zone].pressure_adequacy * 100) },
              ]} />
          </div>
        )}
      </div>
    </div>
  )
}

export default function NetworkPage() {
  const { data, loading, error, reload } = useApi('/network')
  const [colorBy, setColorBy] = useState('zone')
  const [tab, setTab] = useState('map')
  return (
    <div>
      <PageHeader title="Network map" subtitle="Digital twin of the city distribution network (WNTR / EPANET), pressures and flows at the 08:00 peak">
        <div className="flex rounded-lg border border-slate-300 overflow-hidden text-sm">
          {['map', 'imbalance'].map((t) => (
            <button key={t} onClick={() => setTab(t)} className={`px-3 py-1.5 ${tab === t ? 'bg-sky-600 text-white' : 'bg-white text-slate-700'}`}>
              {t === 'map' ? 'Map' : 'Distribution imbalance'}
            </button>
          ))}
        </div>
      </PageHeader>
      {tab === 'imbalance' ? (
        <Imbalance />
      ) : (
        <>
          <ErrorBox error={error} onRetry={reload} />
          {loading && !data && <Loading text="Running the hydraulic simulation..." />}
          {data && (
            <div className="space-y-4">
              <div className="card p-4">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <div className="text-sm text-slate-600">
                    {data.nodes.filter((n) => n.type === 'Junction').length - 1} junctions, {data.links.filter((l) => l.type === 'Pipe').length} pipes, 1 pump, 1 tank, {data.sensors.length} pressure loggers -
                    NRW {data.summary.nrw_pct}%, avg pressure {data.summary.avg_pressure} m
                    {data.active_leaks.length > 0 && <Badge tone="rose">{data.active_leaks.length} leak(s) active in twin</Badge>}
                  </div>
                  <select className="input !w-auto" value={colorBy} onChange={(e) => setColorBy(e.target.value)}>
                    <option value="zone">Colour pipes by zone</option>
                    <option value="flow">Width by flow</option>
                  </select>
                </div>
                <NetworkMap nodes={data.nodes} links={data.links} suspects={data.suspects} activeLeaks={data.active_leaks} colorBy={colorBy} height={560} />
                <MapLegend colorBy={colorBy} zones={data.zones} />
              </div>
              <div className="grid md:grid-cols-5 gap-3">
                {Object.values(data.zone_stats).map((z) => (
                  <div key={z.zone} className="card p-3 border-t-4" style={{ borderTopColor: ZONE_COLORS[z.zone] }}>
                    <div className="text-sm font-medium text-slate-800">{z.name}</div>
                    <div className="text-xs text-slate-500 mt-1">Demand {fmt(z.demand_m3)} m3/day</div>
                    <div className="text-xs text-slate-500">Pressure {z.avg_pressure} m (min {z.min_pressure})</div>
                    <div className="text-xs text-slate-500">Losses {fmt(z.losses_m3)} m3/day</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
