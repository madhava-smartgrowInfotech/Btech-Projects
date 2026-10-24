import { Link, useNavigate } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, ClipboardList, FileText, FlaskConical, GitCompareArrows, Lightbulb, Siren, TrendingUp, UploadCloud } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { day } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, PageHeader, Skeleton, StatCard, Table } from '../components/ui'
import { ChartCard, DonutChart, useChartColors } from '../components/charts'
import { Stagger } from '../components/motion'
import { CriticalBanner, Disclaimer, ReportStatusBadge, SampleDataButton } from '../components/lab'

export default function Dashboard() {
  const navigate = useNavigate()
  const { data, error, loading, reload } = useAsync(() => api.dashboard(), [])
  const c = useChartColors()

  if (error) {
    return (
      <div className="container">
        <PageHeader title="Dashboard" />
        <ErrorState title="Could not load the dashboard" error={error} onRetry={reload} />
      </div>
    )
  }

  const stats = data?.stats
  const recent = data?.recent
  const empty = !loading && stats && stats.total_reports === 0
  const unknown = stats ? Math.max(0, stats.total_tests - stats.normal - stats.abnormal) : 0
  const donut = stats
    ? [
        { name: 'Normal', value: stats.normal, color: c.accent },
        { name: 'Abnormal', value: stats.abnormal, color: c.warn },
        ...(unknown ? [{ name: 'Unknown', value: unknown, color: c.text3 }] : []),
      ]
    : []

  const columns = [
    { key: 'id', label: 'ID', num: true, render: (r) => `#${r.id}`, hideSm: true },
    { key: 'file_name', label: 'File name', render: (r) => <strong className="break">{r.file_name}</strong> },
    { key: 'file_type', label: 'Type', render: (r) => <Badge>{(r.file_type || '').toUpperCase()}</Badge>, hideSm: true },
    { key: 'upload_date', label: 'Uploaded', render: (r) => day(r.upload_date) },
    { key: 'test_count', label: 'Tests', num: true },
    { key: 'abnormal_count', label: 'Abnormal', num: true, render: (r) => (r.abnormal_count ? <Badge tone="warn">{r.abnormal_count}</Badge> : <span className="faint">0</span>) },
    { key: 'processing_status', label: 'Status', render: (r) => <ReportStatusBadge status={r.processing_status} /> },
  ]

  return (
    <div className="container">
      <PageHeader
        title="Dashboard"
        description="Everything on file at a glance - totals across all of your uploaded lab reports."
        actions={
          <Button as={Link} to="/app/upload" variant="primary" icon={UploadCloud}>
            Upload report
          </Button>
        }
      />

      {stats && <CriticalBanner count={stats.critical} />}

      <Stagger className="grid grid-4 mt" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))' }}>
        <StatCard label="Total reports" value={stats?.total_reports} icon={FileText} loading={loading} />
        <StatCard label="Total tests" value={stats?.total_tests} icon={ClipboardList} tone="info" loading={loading} />
        <StatCard label="Normal results" value={stats?.normal} icon={CheckCircle2} loading={loading} />
        <StatCard label="Abnormal results" value={stats?.abnormal} icon={AlertTriangle} tone="warn" loading={loading} />
        <StatCard label="Critical alerts" value={stats?.critical} icon={Siren} tone="danger" loading={loading} />
      </Stagger>

      {empty ? (
        <Card className="mt">
          <EmptyState
            icon={FlaskConical}
            title="No reports uploaded yet"
            actions={
              <>
                <Button as={Link} to="/app/upload" variant="primary" icon={UploadCloud}>
                  Upload your first report
                </Button>
                <SampleDataButton onDone={reload} />
              </>
            }
          >
            Upload a PDF or image of a lab report, or load five synthetic sample reports to explore the app.
          </EmptyState>
        </Card>
      ) : (
        <div className="stack mt">
          <Card>
            <CardHeader
              title="Recent reports"
              subtitle="The ten most recent uploads. Select a row to open its analysis."
              actions={
                <Button as={Link} to="/app/reports" size="sm" variant="ghost">
                  View all
                </Button>
              }
            />
            <Table
              columns={columns}
              rows={recent}
              loading={loading}
              rowKey={(r) => r.id}
              pageSize={10}
              caption="Recent reports"
              onRowClick={(r) => navigate(`/app/analysis/${r.id}`)}
            />
          </Card>
          <div className="grid grid-2">
            <ChartCard title="Results by status" subtitle="All tests across every report" height={240}>
              {loading ? <Skeleton height={220} radius={12} /> : <DonutChart data={donut} centerValue={stats.total_tests} centerLabel="tests" />}
            </ChartCard>
            <Card>
              <CardHeader title="Keep exploring" subtitle="Where to go next with your results." />
              <div className="card-body stack" style={{ gap: 10 }}>
                <Button as={Link} to="/app/trends" icon={TrendingUp}>
                  Follow a test over time
                </Button>
                <Button as={Link} to="/app/compare" icon={GitCompareArrows}>
                  Compare two reports
                </Button>
                <Button as={Link} to="/app/insights" icon={Lightbulb}>
                  Read insights for abnormal results
                </Button>
              </div>
            </Card>
          </div>
        </div>
      )}

      <div className="mt">
        <Disclaimer />
      </div>
    </div>
  )
}
