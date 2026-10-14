import { BedDouble, Clock, HeartPulse, RefreshCw, TrendingUp, UserPlus, Workflow } from 'lucide-react'
import useFetch from '../lib/useFetch'
import { loadTone, pct, shortDate, TONE_COLOR } from '../lib/hospi'
import { PageHeader } from '../components/ui/Layout'
import { Button } from '../components/ui/Button'
import { Badge, Card, StatCard } from '../components/ui/Display'
import { EmptyState, ErrorState, Skeleton, SkeletonBlock } from '../components/ui/Feedback'
import { Table } from '../components/ui/Table'
import ForecastBand from '../components/charts/ForecastBand'
import AlertList from '../components/AlertList'
import { Stagger } from '../components/motion'

const cardTone = (tone) => (tone === 'critical' ? 'coral' : undefined)
const deltaFor = (tone) => ({ critical: 'Over capacity', watch: 'Watch: 90%+', ok: 'Within capacity' })[tone]

export default function Dashboard() {
  const { data, error, loading, reload } = useFetch('/dashboard')
  const header = (
    <PageHeader
      eyebrow={data ? `Operating date ${data.operating_date}` : 'Operating date'}
      title="Dashboard"
      description="Current occupancy, the next 14 days of forecasts, and the warnings that need attention."
      actions={
        <Button icon={RefreshCw} onClick={reload} loading={loading && !!data}>
          Refresh
        </Button>
      }
    />
  )

  if (loading && !data) {
    return (
      <>
        {header}
        <div className="grid grid-4" style={{ '--gap': '16px' }} aria-busy="true">
          {[0, 1, 2, 3].map((i) => (
            <Card key={i}>
              <Skeleton height={84} />
            </Card>
          ))}
        </div>
        <div style={{ marginTop: 24 }}>
          <SkeletonBlock rows={6} label="Loading dashboard" />
        </div>
      </>
    )
  }

  if (!data) {
    return (
      <>
        {header}
        <ErrorState title="The dashboard could not load" error={error} onRetry={reload} />
      </>
    )
  }

  const k = data.kpis
  const occTone = loadTone(k.occupancy)
  const icuTone = loadTone(k.icu_occupancy)
  const peakTone = loadTone(k.peak_occupancy_7d)

  return (
    <>
      {header}
      {error && (
        <div style={{ marginBottom: 16 }}>
          <ErrorState title="Showing the last loaded data" error={error} onRetry={reload} />
        </div>
      )}

      <Stagger className="grid grid-4" style={{ '--gap': '16px' }}>
        <StatCard label="Bed occupancy" value={pct(k.occupancy, 1)} hint={`${k.occupied} of ${k.beds} beds`} icon={BedDouble} tone={cardTone(occTone)} delta={deltaFor(occTone)} deltaTone={TONE_COLOR[occTone]} />
        <StatCard label="ICU occupancy" value={pct(k.icu_occupancy, 1)} hint={`${k.icu_occupied} of ${k.icu_beds} ICU beds`} icon={HeartPulse} tone={cardTone(icuTone)} delta={deltaFor(icuTone)} deltaTone={TONE_COLOR[icuTone]} />
        <StatCard label="Peak occupancy, 7 days" value={pct(k.peak_occupancy_7d, 1)} hint="Expected, all facilities" icon={TrendingUp} tone={cardTone(peakTone)} delta={deltaFor(peakTone)} deltaTone={TONE_COLOR[peakTone]} />
        <StatCard label="Admissions, next 24 h" value={k.admissions_next_24h} hint={`${k.admitted_today_in_app} admitted in HospiSense today`} icon={UserPlus} />
        <StatCard label="Avg predicted stay" value={`${k.avg_predicted_los} d`} hint="Current inpatients" icon={Clock} />
        <StatCard label="Long-stay share" value={pct(k.long_stay_share, 1)} hint="Predicted stay over 5 days" />
        <StatCard label="ICU warnings" value={data.icu_alerts} hint="Facilities, next 14 days" delta={data.icu_alerts ? 'Action needed' : 'None'} deltaTone={data.icu_alerts ? TONE_COLOR.critical : TONE_COLOR.ok} />
        <StatCard
          label="Latest plan"
          value={data.latest_plan ? `#${data.latest_plan.id}` : 'None'}
          hint={data.latest_plan ? `${data.latest_plan.status}, ${data.latest_plan.actions} actions` : 'No plan generated yet'}
          icon={Workflow}
        />
      </Stagger>

      <div className="grid grid-2" style={{ '--gap': '24px', marginTop: 28, alignItems: 'start' }}>
        <Card title="Hospital census, next 14 days" actions={<span className="tiny muted">90% band · red line = beds</span>}>
          <ForecastBand
            data={data.daily.map((d) => ({ label: shortDate(d.date), mean: d.mean, lower: d.lower, upper: d.upper }))}
            capacity={k.beds}
            capacityLabel="beds"
            name="Expected census"
            height={260}
          />
        </Card>
        <Card title="Alerts">
          <AlertList alerts={data.alerts} />
        </Card>
      </div>

      <div className="grid grid-2" style={{ '--gap': '24px', marginTop: 24, alignItems: 'start' }}>
        <Card title="ICU census, next 14 days" actions={<span className="tiny muted">all facilities · red line = ICU beds</span>}>
          <ForecastBand
            data={data.daily.map((d) => ({ label: shortDate(d.date), mean: d.icu }))}
            capacity={k.icu_beds}
            capacityLabel="ICU beds"
            name="Expected ICU census"
            height={220}
          />
        </Card>
        <Card title="Latest allocation plan">
          {data.latest_plan ? (
            <div className="stack" style={{ '--gap': '12px' }}>
              <div className="row">
                <strong>Plan #{data.latest_plan.id}</strong>
                <Badge tone={data.latest_plan.status === 'accepted' ? 'pass' : undefined}>{data.latest_plan.status}</Badge>
              </div>
              <p className="small">{data.latest_plan.summary}</p>
              <div>
                <Button to="/allocation" icon={Workflow}>
                  Open allocation
                </Button>
              </div>
            </div>
          ) : (
            <EmptyState
              icon={Workflow}
              title="No plan yet"
              action={
                <Button to="/allocation" icon={Workflow}>
                  Open allocation
                </Button>
              }
            >
              Administrators can generate a plan from the forecast on the allocation screen.
            </EmptyState>
          )}
        </Card>
      </div>

      <Card title="Facilities" style={{ marginTop: 24 }} className="dashboard-facilities">
        <Table
          caption="Occupancy and ICU demand by facility"
          rows={data.facilities}
          rowKey={(f) => f.facility}
          initialSort={{ key: 'facility', dir: 'asc' }}
          columns={[
            { key: 'facility', label: 'Facility', render: (f) => `Facility ${f.facility}` },
            { key: 'occupied', label: 'Occupied', render: (f) => `${f.occupied} / ${f.beds}`, sortValue: (f) => f.occupied / f.beds, numeric: true },
            { key: 'occupancy', label: 'Occupancy', render: (f) => pct(f.occupancy), numeric: true },
            { key: 'peak', label: '7-day peak', render: (f) => pct(f.peak_occupancy_7d), sortValue: (f) => f.peak_occupancy_7d, numeric: true },
            { key: 'icu', label: 'ICU now', render: (f) => `${f.icu_occupied} / ${f.icu_beds}`, sortValue: (f) => f.icu_occupied / f.icu_beds, numeric: true },
            {
              key: 'icu_peak',
              label: 'ICU 7-day peak',
              render: (f) => (f.icu_peak_7d > f.icu_beds ? `${f.icu_peak_7d.toFixed(0)} (over ${f.icu_beds})` : f.icu_peak_7d.toFixed(0)),
              sortValue: (f) => f.icu_peak_7d,
              numeric: true,
            },
          ]}
        />
      </Card>
    </>
  )
}
