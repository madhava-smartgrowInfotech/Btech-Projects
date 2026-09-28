import { Link } from 'react-router-dom'
import { Activity, BedDouble, BrainCircuit, Gauge, HeartPulse, ShieldCheck, Users, Workflow } from 'lucide-react'

const FEATURES = [
  { icon: BrainCircuit, title: 'Length-of-stay prediction', text: 'Expected days and short/long stay at admission, with the clinical factors behind every estimate (SHAP).' },
  { icon: BedDouble, title: 'Occupancy forecast', text: '14-day bed occupancy per ward from current patients, their predicted stays and forecast admissions, with 90% bands.' },
  { icon: HeartPulse, title: 'ICU early warning', text: 'Expected ICU beds needed per facility and a warning on the first day demand can pass capacity.' },
  { icon: Users, title: 'Staff and equipment demand', text: 'Nurses per shift at safe ratios, plus ventilators, monitors, infusion pumps and dialysis machines.' },
  { icon: Workflow, title: 'Allocation recommendations', text: 'An optimiser proposes bed conversions, diversions, nurse floats, extra shifts and equipment transfers, with the trade-off explained.' },
  { icon: Gauge, title: 'Measured accuracy', text: 'Prediction error, forecast error against naive baselines and the gain over a static allocation.' },
]

export default function Landing({ user }) {
  return (
    <div className="min-h-screen bg-white">
      <header className="max-w-6xl mx-auto flex items-center justify-between px-4 py-5">
        <span className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <Activity className="text-teal-700" /> HospiSense
        </span>
        <Link to={user ? '/dashboard' : '/login'} className="btn-primary">
          {user ? 'Open dashboard' : 'Sign in'}
        </Link>
      </header>

      <section className="bg-gradient-to-b from-teal-50 to-white">
        <div className="max-w-6xl mx-auto px-4 py-16 lg:py-24 grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <h1 className="text-4xl lg:text-5xl font-bold text-slate-900 leading-tight">
              See tomorrow's bed, ICU and staffing pressure today.
            </h1>
            <p className="mt-5 text-lg text-slate-600">
              HospiSense predicts each patient's length of stay, forecasts ward and ICU occupancy for the next two weeks, and recommends how to
              allocate beds, nurses and equipment - with the reasons behind every number.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to={user ? '/dashboard' : '/login'} className="btn-primary">
                Get started
              </Link>
              <a href="#features" className="btn-secondary">
                What it does
              </a>
            </div>
          </div>
          <div className="card p-6">
            <div className="text-sm font-medium text-slate-500 mb-4">How it works</div>
            <ol className="space-y-4 text-sm text-slate-700">
              {[
                ['Admit', 'A clinician enters admission data; the model returns expected days and why.'],
                ['Forecast', 'Current patients + predicted stays + forecast admissions give the 14-day census per ward.'],
                ['Warn', 'The first day ICU or ward demand can pass capacity raises an early warning.'],
                ['Plan', 'The optimiser recommends bed, staff and equipment moves; an administrator accepts or edits them.'],
              ].map(([t, d], i) => (
                <li key={t} className="flex gap-3">
                  <span className="h-7 w-7 shrink-0 rounded-full bg-teal-700 text-white flex items-center justify-center text-xs font-semibold">{i + 1}</span>
                  <span>
                    <strong className="text-slate-900">{t}.</strong> {d}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      <section id="features" className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-semibold text-slate-900 mb-8">Built for bed managers, doctors and operations planners</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card p-5">
              <Icon className="text-teal-700" />
              <h3 className="mt-3 font-semibold text-slate-900">{title}</h3>
              <p className="mt-2 text-sm text-slate-600">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-slate-200">
        <div className="max-w-6xl mx-auto px-4 py-6 text-xs text-slate-500 flex items-start gap-2">
          <ShieldCheck size={16} className="shrink-0" />
          HospiSense is a decision-support tool. Its predictions and recommendations support, and do not replace, the judgement of qualified
          clinical and operational staff.
        </div>
      </footer>
    </div>
  )
}
