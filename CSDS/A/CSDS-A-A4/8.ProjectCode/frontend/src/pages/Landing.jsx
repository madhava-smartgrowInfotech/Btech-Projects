import { useEffect, useRef } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import Lenis from 'lenis'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  ArrowRight,
  BarChart3,
  Boxes,
  Brain,
  Database,
  Gauge,
  MapPin,
  Moon,
  PackageCheck,
  RefreshCcw,
  Sparkles,
  Sun,
  TrendingUp,
  Zap,
} from 'lucide-react'
import NetworkMap from '../components/NetworkMap'
import Blobs from '../components/reactbits/Blobs'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, SlideUp, Stagger } from '../components/motion'
import { Badge, Brand, Button, ErrorState, IconButton, Skeleton } from '../components/ui'
import { api } from '../lib/api'
import { fmtCompact, fmtINR, fmtPct } from '../lib/format'
import { lift } from '../lib/motion'
import { cityIndex, getRegions } from '../lib/shared'
import { useTheme } from '../lib/theme'
import { useApi } from '../lib/useApi'

gsap.registerPlugin(ScrollTrigger)

const STEPS = [
  { icon: Database, tone: 'var(--sky)', title: 'Historical orders', text: '36 months of orders for 90 regions - growth, festival peaks, promotions - cleaned, de-duplicated and gap-filled.' },
  { icon: Brain, tone: 'var(--lavender)', title: 'Random Forest forecast', text: 'Lags, rolling means, seasonality and region attributes predict next-month demand for every region.' },
  { icon: Boxes, tone: 'var(--peach)', title: 'Hub location model', text: 'A capacitated single-allocation MIP: fixed hub cost, transport, delivery-time penalty and an SLA.' },
  { icon: Sparkles, tone: 'var(--mint)', title: 'Matheuristic solve', text: 'Greedy / k-medoids construction, MIP-priced local search, then a kernel search over a restricted exact MIP.' },
  { icon: RefreshCcw, tone: 'var(--rose)', title: 'Re-optimise monthly', text: 'Each new month re-forecasts and re-plans, opening or closing hubs as demand shifts.' },
]

const FEATURES = [
  { icon: Database, tone: 'var(--sky)', title: 'Logistics data pipeline', text: '90 demand regions - 30 Indian cities plus satellite districts - with 36 months of order history.', where: 'hublocator/data.py' },
  { icon: TrendingUp, tone: 'var(--lavender)', title: 'Demand forecasting', text: 'Random Forest with time-based hold-out, compared against last-value and moving-average forecasters.', where: 'hublocator/forecast.py' },
  { icon: Boxes, tone: 'var(--peach)', title: 'Cost · time · capacity model', text: 'Capacitated hub location with a p-hub limit and a soft or hard delivery SLA, built with PuLP.', where: 'hublocator/model.py' },
  { icon: Zap, tone: 'var(--mint)', title: 'Fast matheuristic', text: 'Reaches the exact optimum in seconds and keeps scaling where the exact MIP runs out of time.', where: 'hublocator/matheuristic.py' },
  { icon: RefreshCcw, tone: 'var(--rose)', title: 'Rolling re-optimisation', text: 'Month-by-month re-planning scored on realised demand against a static, fixed-demand plan.', where: 'hublocator/rolling.py' },
  { icon: BarChart3, tone: 'var(--butter)', title: 'Honest comparison', text: 'Exact MIP, greedy, k-means, a largest-markets rule and a historical-average plan - same month, same scoring.', where: 'hublocator/baselines.py' },
]

