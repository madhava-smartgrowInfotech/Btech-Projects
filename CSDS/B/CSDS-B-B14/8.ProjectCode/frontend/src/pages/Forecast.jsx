import { useState } from 'react'
import { CloudRain, Flame, TrendingUp } from 'lucide-react'
import useApi from '../useApi'
import { Badge, ErrorBox, Kpi, Loading, PageHeader, dayLabel, fmt } from '../components/ui.jsx'
import { LineChart } from '../components/Charts.jsx'

export default function Forecast() {
  const [zone, setZone] = useState('Z3')
  const zones = useApi('/forecast/zones')
  const { data, loading, error, reload } = useApi(`/forecast?zone=${zone}`)

  let chart = null
  if (data) {
    const hist = data.history.slice(-21)
    const labels = [...hist.map((h) => h.date), ...data.forecast.map((f) => f.date)].map((d) => dayLabel(d).replace(/^\w+ /, ''))
    const n = hist.length
    const peakIdx = n + data.forecast.findIndex((f) => f.date === data.peak.date)
    chart = (
      <LineChart
        labels={labels}
        height={280}
        yUnit="m3/day"
        rightUnit="max temp C"
        highlight={peakIdx}
        bands={[{ from: n, to: labels.length - 1, color: '#f0f9ff' }]}
        series={[
          { name: 'Billed consumption', color: '#475569', values: [...hist.map((h) => h.consumption_m3), ...data.forecast.map(() => null)], dots: false },
          { name: 'Forecast', color: '#0284c7', dashed: true, dots: true, values: [...hist.map((_, i) => (i === n - 1 ? hist[i].consumption_m3 : null)), ...data.forecast.map((f) => f.forecast_m3)] },
        ]}
        right={[{ name: 'Max temperature', color: '#f97316', values: [...hist.map((h) => h.tmax), ...data.forecast.map((f) => f.tmax)] }]}
      />
    )
  }

  return (
    <div>
      <PageHeader title="Demand forecast" subtitle="Next 7 days per zone from consumption history and Open-Meteo weather (XGBoost)">
        <select className="input !w-auto" value={zone} onChange={(e) => setZone(e.target.value)}>
          {(zones.data || [{ id: 'Z3', name: 'Zone 3' }]).map((z) => (
            <option key={z.id} value={z.id}>{z.name}</option>
          ))}
        </select>
      </PageHeader>
      <ErrorBox error={error || zones.error} onRetry={reload} />
      {loading && <Loading text="Fetching weather and forecasting demand..." />}
      {data && !loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Kpi icon={TrendingUp} label="Peak day" value={dayLabel(data.peak.date)} hint={`${fmt(data.peak.forecast_m3)} m3 at ${data.peak.tmax} C`} tone="rose" />
            <Kpi icon={Flame} label="Hottest day" value={dayLabel(data.hottest.date)} hint={`${data.hottest.tmax} C max`} tone="amber" />
            <Kpi label="7-day total" value={fmt(data.week_totals[zone])} unit="m3" hint={`last 7 days avg ${fmt(data.avg_last_7)} m3/day`} />
            <Kpi label="Model error (MAPE)" value={data.mape ?? '-'} unit="%" hint="7-day recursive, last 90 days" tone="emerald" />
          </div>
          <div className="card p-4">
            <div className="flex flex-wrap justify-between gap-2 mb-2">
              <h2 className="font-semibold text-slate-800">{data.zone_name} - last 3 weeks and next 7 days</h2>
              <span className="text-xs text-slate-500">Data up to {dayLabel(data.data_until)} - weather: {data.weather_source}</span>
            </div>
            {chart}
          </div>
          <div className="card overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr><th className="th">Day</th><th className="th">Forecast m3</th><th className="th">vs last-week avg</th><th className="th">Max / min C</th><th className="th">Rain mm</th><th className="th"></th></tr>
              </thead>
              <tbody>
                {data.forecast.map((f) => (
                  <tr key={f.date} className={f.date === data.peak.date ? 'bg-rose-50/60' : ''}>
                    <td className="td font-medium">{dayLabel(f.date)}</td>
                    <td className="td">{fmt(f.forecast_m3)}</td>
                    <td className="td">{f.forecast_m3 >= data.avg_last_7 ? '+' : ''}{fmt(((f.forecast_m3 - data.avg_last_7) / data.avg_last_7) * 100, 1)}%</td>
                    <td className="td">{f.tmax} / {f.tmin}</td>
                    <td className="td">{f.precip > 0 ? <span className="inline-flex items-center gap-1"><CloudRain className="w-3.5 h-3.5 text-sky-500" />{f.precip}</span> : '0'}</td>
                    <td className="td space-x-1">
                      {f.date === data.peak.date && <Badge tone="rose">peak demand</Badge>}
                      {f.date === data.hottest.date && <Badge tone="amber">hottest</Badge>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
