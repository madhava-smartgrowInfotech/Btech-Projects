import { Link } from 'react-router-dom'
import { Captions, Gauge, Hand, MessagesSquare, Volume2, WifiOff } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import Logo from '../components/Logo.jsx'

const features = [
  { icon: Hand, title: 'Live sign recognition', text: '50 everyday ISL words plus fingerspelling A-Z and 1-9, with a confidence score for every sign.' },
  { icon: MessagesSquare, title: 'Signs become sentences', text: 'A pause closes the sentence. Rules work offline; when online, wording is polished automatically.' },
  { icon: Volume2, title: 'Spoken aloud', text: 'Each sentence is read out with on-device text-to-speech so the hearing person just listens.' },
  { icon: Captions, title: 'Live subtitles', text: 'The hearing person speaks; large subtitles appear for the signer, recognised on this computer.' },
  { icon: WifiOff, title: 'Works offline', text: 'Camera, recognition, speech and subtitles all run locally, with FPS and latency always visible.' },
  { icon: Gauge, title: 'Measured', text: 'Accuracy, confusion matrix and latency are published on the performance page.' },
]

export default function Landing() {
  const { user } = useAuth()
  return (
    <div className="min-h-screen bg-white">
      <header className="max-w-6xl mx-auto px-4 h-16 flex items-center">
        <Logo to="/" />
        <div className="ml-auto flex gap-2">
          {user ? <Link to="/app" className="btn-primary">Open SignBridge</Link> : <>
            <Link to="/login" className="btn-secondary">Sign in</Link>
            <Link to="/register" className="btn-primary">Create account</Link>
          </>}
        </div>
      </header>
      <section className="max-w-6xl mx-auto px-4 pt-16 pb-12 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <span className="chip bg-teal-50 text-teal-700 mb-4">Indian Sign Language ⇄ speech</span>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            Talk both ways, <span className="text-indigo-600">sign and speech</span>, on one screen.
          </h1>
          <p className="mt-5 text-lg text-slate-600">
            SignBridge turns ISL signs into text and speech, and turns the hearing person's voice into live
            subtitles, in real time and without needing the internet.
          </p>
          <div className="mt-8 flex gap-3">
            <Link to={user ? '/app' : '/register'} className="btn-primary !px-6 !py-3 !text-base">Start a conversation</Link>
            <Link to="/login" className="btn-secondary !px-6 !py-3 !text-base">Try the demo account</Link>
          </div>
        </div>
        <div className="rounded-3xl bg-slate-900 p-6 text-white shadow-xl">
          <div className="rounded-2xl bg-slate-800 p-4">
            <div className="text-xs text-slate-400 mb-2">Signer</div>
            <div className="flex gap-2 mb-3">{['HELLO', 'HOW ARE YOU'].map((g) => <span key={g} className="chip bg-indigo-500/20 text-indigo-200">{g}</span>)}</div>
            <p className="text-2xl font-medium">“Hello, how are you?”</p>
          </div>
          <div className="rounded-2xl bg-teal-500/10 border border-teal-400/30 p-4 mt-4">
            <div className="text-xs text-teal-300 mb-2">Subtitle for the signer</div>
            <p className="text-2xl font-medium">I'm fine, thanks. How can I help you today?</p>
          </div>
          <p className="text-xs text-slate-500 mt-3">Illustration of the conversation screen</p>
        </div>
      </section>
      <section className="bg-slate-50 border-t border-slate-200">
        <div className="max-w-6xl mx-auto px-4 py-16 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card p-5">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 grid place-items-center mb-3"><Icon size={20} /></div>
              <h3 className="font-semibold text-slate-900">{title}</h3>
              <p className="text-sm text-slate-600 mt-1">{text}</p>
            </div>
          ))}
        </div>
      </section>
      <footer className="text-center text-xs text-slate-400 py-6">SignBridge · runs on your own computer</footer>
    </div>
  )
}