function useSmoothScroll() {
  const reduce = useReducedMotion()
  useEffect(() => {
    if (reduce) return undefined
    const lenis = new Lenis({ duration: 1.1, smoothWheel: true })
    lenis.on('scroll', ScrollTrigger.update)
    const raf = (time) => lenis.raf(time * 1000)
    gsap.ticker.add(raf)
    gsap.ticker.lagSmoothing(0)
    const onAnchor = (e) => {
      const a = e.target.closest('a[href^="#"]')
      if (!a) return
      const el = document.querySelector(a.getAttribute('href'))
      if (el) {
        e.preventDefault()
        lenis.scrollTo(el, { offset: -80 })
      }
    }
    document.addEventListener('click', onAnchor)
    return () => {
      document.removeEventListener('click', onAnchor)
      gsap.ticker.remove(raf)
      lenis.destroy()
    }
  }, [reduce])
}

function StepsLine() {
  const ref = useRef(null)
  const reduce = useReducedMotion()
  useEffect(() => {
    if (reduce || !ref.current) return undefined
    const ctx = gsap.context(() => {
      gsap.fromTo(ref.current, { scaleX: 0 }, { scaleX: 1, ease: 'none', scrollTrigger: { trigger: ref.current, start: 'top 85%', end: 'top 35%', scrub: 0.6 } })
    })
    return () => ctx.revert()
  }, [reduce])
  return (
    <div className="steps-line" aria-hidden="true">
      <div ref={ref} />
    </div>
  )
}

function ThemeButton() {
  const { theme, toggle } = useTheme()
  return <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} aria-pressed={theme === 'dark'} />
}

