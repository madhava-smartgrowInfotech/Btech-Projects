import { Link, useNavigate } from 'react-router-dom'
import { ChevronRight, Plus, ShieldCheck, Ticket } from 'lucide-react'
import api from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Badge } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'
import { SEVERITY_TONE, STATUS_TONE, statusLabel } from '../format'
import useApi from '../lib/useApi'

export default function MyTokens() {
  const nav = useNavigate()
  const data = useApi(
    () => Promise.all([api.get('/bookings/mine'), api.get('/referrals')]).then(([b, r]) => ({
      bookings: b.data,
      pending: r.data.filter((x) => x.status === 'pending_consent').length,
    })),
    [],
  )
  const { bookings, pending } = data.data || {}

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="patient"
        title="My tokens"
        subtitle="Every visit you have booked. Open a token for its live position and estimated wait."
        actions={
          <Button icon={Plus} onClick={() => nav('/book')}>
            New booking
          </Button>
        }
      />

      {pending > 0 && (
        <Link to="/referrals" className="mb-5 flex items-center gap-3 rounded-[6px] border border-warn/40 bg-warn/10 p-4 text-sm text-fg hover:border-warn">
          <ShieldCheck size={18} className="shrink-0 text-warn" aria-hidden="true" />
          <span className="flex-1">
            {pending} referral{pending > 1 ? 's are' : ' is'} waiting for your consent to share your summary.
          </span>
          <ChevronRight size={16} className="text-warn" aria-hidden="true" />
        </Link>
      )}

      {data.error && <ErrorState error={data.error} onRetry={data.reload} />}
      {!bookings && !data.error && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      )}
      {bookings?.length === 0 && (
        <EmptyState
          icon={Ticket}
          title="No tokens yet"
          body="Describe your symptoms and we will suggest a hospital and a visit date."
          action={<Button onClick={() => nav('/book')}>Book a visit</Button>}
        />
      )}

      <ul className="space-y-3">
        {bookings?.map((b) => (
          <li key={b.id}>
            <Link to={`/tokens/${b.id}`} className="panel-link flex items-center gap-4 p-4">
              <div className="w-16 shrink-0 text-center">
                <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-dim">Token</div>
                <div className="font-mono text-2xl font-semibold text-ok tabular-nums">{b.token}</div>
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate font-medium text-fg">{b.hospital}</div>
                <div className="mt-0.5 font-mono text-[11px] text-muted">
                  {b.date}
                  {b.moved && <span className="text-warn"> - moved from {b.requested_date}</span>}
                  {b.referral_id && <span className="text-cyan"> - referral</span>}
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <Badge tone={SEVERITY_TONE[b.severity]}>{b.severity}</Badge>
                  <Badge tone={STATUS_TONE[b.status]}>{statusLabel(b.status)}</Badge>
                  {b.status === 'waiting' && <span className="font-mono text-[11px] text-muted">#{b.position} - ~{b.wait_min} min</span>}
                </div>
              </div>
              <ChevronRight size={16} className="shrink-0 text-dim" aria-hidden="true" />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
