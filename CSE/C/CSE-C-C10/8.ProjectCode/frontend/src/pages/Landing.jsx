import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'
import { ArrowRight, BarChart3, Brain, FileSearch, GitCompareArrows, Moon, ScanSearch, Sun, Target } from 'lucide-react'
import { useEffect, useLayoutEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useApi } from '../api'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, SlideUp } from '../components/motion'
import Backdrop from '../components/reactbits/Backdrop'
import Logo from '../components/ui/Logo'
import { IconButton } from '../components/ui/controls'
import { StatusDot } from '../components/ui/display'
import Typewriter from '../components/ui/Typewriter'
import { fixed, num, pct } from '../format'
import { useAuth } from '../lib/auth'
import { useReducedMotion } from '../lib/reduced'
import { useTheme } from '../lib/theme'

gsap.registerPlugin(ScrollTrigger)

const FEATURES = [
  { icon: ScanSearch, title: 'Outcome prediction', text: 'Structured signals (funding, rounds, milestones, relationships, industry, investors) plus a free-text description give a SUCCESS or FAILURE estimate with confidence.' },
  { icon: GitCompareArrows, title: 'Similar-case evidence', text: 'Every prediction shows the comparable historical startups it was matched against, with cosine-similarity scores, outcomes, funding and summaries.' },
  { icon: Brain, title: 'Fused representation', text: 'Scaled structured features and all-MiniLM-L6-v2 text embeddings are fused (α = 0.5) so the text and the numbers both count.' },
  { icon: Target, title: 'Four validated models', text: 'Logistic Regression, Decision Tree, Random Forest and XGBoost compared over 5 repeated stratified 80/20 splits; the best by balanced accuracy serves.' },
  { icon: BarChart3, title: 'Live dashboards', text: 'Model comparison, confusion matrix, feature importance, retrieval-size study and industry success rates, computed from the loaded data.' },
  { icon: FileSearch, title: 'Local-first', text: 'No API keys and no external prediction service. Everything, including the embedding model, runs on localhost.' },
]
const STEPS = [
  ['Enter the signals', 'Funding, rounds, milestones, relationships, industry, investors, plus a few sentences describing the business.'],
  ['Fuse and embed', 'Structured features are scaled, the description is embedded, and the two blocks are fused into one vector.'],
  ['Retrieve comparable startups', 'Cosine similarity against training records only returns a balanced set of k historical startups.'],
  ['Predict and explain', 'The best validated classifier gives the outcome and probability; coefficients and retrieval statistics explain it.'],
]
const TICKER = ['balanced accuracy', 'all-MiniLM-L6-v2', 'cosine retrieval', 'logistic regression', 'xgboost', 'random forest', 'confusion matrix', 'k = 50 comparable cases', 'local-first']

function useLenis(reduced) {
  useEffect(() => {
    if (reduced) return
    const lenis = new Lenis({ lerp: 0.1, anchors: true })
    lenis.on('scroll', ScrollTrigger.update)
    const raf = (t) => lenis.raf(t * 1000)
    gsap.ticker.add(raf)
    gsap.ticker.lagSmoothing(0)
    return () => {
      gsap.ticker.remove(raf)
      lenis.destroy()
    }
  }, [reduced])
}

// Real readout of two public endpoints.
function LiveReadout() {
  const health = useApi('/health', { silent: true })
  const insights = useApi('/insights', { silent: true })
  const down = health.error && !health.loading
  const i = insights.data
  const line = (k, v, tone = 'fg') => (
    <div className="flex justify-between gap-4"><span className="text-dim">{k}</span><span style={{ color: `var(--${tone})` }}>{v}</span></div>
  )
  return (
    <div className="panel scan w-full max-w-md overflow-hidden font-mono text-[12px]">
      <div className="relative z-[1] flex items-center gap-1.5 border-b border-line px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-alert/70" /><span className="h-2 w-2 rounded-full bg-warn/70" /><span className="h-2 w-2 rounded-full bg-ok/70" />
        <span className="ml-2 text-[11px] text-dim">venturepulse — live</span>
      </div>
      <div className="relative z-[1] space-y-1 p-4 leading-relaxed">
        <div className="text-ok">$ curl /api/health</div>
        {down ? line('status', 'unreachable - start run.bat', 'alert') : !health.data ? <div className="text-dim">connecting…</div> : (
          <>
            {line('status', health.data.status, 'ok')}
            {line('best_model', health.data.best_model)}
            {line('records', num(health.data.records))}
          </>
        )}
        {i && (
          <>
            <div className="pt-2 text-ok">$ curl /api/insights</div>
            {line('success', num(i.success), 'ok')}
            {line('failure', num(i.failure), 'alert')}
            {line('success_rate', pct(i.success_rate, 1))}
          </>
        )}
        <div className="flex items-center gap-2 pt-1 text-ok">$ <span className="tw-caret" aria-hidden="true" /></div>
      </div>
    </div>
  )
}

