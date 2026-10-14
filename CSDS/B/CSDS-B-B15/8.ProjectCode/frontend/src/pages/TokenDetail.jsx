import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ArrowLeft, CalendarClock } from 'lucide-react'
import api, { describeError } from '../api'
import { useAuth } from '../auth'
import useQueueSocket from '../components/useQueueSocket'
import { PageHeader } from '../components/ui/AppShell'
import { Badge, KeyValueList, StatCard, StatusDot } from '../components/ui/display'
import { ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import { SEVERITY_TONE, STATUS_TONE, statusLabel } from '../format'

const MESSAGE = {
  called: 'You are being called now. Please proceed to the consultation room.',
  done: 'Consultation completed.',
  no_show: 'Marked as not attended. Please book again if you still need a visit.',
  referred: 'You were referred to another hospital - see Referrals.',
}

export default function TokenDetail() {
  const { id } = useParams()
  const { state } = useLocation()
  const { user } = useAuth()
  const toast = useToast()
  const [b, setB] = useState(state?.justBooked || null)
  const [error, setError] = useState(null)
  const prev = useRef(null)

  const load = useCallback(() => {
    api
      .get(`/bookings/${id}`)
      .then((r) => {
        const p = prev.current
        if (p && r.data.status === 'called' && p.status !== 'called') {
          toast({ tone: 'ok', title: "It's your turn", body: 'Please go to the consultation room.' })
        } else if (p && p.position && r.data.position && r.data.position !== p.position) {
          const up = r.data.position < p.position
          toast({ tone: up ? 'ok' : 'warn', title: up ? 'You moved up the queue' : 'An urgent case was placed ahead of you' })
        }
        prev.current = r.data
        setB(r.data)
        setError(null)
      })
      .catch((e) => setError(describeError(e)))
  }, [id, toast])

  useEffect(() => {
    load()
  }, [load])
  const live = useQueueSocket(b?.hospital_id, load)

  const back = user.role === 'patient' ? '/tokens' : '/console'

  if (!b) {
    return error ? (
      <div className="mx-auto max-w-2xl">
        <ErrorState error={error} onRetry={load} />
      </div>
    ) : (
      <div className="mx-auto max-w-2xl space-y-4">
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  const waiting = b.status === 'waiting'
  const justBooked = state?.justBooked?.allocation

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <Link to={back} className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-[0.12em] text-muted hover:text-ok">
        <ArrowLeft size={14} aria-hidden="true" /> {user.role === 'patient' ? 'My tokens' : 'Hospital console'}
      </Link>

      {error && <ErrorState error={error} onRetry={load} />}

      {justBooked && (
        <div
          className="flex items-center gap-2 rounded-[6px] border p-3 text-sm text-fg"
          style={{
            borderColor: state.justBooked.moved ? 'var(--warn)' : 'var(--ok)',
            background: `color-mix(in oklab, ${state.justBooked.moved ? 'var(--warn)' : 'var(--ok)'} 9%, var(--panel))`,
          }}
        >
          <CalendarClock size={16} className={state.justBooked.moved ? 'text-warn' : 'text-ok'} aria-hidden="true" />
          Booked: {state.justBooked.allocation}
        </div>
      )}

      <section className="panel scan overflow-hidden">
        <div className="relative z-[1] border-b border-line px-6 py-8 text-center">
          <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-dim">Your token</div>
          <div className="mt-1 font-mono text-7xl font-semibold tabular-nums tracking-tight text-ok">{b.token}</div>
          <div className="mt-2 text-sm text-fg">{b.hospital}</div>
          <div className="font-mono text-[11px] text-muted">
            {b.date}
            {b.moved && ` - moved from ${b.requested_date} because that day was full`}
          </div>
        </div>

        <div className="relative z-[1] space-y-5 p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Badge tone={STATUS_TONE[b.status]} dot>
              {statusLabel(b.status)}
            </Badge>
            <StatusDot tone={live ? 'ok' : 'warn'} label={live ? 'live' : 'reconnecting'} blink={live} />
          </div>

          {waiting ? (
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Position" value={b.position} sub={`${b.ahead} ahead of you`} />
              <StatCard label="Est. wait" value={b.wait_min} format={(v) => `${Math.round(v)} min`} sub={`around ${b.eta?.slice(11, 16)}`} />
            </div>
          ) : (
            <p className="text-sm text-muted">{MESSAGE[b.status]}</p>
          )}

          <KeyValueList
            items={[
              ['Severity', <Badge key="s" tone={SEVERITY_TONE[b.severity]}>{b.severity}</Badge>],
              ['Department', b.specialty || '-'],
              ['Symptoms', b.symptoms?.length ? b.symptoms.join(', ') : '-'],
            ]}
          />

          {waiting && (
            <p className="text-xs text-muted">
              The wait estimate uses today&apos;s actual consultation times and the chance that patients ahead do not turn up. Urgent cases may be
              seen first.
            </p>
          )}
          {b.severity === 'critical' && (
            <p className="rounded-[4px] border border-alert/40 bg-alert/10 p-2 text-xs text-fg">
              Critical: if your symptoms get worse, call <b>108</b> or go to the nearest emergency department now.
            </p>
          )}
          <p className="border-l-2 border-line-strong pl-3 text-xs text-muted">
            Decision support only - this is not a diagnosis. A qualified clinician confirms severity at the hospital. In an emergency call 108.
          </p>
        </div>
      </section>
    </div>
  )
}
