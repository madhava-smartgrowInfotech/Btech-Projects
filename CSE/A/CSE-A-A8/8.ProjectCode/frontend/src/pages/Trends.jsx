import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowDownRight, ArrowRight, ArrowUpRight, TrendingUp, UploadCloud } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { day, shortDay, value } from '../lib/format'
import { Button, Card, CardHeader, EmptyState, ErrorState, PageHeader, Select, Skeleton, Table } from '../components/ui'
import { ChartCard, TrendChart } from '../components/charts'
import { Callout, Disclaimer, PageSkeleton, SampleDataButton, StatusBadge } from '../components/lab'

const DIRECTION = {
  increasing: { label: 'Increasing', icon: ArrowUpRight },
  decreasing: { label: 'Decreasing', icon: ArrowDownRight },
  stable: { label: 'Stable', icon: ArrowRight },
}

export default function Trends() {
  const tests = useAsync(() => api.tests(), [])
  const [test, setTest] = useState('')
  const names = tests.data || []

  useEffect(() => {
    if (!test && names.length) setTest(names.includes('Hemoglobin') ? 'Hemoglobin' : names[0])
  }, [names, test])

  const trend = useAsync(() => api.trends(test), [test], { enabled: !!test })

  if (tests.loading) return <PageSkeleton cards={0} />
  if (tests.error) {
    return (
      <div className="container">
        <PageHeader title="Health trends" />
        <ErrorState title="Could not load your tests" error={tests.error} onRetry={tests.reload} />
      </div>
    )
  }
  if (names.length === 0) {
    return (
      <div className="container">
        <PageHeader title="Health trends" description="Follow a single test across every report you have uploaded." />
        <Card>
          <EmptyState
            icon={TrendingUp}
            title="No test history yet"
            actions={
              <>
                <Button as={Link} to="/app/upload" variant="primary" icon={UploadCloud}>
                  Upload a report
                </Button>
                <SampleDataButton onDone={tests.reload} />
              </>
            }
          >
            Upload at least one report to start tracking results over time.
          </EmptyState>
        </Card>
      </div>
    )
  }

  const points = trend.data?.points || []
  const unit = points.find((p) => p.unit)?.unit || ''
  const chartData = points.map((p) => ({ date: p.date, value: p.value, low: p.reference_low, high: p.reference_high, status: p.status }))
  const dir = trend.data?.direction ? DIRECTION[trend.data.direction] : null

  const columns = [
    { key: 'date', label: 'Date', render: (p) => day(p.date), sortValue: (p) => p.date },
    { key: 'value', label: 'Result', num: true, render: (p) => <span className="val">{value(p.value)} <span className="faint">{p.unit}</span></span> },
    { key: 'reference_low', label: 'Reference low', num: true, render: (p) => value(p.reference_low) },
    { key: 'reference_high', label: 'Reference high', num: true, render: (p) => value(p.reference_high) },
    { key: 'status', label: 'Status', render: (p) => <StatusBadge status={p.status} /> },
    { key: 'file_name', label: 'Report', hideSm: true, render: (p) => <Link to={`/app/analysis/${p.report_id}`} className="break">{p.file_name}</Link> },
  ]

  return (
    <div className="container">
      <PageHeader title="Health trends" description="Follow a single test across every report you have uploaded." />

      <div className="toolbar">
        <Select label="Select a test to view its trend" value={test} options={names.map((n) => ({ value: n, label: n }))} onChange={(e) => setTest(e.target.value)} />
      </div>

      {trend.error && (
        <div className="mt">
          <ErrorState title="Could not load this trend" error={trend.error} onRetry={trend.reload} />
        </div>
      )}

      {trend.loading && !trend.error && <Skeleton height={360} radius={12} style={{ marginTop: 18 }} />}

      {trend.data && (
        <>
          <div className="mt">
            <ChartCard
              title={`${test} over time`}
              subtitle={points.length > 1 ? `${points.length} reports${unit ? ` · ${unit}` : ''} · shaded band is the reference range` : `1 report${unit ? ` · ${unit}` : ''}`}
              height={320}
            >
              {points.length ? <TrendChart data={chartData} name={test} unit={unit} valueFormat={value} labelFormat={shortDay} /> : null}
            </ChartCard>
          </div>

          <div className="stack mt">
            {dir ? (
              <Callout tone="info" icon={dir.icon} title="Overall pattern across your uploaded reports:">
                <span className="dir">{dir.label}</span>. This reflects the trend across the reports you have uploaded only, and is not a medical conclusion. Please discuss any trend with a healthcare professional.
              </Callout>
            ) : (
              <Callout tone="info" icon={TrendingUp}>
                Only one result is on file for {test}. Upload another report that includes it to see a trend.
              </Callout>
            )}
            <Card>
              <CardHeader title="All results" subtitle={`${points.length} value${points.length === 1 ? '' : 's'} for ${test}`} />
              <Table columns={columns} rows={points} rowKey={(p) => `${p.report_id}`} initialSort={{ key: 'date', dir: 'desc' }} pageSize={10} caption={`${test} results by report`} />
            </Card>
          </div>
        </>
      )}

      <div className="mt">
        <Disclaimer />
      </div>
    </div>
  )
}
