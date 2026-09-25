import { motion } from 'framer-motion'
import { Quote } from 'lucide-react'

const DEPARTMENTS = [
  'General Medicine OPD', 'Pediatrics OPD', 'Emergency', 'Central Laboratory',
  'Pharmacy', 'General Ward', 'Intensive Care Unit',
]

export function Results() {
  const loopItems = [...DEPARTMENTS, ...DEPARTMENTS]

  return (
    <section id="results" className="relative py-28">
      <div className="mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mx-auto max-w-3xl rounded-3xl border border-white/8 bg-gradient-to-br from-ink-850 to-ink-900 p-10 text-center"
        >
          <Quote className="mx-auto text-brand-400" size={28} />
          <p className="mt-5 font-display text-xl font-medium leading-relaxed text-white text-balance sm:text-2xl">
            "Nurses stopped calling the lab to ask about bed status — they just look at the
            screen. That alone gave us back hours every shift."
          </p>
          <p className="mt-5 text-sm text-ink-400">Ward Operations Lead, Pilot Deployment</p>
        </motion.div>

        <div className="mt-16 overflow-hidden">
          <p className="mb-6 text-center text-xs font-semibold uppercase tracking-widest text-ink-500">
            Coordinating every department, live
          </p>
          <div className="relative flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_10%,black_90%,transparent)]">
            <div className="flex shrink-0 animate-marquee gap-4 pr-4">
              {loopItems.map((d, i) => (
                <span
                  key={i}
                  className="whitespace-nowrap rounded-full border border-white/8 bg-ink-850/60 px-5 py-2.5 text-sm text-ink-300"
                >
                  {d}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
