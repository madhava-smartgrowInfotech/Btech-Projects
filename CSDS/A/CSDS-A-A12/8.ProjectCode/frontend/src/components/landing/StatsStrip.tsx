import { Reveal } from '../ui/Reveal'

const stats = [
  { value: '94.2%', label: 'Model accuracy on held-out batches' },
  { value: '7', label: 'Millet varieties supported' },
  { value: '<3s', label: 'Average prediction latency' },
  { value: '6', label: 'Fused environmental signals' },
]

export function StatsStrip() {
  return (
    <section className="relative py-20 px-6 border-t border-[var(--color-border-soft)] bg-[var(--color-bg-soft)]">
      <div className="mx-auto max-w-6xl grid grid-cols-2 lg:grid-cols-4 gap-10">
        {stats.map((s, i) => (
          <Reveal key={s.label} delay={i * 0.08}>
            <div className="text-center lg:text-left">
              <div className="font-display text-4xl sm:text-5xl font-bold text-gradient">{s.value}</div>
              <p className="text-sm text-[var(--color-text-muted)] mt-2">{s.label}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  )
}
