import { lazy, Suspense } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, ArrowRight, Building2, Clock, GitBranch, LayoutDashboard, ShieldAlert, Stethoscope } from 'lucide-react'
import api from '../api'
import { homeFor, useAuth } from '../auth'
import { MagneticButton, Reveal, SlideUp, Stagger } from '../components/motion'
import { Button } from '../components/ui/controls'
import { Card, StatCard } from '../components/ui/display'
import { ErrorState, Skeleton } from '../components/ui/feedback'
import Typewriter from '../components/ui/Typewriter'
import useApi from '../lib/useApi'

// three.js grid: loaded only on this page
const Backdrop = lazy(() => import('../components/reactbits/Backdrop'))

const FEATURES = [
  [Stethoscope, 'Severity triage', 'Pick or describe symptoms. A trained symptom model, severity weights and red-flag rules grade them mild to critical.'],
  [Building2, 'District network', 'Hyderabad hospitals from OpenStreetMap, ranked by severity, distance, specialty and free slots.'],
  [Clock, 'Live queue', 'Your token, position and estimated wait update in real time as patients are called or emergencies arrive.'],
  [ShieldAlert, 'Limits and quotas', 'Daily OP limits, emergency quotas and no-show-aware overbooking. Full days roll over automatically.'],
  [GitBranch, 'Referrals', 'Doctors refer patients to another hospital with a summary shared only after the patient consents.'],
  [LayoutDashboard, 'District dashboard', 'Load, waiting times and severity mix across every hospital at a glance.'],
]

export default function Landing() {
  const { user } = useAuth()
  const nav = useNavigate()
  const hospitals = useApi(() => api.get('/hospitals').then((r) => r.data), [])
  const h = hospitals.data
  const totals = h && {
    hospitals: h.length,
    capacity: h.reduce((s, x) => s + x.op_limit, 0),
    booked: h.reduce((s, x) => s + x.booked, 0),
    emergency: h.filter((x) => x.has_emergency).length,
  }

  return (
    <div className="space-y-10">
      <section className="relative isolate overflow-hidden rounded-[6px] border border-line bg-panel px-6 py-14 sm:px-12 sm:py-20">
        <div className="absolute inset-0 -z-10">
          <Suspense fallback={null}>
            <Backdrop />
          </Suspense>
        </div>
        <div className="relative z-[1] max-w-2xl">
          <SlideUp>
            <div className="inline-flex items-center gap-2 rounded-[4px] border border-line-strong bg-bg/60 px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.14em] text-muted">
              <Activity size={13} className="text-ok" aria-hidden="true" /> Outpatient booking - Hyderabad district
            </div>
          </SlideUp>
          <Typewriter as="h1" text="See the right doctor sooner, without the queue." speed={22} className="mt-6 block font-mono text-3xl font-semibold leading-tight tracking-tight text-fg sm:text-5xl" />
          <SlideUp delay={0.25}>
            <p className="mt-5 max-w-xl text-base text-muted">
              MediQueue grades how urgent your symptoms are, suggests the hospitals that can see you, and shows your live place in line - from your phone.
            </p>
          </SlideUp>
          <SlideUp delay={0.35}>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <MagneticButton>
                <Button size="lg" icon={ArrowRight} onClick={() => nav(user ? homeFor(user) : '/login')}>
                  {user ? 'Open MediQueue' : 'Book a visit'}
                </Button>
              </MagneticButton>
              {!user && (
                <Button size="lg" variant="secondary" onClick={() => nav('/login?role=staff')}>
                  Hospital staff login
                </Button>
              )}
            </div>
          </SlideUp>
        </div>
      </section>

      <section aria-labelledby="live-heading">
        <h2 id="live-heading" className="mb-3 font-mono text-[11px] uppercase tracking-[0.14em] text-dim">
          Live from the district network
        </h2>
        {hospitals.error ? (
          <ErrorState compact title="Live counters unavailable" error={hospitals.error} onRetry={hospitals.reload} />
        ) : !totals ? (
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-28" />
            ))}
          </div>
        ) : (
          <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4" gap={0.08}>
            <StatCard live label="Hospitals" value={totals.hospitals} icon={Building2} sub="across Hyderabad" />
            <StatCard label="OP slots / day" value={totals.capacity} icon={Clock} sub="sum of daily limits" />
            <StatCard label="Booked today" value={totals.booked} icon={Stethoscope} sub="OP bookings so far" />
            <StatCard label="Emergency-ready" value={totals.emergency} icon={ShieldAlert} tone="alert" sub="hospitals with emergency care" />
          </Stagger>
        )}
      </section>

      <Reveal stagger={0.08} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(([Icon, title, text], i) => (
          <Card key={title} title={title} eyebrow={`0${i + 1}`}>
            <Icon size={18} className="mb-3 text-ok" aria-hidden="true" />
            <p className="text-sm text-muted">{text}</p>
          </Card>
        ))}
      </Reveal>

      <div role="note" className="flex items-start gap-3 rounded-[6px] border border-alert/40 bg-alert/[0.07] p-4">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-alert" aria-hidden="true" />
        <p className="text-sm text-fg">
          MediQueue is decision support, not a diagnosis. For chest pain, trouble breathing, fainting or stroke signs, call <b>108</b> or go to the
          nearest emergency department immediately.
        </p>
      </div>
    </div>
  )
}
