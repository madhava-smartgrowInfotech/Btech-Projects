import { useCallback, useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import api, { errorMessage } from '../api'
import ForecastChart, { shortDate } from '../components/ForecastChart'
import { AlertList, Badge, ErrorBox, Loading, PageHeader } from '../components/ui'

const FACILITIES = ['A', 'B', 'C', 'D', 'E']
const TABS = [
  ['occupancy', 'Ward occupancy'],
  ['icu', 'ICU demand'],
  ['resources', 'Staff and equipment'],
]

function useFetch(url, params) {
  const [state, setState] = useState({ data: null, error: '', loading: true })
  const key = JSON.stringify(params)
  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: '' }))
    try {
      const { data } = await api.get(url, { params: JSON.parse(key) })
      setState({ data, error: '', loading: false })
    } catch (err) {
      setState({ data: null, error: errorMessage(err), loading: false })
    }
  }, [url, key])
  useEffect(() => {
    load()
  }, [load])
  return { ...state, reload: load }
}

function FacilityPicker({ value, onChange }) {
  return (
    <div className="flex rounded-lg border border-slate-300 overflow-hidden bg-white">
      {FACILITIES.map((f) => (
        <button key={f} onClick={() => onChange(f)} className={`px-3 py-1.5 text-sm cursor-pointer ${value === f ? 'bg-teal-700 text-white' : 'text-slate-700 hover:bg-slate-50'}`}>
          {f}
        </button>
      ))}
    </div>
  )
}

function WardCard({ w }) {
  const pts = w.series.map((p) => ({ label: shortDate(p.date), mean: p.mean, lower: p.lower, upper: p.upper }))
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-semibold text-slate-900">
          {w.facility === undefined ? '' : `Facility ${w.facility} - `}
          {w.ward}
        </h3>
        {w.alert ? (
          <Badge tone={w.alert.level === 'critical' ? 'red' : 'amber'}>
            {w.alert.level === 'critical' ? 'Over capacity' : 'Early warning'} day {w.alert.day}
          </Badge>
        ) : (
          <Badge tone="teal">Within capacity</Badge>
        )}
      </div>
      <div className="text-xs text-slate-500 mb-2">
        Now {w.current} / {w.capacity} beds - peak {w.peak} expected on day {w.peak_day} (90% upper {w.peak_upper})
      </div>
      <ForecastChart points={pts} capacity={w.capacity} current={w.current} height={170} />
    </div>
  )
}

function Occupancy() {
  const [facility, setFacility] = useState('A')
  const { data, error, loading, reload } = useFetch('/forecast', { facility, days: 14 })
  return (
    <>
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <FacilityPicker value={facility} onChange={setFacility} />
        <button className="btn-secondary" onClick={reload} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>
      <ErrorBox message={error} onRetry={reload} />
      {loading && !data ? (
        <Loading label="Forecasting occupancy..." />
      ) : data ? (
        <>
          <div className="card p-4 mb-4">
            <h2 className="font-semibold text-slate-900 mb-2">Facility {facility} alerts</h2>
            <AlertList alerts={data.alerts} />
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {data.wards.map((w) => (
              <WardCard key={w.ward} w={{ ...w, facility: undefined }} />
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-3">
            Expected census = current patients still in bed (from each patient's predicted stay) + forecast admissions still in bed.
            Shaded area: 90% band. Dashed red line: bed capacity.
          </p>
        </>
      ) : null}
    </>
  )
}

function Icu() {
  const { data, error, loading, reload } = useFetch('/forecast/icu', { days: 14 })
  if (loading && !data) return <Loading label="Forecasting ICU demand..." />
  return (
    <>
      <ErrorBox message={error} onRetry={reload} />
      {data && (
        <>
          <div className="card p-4 mb-4">
            <h2 className="font-semibold text-slate-900 mb-2">ICU early warnings</h2>
            <AlertList alerts={data.alerts} empty="ICU demand stays within capacity at every facility for the next 14 days." />
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {data.facilities.map((w) => (
              <WardCard key={w.facility} w={w} />
            ))}
          </div>
        </>
      )}
    </>
  )
}

function Resources() {
  const [facility, setFacility] = useState('A')
  const [day, setDay] = useState(0)
  const { data, error, loading, reload } = useFetch('/forecast/resources', { facility, days: 7 })
  const d = data?.days[day]
  return (
    <>
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <FacilityPicker value={facility} onChange={setFacility} />
        {data && (
          <select className="input w-auto" value={day} onChange={(e) => setDay(Number(e.target.value))}>
            {data.days.map((x, i) => (
              <option key={i} value={i}>
                Day {x.day} - {x.date} {x.nurse_gap + x.equipment_gap ? '(gaps)' : ''}
              </option>
            ))}
          </select>
        )}
      </div>
      <ErrorBox message={error} onRetry={reload} />
      {loading && !data ? (
        <Loading label="Calculating staff and equipment demand..." />
      ) : d ? (
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="card overflow-x-auto lg:col-span-2">
            <h2 className="font-semibold text-slate-900 px-4 pt-4 pb-2">Nurses per shift - {d.date}</h2>
            <table className="w-full min-w-[520px]">
              <thead>
                <tr>
                  <th className="th">Ward</th>
                  <th className="th">Expected patients</th>
                  {['Day', 'Evening', 'Night'].map((s) => (
                    <th key={s} className="th">{s} need / rostered</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {d.nurses.map((n) => (
                  <tr key={n.ward}>
                    <td className="td font-medium">{n.ward}</td>
                    <td className="td">{n.patients}</td>
                    {n.shifts.map((s) => (
                      <td key={s.shift} className="td">
                        <span className={s.gap ? 'text-red-700 font-semibold' : ''}>{s.needed}</span> / {s.rostered}
                        {s.gap > 0 && <Badge tone="red">-{s.gap}</Badge>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-slate-500 px-4 py-3">
              Ratios (patients per nurse, day/evening/night): {Object.entries(data.ratios).map(([w, r]) => `${w} ${r.Day}/${r.Evening}/${r.Night}`).join(' - ')}
            </p>
          </div>
          <div className="card overflow-x-auto">
            <h2 className="font-semibold text-slate-900 px-4 pt-4 pb-2">Critical equipment</h2>
            <table className="w-full">
              <thead>
                <tr>
                  <th className="th">Item</th>
                  <th className="th">Needed</th>
                  <th className="th">Available</th>
                </tr>
              </thead>
              <tbody>
                {d.equipment.map((e) => (
                  <tr key={e.item}>
                    <td className="td font-medium">{e.item}</td>
                    <td className="td">{e.needed}</td>
                    <td className="td">
                      {e.available} {e.gap > 0 && <Badge tone="red">-{e.gap}</Badge>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-slate-500 px-4 py-3">Needed = expected patients per ward x usage rate per occupied bed.</p>
          </div>
        </div>
      ) : null}
    </>
  )
}

export default function Forecasts() {
  const [tab, setTab] = useState('occupancy')
  return (
    <div>
      <PageHeader title="Occupancy and ICU forecasts" subtitle="Next 14 days per facility and ward, from current patients' predicted stays and forecast admissions" />
      <div className="flex gap-1 border-b border-slate-200 mb-5 overflow-x-auto">
        {TABS.map(([k, label]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap cursor-pointer ${tab === k ? 'border-teal-700 text-teal-800' : 'border-transparent text-slate-500 hover:text-slate-800'}`}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === 'occupancy' && <Occupancy />}
      {tab === 'icu' && <Icu />}
      {tab === 'resources' && <Resources />}
    </div>
  )
}
