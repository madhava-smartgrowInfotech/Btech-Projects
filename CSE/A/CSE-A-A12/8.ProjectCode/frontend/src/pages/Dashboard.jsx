import { lazy, Suspense } from 'react'
import { Link } from 'react-router-dom'
import { Activity, Gauge, ScanLine, ShieldCheck, Stethoscope } from 'lucide-react'
import { Alert, Button, Card, ClassBadge, EmptyState, ErrorState, PageHeader, Skeleton, StatCard } from '../components/ui'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { CLASS_COLOR, CLASS_SHORT, fmtDateTime, fmtPct } from '../lib/format'
import { useAsync, useDocumentTitle } from '../lib/hooks'

const BarBlocks = lazy(() => import('../components/ui/Charts').then((m) => ({ default: m.BarBlocks })))

const ChartFallback = () => <Skeleton height={280} />

function Skeletons() {
  return (
    <div className="stack" role="status" aria-label="Loading dashboard" style={{ '--gap': '20px' }}>
      <div className="grid grid-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} height={150} />
        ))}
      </div>
      <div className="grid grid-2">
        <Skeleton height={340} />
        <Skeleton height={340} />
      </div>
    </div>
  )
}

export default function Dashboard() {
  useDocumentTitle('Dashboard')
  const stats = useAsync(() => api.stats(), [])
  const recent = useAsync(() => api.predictions(5), [])
  const reloadAll = () => {
    stats.reload()
    recent.reload()
  }

  const s = stats.data
  const classData = s ? s.by_class && Object.entries(s.by_class).map(([name, count]) => ({ name, short: CLASS_SHORT[name] || name, count })) : []
  const dayData = s ? s.daily.map((d) => ({ day: d.date.slice(5), count: d.count })) : []

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        description="Everything the system has screened so far, straight from the prediction history."
        actions={
          <Button variant="primary" icon={ScanLine} to="/app/detect">
            New scan
          </Button>
        }
      />

      {s?.demo_mode && (
        <div style={{ marginBottom: 24 }}>
          <Alert tone="warning">
            <strong>Demo model.</strong> Results come from an untrained network, so the class counts below show the pipeline working, not real diagnoses.
          </Alert>
        </div>
      )}

      {stats.loading && !s ? (
        <Skeletons />
      ) : stats.error ? (
        <ErrorState title="Could not load the dashboard" error={stats.error} onRetry={reloadAll} />
      ) : s.total === 0 ? (
        <EmptyState
          icon={Stethoscope}
          title="No scans yet"
          action={
            <Button variant="primary" icon={ScanLine} to="/app/detect">
              Analyze your first X-ray
            </Button>
          }
        >
          Upload a chest X-ray and the totals, class split and daily activity will show up here.
        </EmptyState>
      ) : (
        <div className="stack" style={{ '--gap': '24px' }}>
          <Stagger className="grid grid-4" inView={false}>
            <StatCard label="Total scans" value={s.total} icon={Activity} hint={`Last scan ${fmtDateTime(s.last_scan_at)}`} />
            <StatCard label="Pneumonia flagged" value={s.pneumonia_total} icon={Stethoscope} tone="coral" hint="Bacterial + viral" />
            <StatCard label="Normal" value={s.by_class.Normal ?? 0} icon={ShieldCheck} tone="lime" hint="No pneumonia pattern" />
            <StatCard label="Avg confidence" value={s.avg_confidence === null ? '—' : fmtPct(s.avg_confidence)} icon={Gauge} hint="Top-class probability" />
          </Stagger>

          <div className="grid grid-2">
            <Card title="Scans by class">
              <Suspense fallback={<ChartFallback />}>
                <BarBlocks data={classData} xKey="short" yKey="count" name="Scans" colorFn={(d) => CLASS_COLOR[d.name]} labelKey="name" />
              </Suspense>
            </Card>
            <Card title="Scans, last 7 days (UTC)">
              <Suspense fallback={<ChartFallback />}>
                <BarBlocks data={dayData} xKey="day" yKey="count" name="Scans" color="#7CC6FF" />
              </Suspense>
            </Card>
          </div>

          <Card title="Recent scans" actions={<Button size="sm" variant="ghost" to="/app/history">View all</Button>}>
            {recent.loading && !recent.data ? (
              <Skeleton height={64} />
            ) : recent.error ? (
              <ErrorState title="Could not load recent scans" error={recent.error} onRetry={recent.reload} />
            ) : (
              recent.data.map((r) => (
                <Link key={r.id} to={`/app/result/${r.id}`} className="scan-row">
                  <img className="thumb thumb-lg" src={r.original_url} alt={`X-ray ${r.filename}`} loading="lazy" />
                  <div>
                    <strong>{r.filename}</strong>
                    <span className="small muted">{fmtDateTime(r.created_at)}</span>
                  </div>
                  <ClassBadge label={r.prediction} />
                  <span className="mono only-desktop">{fmtPct(r.confidence)}</span>
                </Link>
              ))
            )}
          </Card>
        </div>
      )}
    </>
  )
}
