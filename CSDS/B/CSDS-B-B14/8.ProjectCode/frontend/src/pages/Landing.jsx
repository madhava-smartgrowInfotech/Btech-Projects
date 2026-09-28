import { Link } from 'react-router-dom'
import { Activity, Droplets, FlaskConical, Gauge, LineChart, Map, ShieldAlert, Users } from 'lucide-react'
import { useAuth } from '../auth.jsx'

const FEATURES = [
  { icon: FlaskConical, title: 'Water-quality prediction', text: 'Stacked ensemble of Random Forest, XGBoost, Gradient Boosting and Decision Tree models, with SHAP reasons and guideline-limit checks for every lab sample.' },
  { icon: Map, title: 'Digital twin of the network', text: 'EPANET-based hydraulic model of zones, pipes, tanks and pumps that recomputes pressures and flows for every scenario.' },
  { icon: LineChart, title: '7-day demand forecast', text: 'Per-zone forecasts from consumption history plus live Open-Meteo weather, so hot days are planned for.' },
  { icon: ShieldAlert, title: 'Leak detection & localisation', text: 'Pressure and inflow residuals against the twin flag leaks and rank the most likely pipes on the map.' },
  { icon: Gauge, title: 'Distribution equity', text: 'Supply versus demand per zone, an equity score, and a rebalancing plan tested on the twin before anyone touches a valve.' },
  { icon: Activity, title: 'Abnormal consumption', text: 'IsolationForest on customer meters finds bursts, continuous night flow and suspected theft.' },
]

export default function Landing() {
  const { user } = useAuth()
  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 to-white">
      <header className="max-w-6xl mx-auto px-4 py-5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sky-700 font-semibold text-xl">
          <Droplets className="w-7 h-7" /> AquaVision
        </div>
        <Link to={user ? '/dashboard' : '/login'} className="btn-primary">
          {user ? 'Open dashboard' : 'Sign in'}
        </Link>
      </header>
      <section className="max-w-6xl mx-auto px-4 pt-12 pb-16 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight">Water-utility intelligence without heavy IoT</h1>
        <p className="mt-5 text-lg text-slate-600 max-w-3xl mx-auto">
          AquaVision predicts water quality and demand, and detects leaks, imbalances and abnormal consumption on a digital twin of the city network, using a
          handful of low-cost pressure loggers and the meters you already read.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to={user ? '/dashboard' : '/login'} className="btn-primary">
            Get started
          </Link>
          <a href="#features" className="btn-secondary">
            See features
          </a>
        </div>
      </section>
      <section id="features" className="max-w-6xl mx-auto px-4 pb-16 grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {FEATURES.map(({ icon: Icon, title, text }) => (
          <div key={title} className="card p-5">
            <div className="rounded-lg bg-sky-50 text-sky-600 p-2 w-fit">
              <Icon className="w-5 h-5" />
            </div>
            <h3 className="mt-3 font-semibold text-slate-900">{title}</h3>
            <p className="mt-1 text-sm text-slate-600">{text}</p>
          </div>
        ))}
      </section>
      <section className="max-w-6xl mx-auto px-4 pb-20">
        <div className="card p-6 flex flex-col md:flex-row gap-6 items-start">
          <Users className="w-8 h-8 text-sky-600 shrink-0" />
          <div>
            <h3 className="font-semibold text-slate-900">Built for utility teams</h3>
            <p className="text-sm text-slate-600 mt-1">
              Network engineers run leak and what-if scenarios on the twin; distribution and operations managers track non-revenue water, pressure,
              quality and alerts in one place; laboratory results feed straight into the quality check.
            </p>
          </div>
        </div>
      </section>
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">AquaVision - decision support for water distribution</footer>
    </div>
  )
}
