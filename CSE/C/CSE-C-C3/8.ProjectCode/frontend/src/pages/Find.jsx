import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowRight, CalendarClock, CheckCircle2, Clock, MapPin, ParkingSquare, Search, ShieldAlert, Wallet } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, Input, KeyValueList, Modal, PageHeader, ProgressBar, Skeleton, useToast } from '../components/ui'
import { Stagger } from '../components/motion'
import PayActions from '../components/PayActions'
import { Api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useAsync } from '../lib/useAsync'
import { defaultWindow, duration, fromLocalInput, money, when } from '../lib/format'

const MAX_DAYS = 30

function checkWindow(start, end) {
  if (!start || !end) return 'Choose both an arrival and a departure time.'
  const s = new Date(start)
  const e = new Date(end)
  if (Number.isNaN(s) || Number.isNaN(e)) return 'One of the times is not a valid date.'
  if (e <= s) return 'Departure must be after arrival.'
  if ((e - s) / 86400e3 > MAX_DAYS) return `Reservations are limited to ${MAX_DAYS} days.`
  return ''
}

export default function Find() {
  const [params] = useSearchParams()
  const initial = useMemo(() => {
    const d = defaultWindow()
    return { start: params.get('start') || d.start, end: params.get('end') || d.end }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  const [start, setStart] = useState(initial.start)
  const [end, setEnd] = useState(initial.end)
  const [formErr, setFormErr] = useState('')
  const [state, setState] = useState({ rows: null, loading: true, error: null, window: null })
  const [pick, setPick] = useState(null)
  const seq = useRef(0)
  const { user, refresh } = useAuth()
  const trust = useAsync(() => Api.trust(), [])

  const run = useCallback(async (s, e) => {
    const bad = checkWindow(s, e)
    setFormErr(bad)
    if (bad) return
    const id = ++seq.current
    setState((p) => ({ ...p, loading: true, error: null }))
    try {
      const rows = await Api.search(fromLocalInput(s), fromLocalInput(e))
      if (id === seq.current) setState({ rows, loading: false, error: null, window: { start: s, end: e } })
    } catch (err) {
      if (id === seq.current) setState({ rows: null, loading: false, error: err, window: null })
    }
  }, [])

  useEffect(() => {
    run(initial.start, initial.end)
  }, [run, initial])

  const { rows, loading, error, window: searched } = state
  const free = rows ? rows.filter((r) => r.available).length : 0

  return (
    <div className="container">
      <PageHeader title="Find parking" description="Pick when you will arrive and leave. We show how many bays can still be reserved at each location for that window." />

      <Card pad className="search-card">
        <form
          className="search-form"
          noValidate
          onSubmit={(ev) => {
            ev.preventDefault()
            run(start, end)
          }}
        >
          <Input label="Arrival" type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
          <Input label="Departure" type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} min={start} />
          <Button type="submit" variant="primary" icon={Search} loading={loading && !!rows}>
            Search availability
          </Button>
        </form>
        {formErr && (
          <p className="field-error" role="alert" style={{ marginTop: 10 }}>
            {formErr}
          </p>
        )}
      </Card>

      <div className="mt" aria-live="polite">
        {loading && !rows ? (
          <div className="grid grid-3" aria-busy="true" aria-label="Searching">
            {[0, 1, 2].map((i) => (
              <Card key={i} pad>
                <Skeleton width="60%" height={20} />
                <Skeleton width="85%" height={14} style={{ margin: '12px 0' }} />
                <Skeleton height={8} />
                <Skeleton width={110} height={38} style={{ marginTop: 18 }} />
              </Card>
            ))}
          </div>
        ) : error ? (
          <ErrorState title="Search failed" error={error} onRetry={() => run(start, end)} />
        ) : rows && rows.length === 0 ? (
          <EmptyState
            icon={ParkingSquare}
            title="No parking locations yet"
            actions={
              user?.role === 'admin' ? (
                <Button as={Link} to="/app/admin/locations" variant="primary" icon={MapPin}>
                  Add a location
                </Button>
              ) : undefined
            }
          >
            {user?.role === 'admin' ? 'Add the first location so drivers can reserve.' : 'An administrator has not added any locations yet. Check back soon.'}
          </EmptyState>
        ) : rows ? (
          <>
            <p className="muted" style={{ marginBottom: 14 }}>
              {free} of {rows.length} locations have space for <strong>{when(fromLocalInput(searched.start))}</strong> to <strong>{when(fromLocalInput(searched.end))}</strong> ({duration(fromLocalInput(searched.start), fromLocalInput(searched.end))}).
            </p>
            <Stagger className="grid grid-3" key={`${searched.start}-${searched.end}`}>
              {rows.map((loc) => (
                <LocationCard key={loc.id} loc={loc} onReserve={() => setPick(loc)} />
              ))}
            </Stagger>
          </>
        ) : null}
      </div>

      <ReserveModal
        loc={pick}
        window={searched}
        multiplier={trust.data?.fee_multiplier}
        credit={user?.account_credit ?? 0}
        onClose={() => setPick(null)}
        onChanged={() => {
          refresh().catch(() => {})
          trust.reload({ quiet: true })
          if (searched) run(searched.start, searched.end)
        }}
      />
    </div>
  )
}

function LocationCard({ loc, onReserve }) {
  const used = Math.min(loc.capacity, loc.capacity - loc.bookable)
  return (
    <Card pad className="loc-card">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ minWidth: 0 }}>
          <h3>{loc.name}</h3>
          <p className="faint">
            <MapPin size={12} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-1px' }} /> {loc.address || 'Address not listed'}
          </p>
        </div>
        <Badge tone={loc.available ? 'safe' : 'danger'} dot>
          {loc.available ? `${loc.bookable} free` : 'Full'}
        </Badge>
      </div>
      <div style={{ margin: '16px 0' }}>
        <ProgressBar value={used} max={loc.capacity} label={`${loc.capacity} bays`} valueLabel={`${used} held or reserved`} variant={loc.available ? undefined : 'risk'} />
      </div>
      <div className="loc-meta">
        <span>
          <strong>{money(loc.price_per_hour)}</strong>/hour
        </span>
        <span title="Bays held back so overstays never strand a driver">Buffer {loc.buffer_size}</span>
      </div>
      <Button variant="primary" icon={CalendarClock} disabled={!loc.available} onClick={onReserve} style={{ width: '100%', marginTop: 14 }}>
        {loc.available ? 'Reserve' : 'No space for this window'}
      </Button>
    </Card>
  )
}

