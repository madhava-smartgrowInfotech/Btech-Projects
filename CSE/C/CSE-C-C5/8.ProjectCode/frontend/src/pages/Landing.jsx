import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'
import { ArrowRight, BarChart3, Building2, Moon, Sparkles, Sun, Target, Users } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CountUp, MagneticButton, Marquee, Reveal, SlideUp } from '../components/motion'
import Backdrop from '../components/three/Backdrop'
import { Container } from '../components/ui/AppShell'
import { Button, IconButton } from '../components/ui/controls'
import { Badge, StatusDot } from '../components/ui/display'
import { ErrorState } from '../components/ui/feedback'
import Logo from '../components/ui/Logo'
import Typewriter from '../components/ui/Typewriter'
import { modelLabel, pct } from '../format'
import { useData } from '../lib/data'
import { useReducedMotion } from '../lib/reduced'
import { useTheme } from '../lib/theme'
import useFetch from '../lib/useFetch'

const HYBRID = 'hybrid_xgb_knn'

const STEPS = [
  ['01', 'Calibrated XGBoost', 'Gradient-boosted trees score each student against a company and role, then Platt scaling makes the probability trustworthy.'],
  ['02', 'kNN residual refinement', 'Borderline probabilities in [0.4, 0.6] are blended with a local kNN, fixing similar-profile errors a global model misses.'],
  ['03', 'SHAP explainability', 'Every decision can be traced to CGPA, company tier, skill index and the other features the officer cares about.'],
  ['04', 'Hybrid company-role ranking', 'Alternatives are ranked on acceptance probability, CGPA proximity and location - the dual-axis idea from the base paper.'],
]
const ROLES = [
  ['/predict', Target, 'Student', 'Check placement probability for any company and role, with skill-gap tips.'],
  ['/recommend', Sparkles, 'Recommendations', 'Rejected or low probability? Get the top company-role pairs with the best chance.'],
  ['/dashboard', BarChart3, 'Placement officer', 'Model metrics, SHAP, PCA, probability histogram and branch-wise placement rates.'],
  ['/recruiter', Users, 'Recruiter', 'Shortlist placement-ready students by CGPA, aptitude and branch.'],
]

// Smooth scrolling for the landing page only; off under reduced motion.
function useSmoothScroll(disabled) {
  useEffect(() => {
    if (disabled) return
    const lenis = new Lenis()
    lenis.on('scroll', ScrollTrigger.update)
    const tick = (t) => lenis.raf(t * 1000)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)
    return () => { gsap.ticker.remove(tick); lenis.destroy() }
  }, [disabled])
}

function Terminal({ lines, ready }) {
  const reduced = useReducedMotion()
  const [shown, setShown] = useState(0)
  useEffect(() => {
    if (!ready) return
    if (reduced) { setShown(lines.length); return }
    setShown(0)
    let i = 0
    const id = setInterval(() => { i += 1; setShown(i); if (i >= lines.length) clearInterval(id) }, 420)
    return () => clearInterval(id)
  }, [ready, lines.length, reduced]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className="panel scan overflow-hidden">
      <div className="relative z-[1] flex items-center gap-2 border-b border-line px-3 py-2 font-mono text-[11px] text-muted">
        <span className="flex gap-1.5" aria-hidden="true"><i className="h-2 w-2 rounded-full bg-alert" /><i className="h-2 w-2 rounded-full bg-warn" /><i className="h-2 w-2 rounded-full bg-ok" /></span>
        <span className="ml-1 truncate">~/placement/boot.log</span>
        <span className="ml-auto"><StatusDot tone={ready ? 'ok' : 'warn'} label={ready ? 'live' : 'connecting'} /></span>
      </div>
      <div className="relative z-[1] min-h-[236px] space-y-1 px-3 py-3 font-mono text-[12px] leading-relaxed" role="log" aria-label="System status log">
        {!ready && <div className="text-dim">$ connecting to api…</div>}
        {lines.slice(0, shown).map((l, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-ok">{l.cmd ? '$' : '›'}</span>
            <span className={l.cmd ? 'text-fg' : 'text-muted'}>{l.text}{l.tag && <span className={`ml-2 ${l.warn ? 'text-warn' : 'text-ok'}`}>[{l.tag}]</span>}</span>
          </div>
        ))}
        {ready && shown >= lines.length && <div className="flex gap-2 text-ok"><span>$</span><span className="tw-caret" aria-hidden="true" /></div>}
      </div>
    </div>
  )
}

