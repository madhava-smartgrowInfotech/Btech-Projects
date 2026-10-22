import { lazy, Suspense, useEffect } from 'react'
import { useReducedMotion } from 'framer-motion'
import Lenis from 'lenis'
import { ArrowRight, Brain, ClipboardList, FlaskConical, Gauge, LineChart, ShieldCheck, TrendingUp, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useAsync } from '../lib/useAsync'
import { fmtSigned, modelLabel } from '../lib/format'
import { Badge, Brand, Button, Container, ErrorState, Skeleton, ThemeToggle } from '../components/ui'
import { CountUp, FadeIn, MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'

const ForecastChart = lazy(() => import('../components/charts/ForecastChart'))

const STEPS = [
  { t: 'Tell us about you', d: 'Twelve demographic and financial inputs, validated on the server.', icon: ClipboardList, tone: 'lavender' },
  { t: 'Engineer features', d: 'Net investment position, age bands, education tiers and more.', icon: Sparkles, tone: 'mint' },
  { t: 'Classify', d: 'The best of four compared models returns a profile and risk band.', icon: Gauge, tone: 'peach' },
  { t: 'Explain', d: 'Live SHAP shows what pushed the score up or down.', icon: Brain, tone: 'sky' },
  { t: 'Forecast & compare', d: 'A 12-month outlook and side-by-side what-if scenarios.', icon: TrendingUp, tone: 'rose' },
]

const FEATURES = [
  { icon: ClipboardList, tone: 'mint', title: 'Financial profiling', text: 'Emerging, Developing or Established - with a confidence score and a Low / Moderate / High risk band.', to: '/app/assess', where: 'Assessment' },
  { icon: Brain, tone: 'peach', title: 'Explainable by default', text: 'SHAP global importance and per-person strengthening and weakening factors in plain language.', to: '/app/explain', where: 'Explainability' },
  { icon: TrendingUp, tone: 'sky', title: 'Economic forecast', text: 'Holt-Winters projection of the index with a 95% interval and a readable interpretation.', to: '/app/forecast', where: 'Forecast' },
  { icon: FlaskConical, tone: 'rose', title: 'What-if scenarios', text: 'Change gains, losses, hours or education and see exactly how the modelled score moves.', to: '/app/whatif', where: 'What-if' },
  { icon: Gauge, tone: 'butter', title: 'Honest validation', text: 'Stratified 5-fold cross-validation and leakage-safe pipelines. Metrics come from real runs.', to: '/app/performance', where: 'Performance' },
  { icon: ShieldCheck, tone: 'lavender', title: 'Responsible by design', text: 'Informational insights only - never loan approval, credit decisions or guaranteed returns.', to: '/app/about', where: 'About' },
]

const TECH = ['XGBoost', 'Random Forest', 'Gradient Boosting', 'Logistic Regression', 'SHAP', 'Holt-Winters', 'scikit-learn', 'statsmodels', 'Flask', 'UCI Adult / Census Income']

function useSmoothScroll() {
  const reduce = useReducedMotion()
  useEffect(() => {
    if (reduce) return undefined
    const lenis = new Lenis({ lerp: 0.12 })
    let raf
    const loop = (t) => {
      lenis.raf(t)
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => {
      cancelAnimationFrame(raf)
      lenis.destroy()
    }
  }, [reduce])
}

function HeroVisual({ forecast, dash }) {
  const f = forecast.data
  return (
    <div className="hero-visual">
      <div className="hero-card">
        <div className="row between" style={{ marginBottom: 10 }}>
          <div>
            <strong>Household Financial Conditions Index</strong>
            <p className="small muted">History and 12-month forecast</p>
          </div>
          <Badge tone="mint">Illustrative series</Badge>
        </div>
        {forecast.loading && <Skeleton height={280} radius={18} />}
        {forecast.error && <ErrorState compact title="Live data unavailable" error={forecast.error} onRetry={forecast.reload} hint="Start the API with run.bat to see live model data here." />}
        {f?.available && (
          <Suspense fallback={<Skeleton height={280} radius={18} />}>
            <ForecastChart history={f.history} forecast={f.forecast} sinceYear={2022} height={280} />
          </Suspense>
        )}
      </div>
      {f?.available && (
        <FadeIn delay={0.7} className="hero-float a" style={{ bottom: -40 }}>
          <span className="stat-ico" style={{ background: 'var(--mint)', width: 38, height: 38, borderRadius: 13 }}><TrendingUp size={18} aria-hidden="true" /></span>
          <div><b>{fmtSigned(f.forecast_pct_change, 2)}</b><span>projected over {f.horizon_months} months</span></div>
        </FadeIn>
      )}
      {dash.data?.metrics?.roc_auc != null && (
        <FadeIn delay={0.9} className="hero-float b">
          <span className="stat-ico" style={{ background: 'var(--lavender)', width: 38, height: 38, borderRadius: 13 }}><Gauge size={18} aria-hidden="true" /></span>
          <div><b>{dash.data.metrics.roc_auc.toFixed(3)}</b><span>ROC-AUC · {modelLabel(dash.data.model)}</span></div>
        </FadeIn>
      )}
    </div>
  )
}

export default function Landing() {
  useSmoothScroll()
  const { user } = useAuth()
  const dash = useAsync(api.dashboard)
  const forecast = useAsync(api.forecast)
  const m = dash.data?.metrics
  const rows = dash.data?.training?.rows

  useEffect(() => {
    document.title = 'FinSight AI · Financial profile, explained'
  }, [])

  return (
    <div className="landing">
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="l-nav">
        <Container>
          <Brand />
          <nav className="l-nav-links" aria-label="Sections">
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#numbers">Numbers</a>
          </nav>
          <span style={{ flex: 1 }} />
          <ThemeToggle />
          {!user && <Button to="/login" size="sm" variant="ghost">Sign in</Button>}
          <Button to="/app" size="sm" className="btn-open-app" iconRight={ArrowRight}><span>Open the app</span></Button>
        </Container>
      </header>

      <main id="main" tabIndex={-1}>
        <section className="hero">
          <Blobs preset="hero" />
          <Container>
            <div className="hero-grid">
              <div>
                <SlideUp><span className="eyebrow"><Sparkles size={14} aria-hidden="true" />AI-based financial identification &amp; forecasting</span></SlideUp>
                <SlideUp delay={0.06}><h1 style={{ marginTop: 18 }}>Understand your financial profile, <span className="hl">gently</span>.</h1></SlideUp>
                <SlideUp delay={0.12}>
                  <p className="hero-lead">FinSight AI looks at age, occupation, education, income signals and location to identify your financial profile, assess risk, explain what drives it and project the economic outlook - in plain language.</p>
                </SlideUp>
                <SlideUp delay={0.18} className="hero-cta">
                  <MagneticButton><Button to="/app/assess" size="lg" icon={ClipboardList}>Start your assessment</Button></MagneticButton>
                  <Button to="/app" size="lg" variant="secondary" iconRight={ArrowRight}>Explore the dashboard</Button>
                </SlideUp>
                <SlideUp delay={0.24} className="hero-note">
                  <Badge tone="mint" icon={ShieldCheck}>Informational, not advice</Badge>
                  <Badge tone="lavender" icon={Brain}>Explained with SHAP</Badge>
                  <Badge tone="sky" icon={LineChart}>Runs locally</Badge>
                </SlideUp>
              </div>
              <HeroVisual forecast={forecast} dash={dash} />
            </div>
          </Container>
        </section>

        <section className="section" id="how">
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">How it works</span>
              <h2>From a few inputs to a clear picture</h2>
              <p>Five calm steps, all running on the model trained in this project.</p>
            </Reveal>
            <Reveal><div className="steps-line"><div /></div></Reveal>
            <Stagger className="steps" inView>
              {STEPS.map((s, i) => (
                <Stagger.Item key={s.t} className="step-card">
                  <span className="n">STEP {i + 1}</span>
                  <span className="ico" style={{ background: `var(--${s.tone})` }}><s.icon size={24} aria-hidden="true" /></span>
                  <h3>{s.t}</h3>
                  <p>{s.d}</p>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="features" style={{ background: 'var(--bg-tint)' }}>
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">Features</span>
              <h2>Everything the model can tell you</h2>
              <p>Each capability has its own screen, wired to the real API.</p>
            </Reveal>
            <Stagger className="features" inView>
              {FEATURES.map((f) => (
                <Stagger.Item key={f.title}>
                  <div className="feature">
                    <span className="ico" style={{ background: `var(--${f.tone})` }}><f.icon size={26} aria-hidden="true" /></span>
                    <h3>{f.title}</h3>
                    <p>{f.text}</p>
                    <div className="where"><Button to={f.to} variant="ghost" size="sm" iconRight={ArrowRight}>{f.where}</Button></div>
                  </div>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="numbers">
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">Numbers</span>
              <h2>Real results, not claims</h2>
              <p>Straight from the training run - held-out test set and 5-fold cross-validation.</p>
            </Reveal>
            {dash.loading && <Skeleton height={120} radius={28} />}
            {dash.error && <ErrorState compact title="Model numbers unavailable" error={dash.error} onRetry={dash.reload} hint="Start the API with run.bat to load live results." />}
            {m && (
              <Reveal className="stats-strip">
                <div className="s"><b><CountUp value={m.accuracy * 100} format={(v) => `${v.toFixed(1)}%`} /></b><span>Test accuracy</span></div>
                <div className="s"><b><CountUp value={m.roc_auc} format={(v) => v.toFixed(3)} /></b><span>ROC-AUC</span></div>
                <div className="s"><b><CountUp value={m.f1} format={(v) => v.toFixed(3)} /></b><span>F1 score</span></div>
                {rows != null && <div className="s"><b><CountUp value={rows} format={(v) => Math.round(v).toLocaleString('en-US')} /></b><span>Records in the dataset</span></div>}
              </Reveal>
            )}
            <div style={{ marginTop: 36 }}>
              <Marquee speed={44}>
                {TECH.map((t) => (
                  <span key={t} className="chip">{t}</span>
                ))}
              </Marquee>
            </div>
          </Container>
        </section>

        <section className="section" style={{ paddingTop: 0 }}>
          <Container>
            <Reveal>
              <div className="cta">
                <Blobs preset="cta" />
                <h2>Ready for a calmer look at your finances?</h2>
                <p>It takes about a minute. Nothing leaves your machine, and the result comes with the reasons behind it.</p>
                <MagneticButton><Button to="/app/assess" size="lg" icon={ClipboardList}>Start your assessment</Button></MagneticButton>
              </div>
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="footer">
        <Container>
          <p style={{ maxWidth: '70ch' }}><strong>FinSight AI</strong> · Informational financial-profile analysis. Model-based estimates, not professional financial advice. No prediction guarantees income, credit or loan outcomes. The forecast uses an illustrative index series.</p>
          <p>Trained on the UCI Adult / Census Income data.</p>
        </Container>
      </footer>
    </div>
  )
}