function ReserveModal({ loc, window: w, multiplier, credit, onClose, onChanged }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(null)
  const [paid, setPaid] = useState(false)

  useEffect(() => {
    if (loc) {
      setError(null)
      setDone(null)
      setPaid(false)
    }
  }, [loc])

  const open = !!loc
  const startIso = w ? fromLocalInput(w.start) : null
  const endIso = w ? fromLocalInput(w.end) : null
  const hours = w ? Math.max(0.25, (new Date(endIso) - new Date(startIso)) / 3600e3) : 0
  const est = loc && multiplier ? Math.round(hours * loc.price_per_hour * multiplier * 100) / 100 : null
  const credited = est != null ? Math.min(credit, est) : 0

  const reserve = async () => {
    setBusy(true)
    setError(null)
    try {
      const r = await Api.reserve({ location_id: loc.id, start_time: startIso, end_time: endIso })
      setDone(r)
      toast({ tone: 'success', title: `Booking #${r.id} reserved`, message: `${r.location_name} for ${duration(r.start_time, r.end_time)}.` })
      onChanged()
    } catch (e) {
      setError(e)
      if (e.status === 409 || e.status === 403) onChanged()
    } finally {
      setBusy(false)
    }
  }

  const title = done ? 'Reservation confirmed' : 'Confirm reservation'
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      footer={
        done ? (
          <>
            <Button variant="ghost" onClick={onClose}>
              Keep searching
            </Button>
            <Button as={Link} to="/app/bookings" variant="primary" iconRight={ArrowRight}>
              View my bookings
            </Button>
          </>
        ) : (
          <>
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" icon={CheckCircle2} loading={busy} onClick={reserve}>
              Reserve{est != null ? ` for ${money(est)}` : ''}
            </Button>
          </>
        )
      }
    >
      {loc && w && (
        <div className="stack" style={{ gap: 16 }}>
          {done ? (
            <>
              <div className="state-inline ok" role="status">
                <CheckCircle2 size={18} aria-hidden="true" /> Booking #{done.id} at {done.location_name} is reserved.
              </div>
              <KeyValueList
                items={[
                  ['Window', `${when(done.start_time)} - ${when(done.end_time)}`],
                  ['Fee', `${money(done.fee)} (x${done.fee_multiplier} trust multiplier)`],
                  done.credit_applied > 0 && ['Account credit used', money(done.credit_applied)],
                  ['Amount due', done.amount_due > 0 ? money(done.amount_due) : 'Nothing - covered by credit'],
                ]}
              />
              {done.amount_due > 0 && !paid && (
                <div>
                  {!done.stripe_configured && <p className="faint" style={{ marginBottom: 10 }}>Stripe keys are not set on this server, so payment uses the built-in demo checkout.</p>}
                  <PayActions rid={done.id} amount={done.amount_due} provider={done.checkout?.provider} url={done.checkout?.url} onPaid={() => { setPaid(true); onChanged() }} />
                </div>
              )}
              {paid && (
                <div className="state-inline ok" role="status">
                  <CheckCircle2 size={18} aria-hidden="true" /> Payment confirmed.
                </div>
              )}
              <p className="faint">Check in from My bookings when you arrive, and check out on time to grow your Trust Score.</p>
            </>
          ) : (
            <>
              <KeyValueList
                items={[
                  ['Location', loc.name],
                  ['Arrival', when(startIso)],
                  ['Departure', when(endIso)],
                  ['Duration', duration(startIso, endIso)],
                  ['Rate', `${money(loc.price_per_hour)}/hour`],
                  multiplier && ['Your trust multiplier', `x${multiplier}`],
                  est != null && ['Estimated fee', money(est)],
                  credit > 0 && est != null && ['Account credit applied', `${money(credited)} of ${money(credit)}`],
                ]}
              />
              <p className="faint">
                <Clock size={12} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-1px' }} /> The server calculates the final fee when you reserve; the figure above uses the same formula.
                {credit > 0 && (
                  <>
                    {' '}
                    <Wallet size={12} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-1px' }} /> Credit is used automatically.
                  </>
                )}
              </p>
              {error && (
                <div className="state-inline bad" role="alert">
                  <ShieldAlert size={18} aria-hidden="true" />
                  <div>
                    <strong>{error.status === 409 ? 'No space for that window' : error.status === 403 ? 'Booking is paused' : 'Could not reserve'}</strong>
                    <div>{error.message}</div>
                    <div className="faint">{error.status === 409 ? 'Close this and try another time or location.' : error.status === 403 ? 'Your Trust Score page shows when you can book again.' : 'Check the details and try again.'}</div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </Modal>
  )
}
