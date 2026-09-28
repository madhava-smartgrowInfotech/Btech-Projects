import { Link } from 'react-router-dom'
import {
  ShieldCheck, Bug, Gauge, FileText, Bot, ListChecks, Lock,
} from 'lucide-react'
import { useAuth } from '../auth'

const FEATURES = [
  { icon: Bug, title: 'OWASP API Top 10 tests', body: 'BOLA/IDOR, broken auth, excessive data exposure, mass assignment, missing rate limits, function-level auth, injection and misconfiguration.' },
  { icon: Bot, title: 'AI-generated tests', body: 'Gemini reads your spec and proposes business-logic abuse tests — negative amounts, foreign account transfers, replayed payments — then the scanner runs them.' },
  { icon: Gauge, title: 'Security score', body: 'A 0–100 score with a letter grade, weighted by severity, plus a per-endpoint breakdown.' },
  { icon: FileText, title: 'Reports & CLI', body: 'Shareable HTML/PDF reports and a CLI (--fail-on high) that fails your build on serious findings.' },
  { icon: ListChecks, title: 'Validation', body: 'Compare findings against a target’s known-vulnerability list for a detection rate and false-positive count.' },
  { icon: Lock, title: 'Scope guard', body: 'Scans only run against allow-listed hosts (localhost by default) after you confirm you are authorised.' },
]

export default function Landing() {
  const { email } = useAuth()
  const cta = email ? '/app/targets' : '/login'
  return (
    <div className="min-h-screen">
      <header className="max-w-6xl mx-auto px-4 h-16 flex items-center">
        <div className="flex items-center gap-2 font-extrabold text-xl">
          <ShieldCheck className="text-brand-500" /> APISentry
        </div>
        <Link to={cta} className="btn-primary ml-auto">
          {email ? 'Open app' : 'Sign in'}
        </Link>
      </header>

      <section className="max-w-4xl mx-auto px-4 pt-16 pb-12 text-center">
        <span className="inline-block text-brand-700 bg-brand-50 border border-brand-100
          rounded-full px-3 py-1 text-sm font-semibold mb-5">
          Security testing for payment APIs
        </span>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight">
          Find API vulnerabilities <span className="text-brand-500">before</span> you deploy.
        </h1>
        <p className="mt-5 text-lg text-slate-600 max-w-2xl mx-auto">
          APISentry imports your REST API spec, runs the OWASP API Top 10 plus AI-generated
          business-logic tests, and hands developers a security score and clear fixes.
        </p>
        <div className="mt-8 flex gap-3 justify-center">
          <Link to={cta} className="btn-primary px-6 py-3 text-base">Start scanning</Link>
          <a href="#features" className="btn-ghost px-6 py-3 text-base">See features</a>
        </div>
      </section>

      <section id="features" className="max-w-6xl mx-auto px-4 pb-20">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="card p-5">
              <f.icon className="text-brand-500 mb-3" />
              <h3 className="font-bold mb-1">{f.title}</h3>
              <p className="text-sm text-slate-600">{f.body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