function HowItWorks({ reduced }) {
  const rail = useRef(null)
  const section = useRef(null)
  useLayoutEffect(() => {
    if (reduced || !rail.current) return
    const ctx = gsap.context(() => {
      gsap.fromTo(rail.current, { scaleY: 0 }, { scaleY: 1, ease: 'none', scrollTrigger: { trigger: section.current, start: 'top 60%', end: 'bottom 70%', scrub: true } })
    }, section)
    return () => ctx.revert()
  }, [reduced])
  return (
    <section id="how" ref={section} className="relative mx-auto grid max-w-6xl grid-cols-1 gap-10 px-4 py-24 sm:px-6 lg:grid-cols-[1fr_1.3fr]">
      <div className="lg:sticky lg:top-28 lg:self-start">
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-ok">// how it works</div>
        <h2 className="mt-3 font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">From a few signals to an evidence-backed estimate in four passes.</h2>
        <p className="mt-4 max-w-md text-muted">Every pass runs on your machine against the stored historical startups. The first start trains the models; later starts load them in seconds.</p>
      </div>
      <ol className="relative space-y-6 pl-8">
        <span className="absolute bottom-2 left-[7px] top-2 w-px bg-line-strong" aria-hidden="true" />
        <span ref={rail} className="absolute bottom-2 left-[7px] top-2 w-px origin-top bg-ok shadow-[0_0_12px_var(--ok)]" aria-hidden="true" />
        {STEPS.map(([title, text], i) => (
          <Reveal as="li" key={title} className="relative" y={40}>
            <span className="absolute -left-8 top-5 grid h-[15px] w-[15px] place-items-center rounded-full border border-ok bg-bg" aria-hidden="true">
              <span className="h-1.5 w-1.5 rounded-full bg-ok" />
            </span>
            <div className="panel scan p-5">
              <div className="relative z-[1] font-mono text-[11px] text-ok">0{i + 1} / 04</div>
              <h3 className="relative z-[1] mt-1 font-mono text-lg font-semibold text-fg">{title}</h3>
              <p className="relative z-[1] mt-2 text-sm text-muted">{text}</p>
            </div>
          </Reveal>
        ))}
      </ol>
    </section>
  )
}

function StatsStrip() {
  const insights = useApi('/insights', { silent: true })
  const metrics = useApi('/model-metrics', { silent: true })
  const i = insights.data
  const m = metrics.data
  const best = m && m.models[m.best_model]
  const items = i && best
    ? [[i.total, 'historical startups', num], [i.success_rate * 100, 'overall success rate', (v) => `${v.toFixed(1)}%`],
      [best.balanced_accuracy.mean, 'balanced accuracy (best model)', (v) => fixed(v, 3)], [Object.keys(m.models).length, 'classifiers compared', num]]
    : [[4, 'classifiers compared', num], [5, 'repeated 80/20 splits', num], [384, 'text-embedding dimensions', num], [50, 'default comparable cases', num]]
  return (
    <section className="border-y border-line bg-panel/60">
      <Reveal stagger={0.08} className="mx-auto grid max-w-6xl grid-cols-2 divide-line px-4 sm:px-6 lg:grid-cols-4 lg:divide-x">
        {items.map(([v, label, f]) => (
          <div key={label} className="px-2 py-8 lg:px-6">
            <div className="font-mono text-3xl font-semibold text-fg sm:text-4xl"><CountUp value={v} format={f} /></div>
            <div className="mt-1 font-mono text-[11px] uppercase tracking-[0.14em] text-muted">{label}</div>
          </div>
        ))}
      </Reveal>
      <p className="mx-auto max-w-6xl px-4 pb-4 font-mono text-[10px] uppercase tracking-wider text-dim sm:px-6">
        {i ? <><StatusDot tone="ok" className="mr-1.5" /> live from the running API</> : 'start the backend to see live counts'}
      </p>
    </section>
  )
}

