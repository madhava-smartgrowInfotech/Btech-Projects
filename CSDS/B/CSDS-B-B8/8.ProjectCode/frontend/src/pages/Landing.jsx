import { Link } from 'react-router-dom'
import { Bell, CalendarDays, EyeOff, Moon, PersonStanding, ShieldAlert } from 'lucide-react'

const FEATURES = [
  { icon: PersonStanding, title: 'Activity recognition', text: 'Walking, standing, sitting, lying, drinking water and picking things up - recognised live from body keypoints.' },
  { icon: ShieldAlert, title: 'Real-time fall detection', text: 'A rapid drop to the floor followed by stillness is confirmed before anyone is disturbed.' },
  { icon: Bell, title: 'Instant alerts', text: "An on-screen 'I'm OK' countdown, then Telegram with a snapshot and an email to family." },
  { icon: EyeOff, title: 'Privacy first', text: 'The live view shows only a skeleton. No video is stored - a snapshot is kept only with an alert.' },
  { icon: Moon, title: 'Works in dim rooms', text: 'Automatic low-light enhancement keeps recognition going when the lights are low.' },
  { icon: CalendarDays, title: 'Daily report', text: 'Time spent per activity and long-inactivity warnings, day by day.' },
]

export default function Landing() {
  const signedIn = !!localStorage.getItem('cw_token')
  return (
    <div className="min-h-screen bg-gradient-to-b from-teal-50 to-white">
      <header className="max-w-6xl mx-auto px-4 h-16 flex items-center">
        <div className="flex items-center gap-2 font-semibold text-slate-900 text-lg">
          <img src="/favicon.svg" className="w-8 h-8" alt="" /> CareWatch
        </div>
        <Link to={signedIn ? '/monitor' : '/login'} className="btn btn-primary ml-auto">
          {signedIn ? 'Open monitor' : 'Sign in'}
        </Link>
      </header>
      <section className="max-w-6xl mx-auto px-4 pt-14 pb-12 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight">
          Peace of mind for people<br className="hidden md:block" /> who live alone
        </h1>
        <p className="text-lg text-slate-600 mt-5 max-w-2xl mx-auto">
          CareWatch turns a webcam or an old phone into a privacy-first carer: it recognises daily activities,
          spots falls in real time and alerts family within seconds.
        </p>
        <div className="flex flex-wrap justify-center gap-3 mt-8">
          <Link to="/login" className="btn btn-primary px-6 py-3 text-base">Get started</Link>
          <Link to="/login?demo=1" className="btn btn-secondary px-6 py-3 text-base">Try the demo account</Link>
        </div>
      </section>
      <section className="max-w-6xl mx-auto px-4 pb-16 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {FEATURES.map(({ icon: Icon, title, text }) => (
          <div key={title} className="card p-5">
            <div className="w-10 h-10 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center"><Icon className="w-5 h-5" /></div>
            <h3 className="font-semibold text-slate-900 mt-3">{title}</h3>
            <p className="text-sm text-slate-600 mt-1">{text}</p>
          </div>
        ))}
      </section>
      <section className="max-w-6xl mx-auto px-4 pb-16">
        <div className="card p-6 grid md:grid-cols-3 gap-6 text-sm text-slate-600">
          <div><b className="text-slate-900">For elderly people living alone</b><p className="mt-1">No wearable to forget - the camera watches over them, only as a skeleton.</p></div>
          <div><b className="text-slate-900">For family and caregivers</b><p className="mt-1">Get a Telegram message with a photo and an email the moment a fall is confirmed.</p></div>
          <div><b className="text-slate-900">For care homes</b><p className="mt-1">Daily activity reports and inactivity warnings for each monitored room.</p></div>
        </div>
      </section>
      <footer className="text-center text-xs text-slate-400 pb-8">CareWatch - privacy-first activity and fall monitoring</footer>
    </div>
  )
}