export default function Landing() {
  useSmoothScroll()
  useEffect(() => {
    document.title = 'HubOptima · Forecast-driven hub location'
  }, [])
  const { data, error, loading, reload } = useApi(async (o) => {
    const [summary, regions, cmp] = await Promise.all([api.summary(o), getRegions(), api.compare(o)])
    return { summary, regions: regions.regions, cmp }
  })

  const s = data?.summary
  const proposed = data?.cmp?.methods?.proposed
  const greedy = data?.cmp?.methods?.greedy
  const ro = s?.rolling
  let map = null
  if (data && proposed) {
    const idx = cityIndex(data.regions)
    const demand = Object.fromEntries(proposed.assignment.map((a) => [a.region_id, a.demand]))
    map = { hubs: proposed.hubs, assign: proposed.assignment.map((a) => idx[a.hub]), demand: data.regions.map((r) => demand[r.region_id] || 0) }
  }
  const majors = data ? data.regions.filter((r) => !r.parent || r.parent === r.city) : []

  return (
    <div className="landing">
      <a className="skip-link" href="#top">
        Skip to content
      </a>
      <header className="l-nav">
        <div className="container">
          <Brand />
          <nav className="l-nav-links" aria-label="Sections">
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#results">Results</a>
          </nav>
          <span style={{ flex: 1 }} />
          <ThemeButton />
          <Button to="/app" size="sm" iconRight={ArrowRight} className="btn-open-app">
            <span>Open the app</span>
          </Button>
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <Parallax offset={50} style={{ position: 'absolute', inset: 0 }}>
            <Blobs preset="hero" />
          </Parallax>
          <div className="container hero-grid">
            <div>
              <SlideUp>
                <span className="eyebrow">
                  <Sparkles size={14} aria-hidden="true" />
                  Predict, then optimise · E-commerce logistics
                </span>
              </SlideUp>
              <SlideUp delay={0.08}>
                <h1 style={{ marginTop: 20 }}>
                  Put hubs where tomorrow’s <span className="hl">orders</span> will be.
                </h1>
              </SlideUp>
              <SlideUp delay={0.16}>
                <p className="hero-lead">
                  HubOptima forecasts regional demand with a Random Forest and feeds it to a capacitated hub-location model that a matheuristic solves in seconds -
                  then re-plans every month as demand moves.
                </p>
              </SlideUp>
              <SlideUp delay={0.24} className="hero-cta">
                <MagneticButton>
                  <Button to="/app/plan" size="lg" icon={Zap}>
                    Plan a network
                  </Button>
                </MagneticButton>
                <MagneticButton>
                  <Button to="/app/compare" size="lg" variant="secondary" iconRight={ArrowRight}>
                    See the evidence
                  </Button>
                </MagneticButton>
              </SlideUp>
              <SlideUp delay={0.32} className="hero-note">
                {s ? (
                  <>
                    <Badge tone="lavender" dot>
                      {s.dataset.regions} regions
                    </Badge>
                    {s.forecaster.random_forest && (
                      <Badge tone="mint" dot>
                        RF MAPE {s.forecaster.random_forest.mape}%
                      </Badge>
                    )}
                    <Badge tone="sky" dot>
                      {s.has_pulp ? 'CBC solver online' : 'greedy fallback'}
                    </Badge>
                  </>
                ) : loading ? (
                  <Skeleton width={260} height={26} radius={99} />
                ) : null}
              </SlideUp>
            </div>

            <motion.div className="hero-visual" initial={{ opacity: 0, scale: 0.94, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ type: 'spring', stiffness: 120, damping: 18, delay: 0.2 }}>
              <div className="hero-card">
                {loading && <Skeleton height={420} radius={22} />}
                {error && <ErrorState compact title="Live plan unavailable" error={error} onRetry={reload} />}
                {map && (
                  <>
                    <NetworkMap regions={data.regions} hubs={map.hubs} assign={map.assign} demand={map.demand} label="Map of the proposed hub network" />
                    <p className="small muted" style={{ marginTop: 10, textAlign: 'center' }}>
                      Proposed plan · {proposed.hub_cities.join(', ')}
                    </p>
                  </>
                )}
                {data && !proposed && <p className="muted" style={{ padding: 40, textAlign: 'center' }}>Run a comparison in the app to see the proposed network here.</p>}
              </div>
              {proposed && (
                <motion.div className="hero-float b" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: [0, -6, 0] }} transition={{ opacity: { delay: 0.8 }, y: { duration: 5, repeat: Infinity, ease: 'easeInOut' } }}>
                  <span className="stat-ico" style={{ background: 'var(--peach)' }}>
                    <Gauge size={18} aria-hidden="true" />
                  </span>
                  <div>
                    <b>{fmtINR(proposed.total_cost)}</b>
                    <span>monthly operating cost</span>
                  </div>
                </motion.div>
              )}
              {ro && (
                <motion.div className="hero-float a" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: [0, 6, 0] }} transition={{ opacity: { delay: 1 }, y: { duration: 6, repeat: Infinity, ease: 'easeInOut' } }}>
                  <span className="stat-ico" style={{ background: 'var(--mint)' }}>
                    <PackageCheck size={18} aria-hidden="true" />
                  </span>
                  <div>
                    <b>+{((ro.adaptive_avg.fulfilment_rate - ro.static_avg.fulfilment_rate) * 100).toFixed(1)} pts</b>
                    <span>fulfilment vs a static plan</span>
                  </div>
                </motion.div>
              )}
            </motion.div>
          </div>
        </section>

        {majors.length > 0 && (
          <section aria-label="Cities in the network" style={{ paddingBottom: 24 }}>
            <Marquee speed={55}>
              {majors.map((r) => (
                <span key={r.region_id} className="chip">
                  <MapPin size={14} aria-hidden="true" style={{ color: 'var(--lavender-ink)' }} />
                  {r.city}
                </span>
              ))}
            </Marquee>
          </section>
        )}

        <section className="section" id="how">
          <div className="container">
            <Reveal className="section-head">
              <span className="eyebrow">How it works</span>
              <h2>From order history to an open hub, in five calm steps</h2>
              <p>The predict-then-optimise loop from the base paper (IEEE Access 2025), running end to end on your machine.</p>
            </Reveal>
            <StepsLine />
            <Stagger className="steps" inView gap={0.09}>
              {STEPS.map((st, i) => (
                <Stagger.Item key={st.title}>
                  <motion.div className="step-card" {...lift} style={{ height: '100%' }}>
                    <span className="n">STEP {String(i + 1).padStart(2, '0')}</span>
                    <div className="ico" style={{ background: st.tone }}>
                      <st.icon size={22} aria-hidden="true" />
                    </div>
                    <h3>{st.title}</h3>
                    <p>{st.text}</p>
                  </motion.div>
                </Stagger.Item>
              ))}
            </Stagger>
          </div>
        </section>

        <section className="section" id="features" style={{ background: 'var(--bg-tint)' }}>
          <div className="container">
            <Reveal className="section-head">
              <span className="eyebrow">What’s inside</span>
              <h2>Six objectives, each one a working module</h2>
              <p>Every screen in the app is wired to these modules through a small JSON API.</p>
            </Reveal>
            <Stagger className="features" inView gap={0.07}>
              {FEATURES.map((f) => (
                <Stagger.Item key={f.title}>
                  <motion.article className="feature" {...lift}>
                    <div className="ico" style={{ background: f.tone }}>
                      <f.icon size={24} aria-hidden="true" />
                    </div>
                    <h3>{f.title}</h3>
                    <p>{f.text}</p>
                    <div className="where">
                      <code className="mono badge neutral">{f.where}</code>
                    </div>
                  </motion.article>
                </Stagger.Item>
              ))}
            </Stagger>
          </div>
        </section>

        <section className="section" id="results">
          <div className="container">
            <Reveal className="section-head">
              <span className="eyebrow">Live numbers</span>
              <h2>Straight from the latest runs</h2>
              <p>Read from the API right now - retrain or re-run in the app and these update.</p>
            </Reveal>
            {error ? (
              <ErrorState title="Live numbers unavailable" error={error} onRetry={reload} />
            ) : (
              <Reveal className="stats-strip">
                <div className="s">
                  <b>{s ? <CountUp value={s.dataset.regions} /> : '–'}</b>
                  <span>demand regions</span>
                </div>
                <div className="s">
                  <b>{s ? <CountUp value={s.dataset.total_orders} format={fmtCompact} /> : '–'}</b>
                  <span>orders over {s?.dataset.periods ?? '–'} months</span>
                </div>
                <div className="s">
                  <b>{s?.forecaster.random_forest ? <CountUp value={s.forecaster.random_forest.mape} format={(v) => `${v.toFixed(1)}%`} /> : '–'}</b>
                  <span>Random Forest MAPE</span>
                </div>
                <div className="s">
                  <b>{ro ? <CountUp value={ro.adaptive_avg.fulfilment_rate * 100} format={(v) => `${v.toFixed(1)}%`} /> : '–'}</b>
                  <span>fulfilment with monthly re-planning{ro ? ` (static ${fmtPct(ro.static_avg.fulfilment_rate)})` : ''}</span>
                </div>
                <div className="s">
                  <b>{greedy ? <CountUp value={greedy.cost_vs_proposed_pct} format={(v) => `${v.toFixed(1)}%`} /> : '–'}</b>
                  <span>higher cost with a greedy heuristic</span>
                </div>
              </Reveal>
            )}
          </div>
        </section>

        <section className="section">
          <div className="container">
            <Reveal className="cta">
              <Blobs preset="cta" />
              <h2>Ready to plan next month’s network?</h2>
              <p>Pick a month, set the hub budget and SLA, and watch the matheuristic choose where to open hubs.</p>
              <div className="row" style={{ justifyContent: 'center' }}>
                <MagneticButton>
                  <Button to="/app/plan" size="lg" icon={Zap}>
                    Start planning
                  </Button>
                </MagneticButton>
                <Button to="/app" size="lg" variant="secondary">
                  Open the dashboard
                </Button>
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="container">
          <div>
            <strong style={{ color: 'var(--text)' }}>HubOptima</strong> · Advanced Optimization in E-Commerce Logistics: Combining Matheuristics With Random Forests for Hub Location Efficiency
          </div>
          <div>Batch CSDS-A-A4 · base paper IEEE Access 2025 · {s ? (s.has_pulp ? 'CBC via PuLP' : 'greedy fallback') : 'API offline'}</div>
        </div>
      </footer>
    </div>
  )
}
