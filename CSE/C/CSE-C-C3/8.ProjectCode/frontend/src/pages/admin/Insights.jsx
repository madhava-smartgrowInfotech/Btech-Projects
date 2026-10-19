import { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { Button, Card, CardHeader, EmptyState, ErrorState, KeyValueList, PageHeader, Select, Skeleton, Table } from '../../components/ui'
import { SlideUp } from '../../components/motion'
import InsightsChart from '../../components/InsightsChart'
import { Api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { STRATEGY_LABEL } from '../../lib/format'

const WINDOWS = [7, 30, 60, 90].map((d) => ({ value: d, label: `Last ${d} days` }))

export default function Insights() {
  const [days, setDays] = useState(60)
  const { data, error, loading, reload } = useAsync(() => Api.adminInsights(days), [days])

  const columns = [
    { key: 'location', label: 'Location', render: (r) => <strong>{r.location}</strong> },
    { key: 'capacity', label: 'Bays', num: true },
    { key: 'current_buffer', label: 'Buffer now', num: true },
    { key: 'requests', label: 'Requests', num: true },
    { key: 'a_unable', label: 'Actual unable', num: true, render: (r) => r.actual.unable_to_park, sortValue: (r) => r.actual.unable_to_park },
    { key: 'a_declined', label: 'Actual declined', num: true, render: (r) => r.actual.declined, sortValue: (r) => r.actual.declined },
    { key: 's_unable', label: 'Dynamic unable', num: true, render: (r) => r.simulated.dynamic.unable_to_park, sortValue: (r) => r.simulated.dynamic.unable_to_park },
    { key: 's_declined', label: 'Dynamic declined', num: true, render: (r) => r.simulated.dynamic.declined, sortValue: (r) => r.simulated.dynamic.declined },
  ]

  return (
    <div className="container">
      <PageHeader
        title="Strategy insights"
        description="Computed from stored booking history by a deterministic replay - the same input always gives the same numbers."
        actions={
          <>
            <Select labelHidden label="Time window" value={days} onChange={(e) => setDays(Number(e.target.value))} options={WINDOWS} />
            <Button variant="primary" icon={RefreshCw} loading={loading && !!data} onClick={() => reload()}>
              Recompute
            </Button>
          </>
        }
      />
      {error ? (
        <ErrorState title="Could not compute insights" error={error} onRetry={() => reload()} />
      ) : loading && !data ? (
        <Card pad aria-busy="true" aria-label="Computing insights">
          <Skeleton width={240} height={22} />
          <Skeleton height={260} style={{ margin: '16px 0' }} />
          <Skeleton height={20} />
        </Card>
      ) : (
        <div className="stack">
          <SlideUp>
            <InsightsChart totals={data.totals} />
          </SlideUp>
          <SlideUp inView>
            <Card>
              <CardHeader title="Per location" subtitle="Actual outcomes versus the dynamic policy replayed on the same requests" />
              <Table
                caption="Strategy insights per location"
                columns={columns}
                rows={data.per_location}
                rowKey={(r) => r.location_id}
                pageSize={10}
                empty={<EmptyState title="No bookings in this window">Reservations made in the last {data.window_days} days appear here once they exist.</EmptyState>}
              />
            </Card>
          </SlideUp>
          <SlideUp inView>
            <Card>
              <CardHeader title="Policy and totals" />
              <div className="card-body stack" style={{ gap: 14 }}>
                <KeyValueList
                  items={[
                    ['Window', `${data.window_days} days`],
                    ['Buffer start', data.policy.init],
                    ['Buffer maximum', data.policy.max],
                    ['Buffer reset', `every ${data.policy.reset_hours} h`],
                    ...Object.keys(STRATEGY_LABEL).map((k) => [STRATEGY_LABEL[k], `${data.totals[k].unable_to_park} unable to park, ${data.totals[k].declined} declined`]),
                  ]}
                />
                <p className="faint">{data.note}</p>
              </div>
            </Card>
          </SlideUp>
        </div>
      )}
    </div>
  )
}
