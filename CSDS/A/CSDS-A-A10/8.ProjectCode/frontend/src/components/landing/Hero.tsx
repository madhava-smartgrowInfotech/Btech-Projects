import { Suspense, lazy } from 'react'
import { type Variants, motion } from 'framer-motion'
import { ArrowRight, PlayCircle, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

import { AnimatedNumber } from '@/components/ui/AnimatedNumber'
import { Button } from '@/components/ui/Button'

const PulseScene = lazy(() => import('./PulseScene').then((m) => ({ default: m.PulseScene })))

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 28 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.7, ease: [0.16, 1, 0.3, 1] as const },
  }),
}

export function Hero() {
  return (
    <section id="top" className="relative min-h-screen overflow-hidden pt-32 pb-20">
      <div className="pointer-events-none absolute left-1/2 top-0 h-[700px] w-[1100px] -translate-x-1/2 rounded-full bg-brand-500/10 blur-[140px]" />
      <div className="pointer-events-none absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,black,transparent)]" />

      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-6 lg:grid-cols-2">
        <div>
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={0}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-xs font-medium text-brand-300"
          >
            <Sparkles size={13} />
            AI-assisted triage &amp; wait-time prediction
          </motion.div>

          <motion.h1
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={1}
            className="mt-6 font-display text-4xl font-extrabold leading-[1.08] text-white text-balance sm:text-5xl lg:text-6xl"
          >
            Hospital patient flow,
            <br />
            <span className="bg-gradient-to-r from-brand-400 via-vital-400 to-brand-300 bg-clip-text text-transparent">
              orchestrated in real time.
            </span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={2}
            className="mt-6 max-w-lg text-base leading-relaxed text-ink-300 sm:text-lg"
          >
            MedFlow replaces manual token boards and phone-call bed checks with one live system —
            digital queues, department-to-department tracking, lab scheduling and predictive
            triage, all synced to the second.
          </motion.p>

          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={3}
            className="mt-9 flex flex-wrap items-center gap-4"
          >
            <Link to="/login">
              <Button size="lg">
                Open Staff Console
                <ArrowRight size={18} />
              </Button>
            </Link>
            <Link to="/board">
              <Button size="lg" variant="outline">
                <PlayCircle size={18} />
                View Live Waiting Board
              </Button>
            </Link>
          </motion.div>

          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={4}
            className="mt-14 grid grid-cols-3 gap-6 border-t border-white/8 pt-8"
          >
            <div>
              <p className="font-display text-3xl font-bold text-white">
                <AnimatedNumber value={42} suffix="%" />
              </p>
              <p className="mt-1 text-xs text-ink-400">Avg. wait-time reduction</p>
            </div>
            <div>
              <p className="font-display text-3xl font-bold text-white">
                <AnimatedNumber value={6} />
              </p>
              <p className="mt-1 text-xs text-ink-400">Departments unified</p>
            </div>
            <div>
              <p className="font-display text-3xl font-bold text-white">
                <AnimatedNumber value={97} suffix="%" />
              </p>
              <p className="mt-1 text-xs text-ink-400">Triage model accuracy</p>
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="relative h-[420px] sm:h-[520px]"
        >
          <Suspense fallback={<div className="h-full w-full animate-pulse rounded-full bg-brand-500/5" />}>
            <PulseScene />
          </Suspense>
          <div className="pointer-events-none absolute inset-x-8 bottom-4 flex justify-center">
            <div className="glass-panel flex items-center gap-3 rounded-2xl px-4 py-3 text-xs text-ink-300">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400" />
              Live: 214 patients tracked across the hospital right now
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
