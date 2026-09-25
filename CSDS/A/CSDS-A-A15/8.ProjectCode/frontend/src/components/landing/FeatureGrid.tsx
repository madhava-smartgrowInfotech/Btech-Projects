import { motion } from 'framer-motion'
import { BrainCircuit, FileText, Flame, Gauge, LayoutDashboard, Microscope } from 'lucide-react'
import { SpotlightCard } from '@/components/effects/SpotlightCard'

const FEATURES = [
  {
    icon: BrainCircuit,
    title: 'Deep Learning Detection',
    description:
      'A convolutional network trained on industrial surface imagery classifies six defect categories in milliseconds.',
  },
  {
    icon: Flame,
    title: 'Explainable Heatmaps',
    description:
      'Grad-CAM visual explanations show exactly which pixels drove the model’s decision — no black-box guessing.',
  },
  {
    icon: Microscope,
    title: 'Root-Cause Engine',
    description:
      'A curated process-failure knowledge base translates each detection into probable causes on the production line.',
  },
  {
    icon: FileText,
    title: 'Automated Reporting',
    description:
      'Every inspection compiles into a shareable PDF report with imagery, findings and corrective actions — instantly.',
  },
  {
    icon: LayoutDashboard,
    title: 'Unified Dashboard',
    description:
      'Upload, review and track inspections from one console built for quality engineers, not data scientists.',
  },
  {
    icon: Gauge,
    title: 'Live Performance Metrics',
    description:
      'Track detection accuracy, severity trends and throughput with analytics pulled straight from the model.',
  },
]

export function FeatureGrid() {
  return (
    <section id="platform" className="relative py-28">
      <div className="mx-auto max-w-7xl px-6">
        <div className="max-w-2xl mb-16">
          <p className="text-sm font-medium text-cyan-400 mb-3">Platform</p>
          <h2 className="font-display text-4xl font-bold text-white">
            Everything a quality line needs to inspect, explain and act.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5, delay: i * 0.06 }}
            >
              <SpotlightCard>
                <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-cyan-400/20 to-violet-500/20 flex items-center justify-center mb-5">
                  <feature.icon className="h-5 w-5 text-cyan-300" />
                </div>
                <h3 className="font-display text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{feature.description}</p>
              </SpotlightCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