export default function Landing() {
  const reduced = useReducedMotion()
  const { theme, toggle } = useTheme()
  const { companies, stats, error, reload } = useData()
  const metrics = useFetch('/metrics')
  const health = useFetch('/health', { silent: true })
  useSmoothScroll(reduced)

  const res = metrics.data?.results
  const hy = res?.[HYBRID]
  const ready = !!(stats && res && companies && health.data)
  const lines = ready ? [
    { cmd: true, text: 'placement --status' },
    { text: `models: xgb_calibrated · knn_residual · preprocess`, tag: health.data.models_ready ? 'ready' : 'missing', warn: !health.data.models_ready },
    { text: `dataset: ${stats.total.toLocaleString('en-IN')} students · ${pct(stats.placed_rate)} placed · avg CGPA ${stats.avg_cgpa}`, tag: 'ok' },
    { text: `companies: ${companies.length} loaded across 3 tiers`, tag: 'ok' },
    { cmd: true, text: 'placement --evaluate hybrid_xgb_knn' },
    { text: `auc ${hy.roc_auc.toFixed(4)} · f1 ${hy.f1.toFixed(4)} · recall ${hy.recall.toFixed(4)}`, tag: 'test set' },
    { text: `9-fold cv ${metrics.data.cv_xgb_9fold} · brier ${metrics.data.brier_platt} · residual ${pct(metrics.data.residual_rate)}`, tag: 'ok' },
  ] : []

  const modelRows = res ? Object.entries(res) : []

  return (
    <div className="relative min-h-screen overflow-x-clip">
      <a href="#top" className="sr-only z-50 rounded bg-ok px-3 py-2 text-on-ok focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
      <header className="sticky top-0 z-40 border-b border-line bg-bg/80 backdrop-blur-md">
        <Container className="flex h-14 items-center gap-3">
          <Link to="/" aria-label="Campus placement home"><Logo /></Link>
          <nav aria-label="Landing" className="ml-6 hidden items-center gap-5 font-mono text-xs text-muted md:flex">
            <a href="#pipeline" className="hover:text-ok">pipeline</a>
            <a href="#screens" className="hover:text-ok">screens</a>
            <a href="#models" className="hover:text-ok">models</a>
          </nav>
          <div className="flex-1" />
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
          <Link to="/predict" className="hidden sm:block"><Button size="sm" icon={ArrowRight}>Open console</Button></Link>
        </Container>
      </header>

      <main id="top">
        <section className="relative">
          <Backdrop intensity={1.1} className="absolute inset-x-0 top-0 h-[640px] fade-mask-bottom" />
          <Container className="relative grid gap-10 pb-16 pt-14 lg:grid-cols-[1.1fr_1fr] lg:items-center lg:pb-24 lg:pt-24">
            <div>
              <SlideUp><Badge tone="ok" dot>arXiv:2603.29881 · hybrid ML</Badge></SlideUp>
              <h1 className="mt-5 font-mono text-3xl font-semibold leading-[1.15] tracking-tight text-fg sm:text-4xl lg:text-[44px]">
                <Typewriter text="Predict the placement." speed={34} className="block" />
                <Typewriter text="Recommend the next offer." speed={34} delay={900} className="block text-ok" />
              </h1>
              <SlideUp delay={0.2}>
                <p className="mt-5 max-w-xl text-base text-muted">
                  A campus placement control room: a calibrated XGBoost model refined by kNN on borderline students,
                  explained with SHAP, plus a hybrid company-role recommender for everyone who just missed the cutoff.
                </p>
              </SlideUp>
              <SlideUp delay={0.3} className="mt-8 flex flex-wrap items-center gap-3">
                <MagneticButton><Link to="/predict"><Button size="lg" icon={ArrowRight}>Check my eligibility</Button></Link></MagneticButton>
                <Link to="/dashboard"><Button size="lg" variant="secondary" icon={BarChart3}>Officer dashboard</Button></Link>
              </SlideUp>
            </div>
            <SlideUp delay={0.25}>
              {error && !stats ? <ErrorState error={error} onRetry={reload} title="API offline" /> : <Terminal lines={lines} ready={ready} />}
            </SlideUp>
          </Container>
        </section>

        <section aria-label="Live figures" className="border-y border-line bg-panel/60">
          <Container className="grid grid-cols-2 gap-px bg-line py-0 md:grid-cols-4">
            {[
              ['Students', stats?.total, (v) => Math.round(v).toLocaleString('en-IN'), 'in the campus dataset'],
              ['Placed rate', stats && stats.placed_rate * 100, (v) => `${v.toFixed(1)}%`, 'historical'],
              ['Hybrid AUC', hy?.roc_auc, (v) => v.toFixed(4), 'XGBoost + kNN'],
              ['Companies', companies?.length, (v) => String(Math.round(v)), 'tiers 1 - 3'],
            ].map(([label, value, format, sub]) => (
              <div key={label} className="bg-bg px-4 py-6 sm:px-6">
                <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">{label}</div>
                <div className="mt-1 font-mono text-3xl font-semibold text-fg sm:text-4xl">
                  {typeof value === 'number' ? <CountUp value={value} format={format} /> : <span className="text-dim">…</span>}
                </div>
                <div className="mt-1 text-xs text-muted">{sub}</div>
              </div>
            ))}
          </Container>
        </section>

        <section id="pipeline" className="py-20">
          <Container>
            <Reveal>
              <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ok">// how it works</div>
              <h2 className="mt-2 max-w-2xl font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">Global model first, local correction where it is unsure.</h2>
            </Reveal>
            <Reveal stagger={0.1} className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {STEPS.map(([n, t, d]) => (
                <div key={n} className="panel scan p-5">
                  <div className="relative z-[1]">
                    <div className="font-mono text-2xl text-ok">{n}</div>
                    <h3 className="mt-3 font-mono text-sm font-semibold text-fg">{t}</h3>
                    <p className="mt-2 text-sm text-muted">{d}</p>
                  </div>
                </div>
              ))}
            </Reveal>
          </Container>
        </section>

        <section id="screens" className="border-t border-line bg-panel/40 py-20">
          <Container>
            <Reveal>
              <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ok">// workspaces</div>
              <h2 className="mt-2 font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">One platform, four people.</h2>
            </Reveal>
            <Reveal stagger={0.08} className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {ROLES.map(([to, Icon, t, d]) => (
                <Link key={to} to={to} className="panel scan group block p-5 transition-colors hover:border-ok/50">
                  <div className="relative z-[1]">
                    <Icon size={20} className="text-ok" aria-hidden="true" />
                    <h3 className="mt-4 font-mono text-sm font-semibold text-fg">{t}</h3>
                    <p className="mt-2 text-sm text-muted">{d}</p>
                    <span className="mt-4 inline-flex items-center gap-1 font-mono text-xs text-ok">open <ArrowRight size={13} className="transition-transform group-hover:translate-x-1" aria-hidden="true" /></span>
                  </div>
                </Link>
              ))}
            </Reveal>
          </Container>
        </section>

        <section id="models" className="py-20">
          <Container>
            <Reveal>
              <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ok">// model performance</div>
              <h2 className="mt-2 font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">Nine models, one held-out test set.</h2>
              <p className="mt-2 max-w-2xl text-sm text-muted">Measured on {metrics.data?.test_size ?? '…'} unseen students. The hybrid XGBoost + kNN leads on accuracy, F1 and recall.</p>
            </Reveal>
            <Reveal className="panel scan mt-8 overflow-hidden">
              <div className="relative z-[1] overflow-x-auto p-4">
                {metrics.error ? <ErrorState error={metrics.error} onRetry={metrics.reload} title="Could not load metrics" compact /> : (
                  <table className="w-full min-w-[520px] border-collapse text-sm">
                    <caption className="sr-only">Model metrics on the test set</caption>
                    <thead><tr className="border-b border-line-strong text-left font-mono text-[10px] uppercase tracking-[0.12em] text-dim">
                      <th scope="col" className="py-2 pr-3">Model</th>{['Acc', 'AUC', 'F1', 'Prec', 'Rec'].map((h) => <th key={h} scope="col" className="py-2 pr-3 text-right last:pr-0">{h}</th>)}
                    </tr></thead>
                    <tbody>
                      {modelRows.length === 0 && Array.from({ length: 5 }, (_, i) => <tr key={i}><td colSpan={6} className="py-2"><div className="skeleton h-6" /></td></tr>)}
                      {modelRows.map(([k, v]) => (
                        <tr key={k} className={`border-b border-line ${k === HYBRID ? 'bg-ok/[0.06]' : ''}`}>
                          <td className="py-2 pr-3 font-medium text-fg">{modelLabel(k)} {k === HYBRID && <Badge tone="ok" className="ml-1">proposed</Badge>}</td>
                          {['accuracy', 'roc_auc', 'f1', 'precision', 'recall'].map((m) => <td key={m} className="py-2 pr-3 text-right font-mono tabular-nums last:pr-0">{v[m].toFixed(4)}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </Reveal>
          </Container>
        </section>

        {companies && (
          <section aria-label="Recruiting companies" className="border-y border-line bg-panel/40 py-5">
            <Marquee duration={60}>
              {companies.map((c) => (
                <span key={c.Company} className="mx-5 inline-flex items-center gap-2 whitespace-nowrap font-mono text-sm text-muted">
                  <Building2 size={13} className="text-dim" aria-hidden="true" />{c.Company}<span className="text-ok">{c.Package_LPA} LPA</span>
                </span>
              ))}
            </Marquee>
          </section>
        )}

        <section className="py-20">
          <Container className="text-center">
            <Reveal>
              <h2 className="mx-auto max-w-2xl font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">Know your odds before the drive starts.</h2>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Link to="/predict"><Button size="lg" icon={ArrowRight}>Run a prediction</Button></Link>
                <Link to="/companies"><Button size="lg" variant="secondary" icon={Building2}>Browse companies</Button></Link>
              </div>
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="border-t border-line py-8">
        <Container className="flex flex-wrap items-center justify-between gap-3 font-mono text-[11px] text-dim">
          <Logo />
          <span>Smart Campus Placement System · Batch C-05 · base paper arXiv:2603.29881</span>
        </Container>
      </footer>
    </div>
  )
}