export default function Landing() {
  const { user } = useAuth()
  const { theme, toggle } = useTheme()
  const reduced = useReducedMotion()
  useLenis(reduced)
  const cta = user ? '/app' : '/login'

  return (
    <div className="relative min-h-screen overflow-x-clip">
      <header className="sticky top-0 z-30 border-b border-line bg-bg/70 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4 sm:px-6">
          <Link to="/"><Logo /></Link>
          <nav aria-label="Sections" className="ml-4 hidden gap-5 font-mono text-[11px] uppercase tracking-[0.14em] text-muted md:flex">
            <a href="#how" className="hover:text-ok">How it works</a>
            <a href="#features" className="hover:text-ok">Features</a>
          </nav>
          <div className="flex-1" />
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
          <Link to={cta} className="inline-flex h-9 items-center gap-1.5 rounded-[6px] border border-line-strong px-3 font-mono text-xs text-fg hover:border-ok hover:text-ok">
            {user ? 'Open dashboard' : 'Sign in'} <ArrowRight size={14} />
          </Link>
        </div>
      </header>

      <section className="relative">
        <Backdrop className="absolute inset-0 fade-mask" />
        <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-4 pb-20 pt-16 sm:px-6 sm:pt-24 lg:grid-cols-[1.25fr_1fr]">
          <div>
            <SlideUp className="inline-flex items-center gap-2 rounded-full border border-ok/30 bg-ok/5 px-3 py-1 font-mono text-[11px] uppercase tracking-[0.14em] text-ok">
              <StatusDot tone="ok" /> startup outcome prediction
            </SlideUp>
            <Typewriter as="h1" speed={22} delay={250} keepCaret
              text="Will this startup succeed? Read the signals, then check the evidence."
              className="mt-6 font-mono text-3xl font-semibold leading-[1.15] tracking-tight text-fg sm:text-5xl" />
            <SlideUp delay={0.35}>
              <p className="mt-6 max-w-xl text-lg text-muted">
                VenturePulse combines funding and traction signals with a business description, finds comparable historical
                startups, and predicts SUCCESS or FAILURE with a validated machine-learning model.
              </p>
            </SlideUp>
            <SlideUp delay={0.5} className="mt-8 flex flex-wrap gap-3">
              <MagneticButton>
                <Link to={cta} className="inline-flex h-11 items-center gap-2 rounded-[6px] bg-ok px-5 text-sm font-semibold text-on-ok shadow-[0_0_0_1px_var(--ok),0_0_28px_-6px_var(--ok)] hover:brightness-110">
                  {user ? 'Open the control room' : 'Get started'} <ArrowRight size={16} />
                </Link>
              </MagneticButton>
              {!user && (
                <MagneticButton>
                  <Link to="/login?demo=1" className="inline-flex h-11 items-center gap-2 rounded-[6px] border border-line-strong bg-panel/70 px-5 text-sm font-medium text-fg hover:border-ok/60 hover:text-ok">
                    Try the demo account
                  </Link>
                </MagneticButton>
              )}
            </SlideUp>
          </div>
          <Parallax speed={0.12} className="flex justify-center lg:justify-end">
            <SlideUp delay={0.6} className="w-full max-w-md"><LiveReadout /></SlideUp>
          </Parallax>
        </div>
      </section>

      <div className="border-y border-line bg-panel/50 py-3">
        <Marquee duration={36}>
          {TICKER.map((t) => (
            <span key={t} className="flex items-center gap-6 pr-6 font-mono text-xs uppercase tracking-[0.18em] text-muted">
              <span className="text-ok">◆</span>{t}
            </span>
          ))}
        </Marquee>
      </div>

      <HowItWorks reduced={reduced} />

      <section id="features" className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-ok">// capabilities</div>
        <h2 className="mt-3 max-w-2xl font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">Built for analysts, students and early-stage investors.</h2>
        <Reveal stagger={0.08} className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="panel scan group p-5 transition-[border-color,box-shadow] duration-300 hover:border-ok/40 hover:shadow-[0_0_0_1px_var(--ok),0_0_30px_-14px_var(--ok)]">
              <div className="relative z-[1] grid h-9 w-9 place-items-center rounded-[6px] border border-ok/30 bg-ok/10 text-ok"><Icon size={18} aria-hidden="true" /></div>
              <h3 className="relative z-[1] mt-4 font-mono text-[15px] font-semibold text-fg">{title}</h3>
              <p className="relative z-[1] mt-2 text-sm text-muted">{text}</p>
            </div>
          ))}
        </Reveal>
      </section>

      <StatsStrip />

      <section className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <Reveal className="panel scan relative overflow-hidden p-8 sm:p-12">
          <Backdrop intensity={1.4} className="absolute inset-0 opacity-60 fade-mask" />
          <div className="relative z-[1] max-w-2xl">
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-ok">// ready</div>
            <h2 className="mt-3 font-mono text-2xl font-semibold tracking-tight text-fg sm:text-4xl">Describe a startup and see what the history says.</h2>
            <p className="mt-4 text-muted">Sign in with the demo account; the models are already trained and the historical data is loaded.</p>
            <div className="mt-8">
              <MagneticButton>
                <Link to={user ? '/app/analyze' : '/login?demo=1'} className="inline-flex h-11 items-center gap-2 rounded-[6px] bg-ok px-5 text-sm font-semibold text-on-ok hover:brightness-110">
                  {user ? 'Analyze a startup' : 'Sign in with the demo account'} <ArrowRight size={16} />
                </Link>
              </MagneticButton>
            </div>
          </div>
        </Reveal>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-8 sm:px-6">
          <Logo />
          <p className="max-w-xl font-mono text-[11px] text-dim">Estimated startup outcome. Predictions are probabilistic estimates from historical correlations, not investment advice.</p>
          <nav aria-label="Footer" className="flex gap-4 font-mono text-[11px] uppercase tracking-wider text-muted">
            <a href="#how" className="hover:text-ok">How it works</a>
            <a href="#features" className="hover:text-ok">Features</a>
            <Link to={cta} className="hover:text-ok">{user ? 'Dashboard' : 'Sign in'}</Link>
          </nav>
        </div>
      </footer>
    </div>
  )
}
