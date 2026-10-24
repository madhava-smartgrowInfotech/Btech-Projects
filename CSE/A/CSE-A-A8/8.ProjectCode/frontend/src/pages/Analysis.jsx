import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, FileSearch, ListChecks, UploadCloud } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { day } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, PageHeader, Select, Skeleton, StatCard, Tabs } from '../components/ui'
import { Callout, Disclaimer, InsightCard, PageSkeleton, ReportStatusBadge, ResultsTable, SampleDataButton } from '../components/lab'

export default function Analysis() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState('all')
  const list = useAsync(() => api.reports(), [])
  const detail = useAsync(() => api.report(id), [id], { enabled: !!id })

  useEffect(() => setTab('all'), [id])

  const results = detail.data?.results || []
  const abnormal = useMemo(() => results.filter((r) => r.status === 'LOW' || r.status === 'HIGH'), [results])

  if (list.loading) return <PageSkeleton cards={3} />
  if (list.error) {
    return (
      <div className="container">
        <PageHeader title="Report analysis" />
        <ErrorState title="Could not load your reports" error={list.error} onRetry={list.reload} />
      </div>
    )
  }
  const reports = list.data || []
  if (reports.length === 0) {
    return (
      <div className="container">
        <PageHeader title="Report analysis" description="Results and plain-language insights for one report." />
        <Card>
          <EmptyState
            icon={FileSearch}
            title="No reports available"
            actions={
              <>
                <Button as={Link} to="/app/upload" variant="primary" icon={UploadCloud}>
                  Upload a report
                </Button>
                <SampleDataButton onDone={list.reload} />
              </>
            }
          >
            Upload a lab report first, then come back to see every result and what it may mean.
          </EmptyState>
        </Card>
      </div>
    )
  }
  if (!id) return <Navigate to={`/app/analysis/${reports[0].id}`} replace />

  const options = reports.map((r) => ({ value: String(r.id), label: `#${r.id} - ${r.file_name} (${day(r.upload_date)})` }))
  const report = detail.data?.report
  const normal = results.filter((r) => r.status === 'NORMAL').length

  return (
    <div className="container">
      <PageHeader title="Report analysis" description="Every extracted result, plus plain-language explanations for anything outside its reference range." />

      <div className="toolbar">
        <Select label="Select a report" value={String(id)} options={options} onChange={(e) => navigate(`/app/analysis/${e.target.value}`)} />
      </div>

      {detail.loading && (
        <div className="stack mt" aria-busy="true" aria-label="Loading report">
          <Skeleton height={110} radius={12} />
          <Skeleton height={320} radius={12} />
        </div>
      )}

      {detail.error && (
        <div className="mt">
          <ErrorState
            title={detail.error.status === 404 ? 'This report no longer exists' : 'Could not load this report'}
            error={detail.error}
            onRetry={detail.error.status === 404 ? undefined : detail.reload}
          >
            {detail.error.status === 404 && (
              <Button as={Link} to="/app/analysis" variant="primary">
                Pick another report
              </Button>
            )}
          </ErrorState>
        </div>
      )}

      {report && report.processing_status !== 'Completed' && (
        <div className="mt">
          <Callout tone="warn" icon={AlertTriangle} title={`Report status: ${report.processing_status}.`}>
            {report.error_message || 'This report has no results to show yet.'}
          </Callout>
        </div>
      )}

      {report && report.processing_status === 'Completed' && (
        <>
          <div className="grid mt" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))' }}>
            <StatCard label="Tests extracted" value={results.length} icon={ListChecks} tone="info" />
            <StatCard label="Normal" value={normal} icon={CheckCircle2} />
            <StatCard label="Abnormal" value={abnormal.length} icon={AlertTriangle} tone="warn" />
            <Card className="stat">
              <div className="stat-top">
                <span className="stat-label">Report</span>
                <ReportStatusBadge status={report.processing_status} />
              </div>
              <div className="stat-value is-text break" style={{ fontSize: 17 }}>
                {report.file_name}
              </div>
              <div className="stat-foot faint">Uploaded {day(report.upload_date)}</div>
            </Card>
          </div>

          {results.length === 0 ? (
            <Card className="mt">
              <EmptyState icon={FileSearch} title="No test results were extracted">
                The file was read but no rows with a value and a unit or range were recognised.
              </EmptyState>
            </Card>
          ) : (
            <>
              <Card className="mt">
                <CardHeader
                  title="Results"
                  actions={
                    <Tabs
                      label="Result filter"
                      value={tab}
                      onChange={setTab}
                      tabs={[
                        { value: 'all', label: `All (${results.length})` },
                        { value: 'abnormal', label: `Abnormal (${abnormal.length})` },
                      ]}
                    />
                  }
                />
                <ResultsTable
                  results={tab === 'all' ? results : abnormal}
                  pageSize={15}
                  empty={
                    <EmptyState icon={CheckCircle2} title="All results are within the normal reference range">
                      Nothing in this report needs a closer look.
                    </EmptyState>
                  }
                />
              </Card>

              {abnormal.length > 0 && (
                <>
                  <h2 className="section-title">Health insights for abnormal results</h2>
                  <div className="insight-grid">
                    {abnormal.map((r) => (
                      <InsightCard key={r.id} result={r} />
                    ))}
                  </div>
                </>
              )}
            </>
          )}

          {detail.data.raw_text && (
            <Card pad className="mt">
              <details className="disclose">
                <summary>Show raw extracted text</summary>
                <pre className="rawtext">{detail.data.raw_text}</pre>
              </details>
            </Card>
          )}
        </>
      )}

      <div className="mt">
        <Disclaimer />
      </div>
    </div>
  )
}
