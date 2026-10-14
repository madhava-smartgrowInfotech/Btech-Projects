import { useState } from 'react'
import { BedDouble, HeartPulse, RefreshCw, Users } from 'lucide-react'
import useFetch from '../lib/useFetch'
import { shortDate } from '../lib/hospi'
import { PageHeader } from '../components/ui/Layout'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Form'
import { Badge, Card } from '../components/ui/Display'
import { Tabs } from '../components/ui/Navigation'
import { ErrorState, SkeletonBlock } from '../components/ui/Feedback'
import { Table } from '../components/ui/Table'
import ForecastBand from '../components/charts/ForecastBand'
import AlertList from '../components/AlertList'

const FACILITY_OPTS = ['A', 'B', 'C', 'D', 'E'].map((f) => ({ value: f, label: `Facility ${f}` }))
const SHIFTS = ['Day', 'Evening', 'Night']

const TABS = [
  { id: 'occupancy', label: 'Ward occupancy', icon: BedDouble },
  { id: 'icu', label: 'ICU demand', icon: HeartPulse },
  { id: 'resources', label: 'Staff and equipment', icon: Users },
]

/** One ward or one facility's ICU: the 14-day census with its 90% band and the bed capacity line. */
function SeriesCard({ title, w }) {
  const pts = w.series.map((p) => ({ label: shortDate(p.date), mean: p.mean, lower: p.lower, upper: p.upper }))
  const status = w.alert ? (w.alert.level === 'critical' ? 'Over capacity' : 'Early warning') : 'Within capacity'
  return (
    <Card
      title={title}
      actions={
        <Badge tone={w.alert ? 'closed' : 'pass'}>
          {status}
          {w.alert ? ` on day ${w.alert.day}` : ''}
        </Badge>
      }
    >
      <p className="small muted" style={{ marginBottom: 12 }}>
        Now {w.current} of {w.capacity} beds. Expected peak {w.peak} on day {w.peak_day} (90% upper {w.peak_upper}).
      </p>
      <ForecastBand data={pts} capacity={w.capacity} name="Expected" height={200} />
    </Card>
  )
}

function Occupancy() {
  const [facility, setFacility] = useState('A')
  const { data, error, loading, reload } = useFetch('/forecast', { facility, days: 14 })
  return (
    <>
      <div className="row">
        <Select label="Facility" options={FACILITY_OPTS} value={facility} onChange={(e) => setFacility(e.target.value)} />
        <Button icon={RefreshCw} onClick={reload} loading={loading && !!data}>
          Refresh
        </Button>
      </div>
      {error && !data && <ErrorState title="Occupancy forecast could not load" error={error} onRetry={reload} />}
      {error && data && <ErrorState title="Showing the last loaded forecast" error={error} onRetry={reload} />}
      {!data && !error && <SkeletonBlock rows={6} label="Forecasting occupancy" />}
      {data && (
        <>
          <Card title={`Facility ${facility} alerts`}>
            <AlertList alerts={data.alerts} empty="No ward in this facility is forecast to pass capacity in the next 14 days." />
          </Card>
          <div className="grid grid-2" style={{ '--gap': '20px' }}>
            {data.wards.map((w) => (
              <SeriesCard key={w.ward} title={w.ward} w={w} />
            ))}
          </div>
          <p className="tiny muted">
            Expected census = current patients still in bed (from each patient&apos;s predicted stay) plus forecast admissions still in bed. Shaded
            area: 90% band. Red line: bed capacity.
          </p>
        </>
      )}
    </>
  )
}

function Icu() {
  const { data, error, loading, reload } = useFetch('/forecast/icu', { days: 14 })
  return (
    <>
      <div className="row">
        <Button icon={RefreshCw} onClick={reload} loading={loading && !!data}>
          Refresh
        </Button>
      </div>
      {error && !data && <ErrorState title="ICU forecast could not load" error={error} onRetry={reload} />}
      {error && data && <ErrorState title="Showing the last loaded forecast" error={error} onRetry={reload} />}
      {!data && !error && <SkeletonBlock rows={6} label="Forecasting ICU demand" />}
      {data && (
        <>
          <Card title="ICU early warnings">
            <AlertList alerts={data.alerts} empty="ICU demand stays within capacity at every facility for the next 14 days." />
          </Card>
          <div className="grid grid-2" style={{ '--gap': '20px' }}>
            {data.facilities.map((f) => (
              <SeriesCard key={f.facility} title={`Facility ${f.facility}, ICU`} w={f} />
            ))}
          </div>
        </>
      )}
    </>
  )
}

