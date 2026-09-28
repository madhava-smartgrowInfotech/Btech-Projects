import { Link } from 'react-router-dom'
import { AudioLines, BarChart3, FileText, Gauge, HeartPulse, Mic, Tags } from 'lucide-react'

const features = [
  { icon: Mic, title: 'Every call, transcribed', text: 'Upload recordings in bulk or record from the microphone. faster-whisper transcribes on CPU and separates agent and customer.' },
  { icon: Tags, title: 'Intent, topic & keywords', text: 'A model trained on 27k customer-support requests tags why the customer called and pulls out the key terms.' },
  { icon: HeartPulse, title: 'Emotion timeline', text: 'Text sentiment plus voice emotion per turn, drawn over the call, with escalation flags where it goes wrong.' },
  { icon: FileText, title: 'Summaries & action items', text: 'Gemini writes the reason for the call, the resolution and the follow-ups, so nobody has to listen back.' },
  { icon: Gauge, title: 'Agent scorecards', text: 'Greeting, empathy, talk/listen, silence, interruptions, resolution and sentiment change, each with its evidence.' },
  { icon: BarChart3, title: 'Live analytics', text: 'Volumes, top intents, sentiment trends and an agent leaderboard, with search across every transcript.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 to-slate-50">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2 text-lg font-bold text-indigo-800">
          <AudioLines className="h-6 w-6" /> CallSense
        </div>
        <Link to="/login" className="btn-primary">Sign in</Link>
      </header>
      <section className="mx-auto max-w-6xl px-4 pb-10 pt-10 text-center">
        <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Analyse every customer call, not just a sample
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          CallSense turns call recordings into transcripts, intent, emotion, summaries and agent scorecards
          automatically, so supervisors and QA teams see what customers feel while it still matters.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/login" className="btn-primary px-6 py-2.5">Open the dashboard</Link>
        </div>
      </section>
      <section className="mx-auto grid max-w-6xl gap-4 px-4 pb-16 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, text }) => (
          <div key={title} className="card">
            <Icon className="h-6 w-6 text-indigo-700" />
            <h3 className="mt-3 font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-slate-600">{text}</p>
          </div>
        ))}
      </section>
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        CallSense - call analytics for contact centres. Speech and text models run locally on CPU; summaries use Gemini.
      </footer>
    </div>
  )
}
