import { Reveal } from '../ui/Reveal'

const steps = [
  {
    n: '01',
    title: 'Capture',
    desc: 'Photograph a seed sample and log the field or lab conditions — moisture, temperature, humidity, rainfall, soil pH.',
  },
  {
    n: '02',
    title: 'Encode',
    desc: 'A self-supervised vision encoder extracts morphological and spectral embeddings directly from the image.',
  },
  {
    n: '03',
    title: 'Fuse & predict',
    desc: 'Visual embeddings merge with environmental data and pass through the germination classifier.',
  },
  {
    n: '04',
    title: 'Explain',
    desc: 'The advisory layer ranks the driving factors and generates a clear, actionable recommendation.',
  },
]

export function HowItWorks() {
  return (
    <section className="relative py-28 px-6 border-t border-[var(--color-border-soft)]">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <span className="text-amber-400 text-sm font-semibold tracking-wide uppercase">Pipeline</span>
          <h2 className="font-display text-3xl sm:text-4xl font-bold mt-3 max-w-xl">
            From photo to prediction in four stages
          </h2>
        </Reveal>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mt-16 relative">
          <div className="hidden md:block absolute top-6 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--color-border)] to-transparent" />
          {steps.map((s, i) => (
            <Reveal key={s.n} delay={i * 0.1}>
              <div className="relative">
                <div className="w-12 h-12 rounded-full glass flex items-center justify-center font-display font-bold text-emerald-300 relative z-10">
                  {s.n}
                </div>
                <h3 className="font-display text-lg font-semibold mt-5">{s.title}</h3>
                <p className="text-sm text-[var(--color-text-muted)] mt-2 leading-relaxed">{s.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