function ShiftCell({ row, shift }) {
  const s = row.shifts.find((x) => x.shift === shift)
  if (!s) return '—'
  return (
    <span className="row" style={{ '--gap': '6px', flexWrap: 'nowrap' }}>
      <span style={{ fontWeight: s.gap ? 700 : 400 }}>{s.needed}</span>
      <span className="muted">/ {s.rostered}</span>
      {s.gap > 0 && <Badge tone="closed">short {s.gap}</Badge>}
    </span>
  )
}

function Resources() {
  const [facility, setFacility] = useState('A')
  const [day, setDay] = useState(0)
  const { data, error, loading, reload } = useFetch('/forecast/resources', { facility, days: 7 })
  const d = data?.days[Math.min(day, (data?.days.length || 1) - 1)]
  const dayOpts = data?.days.map((x, i) => ({
    value: i,
    label: `Day ${x.day}, ${x.date}${x.nurse_gap + x.equipment_gap ? ' (gaps)' : ''}`,
  }))

  return (
    <>
      <div className="row">
        <Select label="Facility" options={FACILITY_OPTS} value={facility} onChange={(e) => setFacility(e.target.value)} />
        {dayOpts && <Select label="Day" options={dayOpts} value={day} onChange={(e) => setDay(Number(e.target.value))} />}
        <Button icon={RefreshCw} onClick={reload} loading={loading && !!data}>
          Refresh
        </Button>
      </div>
      {error && !data && <ErrorState title="Staff and equipment forecast could not load" error={error} onRetry={reload} />}
      {error && data && <ErrorState title="Showing the last loaded forecast" error={error} onRetry={reload} />}
      {!d && !error && <SkeletonBlock rows={6} label="Calculating staff and equipment demand" />}
      {d && (
        <div className="grid" style={{ '--gap': '20px', gridTemplateColumns: 'minmax(0, 2fr) minmax(260px, 1fr)' }}>
          <Card title={`Nurses per shift, ${d.date}`} className="table-scroll-x">
            <Table
              caption="Nurses needed and rostered per ward and shift"
              rows={d.nurses}
              rowKey={(n) => n.ward}
              pageSize={10}
              columns={[
                { key: 'ward', label: 'Ward' },
                { key: 'patients', label: 'Expected patients', numeric: true, render: (n) => n.patients },
                ...SHIFTS.map((s) => ({ key: s, label: `${s} need / rostered`, sortable: false, render: (n) => <ShiftCell row={n} shift={s} /> })),
              ]}
            />
            <p className="tiny muted" style={{ marginTop: 12 }}>
              Safe ratios, patients per nurse (day / evening / night):{' '}
              {Object.entries(data.ratios)
                .map(([w, r]) => `${w} ${r.Day}/${r.Evening}/${r.Night}`)
                .join(', ')}
            </p>
          </Card>
          <Card title="Critical equipment">
            <Table
              caption="Equipment needed and available"
              rows={d.equipment}
              rowKey={(e) => e.item}
              pageSize={10}
              columns={[
                { key: 'item', label: 'Item' },
                { key: 'needed', label: 'Needed', numeric: true },
                {
                  key: 'available',
                  label: 'Available',
                  numeric: true,
                  render: (e) => (
                    <span className="row" style={{ '--gap': '6px', flexWrap: 'nowrap' }}>
                      {e.available}
                      {e.gap > 0 && <Badge tone="closed">short {e.gap}</Badge>}
                    </span>
                  ),
                },
              ]}
            />
            <p className="tiny muted" style={{ marginTop: 12 }}>
              Needed = expected patients on each ward multiplied by the usage rate per occupied bed.
            </p>
          </Card>
        </div>
      )}
    </>
  )
}

export default function Forecasts() {
  const [tab, setTab] = useState('occupancy')
  return (
    <>
      <PageHeader
        eyebrow="Forecast"
        title="Occupancy and ICU forecasts"
        description="The next 14 days per facility and ward, from current patients' predicted stays and forecast admissions."
      />
      <Tabs tabs={TABS} value={tab} onChange={setTab} label="Forecast views" />
      <div className="stack" style={{ '--gap': '20px', marginTop: 24 }}>
        {tab === 'occupancy' && <Occupancy />}
        {tab === 'icu' && <Icu />}
        {tab === 'resources' && <Resources />}
      </div>
    </>
  )
}
