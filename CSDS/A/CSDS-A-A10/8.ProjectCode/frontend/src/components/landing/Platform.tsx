import { motion } from 'framer-motion'
import { BedDouble, Brain, FlaskConical, QrCode, Radar, Users } from 'lucide-react'

import { SpotlightCard } from './SpotlightCard'

const FEATURES = [
  {
    icon: <QrCode size={20} />,
    title: 'Digital token queues',
    description: 'Every patient gets a live token at registration — no name-calling, no printed slips, no guesswork.',
    accent: '#3b82f6',
  },
  {
    icon: <Radar size={20} />,
    title: 'Department-to-department tracking',
    description: 'Follow every patient across OPD, lab, pharmacy, wards and ICU with a full movement timeline.',
    accent: '#06b6d4',
  },
  {
    icon: <FlaskConical size={20} />,
    title: 'Lab scheduling that clears backlogs',
    description: 'Tests are ordered, scheduled and resulted from one queue — synced back to the patient record instantly.',
    accent: '#8b5cf6',
  },
  {
    icon: <BedDouble size={20} />,
    title: 'Live bed & ICU visibility',
    description: 'Ward and ICU occupancy update the moment a bed changes state — no more phone calls to check availability.',
    accent: '#10b981',
  },
  {
    icon: <Brain size={20} />,
    title: 'Predictive triage',
    description: 'A clinically-informed model scores vitals in real time and flags critical cases before they reach the front of the queue.',
    accent: '#f59e0b',
  },
  {
    icon: <Users size={20} />,
    title: 'Role-based dashboards',
    description: 'Doctors, nurses, lab staff, reception and admins each see exactly the view their job needs.',
    accent: '#ec4899',
  },
]

export function Platform() {
  return (
    <section id="platform" className="relative py-28">
      <div className="mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="mx-auto max-w-2xl text-center"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-400">Platform</p>
          <h2 className="mt-3 font-display text-3xl font-bold text-white sm:text-4xl text-balance">
            Everything a busy hospital floor needs, in one system
          </h2>
          <p className="mt-4 text-ink-400">
            MedFlow was built around the actual patient journey — not just appointments and billing.
          </p>
        </motion.div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5, delay: (i % 3) * 0.08 }}
            >
              <SpotlightCard {...f} />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
