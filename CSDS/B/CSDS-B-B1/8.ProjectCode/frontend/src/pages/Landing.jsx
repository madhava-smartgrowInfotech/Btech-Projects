import { ArrowRight, BarChart3, Brain, Clock, Languages, MessageSquare, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { homeFor, useAuth } from '../auth.jsx'
import { Logo } from '../components/Layout.jsx'

const FEATURES = [
  { icon: Languages, title: 'Understands English, Hindi and Hinglish', text: 'Citizens write the way they speak. Complaints are classified by category and routed to the right department automatically.' },
  { icon: Clock, title: 'Priority and resolution time', text: 'Every complaint gets a Low to Critical priority and an expected resolution time learned from real service-request history, with an SLA-breach warning.' },
  { icon: Brain, title: 'Explains every suggestion', text: 'Officers see the words that drove the category and the factors behind priority and time - no black boxes.' },
  { icon: ShieldCheck, title: 'Officers stay in control', text: 'Accept or override each suggestion with a reason. Overrides become training labels and the model retrains in one click.' },
  { icon: BarChart3, title: 'Hotspots and SLA analytics', text: 'See recurring issues by ward, SLA compliance by department and category trends as they happen.' },
  { icon: MessageSquare, title: 'Replies in the citizen’s language', text: 'A status reply is drafted in the language the citizen used, ready for the officer to edit and send.' },
]

export default function Landing() {
  const { user } = useAuth()
  return (
    <div className="min-h-screen bg-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Logo />
        <Link to={user ? homeFor(user) : '/login'} className="btn-secondary">
          {user ? 'Open dashboard' : 'Log in'}
        </Link>
      </header>

      <section className="border-b border-slate-100 bg-gradient-to-b from-brand-50 to-white">
        <div className="mx-auto max-w-6xl px-4 py-16 md:py-24">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand-700">Decision support for grievance offices</p>
          <h1 className="mt-3 max-w-3xl text-4xl font-bold leading-tight text-slate-900 md:text-5xl">
            Every citizen complaint understood, prioritised and routed - with the reasons shown.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-slate-600">
            CivicPulse reads complaints in English, Hindi and Hinglish, predicts priority and resolution time, recommends the
            responsible department and explains each suggestion. Officers make the final call.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={user?.role === 'citizen' ? '/file' : '/login'} className="btn-primary px-5 py-2.5 text-base">
              File a complaint <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to={user && user.role !== 'citizen' ? '/queue' : '/login'} className="btn-secondary px-5 py-2.5 text-base">
              Officer workbench
            </Link>
          </div>
          <p className="mt-6 text-sm text-slate-500" lang="hi">
            उदाहरण: “हमारी गली की स्ट्रीट लाइट दो हफ्ते से बंद है, रात में बहुत अंधेरा रहता है।”
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card p-5">
              <Icon className="h-6 w-6 text-brand-700" />
              <h3 className="mt-3 font-semibold text-slate-900">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-slate-100 bg-slate-50">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 py-12 md:grid-cols-4">
          {[
            ['1', 'Citizen files', 'Text, photo and a map pin. A tracking ID is issued instantly.'],
            ['2', 'AI suggests', 'Category, department, priority, expected days and the reasons.'],
            ['3', 'Officer decides', 'Accept or override. Every override improves the model.'],
            ['4', 'Citizen is updated', 'Status timeline and a reply in their own language.'],
          ].map(([n, t, d]) => (
            <div key={n}>
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-700 text-sm font-semibold text-white">{n}</div>
              <h4 className="mt-3 font-semibold text-slate-900">{t}</h4>
              <p className="mt-1 text-sm text-slate-600">{d}</p>
            </div>
          ))}
        </div>
      </section>
      <footer className="py-8 text-center text-xs text-slate-400">CivicPulse</footer>
    </div>
  )
}
