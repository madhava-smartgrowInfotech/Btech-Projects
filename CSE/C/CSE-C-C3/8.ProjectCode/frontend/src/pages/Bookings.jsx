import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarClock, CarFront, LogIn, LogOut, RefreshCw, Search, XCircle } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, Modal, PageHeader, Table, Tabs, useToast } from '../components/ui'
import PayActions from '../components/PayActions'
import { Api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useAsync } from '../lib/useAsync'
import { PAYMENT, STATUS, money, when } from '../lib/format'

const FILTERS = {
  all: () => true,
  upcoming: (r) => r.status === 'reserved',
  parked: (r) => r.status === 'active',
  history: (r) => !['reserved', 'active'].includes(r.status),
}

export function StatusBadge({ status }) {
  const s = STATUS[status] || { label: status, tone: 'neutral' }
  return <Badge tone={s.tone}>{s.label}</Badge>
}

export function PaymentBadge({ status }) {
  if (!status) return <span className="faint">-</span>
  const p = PAYMENT[status] || { label: status, tone: 'neutral' }
  return <Badge tone={p.tone}>{p.label}</Badge>
}

export default function Bookings() {
  const toast = useToast()
  const { refresh } = useAuth()
  const { data, error, loading, reload } = useAsync(() => Api.reservations(), [])
  const [tab, setTab] = useState('all')
  const [busyId, setBusyId] = useState(null)
  const [confirmCancel, setConfirmCancel] = useState(null)

  const rows = data || []
  const counts = useMemo(() => Object.fromEntries(Object.entries(FILTERS).map(([k, f]) => [k, rows.filter(f).length])), [rows])
  const shown = useMemo(() => rows.filter(FILTERS[tab]), [rows, tab])

  const after = async () => {
    await reload({ quiet: true })
    refresh().catch(() => {})
  }

  const act = async (r, op) => {
    setBusyId(r.id)
    try {
      const res = await Api.act(r.id, op)
      if (op === 'checkin') {
        if (res.failed) toast({ tone: 'error', title: 'Could not park you', message: res.message, duration: 9000 })
        else if (res.moved) toast({ tone: 'info', title: `Moved to ${res.alternate.name}`, message: `${res.message} Booking #${res.reservation.id} replaces #${r.id}.`, duration: 9000 })
        else toast({ tone: 'success', title: 'Checked in', message: res.message })
      } else if (op === 'checkout') {
        toast({ tone: res.on_time ? 'success' : 'error', title: res.on_time ? 'Checked out on time' : 'Late checkout recorded', message: `${res.message} Your Trust Score page shows the effect.`, duration: 8000 })
      } else {
        toast({ tone: 'success', title: `Booking #${r.id} cancelled`, message: r.payment_status === 'paid' ? `${money(r.fee)} was added to your account credit.` : 'No payment was taken.' })
      }
      await after()
    } catch (e) {
      toast({ tone: 'error', title: `Could not ${op === 'checkin' ? 'check in' : op === 'checkout' ? 'check out' : 'cancel'}`, message: e.message, duration: 8000 })
      await reload({ quiet: true })
    } finally {
      setBusyId(null)
    }
  }

  const columns = [
    { key: 'id', label: 'Booking', render: (r) => <span className="mono">#{r.id}</span>, sortValue: (r) => r.id },
    {
      key: 'location_name',
      label: 'Location',
      render: (r) => (
        <>
          <strong>{r.location_name}</strong>
          {r.parent_id && (
            <div className="faint">Alternate for #{r.parent_id}</div>
          )}
        </>
      ),
    },
    { key: 'start_time', label: 'Window', className: 'nowrap', render: (r) => (<><div>{when(r.start_time)}</div><div className="faint">to {when(r.end_time)}</div></>), sortValue: (r) => r.start_time },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <>
          <StatusBadge status={r.status} />
          {r.decline_reason && <div className="faint reason">{r.decline_reason}</div>}
        </>
      ),
    },
    { key: 'fee', label: 'Fee', num: true, render: (r) => (r.status === 'declined' ? <span className="faint">-</span> : <>{money(r.fee)} <span className="faint">x{r.fee_multiplier}</span></>) },
    { key: 'payment_status', label: 'Payment', render: (r) => <PaymentBadge status={r.payment_status} />, sortValue: (r) => r.payment_status || '' },
    {
      key: 'actions',
      label: '',
      sortable: false,
      render: (r) => (
        <div className="row" style={{ gap: 6 }}>
          {r.status === 'reserved' && (
            <>
              <Button size="sm" variant="primary" icon={LogIn} loading={busyId === r.id} onClick={() => act(r, 'checkin')}>
                Check in
              </Button>
              <Button size="sm" variant="ghost" icon={XCircle} disabled={busyId === r.id} onClick={() => setConfirmCancel(r)}>
                Cancel
              </Button>
            </>
          )}
          {r.status === 'active' && (
            <Button size="sm" variant="primary" icon={LogOut} loading={busyId === r.id} onClick={() => act(r, 'checkout')}>
              Check out
            </Button>
          )}
          {r.payment_status === 'pending' && r.status !== 'cancelled' && <PayActions size="sm" rid={r.id} provider={r.payment_provider} onPaid={after} />}
        </div>
      ),
    },
  ]

  return (
    <div className="container">
      <PageHeader
        title="My bookings"
        description="Check in when you arrive and check out before your window ends (10 minutes of grace) to keep your Trust Score growing."
        actions={
          <>
            <Button icon={RefreshCw} onClick={() => reload()} loading={loading && !!data}>
              Refresh
            </Button>
            <Button as={Link} to="/app/find" variant="primary" icon={Search}>
              Find parking
            </Button>
          </>
        }
      />
      {error ? (
        <ErrorState title="Could not load your bookings" error={error} onRetry={() => reload()} />
      ) : (
        <Card>
          <div className="card-body" style={{ paddingBottom: 0 }}>
            <Tabs
              label="Filter bookings"
              value={tab}
              onChange={setTab}
              tabs={[
                { value: 'all', label: `All (${counts.all})` },
                { value: 'upcoming', label: `Upcoming (${counts.upcoming})`, icon: CalendarClock },
                { value: 'parked', label: `Parked (${counts.parked})`, icon: CarFront },
                { value: 'history', label: `History (${counts.history})` },
              ]}
            />
          </div>
          <Table
            caption="My bookings"
            columns={columns}
            rows={shown}
            rowKey={(r) => r.id}
            loading={loading && !data}
            initialSort={{ key: 'start_time', dir: 'desc' }}
            pageSize={8}
            empty={
              <EmptyState
                icon={CalendarClock}
                title={rows.length === 0 ? 'No bookings yet' : 'Nothing in this tab'}
                actions={
                  rows.length === 0 ? (
                    <Button as={Link} to="/app/find" variant="primary" icon={Search}>
                      Find parking
                    </Button>
                  ) : (
                    <Button onClick={() => setTab('all')}>Show all bookings</Button>
                  )
                }
              >
                {rows.length === 0 ? 'Search a time window, pick a location and your reservation will appear here.' : 'Try another tab to see your other bookings.'}
              </EmptyState>
            }
          />
        </Card>
      )}

      <Modal
        open={!!confirmCancel}
        onClose={() => setConfirmCancel(null)}
        title="Cancel this booking?"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirmCancel(null)}>
              Keep booking
            </Button>
            <Button
              variant="danger"
              icon={XCircle}
              onClick={() => {
                const r = confirmCancel
                setConfirmCancel(null)
                act(r, 'cancel')
              }}
            >
              Cancel booking
            </Button>
          </>
        }
      >
        {confirmCancel && (
          <p>
            Booking <strong>#{confirmCancel.id}</strong> at <strong>{confirmCancel.location_name}</strong> ({when(confirmCancel.start_time)}).{' '}
            {confirmCancel.payment_status === 'paid' ? `The ${money(confirmCancel.fee)} you paid is added to your account credit.` : 'You have not paid yet, so nothing is charged.'}
          </p>
        )}
      </Modal>
    </div>
  )
}
