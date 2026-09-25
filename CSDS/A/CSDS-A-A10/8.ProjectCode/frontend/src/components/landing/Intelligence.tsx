import { motion } from 'framer-motion'
import { Brain, Gauge, ShieldAlert } from 'lucide-react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts'

import { CHART_CATEGORICAL, CHART_MUTED } from '@/lib/chartColors'

const WAIT_TREND = [
  { hour: '8am', before: 38, after: 22 },
  { hour: '10am', before: 52, after: 27 },
  { hour: '12pm', before: 61, after: 31 },
  { hour: '2pm', before: 49, after: 24 },
  { hour: '4pm', before: 55, after: 26 },
  { hour: '6pm', before: 44, after: 21 },
]

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-white/10 bg-ink-900 px-3 py-2 text-xs shadow-xl">
      <p className="mb-1 font-medium text-ink-200">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.dataKey === 'before' ? 'Manual process' : 'With MedFlow'}: {p.value} min
        </p>
      ))}
    </div>
  )
}

export function Intelligence() {
  return (
    <section id="intelligence" className="relative py-28">
      <div className="pointer-events-none absolute right-0 top-1/4 h-96 w-96 rounded-full bg-vital-500/10 blur-[120px]" />
      <div className="mx-auto grid max-w-7xl items-center gap-14 px-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-400">Intelligence</p>
          <h2 className="mt-3 font-display text-3xl font-bold text-white sm:text-4xl text-balance">
            Prediction that actually changes the queue
          </h2>
          <p className="mt-4 text-ink-400">
            MedFlow's wait-time model learns from live department load and priority mix, while the
            triage model scores incoming vitals against a clinical early-warning formula — so the
            sickest patients never wait behind routine visits.
          </p>

          <div className="mt-8 space-y-4">
            {[
              { icon: Gauge, title: 'Wait-time regression', desc: 'Recalculated per patient from real-time queue depth, department type and time of day.' },
              { icon: ShieldAlert, title: 'Clinical early-warning triage', desc: 'Vitals — heart rate, SpO2, BP, respiratory rate — are scored against a NEWS2-style composite.' },
              { icon: Brain, title: 'Continuously re-ranked queues', desc: 'The moment a critical case registers, every department queue re-prioritises automatically.' },
            ].map((item) => (
              <div key={item.title} className="flex gap-3.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-500/15 text-brand-400">
                  <item.icon size={17} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{item.title}</p>
                  <p className="mt-0.5 text-sm text-ink-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="rounded-2xl border border-white/8 bg-ink-850/70 p-6"
        >
          <div className="mb-1 flex items-center justify-between">
            <h3 className="font-display text-sm font-semibold text-white">Average wait time, by hour</h3>
            <div className="flex items-center gap-4 text-[11px] text-ink-400">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: CHART_MUTED }} /> Manual
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: CHART_CATEGORICAL[0] }} /> MedFlow
              </span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={WAIT_TREND} margin={{ top: 16, right: 8, left: -18, bottom: 0 }}>
                <defs>
                  <linearGradient id="afterFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={CHART_CATEGORICAL[0]} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={CHART_CATEGORICAL[0]} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="hour" stroke={CHART_MUTED} fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area
                  type="monotone"
                  dataKey="before"
                  stroke={CHART_MUTED}
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  fill="transparent"
                />
                <Area
                  type="monotone"
                  dataKey="after"
                  stroke={CHART_CATEGORICAL[0]}
                  strokeWidth={2.5}
                  fill="url(#afterFill)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
