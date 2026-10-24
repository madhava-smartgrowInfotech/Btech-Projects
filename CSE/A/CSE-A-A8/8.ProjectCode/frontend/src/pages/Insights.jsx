import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Lightbulb, PartyPopper, UploadCloud } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { Button, Card, EmptyState, ErrorState, PageHeader, SearchField, Tabs } from '../components/ui'
import { Disclaimer, InsightCard, PageSkeleton, SampleDataButton } from '../components/lab'

export default function Insights() {
  const { data, error, loading, reload } = useAsync(() => api.insights(), [])
  const reports = useAsync(() => api.reports(), [])
  const [tab, setTab] = useState('all')
  const [query, setQuery] = useState('')

  const items = data || []
  const shown = useMemo(() => {
    const q = query.trim().toLowerCase()
    return items.filter((r) => (tab === 'all' || r.status === tab.toUpperCase()) && (!q || r.test_name.toLowerCase().includes(q) || (r.file_name || '').toLowerCase().includes(q)))
  }, [items, tab, query])

  if (loading || reports.loading) return <PageSkeleton cards={0} />
  if (error) {
    return (
      <div className="container">
        <PageHeader title="Health insights" />
        <ErrorState title="Could not load insights" error={error} onRetry={reload} />
      </div>
    )
  }

  const noReports = (reports.data || []).length === 0
  const low = items.filter((r) => r.status === 'LOW').length
  const high = items.filter((r) => r.status === 'HIGH').length

  return (
    <div className="container">
      <PageHeader title="Health insights" description="A consolidated view of the explanations for every abnormal result on file." />

      {items.length === 0 ? (
        <Card>
          {noReports ? (
            <EmptyState
              icon={Lightbulb}
              title="No reports yet, so no insights"
              actions={
                <>
                  <Button as={Link} to="/app/upload" variant="primary" icon={UploadCloud}>
                    Upload a report
                  </Button>
                  <SampleDataButton onDone={() => { reload(); reports.reload() }} />
                </>
              }
            >
              Insights are written for results that fall outside their reference range.
            </EmptyState>
          ) : (
            <EmptyState icon={PartyPopper} title="No abnormal results on file">
              Every result in your reports is within its reference range.
            </EmptyState>
          )}
        </Card>
      ) : (
        <>
          <div className="toolbar" style={{ justifyContent: 'space-between' }}>
            <Tabs
              label="Status filter"
              value={tab}
              onChange={setTab}
              tabs={[
                { value: 'all', label: `All (${items.length})` },
                { value: 'low', label: `Low (${low})` },
                { value: 'high', label: `High (${high})` },
              ]}
            />
            <SearchField value={query} onChange={setQuery} label="Search insights" placeholder="Search test or report…" />
          </div>
          {shown.length === 0 ? (
            <Card className="mt">
              <EmptyState title="No insights match your filter" actions={<Button onClick={() => { setTab('all'); setQuery('') }}>Reset filters</Button>}>
                Try another status or search term.
              </EmptyState>
            </Card>
          ) : (
            <div className="insight-grid mt">
              {shown.map((r) => (
                <InsightCard key={r.id} result={r} />
              ))}
            </div>
          )}
        </>
      )}

      <div className="mt">
        <Disclaimer />
      </div>
    </div>
  )
}
