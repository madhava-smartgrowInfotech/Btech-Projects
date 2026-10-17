import { useEffect } from 'react'
import { useReducedMotion } from 'framer-motion'
import { ArrowRight, BarChart3, Atom, FileSpreadsheet, FlaskConical, Gauge, LayoutDashboard, ScanSearch, ShieldCheck, Sparkles, Wand2 } from 'lucide-react'
import { api } from '../lib/api'
import { useApi } from '../lib/useApi'
import { fmtInt, fmtPoints } from '../lib/format'
import { CHANNELS, MERCHANTS, MODE_CODE, MODE_LABEL } from '../lib/labels'
import { BarCompare } from '../components/charts'
import { Badge, Brand, Button, Container, ErrorState, Skeleton, ThemeToggle } from '../components/ui'
import { CountUp, FadeIn, MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'

const STEPS = [
  { icon: ScanSearch, tone: 'var(--lavender)', title: 'Describe the payment', text: 'Enter one transaction or upload a CSV: amount, merchant, channel, card and country signals.' },
  { icon: Wand2, tone: 'var(--mint)', title: 'Prepare the features', text: 'The same encoding and scaling used in training is applied, so inputs match what the models learned.' },
  { icon: Atom, tone: 'var(--sky)', title: 'Three models vote', text: 'Classical, annealing and quantum-inspired RBM classifiers each score the transaction.' },
  { icon: Gauge, tone: 'var(--peach)', title: 'Get a decision band', text: 'Below 40% approve, 40 to 70% challenge, above 70% decline and alert.' },
]

const FEATURES = [
  { icon: ScanSearch, tone: 'var(--lavender)', title: 'Verify a transaction', text: 'An instant fraud probability with a per-model breakdown and a recommended action.', to: '/app/verify', where: 'Verify' },
  { icon: FileSpreadsheet, tone: 'var(--mint)', title: 'Bulk verification', text: 'Screen a whole CSV at once, score it against labels and download every prediction.', to: '/app/bulk', where: 'Bulk' },
  { icon: BarChart3, tone: 'var(--sky)', title: 'Fraud analytics', text: 'See fraud rate by merchant, channel, hour, amount band and card signals.', to: '/app/analytics', where: 'Analytics' },
  { icon: Atom, tone: 'var(--rose)', title: 'Model comparison', text: 'Compare the three samplers, their training curves, features and QUBO matrix.', to: '/app/models', where: 'Models' },
  { icon: FlaskConical, tone: 'var(--butter)', title: 'Model lab', text: 'Regenerate data, rebuild preprocessing and retrain when you want fresh models.', to: '/app/lab', where: 'Lab' },
  { icon: LayoutDashboard, tone: 'var(--peach)', title: 'Dashboard', text: 'A calm overview of the dataset, the loaded models and what fraud looks like in it.', to: '/app', where: 'Dashboard' },
]

function useSmoothScroll() {
  const reduce = useReducedMotion()
  useEffect(() => {
    if (reduce) return undefined
    let raf
    let lenis
    let cancelled = false
    import('lenis').then(({ default: Lenis }) => {
      if (cancelled) return
      lenis = new Lenis({ lerp: 0.12 })
      const tick = (t) => {
        lenis.raf(t)
        raf = requestAnimationFrame(tick)
      }
      raf = requestAnimationFrame(tick)
    })
    return () => {
      cancelled = true
      cancelAnimationFrame(raf)
      lenis?.destroy()
    }
  }, [reduce])
}

export default function Landing() {
  useSmoothScroll()
  const state = useApi(() => Promise.all([api.comparison(), api.health()]))
  const [comparison, health] = state.data || []
  const best = comparison?.length ? [...comparison].sort((a, b) => b['F1-Score'] - a['F1-Score'])[0] : null

  useEffect(() => {
    document.title = 'SecurePay AI · Card fraud screening'
  }, [])

  return (
    <div className="landing">
      <a className="skip-link" href="#top">Skip to content</a>
      <header className="l-nav">
        <Container>
          <Brand />
          <nav className="l-nav-links" aria-label="Page sections">
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#signals">Signals</a>
          </nav>
          <div className="l-actions">
            <ThemeToggle />
            <Button to="/app" size="sm" className="btn-open-app" iconRight={ArrowRight}><span>Open the app</span></Button>
          </div>
        </Container>
      </header>

      <main id="top">
        <section className="hero">
          <Blobs preset="hero" />
          <Container>
            <div className="hero-grid">
              <div>
                <FadeIn>
                  <Badge tone="lavender" icon={Sparkles}>Quantum-assisted fraud screening</Badge>
                </FadeIn>
                <SlideUp delay={0.05}>
                  <h1 style={{ marginTop: 18 }}>
                    Catch card fraud <span className="hl">before</span> it settles
                  </h1>
                </SlideUp>
                <SlideUp delay={0.12}>
                  <p className="hero-lead">
                    SecurePay AI scores every card transaction with three restricted Boltzmann machine classifiers and tells you whether to approve, challenge or decline.
                  </p>
                </SlideUp>
                <SlideUp delay={0.18} className="hero-cta">
                  <MagneticButton>
                    <Button to="/app" size="lg" iconRight={ArrowRight}>Open the dashboard</Button>
                  </MagneticButton>
                  <Button to="/app/verify" size="lg" variant="secondary" icon={ScanSearch}>Verify a transaction</Button>
                </SlideUp>
                <FadeIn delay={0.4} className="hero-note">
                  {MERCHANTS.slice(0, 4).map((m) => (
                    <Badge key={m} tone="neutral">{m}</Badge>
                  ))}
                  <Badge tone="neutral">+ more categories</Badge>
                </FadeIn>
              </div>
              <SlideUp delay={0.2} className="hero-visual">
                <div className="hero-card">
                  <div className="row between" style={{ marginBottom: 6 }}>
                    <h2 style={{ fontSize: 16 }}>Model F1 at best epoch</h2>
                    <Badge tone="mint" dot>Live from the API</Badge>
                  </div>
                  {state.loading && !state.data && <Skeleton height={230} radius={18} />}
                  {state.error && <ErrorState compact title="Live numbers unavailable" error={state.error} onRetry={state.reload} />}
                  {comparison && (
                    <BarCompare
                      height={230}
                      name="F1"
                      label="F1 score for each of the three models"
                      valueFormat={(v) => `${v}%`}
                      data={comparison.map((c) => ({ name: MODE_CODE[c.mode], value: c['F1-Score'], highlight: c.mode === best?.mode }))}
                    />
                  )}
                </div>
                {best && (
                  <div className="hero-float b">
                    <ShieldCheck size={24} aria-hidden="true" style={{ color: 'var(--mint-ink)' }} />
                    <div>
                      <b>{fmtPoints(best['F1-Score'])}</b>
                      <span>{MODE_LABEL[best.mode]} F1</span>
                    </div>
                  </div>
                )}
                {health && (
                  <div className="hero-float a">
                    <Gauge size={24} aria-hidden="true" style={{ color: 'var(--lavender-ink)' }} />
                    <div>
                      <b>{fmtInt(health.data_rows)}</b>
                      <span>transactions in the dataset</span>
                    </div>
                  </div>
                )}
              </SlideUp>
            </div>
          </Container>
        </section>

        {comparison && health && (
          <Container>
            <Reveal>
              <div className="stats-strip" aria-label="Headline numbers">
                <div className="s"><b><CountUp value={health.data_rows} /></b><span>transactions in the dataset</span></div>
                <div className="s"><b><CountUp value={health.models_trained.length} /> of 3</b><span>models loaded</span></div>
                <div className="s"><b><CountUp value={best?.['F1-Score'] ?? 0} format={(v) => `${v.toFixed(1)}%`} /></b><span>best F1 ({best ? MODE_CODE[best.mode] : '–'})</span></div>
                <div className="s"><b><CountUp value={best?.Precision ?? 0} format={(v) => `${v.toFixed(1)}%`} /></b><span>precision of the best model</span></div>
              </div>
            </Reveal>
          </Container>
        )}

        <section className="section" id="how">
          <Container>
            <Reveal className="section-head">
              <Badge tone="sky">How it works</Badge>
              <h2>From one payment to one clear decision</h2>
              <p>Four calm steps, the same every time.</p>
            </Reveal>
            <div className="steps-line" aria-hidden="true"><div /></div>
            <Stagger className="steps" inView>
              {STEPS.map((s, i) => (
                <Stagger.Item key={s.title} className="step-card">
                  <span className="n">Step {i + 1}</span>
                  <span className="ico" style={{ background: s.tone }}><s.icon size={24} aria-hidden="true" /></span>
                  <h3>{s.title}</h3>
                  <p>{s.text}</p>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="features" style={{ background: 'var(--bg-tint)' }}>
          <Container>
            <Reveal className="section-head">
              <Badge tone="mint">Features</Badge>
              <h2>Everything a risk team reaches for</h2>
              <p>Six screens, each wired to the live API.</p>
            </Reveal>
            <Stagger className="features" inView>
              {FEATURES.map((f) => (
                <Stagger.Item key={f.title}>
                  <div className="feature">
                    <span className="ico" style={{ background: f.tone }}><f.icon size={26} aria-hidden="true" /></span>
                    <h3>{f.title}</h3>
                    <p>{f.text}</p>
                    <div className="where">
                      <Button to={f.to} variant="ghost" size="sm" iconRight={ArrowRight}>Open {f.where}</Button>
                    </div>
                  </div>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="signals">
          <Container>
            <Reveal className="section-head">
              <Badge tone="peach">Signals</Badge>
              <h2>What the models look at</h2>
              <p>Merchant, channel, card presence, country match, amount, time and 22 anonymised behaviour features.</p>
            </Reveal>
            <Marquee>
              {[...MERCHANTS, ...CHANNELS.filter((c) => !MERCHANTS.includes(c)), 'Card present', 'Country match', 'Amount', 'Time of day'].map((c) => (
                <span className="chip" key={c}><Sparkles size={14} aria-hidden="true" />{c}</span>
              ))}
            </Marquee>
          </Container>
        </section>

        <section className="section">
          <Container>
            <Reveal className="cta">
              <Blobs preset="cta" />
              <h2>Ready to screen your first transaction?</h2>
              <p>Open the dashboard, try the example fraud case, or drop in a CSV.</p>
              <div className="row" style={{ justifyContent: 'center' }}>
                <MagneticButton><Button to="/app/verify" size="lg" iconRight={ArrowRight}>Verify a transaction</Button></MagneticButton>
                <Button to="/app/bulk" size="lg" variant="secondary">Upload a CSV</Button>
              </div>
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="footer">
        <Container>
          <span>© 2026 SecurePay AI · Credit card fraud detection using machine learning</span>
          <span>Trained on a synthetic dataset; not for production payments.</span>
        </Container>
      </footer>
    </div>
  )
}
