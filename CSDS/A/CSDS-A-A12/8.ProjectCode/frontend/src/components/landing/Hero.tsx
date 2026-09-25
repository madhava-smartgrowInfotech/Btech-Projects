import { Suspense, lazy } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'

const SeedField = lazy(() => import('../three/SeedField').then((m) => ({ default: m.SeedField })))

export function Hero() {
  return (
    <section className="relative min-h-[100svh] flex items-center overflow-hidden pt-28 pb-16">
      <div className="absolute inset-0 grid-fade -z-10" />
      <div className="absolute inset-0 -z-20 opacity-70">
        <Suspense fallback={null}>
          <SeedField />
        </Suspense>
      </div>
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-transparent via-transparent to-[var(--color-bg)]" />

      <div className="mx-auto max-w-6xl px-6 w-full">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <Badge tone="emerald" className="mb-6">
            <Sparkles size={12} />
            Self-supervised vision · environmental fusion · explainable AI
          </Badge>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight max-w-3xl leading-[1.05]"
        >
          Know a seed's future <span className="text-gradient">before you sow it.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.22, ease: [0.16, 1, 0.3, 1] }}
          className="mt-6 max-w-xl text-lg text-[var(--color-text-muted)] leading-relaxed"
        >
          SeedIQ fuses a self-supervised vision encoder with live soil and climate data to
          predict millet seed germination in seconds — and explains exactly why, with
          actionable guidance for every batch.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.34, ease: [0.16, 1, 0.3, 1] }}
          className="mt-9 flex flex-wrap items-center gap-4"
        >
          <Link to="/app">
            <Button size="lg" icon={<ArrowRight size={17} />}>
              Analyze a seed batch
            </Button>
          </Link>
          <Link to="/insights">
            <Button variant="secondary" size="lg">
              View model performance
            </Button>
          </Link>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.6 }}
          className="mt-16 flex flex-wrap items-center gap-x-10 gap-y-4 text-sm text-[var(--color-text-faint)]"
        >
          <span>7 millet varieties supported</span>
          <span className="w-1 h-1 rounded-full bg-[var(--color-border)]" />
          <span>Morphological + spectral trait extraction</span>
          <span className="w-1 h-1 rounded-full bg-[var(--color-border)]" />
          <span>Plain-language agronomic advisories</span>
        </motion.div>
      </div>
    </section>
  )
}
