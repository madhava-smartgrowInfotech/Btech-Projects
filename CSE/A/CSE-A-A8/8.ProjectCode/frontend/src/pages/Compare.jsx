import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowDown, ArrowUp, GitCompareArrows, Minus, UploadCloud } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { day, value } from '../lib/format'
import { Button, Card, CardHeader, EmptyState, ErrorState, PageHeader, Select, Skeleton, Table, Tabs } from '../components/ui'
import { ChartCard, GroupedBarChart } from '../components/charts'
import { Callout, Disclaimer, PageSkeleton, SampleDataButton, StatusBadge } from '../components/lab'

function Change({ row }) {
  if (row.change === null || row.change === undefined) return <span className="faint">-</span>
  if (row.change === 0)
    return (
      <span className="delta-flat chg">
        <Minus size={13} aria-hidden="true" /> 0
      </span>
    )
  const up = row.change > 0
  return (
    <span className={`${up ? 'delta-up' : 'delta-down'} chg`} style={{ fontWeight: 600 }}>
      {up ? <ArrowUp size={13} aria-hidden="true" /> : <ArrowDown size={13} aria-hidden="true" />} {up ? '+' : ''}
      {value(row.change)}
    </span>
  )
}

export default function Compare() {
  const list = useAsync(() => api.reports(), [])
  const completed = useMemo(() => (list.data || []).filter((r) => r.processing_status === 'Completed'), [list.data])
  // Same defaults as the original page: Report 1 = second newest, Report 2 = newest
  const [a, setA] = useState('')
  const [b, setB] = useState('')
  const [unitTab, setUnitTab] = useState('')

  useEffect(() => {
    if (completed.length >= 2 && !a && !b) {
      setA(String(completed[1].id))
      setB(String(completed[0].id))
    }
  }, [completed, a, b])

  const same = a && b && a === b
  const cmp = useAsync(() => api.compare(a, b), [a, b], { enabled: !!a && !!b && !same })
  const rows = cmp.data?.rows || []

  const units = useMemo(() => [...new Set(rows.map((r) => r.unit || 'no unit'))], [rows])
  useEffect(() => {
    if (units.length && !units.includes(unitTab)) setUnitTab(units[0])
  }, [units, unitTab])

  if (list.loading) return <PageSkeleton cards={0} />
  if (list.error) {
    return (
      <div className="container">
        <PageHeader title="Compare reports" />
        <ErrorState title="Could not load your reports" error={list.error} onRetry={list.reload} />
      </div>
    )
  }
  if (completed.length < 2) {
    return (
      <div className="container">
        <PageHeader title="Compare reports" description="Put two reports side by side and see what changed." />
        <Card>
          <EmptyState
            icon={GitCompareArrows}
            title="You need at least two completed reports to compare"
            actions={
              <>
                <Button as={Link} to="/app/upload" variant="primary" icon={UploadCloud}>
                  Upload a report
                </Button>
                {(list.data || []).length === 0 && <SampleDataButton onDone={list.reload} />}
              </>
            }
          >
            {completed.length === 1 ? 'One completed report is on file. Upload one more.' : 'No completed reports are on file yet.'}
          </EmptyState>
        </Card>
      </div>
    )
  }

  const options = completed.map((r) => ({ value: String(r.id), label: `#${r.id} - ${r.file_name} (${day(r.upload_date)})` }))
  const nameA = cmp.data ? `#${cmp.data.report_a.id}` : 'Report 1'
  const nameB = cmp.data ? `#${cmp.data.report_b.id}` : 'Report 2'
  const chartRows = rows.filter((r) => (r.unit || 'no unit') === unitTab && r.a !== null && r.b !== null).map((r) => ({ test: r.test, a: r.a, b: r.b }))

  const columns = [
    { key: 'test', label: 'Test', render: (r) => <strong>{r.test}</strong> },
    { key: 'a', label: `Report 1 (${nameA})`, num: true, render: (r) => <span className="val">{value(r.a)} <StatusBadge status={r.status_a} /></span> },
    { key: 'b', label: `Report 2 (${nameB})`, num: true, render: (r) => <span className="val">{value(r.b)} <StatusBadge status={r.status_b} /></span> },
    { key: 'unit', label: 'Unit', render: (r) => <span className="faint">{r.unit}</span>, hideSm: true },
    { key: 'change', label: 'Change', num: true, render: (r) => <Change row={r} />, sortValue: (r) => r.change },
  ]

  return (
    <div className="container">
      <PageHeader title="Compare reports" description="Put two reports side by side. Change is Report 2 minus Report 1." />

      <div className="toolbar">
        <Select label="Report 1" value={a} options={options} onChange={(e) => setA(e.target.value)} />
        <Select label="Report 2" value={b} options={options} onChange={(e) => setB(e.target.value)} />
      </div>

      {same && (
        <div className="mt">
          <Callout tone="warn" icon={AlertTriangle}>
            Please select two different reports.
          </Callout>
        </div>
      )}

      {cmp.error && !same && (
        <div className="mt">
          <ErrorState title="Could not compare these reports" error={cmp.error} onRetry={cmp.reload} />
        </div>
      )}

      {cmp.loading && !cmp.error && !same && <Skeleton height={320} radius={12} style={{ marginTop: 18 }} />}

      {cmp.data && !same && rows.length === 0 && (
        <Card className="mt">
          <EmptyState icon={GitCompareArrows} title="These two reports have no lab tests in common">
            Pick reports that include the same tests, for example two health check-ups.
          </EmptyState>
        </Card>
      )}

      {cmp.data && !same && rows.length > 0 && (
        <div className="stack mt">
          <Card>
            <CardHeader title="Tests in common" subtitle={`${rows.length} tests appear in both reports`} />
            <Table columns={columns} rows={rows} rowKey={(r) => r.test} pageSize={15} caption="Comparison of tests present in both reports" />
          </Card>
          <ChartCard
            title="Report 1 vs Report 2"
            subtitle="Tests are grouped by unit so each chart has one comparable scale"
            height={300}
            actions={units.length > 1 ? <Tabs label="Unit" value={unitTab} onChange={setUnitTab} tabs={units.map((u) => ({ value: u, label: u }))} /> : <span className="faint">{units[0]}</span>}
          >
            {chartRows.length ? (
              <GroupedBarChart
                data={chartRows}
                xKey="test"
                series={[
                  { key: 'a', label: `Report 1 (${nameA})` },
                  { key: 'b', label: `Report 2 (${nameB})` },
                ]}
                yDomain={[0, 'auto']}
                valueFormat={value}
              />
            ) : (
              <p className="muted">No numeric values to chart for this unit.</p>
            )}
          </ChartCard>
        </div>
      )}

      <div className="mt">
        <Disclaimer />
      </div>
    </div>
  )
}
