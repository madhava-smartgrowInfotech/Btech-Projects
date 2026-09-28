import { Link } from 'react-router-dom'
import { Activity, ArrowRight, Building2, Clock, GitBranch, LayoutDashboard, ShieldAlert, Stethoscope } from 'lucide-react'
import { homeFor, useAuth } from '../auth'

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
  return (
    <div className="space-y-10">
      <section className="rounded-2xl bg-gradient-to-br from-teal-800 to-teal-600 text-white px-6 py-12 md:px-12">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-medium">
            <Activity className="h-3.5 w-3.5" /> Outpatient booking for the Hyderabad district
          </div>
          <h1 className="mt-4 text-3xl md:text-5xl font-bold leading-tight">See the right doctor sooner, without the queue.</h1>
          <p className="mt-4 text-teal-50 md:text-lg">
            MediQueue grades how urgent your symptoms are, suggests the hospitals that can see you, and shows your live place in
            line - from your phone.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to={user ? homeFor(user) : '/login'} className="btn bg-white text-teal-800 hover:bg-teal-50">
              {user ? 'Open MediQueue' : 'Book a visit'} <ArrowRight className="h-4 w-4" />
            </Link>
            {!user && (
              <Link to="/login?role=staff" className="btn border border-white/40 text-white hover:bg-white/10">
                Hospital staff login
              </Link>
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(([Icon, title, text]) => (
          <div key={title} className="card p-5">
            <Icon className="h-6 w-6 text-teal-700" />
            <h3 className="mt-3 font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-slate-600">{text}</p>
          </div>
        ))}
      </section>

      <section className="card p-5 flex gap-3 items-start border-red-200 bg-red-50">
        <ShieldAlert className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
        <p className="text-sm text-red-800">
          MediQueue is decision support, not a diagnosis. For chest pain, trouble breathing, fainting or stroke signs, call{' '}
          <b>108</b> or go to the nearest emergency department immediately.
        </p>
      </section>
    </div>
  )
}
