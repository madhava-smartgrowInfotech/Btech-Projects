import { Link } from 'react-router-dom'
import { Bell, Bot, Building2, FileJson, Fingerprint, HeartPulse, RefreshCcw, ShieldCheck } from 'lucide-react'
import { useAuth, HOME } from '../App.jsx'

const FEATURES = [
  { icon: Building2, title: 'Connected hospitals', text: 'Three independent HL7 FHIR R4 servers, each with its own database and patient IDs.' },
  { icon: Fingerprint, title: 'Master Patient Index', text: 'Fuzzy matching on name, birth date, gender and phone links one person across hospitals, with a confidence score.' },
  { icon: ShieldCheck, title: 'Consent you control', text: 'Grant or revoke access per hospital and data category, stored as FHIR Consent in a tamper-evident ledger.' },
  { icon: FileJson, title: 'Secure retrieval', text: 'Doctors pass a consent check before FHIR REST calls fetch and merge records. Every access is audited.' },
  { icon: RefreshCcw, title: 'Post-treatment sync', text: 'Hospitals push a FHIR summary after treatment and keep ownership of the original record.' },
  { icon: HeartPulse, title: 'Risk prediction', text: 'Random Forest models estimate heart-disease and diabetes risk from values in your record, with the reasons.' },
  { icon: Bot, title: 'AI assistant', text: 'Plain-language explanations of lab reports and treatment summaries, in your language.' },
  { icon: Bell, title: 'Reminders', text: 'Medication and follow-up reminders built from your prescriptions and care plans.' },
]

export default function Landing() {
  const { user } = useAuth()
  return (
    <div className="min-h-screen bg-gradient-to-b from-teal-50 to-white">
      <header className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-lg text-slate-900"><HeartPulse className="w-7 h-7 text-teal-600" /> UniHealth</div>
        <Link to={user ? HOME[user.role] : '/login'} className="rounded-lg bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 text-sm font-medium">
          {user ? 'Open dashboard' : 'Sign in'}
        </Link>
      </header>
      <section className="max-w-6xl mx-auto px-4 pt-12 pb-10 text-center">
        <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 tracking-tight">One health record.<br />Every hospital. Your consent.</h1>
        <p className="mt-5 text-lg text-slate-600 max-w-2xl mx-auto">
          UniHealth brings a patient's records from different hospitals into a single timeline over HL7 FHIR,
          lets the patient decide who may see what, and explains the results in plain language.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/login" className="rounded-lg bg-teal-600 hover:bg-teal-700 text-white px-5 py-2.5 font-medium">Try the demo</Link>
          <a href="#features" className="rounded-lg border border-slate-300 bg-white hover:bg-slate-50 px-5 py-2.5 font-medium text-slate-700">How it works</a>
        </div>
      </section>
      <section id="features" className="max-w-6xl mx-auto px-4 pb-16 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {FEATURES.map(({ icon: Icon, title, text }) => (
          <div key={title} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <Icon className="w-6 h-6 text-teal-600" />
            <h3 className="mt-3 font-semibold text-slate-900">{title}</h3>
            <p className="mt-1 text-sm text-slate-600">{text}</p>
          </div>
        ))}
      </section>
      <footer className="text-center text-xs text-slate-500 pb-8 px-4">
        Clinical decision support only - AI and risk outputs assist qualified professionals and are never a final diagnosis.
        Patient data shown is synthetic sample data (Synthea).
      </footer>
    </div>
  )
}
