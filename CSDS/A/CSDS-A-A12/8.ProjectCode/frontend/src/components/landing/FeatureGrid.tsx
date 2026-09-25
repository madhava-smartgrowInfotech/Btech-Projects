import { ScanEye, CloudSun, MessagesSquare, TrendingUp, Layers, ShieldCheck } from 'lucide-react'
import { Card } from '../ui/Card'
import { Reveal } from '../ui/Reveal'

const features = [
  {
    icon: ScanEye,
    title: 'Vision-first trait extraction',
    desc: 'A self-supervised encoder reads morphology, texture, and color signal straight from a single seed photo — no manual measurement.',
    span: 'lg:col-span-2',
  },
  {
    icon: CloudSun,
    title: 'Environmental fusion',
    desc: 'Soil moisture, temperature, humidity, rainfall, and pH are fused with visual embeddings for context-aware predictions.',
    span: '',
  },
  {
    icon: MessagesSquare,
    title: 'Explainable advisories',
    desc: 'Every prediction ships with a plain-language explanation and concrete crop-management recommendations.',
    span: '',
  },
  {
    icon: TrendingUp,
    title: 'Batch analytics',
    desc: 'Track germination rate trends, confidence distributions, and variety performance across every batch you run.',
    span: 'lg:col-span-2',
  },
  {
    icon: Layers,
    title: 'Multi-variety coverage',
    desc: 'Pearl, finger, foxtail, kodo, little, proso, and barnyard millet — tuned per-variety.',
    span: '',
  },
  {
    icon: ShieldCheck,
    title: 'Confidence-scored output',
    desc: 'Risk-tiered results (low / medium / high) so agronomists know when to trust the call — and when to re-test.',
    span: '',
  },
]

export function FeatureGrid() {
  return (
    <section className="relative py-28 px-6">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <span className="text-emerald-400 text-sm font-semibold tracking-wide uppercase">Platform</span>
          <h2 className="font-display text-3xl sm:text-4xl font-bold mt-3 max-w-xl">
            Everything an agronomy team needs to trust a prediction
          </h2>
        </Reveal>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mt-14">
          {features.map((f, i) => (
            <Reveal key={f.title} delay={i * 0.06} className={f.span}>
              <Card glow className="h-full group hover:-translate-y-1 transition-transform duration-300">
                <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-5 group-hover:bg-emerald-500/15 transition-colors">
                  <f.icon size={20} className="text-emerald-300" />
                </div>
                <h3 className="font-display text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">{f.desc}</p>
              </Card>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
