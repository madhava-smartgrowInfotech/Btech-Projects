import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BedDouble, Clock, HeartPulse, RefreshCw, TrendingUp, UserPlus } from 'lucide-react'
import api, { errorMessage } from '../api'
import ForecastChart, { shortDate } from '../components/ForecastChart'
import { AlertList, Badge, ErrorBox, Kpi, Loading, PageHeader, pct } from '../components/ui'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/dashboard')
      setData(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading && !data) return <Loading label="Loading dashboard..." />
  if (!data) return <ErrorBox message={error} onRetry={load} />
  const k = data.kpis
  const tone = (x) => (x >= 1 ? 'red' : x >= 0.9 ? 'amber' : 'teal')

  return (
    <div>
      <PageHeader title="Dashboard" subtitle={`Operating date ${data.operating_date} - forecasts cover the next 14 days`}>
        <button className="btn-secondary" onClick={load} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </PageHeader>
      <ErrorBox message={error} onRetry={load} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Kpi label="Bed occupancy" value={pct(k.occupancy, 1)} sub={`${k.occupied} of ${k.beds} beds`} tone={tone(k.occupancy)} icon={BedDouble} />
        <Kpi label="ICU occupancy" value={pct(k.icu_occupancy, 1)} sub={`${k.icu_occupied} of ${k.icu_beds} ICU beds`} tone={tone(k.icu_occupancy)} icon={HeartPulse} />
        <Kpi label="Peak occupancy (7 days)" value={pct(k.peak_occupancy_7d, 1)} sub="expected, all facilities" tone={tone(k.peak_occupancy_7d)} icon={TrendingUp} />
        <Kpi label="Admissions next 24h" value={k.admissions_next_24h} sub={`${k.admitted_today_in_app} admitted in HospiSense today`} icon={UserPlus} />
        <Kpi label="Avg predicted stay" value={`${k.avg_predicted_los} d`} sub="current inpatients" icon={Clock} />
        <Kpi label="Long-stay share" value={pct(k.long_stay_share, 1)} sub="predicted stay > 5 days" />
        <Kpi label="ICU warnings" value={data.icu_alerts} sub="facilities, next 14 days" tone={data.icu_alerts ? 'red' : 'teal'} />
        <Kpi
          label="Latest plan"
          value={data.latest_plan ? `#${data.latest_plan.id}` : 'None'}
          sub={data.latest_plan ? `${data.latest_plan.status}, ${data.latest_plan.actions} actions` : 'run the optimiser'}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-slate-900">Hospital census forecast</h2>
            <span className="text-xs text-slate-500">all facilities, expected with 90% band</span>
          </div>
          <ForecastChart
            points={data.daily.map((d) => ({ label: shortDate(d.date), mean: d.mean, upper: d.upper, lower: d.lower }))}
            capacity={k.beds}
            height={220}
          />
          <h3 className="text-sm font-medium text-slate-700 mt-4 mb-1">ICU census forecast</h3>
          <ForecastChart points={data.daily.map((d) => ({ label: shortDate(d.date), mean: d.icu }))} capacity={k.icu_beds} height={140} />
        </div>
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-900">Alerts</h2>
            <Link to="/forecasts" className="text-xs text-teal-700 font-medium">View forecasts</Link>
          </div>
          <AlertList alerts={data.alerts} />
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="card overflow-x-auto lg:col-span-2">
          <h2 className="font-semibold text-slate-900 px-5 pt-5 pb-2">Facilities</h2>
          <table className="w-full min-w-[560px]">
            <thead>
              <tr>
                <th className="th">Facility</th>
                <th className="th">Occupied</th>
                <th className="th">Occupancy</th>
                <th className="th">7-day peak</th>
                <th className="th">ICU now</th>
                <th className="th">ICU 7-day peak</th>
              </tr>
            </thead>
            <tbody>
              {data.facilities.map((f) => (
                <tr key={f.facility}>
                  <td className="td font-medium">Facility {f.facility}</td>
                  <td className="td">{f.occupied} / {f.beds}</td>
                  <td className="td"><Badge tone={tone(f.occupancy) === 'teal' ? 'teal' : tone(f.occupancy)}>{pct(f.occupancy)}</Badge></td>
                  <td className="td">{pct(f.peak_occupancy_7d)}</td>
                  <td className="td">{f.icu_occupied} / {f.icu_beds}</td>
                  <td className="td">
                    <Badge tone={f.icu_peak_7d > f.icu_beds ? 'red' : f.icu_peak_7d > 0.9 * f.icu_beds ? 'amber' : 'teal'}>{f.icu_peak_7d.toFixed(0)}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 mb-2">Allocation plan</h2>
          {data.latest_plan ? (
            <>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium">Plan #{data.latest_plan.id}</span>
                <Badge tone={data.latest_plan.status === 'accepted' ? 'teal' : 'amber'}>{data.latest_plan.status}</Badge>
              </div>
              <p className="text-sm text-slate-600">{data.latest_plan.summary}</p>
            </>
          ) : (
            <p className="text-sm text-slate-500">No plan yet. Administrators can generate one from the forecast.</p>
          )}
          <Link to="/allocation" className="btn-secondary mt-4">Open allocation</Link>
        </div>
      </div>
    </div>
  )
}
