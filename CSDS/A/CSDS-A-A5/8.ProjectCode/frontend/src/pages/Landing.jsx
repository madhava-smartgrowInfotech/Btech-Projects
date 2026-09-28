import { ArrowRight, Brain, FileText, Network, Radar, Scale, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../App'
import { Logo } from '../components/Layout'

const FEATURES = [
  { icon: Brain, title: 'Learns normal GST behaviour', text: 'A self-supervised JEPA encoder learns what a normal taxpayer-month looks like from unlabelled invoices and returns. No fraud labels needed.' },
  { icon: Network, title: 'Finds fraud rings', text: 'Graph analytics trace circular-trading loops and clusters of registrations sharing an address or contact number.' },
  { icon: Target, title: 'Multi-layer risk', text: 'Invoice, return-behaviour and network signals combine into one ranked risk score per taxpayer and per invoice chain.' },
  { icon: FileText, title: 'Explains every flag', text: 'Gemini turns the evidence into an investigator-style case note, citing each fact it uses.' },
  { icon: Radar, title: 'Four patterns covered', text: 'Fake invoices, circular trading, shell entities and abnormal spikes in ITC claims.' },
  { icon: Scale, title: 'Measured, not assumed', text: 'Precision@k, recall and F1 against ground truth, side by side with a rule-based baseline.' },
]

export default function Landing() {
  const { user } = useAuth()
  return (
    <div className="min-h-screen bg-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <Logo />
        <Link to={user ? '/app' : '/login'} className="text-sm font-medium text-indigo-700 hover:underline">
          {user ? 'Open dashboard' : 'Sign in'}
        </Link>
      </header>
      <section className="bg-gradient-to-b from-indigo-50 to-white">
        <div className="mx-auto max-w-6xl px-5 py-16 sm:py-24">
          <p className="text-sm font-medium text-indigo-700">GST input-tax-credit fraud analytics</p>
          <h1 className="mt-3 max-w-3xl text-3xl sm:text-5xl font-semibold tracking-tight text-slate-900">
            Find the fake invoices, circular trades and shell firms behind suspicious ITC claims.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-slate-600">
            TaxSentinel learns how normal businesses file and trade, ranks taxpayers and invoice chains by how far
            they deviate, and writes a plain-language case note that cites the evidence.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={user ? '/app' : '/login'} className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700">
              {user ? 'Open dashboard' : 'Get started'} <ArrowRight size={16} />
            </Link>
            <Link to="/login?demo=1" className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
              Try the demo account
            </Link>
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-6xl px-5 py-14">
        <h2 className="text-xl font-semibold text-slate-900">Built for investigators, forensic accountants and compliance teams</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="rounded-xl border border-slate-200 p-5">
              <div className="inline-flex rounded-lg bg-indigo-50 p-2 text-indigo-600"><Icon size={20} /></div>
              <h3 className="mt-3 font-semibold text-slate-900">{title}</h3>
              <p className="mt-1.5 text-sm text-slate-600">{text}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-6xl px-5 pb-16">
        <div className="rounded-xl bg-slate-900 p-6 sm:p-8 text-slate-200">
          <h2 className="text-lg font-semibold text-white">How it works</h2>
          <ol className="mt-4 grid gap-4 sm:grid-cols-4 text-sm">
            {['Generate or load a GST ecosystem: taxpayers, invoices, GSTR-1/2B/3B returns.',
              'Build invoice, behaviour and network features for every taxpayer-month.',
              'Score deviation with the JEPA encoder and trace rings with graph analytics.',
              'Rank risk, drill into evidence and read the written case note.'].map((s, i) => (
              <li key={i}><span className="font-mono text-indigo-300">0{i + 1}</span><p className="mt-1">{s}</p></li>
            ))}
          </ol>
        </div>
        <p className="mt-6 text-xs text-slate-400">The bundled ecosystem is synthetic sample data produced by a seeded generator.</p>
      </section>
    </div>
  )
}
