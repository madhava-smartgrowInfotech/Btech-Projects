import { Link } from 'react-router-dom'
import { BarChart3, CalendarClock, CircleDollarSign, Clock, MapPin, ParkingSquareOff, ShieldX, Users } from 'lucide-react'
import { Button, Card, CardHeader, ErrorState, PageHeader, Skeleton, StatCard } from '../../components/ui'
import { Stagger } from '../../components/motion'
import InsightsChart from '../../components/InsightsChart'
import { Api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { money } from '../../lib/format'

export default function Overview() {
  const ov = useAsync(() => Api.adminOverview(), [])
  const ins = useAsync(() => Api.adminInsights(60), [])
  const o = ov.data

  return (
    <div className="container">
      <PageHeader
        title="Admin overview"
        description="Live totals from the reservation database."
        actions={
          <>
            <Button as={Link} to="/app/admin/locations" icon={MapPin}>
              Manage locations
            </Button>
            <Button as={Link} to="/app/admin/insights" variant="primary" icon={BarChart3}>
              Strategy insights
            </Button>
          </>
        }
      />
      {ov.error ? (
        <ErrorState title="Could not load the overview" error={ov.error} onRetry={() => ov.reload()} />
      ) : (
        <Stagger className="grid grid-3">
          <StatCard label="Users" value={o?.users} icon={Users} loading={ov.loading} />
          <StatCard label="Locations" value={o?.locations} icon={MapPin} loading={ov.loading} />
          <StatCard label="Reservations" value={o?.reservations} icon={CalendarClock} loading={ov.loading} />
          <StatCard label="Revenue (paid)" value={o ? money(o.revenue) : undefined} icon={CircleDollarSign} loading={ov.loading} />
          <StatCard label="Unable to park" value={o?.unable_to_park} icon={ParkingSquareOff} tone="danger" loading={ov.loading} delta="Admitted, but no bay on arrival" />
          <StatCard label="Declined" value={o?.declined} icon={ShieldX} tone="warn" loading={ov.loading} delta="Refused by the admission rule" />
        </Stagger>
      )}

      <div className="mt">
        {ins.error ? (
          <ErrorState title="Could not load strategy insights" error={ins.error} onRetry={() => ins.reload()} />
        ) : ins.loading ? (
          <Card pad aria-busy="true" aria-label="Loading chart">
            <Skeleton width={240} height={22} />
            <Skeleton height={260} style={{ marginTop: 16 }} />
          </Card>
        ) : (
          <InsightsChart
            totals={ins.data.totals}
            actions={
              <Button as={Link} to="/app/admin/insights" size="sm" icon={Clock}>
                Last {ins.data.window_days} days - details
              </Button>
            }
          />
        )}
      </div>
    </div>
  )
}
