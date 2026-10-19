import { useMemo, useState } from 'react'
import { ListChecks, RefreshCw } from 'lucide-react'
import { Button, Card, EmptyState, ErrorState, PageHeader, SearchField, Select, Table } from '../../components/ui'
import { Api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { STATUS, money, when } from '../../lib/format'
import { PaymentBadge, StatusBadge } from '../Bookings'

const STATUS_OPTIONS = [{ value: '', label: 'All statuses' }, ...Object.entries(STATUS).map(([value, s]) => ({ value, label: s.label }))]

export default function AdminBookings() {
  const { data, error, loading, reload } = useAsync(() => Api.adminBookings(), [])
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (data || []).filter((r) => (!status || r.status === status) && (!needle || `${r.id} ${r.location_name}`.toLowerCase().includes(needle)))
  }, [data, q, status])

  const columns = [
    { key: 'id', label: 'Booking', render: (r) => <span className="mono">#{r.id}</span>, sortValue: (r) => r.id },
    { key: 'location_name', label: 'Location', render: (r) => (<>{r.location_name}{r.parent_id && <div className="faint">Alternate for #{r.parent_id}</div>}</>) },
    { key: 'start_time', label: 'Window', className: 'nowrap', render: (r) => (<><div>{when(r.start_time)}</div><div className="faint">to {when(r.end_time)}</div></>), sortValue: (r) => r.start_time },
    { key: 'status', label: 'Status', render: (r) => (<><StatusBadge status={r.status} />{r.decline_reason && <div className="faint reason">{r.decline_reason}</div>}</>) },
    { key: 'fee', label: 'Fee', num: true, render: (r) => (r.status === 'declined' ? <span className="faint">-</span> : money(r.fee)) },
    { key: 'payment_status', label: 'Payment', render: (r) => <PaymentBadge status={r.payment_status} />, sortValue: (r) => r.payment_status || '' },
  ]

  return (
    <div className="container">
      <PageHeader
        title="All bookings"
        description="The 300 most recent reservations across every driver."
        actions={
          <Button icon={RefreshCw} onClick={() => reload()} loading={loading && !!data}>
            Refresh
          </Button>
        }
      />
      {error ? (
        <ErrorState title="Could not load bookings" error={error} onRetry={() => reload()} />
      ) : (
        <Card>
          <div className="card-body filters">
            <SearchField value={q} onChange={setQ} label="Search bookings" placeholder="Search by booking number or location" />
            <Select labelHidden label="Filter by status" value={status} onChange={(e) => setStatus(e.target.value)} options={STATUS_OPTIONS} />
          </div>
          <Table
            caption="All bookings"
            columns={columns}
            rows={rows}
            rowKey={(r) => r.id}
            loading={loading && !data}
            initialSort={{ key: 'start_time', dir: 'desc' }}
            pageSize={12}
            empty={
              <EmptyState icon={ListChecks} title={data?.length ? 'No bookings match' : 'No bookings yet'} actions={data?.length ? <Button onClick={() => { setQ(''); setStatus('') }}>Clear filters</Button> : undefined}>
                {data?.length ? 'Try a different search or status.' : 'Reservations from drivers appear here.'}
              </EmptyState>
            }
          />
        </Card>
      )}
    </div>
  )
}
