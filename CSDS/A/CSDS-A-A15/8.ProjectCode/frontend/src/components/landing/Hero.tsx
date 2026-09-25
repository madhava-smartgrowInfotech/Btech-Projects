import { motion, type Variants } from 'framer-motion'
import { ArrowRight, PlayCircle } from 'lucide-react'
import { Suspense, lazy } from 'react'
import { Link } from 'react-router-dom'

const ScanField = lazy(() => import('@/three/ScanField').then((m) => ({ default: m.ScanField })))

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.7, ease: [0.16, 1, 0.3, 1] as const },
  }),
}

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-grid">
      <div className="absolute inset-0 -z-10 opacity-70">
        <Suspense fallback={null}>
          <ScanField />
        </Suspense>
      </div>
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-transparent via-[#05070c]/40 to-[#05070c]" />

      <div className="mx-auto max-w-7xl px-6 pt-32 pb-24 w-full">
        <div className="max-w-3xl">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={0}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-cyan-300 mb-6"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
            Explainable Computer Vision · Live on production lines
          </motion.div>

          <motion.h1
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={1}
            className="font-display text-5xl md:text-7xl font-bold tracking-tight text-white leading-[1.05]"
          >
            See every defect.
            <br />
            <span className="text-gradient">Understand every cause.</span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={2}
            className="mt-6 text-lg text-slate-400 max-w-xl leading-relaxed"
          >
            VisionForge AI inspects industrial surfaces in real time, highlights exactly why a
            defect was flagged with explainable heatmaps, and writes the root-cause report for you —
            so quality teams stop guessing and start fixing.
          </motion.p>

          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={3}
            className="mt-10 flex flex-wrap items-center gap-4"
          >
            <Link
              to="/signup"
              className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400 to-violet-500 px-7 py-3.5 text-base font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-shadow"
            >
              Start Inspecting
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center gap-2 rounded-xl border border-white/15 px-7 py-3.5 text-base font-medium text-white hover:bg-white/5 transition"
            >
              <PlayCircle className="h-4 w-4" />
              See how it works
            </a>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
