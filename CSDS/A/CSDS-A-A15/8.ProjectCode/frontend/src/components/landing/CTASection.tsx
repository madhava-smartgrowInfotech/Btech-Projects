import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

export function CTASection() {
  return (
    <section className="relative py-28 border-t border-white/5">
      <div className="mx-auto max-w-5xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6 }}
          className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.06] to-transparent px-8 py-16 text-center"
        >
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 h-64 w-64 rounded-full bg-cyan-500/20 blur-3xl" />
          <h2 className="relative font-display text-4xl md:text-5xl font-bold text-white max-w-2xl mx-auto">
            Stop shipping defects your team can&rsquo;t explain.
          </h2>
          <p className="relative mt-4 text-slate-400 max-w-lg mx-auto">
            Set up VisionForge AI on your line in minutes and start turning raw inspection images into
            explained, actionable reports.
          </p>
          <Link
            to="/signup"
            className="relative mt-8 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400 to-violet-500 px-7 py-3.5 text-base font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-shadow"
          >
            Create your free account
            <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </div>
    </section>
  )
}
