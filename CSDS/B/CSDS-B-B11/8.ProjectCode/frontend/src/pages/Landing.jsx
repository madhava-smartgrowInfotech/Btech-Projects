import { Link } from 'react-router-dom'
import { Camera, CalendarDays, Leaf, LineChart, Repeat, ShieldCheck } from 'lucide-react'

const features = [
  { icon: CalendarDays, title: 'Optimised 7-day plans', text: 'A linear-programming optimiser picks Indian dishes and portions that hit your calories, protein, carbs, fat and fibre every day.' },
  { icon: ShieldCheck, title: 'Safe by design', text: 'Allergens are hard-blocked, and diabetes, hypertension and cholesterol limits are enforced. Calories never drop below a safe floor.' },
  { icon: Repeat, title: 'Smart swaps', text: 'Swap any dish for a nutritionally similar one from a clustered database of Indian foods, with the portion adjusted to match.' },
  { icon: Camera, title: 'Log by photo', text: 'Snap your plate. AI recognises the dish and estimates the portion, and you confirm it before it is logged.' },
  { icon: LineChart, title: 'Adapts as you progress', text: 'Weight and intake charts plus an adherence score. Your target is recalculated weekly from your real weight trend.' },
  { icon: Leaf, title: 'North and South Indian', text: 'Dal, sabzi, roti, idli, dosa, sambar and more, with recipe steps written for your allergies and conditions.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 to-white">
      <header className="mx-auto max-w-6xl px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold text-emerald-700 text-lg"><Leaf className="h-6 w-6" /> NutriSense</div>
        <div className="flex gap-2">
          <Link to="/login" className="btn-ghost">Log in</Link>
          <Link to="/register" className="btn-primary">Get started</Link>
        </div>
      </header>
      <section className="mx-auto max-w-6xl px-4 pt-12 pb-16 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight">Indian meal plans built around <span className="text-emerald-600">your</span> body</h1>
        <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
          NutriSense works out your calorie and nutrient needs, then builds a week of balanced meals.
          The plan respects your allergies, diet and health conditions and adapts as you make progress.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/register" className="btn-primary !px-6 !py-3 text-base">Create my plan</Link>
          <Link to="/login" className="btn-ghost !px-6 !py-3 text-base">Try the sample account</Link>
        </div>
      </section>
      <section className="mx-auto max-w-6xl px-4 pb-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, text }) => (
          <div key={title} className="card p-5">
            <div className="h-10 w-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3"><Icon className="h-5 w-5" /></div>
            <h3 className="font-semibold text-slate-800">{title}</h3>
            <p className="text-sm text-slate-600 mt-1">{text}</p>
          </div>
        ))}
      </section>
      <footer className="text-center text-xs text-slate-500 pb-8 px-4">
        General nutrition guidance, not medical advice. Consult a doctor or registered dietitian for medical conditions.
      </footer>
    </div>
  )
}
