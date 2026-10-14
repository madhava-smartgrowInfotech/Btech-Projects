import { Suspense, lazy, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Lenis from 'lenis'
import {
  ArrowRight,
  BrainCircuit,
  CloudDownload,
  Fingerprint,
  Moon,
  RefreshCw,
  ScanSearch,
  ShieldAlert,
  ShieldCheck,
  Sun,
  Undo2,
  Users,
  Zap,
} from 'lucide-react'
import { useStats } from '../lib/stats'
import { useTheme } from '../lib/theme'
import { useMediaQuery, useReducedMotion } from '../lib/motion'
import { modelLabel, num, pct } from '../lib/format'
import { BrandMark, Button, Card, IconButton, Tooltip } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, ScrollTrigger, SlideUp, Stagger, gsap } from '../components/motion'
import '../styles/landing.css'

const HeroVisual = lazy(() => import('../components/three/HeroVisual'))

// Example used to illustrate stage 1 (from the project README); each label is the rule in features.py it trips.
const ANATOMY = [
  { part: 'http://', tag: 'scheme', note: 'no TLS' },
  { part: 'paypal-login.', tag: 'subdomain', note: 'brand outside the registered domain', hot: true },
  { part: 'verify-account', tag: 'domain', note: 'hyphenated registered domain', hot: true },
  { part: '.tk', tag: 'TLD', note: 'TLD frequently abused by phishing', hot: true },
  { part: '/signin', tag: 'path', note: 'credential-related keyword', hot: true },
]

const FEATURES = [
  { icon: Zap, title: 'Zero-day override', body: 'A URL confirmed by the community or a trusted feed is blocked instantly - no retraining needed before it is caught.' },
  { icon: BrainCircuit, title: 'Three models, one winner', body: 'Random Forest, XGBoost and Logistic Regression are trained on the same split; the best F1 model serves live traffic.' },
  { icon: Fingerprint, title: 'Explainable verdicts', body: 'Every result lists the red flags behind it and the full 47-value feature vector the classifier scored.' },
  { icon: RefreshCw, title: 'Continuous refinement', body: 'Confirmed URLs are folded back into training with extra weight; retraining hot-swaps the model without a restart.' },
  { icon: CloudDownload, title: 'Public feed sync', body: 'Pull fresh phishing URLs from OpenPhish and URLhaus straight into the threat-intelligence store.' },
  { icon: Undo2, title: 'False-positive repair', body: 'When the crowd confirms a site is legitimate, that verdict overrides the model for every future check.' },
]

function useLenis(enabled) {
  useEffect(() => {
    if (!enabled) return undefined
    const lenis = new Lenis({ duration: 1.15, smoothWheel: true })
    lenis.on('scroll', ScrollTrigger.update)
    const raf = (t) => lenis.raf(t * 1000)
    gsap.ticker.add(raf)
    gsap.ticker.lagSmoothing(0)
    return () => {
      gsap.ticker.remove(raf)
      lenis.destroy()
    }
  }, [enabled])
}

function LandingNav() {
  const { theme, toggle } = useTheme()
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])
  return (
    <header className={`l-nav ${scrolled ? 'scrolled' : ''}`}>
      <div className="l-wrap l-nav-inner">
        <Link to="/" className="brand" aria-label="PhishGuard home">
          <BrandMark />
          <span>PhishGuard</span>
        </Link>
        <nav aria-label="Landing sections" className="l-nav-links">
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
          <a href="#numbers">Numbers</a>
        </nav>
        <div className="row" style={{ gap: 6 }}>
          <Tooltip label={theme === 'dark' ? 'Light mode' : 'Dark mode'} placement="bottom">
            <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
          </Tooltip>
          <Button as={Link} to="/app/check" variant="primary" size="sm" iconRight={ArrowRight}>
            Open app
          </Button>
        </div>
      </div>
    </header>
  )
}

function Hero() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const { metrics } = useStats()
  const best = metrics?.models?.[metrics.best_model]
  return (
    <section className="hero" aria-labelledby="hero-title">
      {/* depth layers: each moves at its own rate on scroll */}
      <Parallax speed={-0.35} className="hero-layer hero-grid" />
      <Parallax speed={0.55} className="hero-layer hero-orbs">
        <span className="orb orb-a" />
        <span className="orb orb-b" />
      </Parallax>
      <Parallax speed={0.18} className="hero-layer hero-visual">
        <Suspense fallback={<img className="hero-fallback" src="/hero-fallback.svg" alt="" aria-hidden="true" />}>
          <HeroVisual />
        </Suspense>
      </Parallax>

      <div className="l-wrap hero-inner">
        <div className="hero-copy">
          <SlideUp>
            <span className="eyebrow">
              <span className="pulse" aria-hidden="true" /> Machine learning + crowdsourced threat intelligence
            </span>
          </SlideUp>
          <SlideUp delay={0.08}>
            <h1 id="hero-title">
              Catch the phishing link <span className="text-grad">before it catches you.</span>
            </h1>
          </SlideUp>
          <SlideUp delay={0.16}>
            <p className="hero-sub">
              PhishGuard reads 47 lexical, structural and domain signals from any URL, scores it with the strongest of three trained classifiers and lets the
              community overrule the model the moment a new attack appears.
            </p>
          </SlideUp>
          <SlideUp delay={0.24}>
            <form
              className="hero-form"
              onSubmit={(e) => {
                e.preventDefault()
                navigate(url.trim() ? `/app/check?url=${encodeURIComponent(url.trim())}` : '/app/check')
              }}
            >
              <label htmlFor="hero-url" className="sr-only">
                URL to check
              </label>
              <ScanSearch size={18} aria-hidden="true" className="hero-form-icon" />
              <input id="hero-url" className="mono" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="Paste a suspicious link…" autoComplete="off" spellCheck={false} />
              <MagneticButton>
                <Button type="submit" variant="primary" iconRight={ArrowRight}>
                  Check it
                </Button>
              </MagneticButton>
            </form>
          </SlideUp>
          <SlideUp delay={0.32}>
            <div className="hero-meta">
              {best ? (
                <>
                  <span>
                    <ShieldCheck size={15} aria-hidden="true" /> {modelLabel(metrics.best_model)} live
                  </span>
                  <span>F1 {pct(best.f1)}</span>
                  <span>ROC-AUC {best.roc_auc.toFixed(3)}</span>
                </>
              ) : (
                <span>Three-stage pipeline: features → classifier → community</span>
              )}
            </div>
          </SlideUp>
        </div>
      </div>
      <a href="#how" className="scroll-cue" aria-label="Scroll to how it works">
        <span />
      </a>
    </section>
  )
}

function StepVisual({ step, metrics, config, ti }) {
  const names = metrics ? Object.keys(metrics.models) : []
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={step}
        className="viz"
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -12, scale: 0.98 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      >
        {step === 0 && (
          <div className="viz-anatomy">
            <div className="viz-label">URL anatomy</div>
            <div className="anatomy-url mono">
              {ANATOMY.map((a) => (
                <span key={a.part} className={a.hot ? 'hot' : ''}>
                  {a.part}
                </span>
              ))}
            </div>
            <ul className="anatomy-list">
              {ANATOMY.map((a) => (
                <li key={a.tag}>
                  <span className={`anatomy-tag ${a.hot ? 'hot' : ''}`}>{a.tag}</span>
                  <span>{a.note}</span>
                </li>
              ))}
            </ul>
            <div className="viz-foot">
              {config ? (
                <>
                  {config.feature_groups.lexical.length} lexical · {config.feature_groups.structural.length} structural · {config.feature_groups.domain.length} domain features
                </>
              ) : (
                '47 offline features - no WHOIS or DNS needed'
              )}
            </div>
          </div>
        )}
        {step === 1 && (
          <div>
            <div className="viz-label">Held-out F1 by model</div>
            {metrics ? (
              <div className="viz-bars">
                {names.map((n) => (
                  <div key={n} className={`viz-bar ${n === metrics.best_model ? 'best' : ''}`}>
                    <div className="row" style={{ justifyContent: 'space-between' }}>
                      <span>{modelLabel(n)}</span>
                      <strong>{pct(metrics.models[n].f1)}</strong>
                    </div>
                    <div className="viz-track">
                      <motion.i initial={{ width: 0 }} animate={{ width: `${metrics.models[n].f1 * 100}%` }} transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }} />
                    </div>
                  </div>
                ))}
                <div className="viz-foot">
                  {num(metrics.test_rows)} test URLs · best model serves live checks
                </div>
              </div>
            ) : (
              <p className="muted">Metrics appear once the models are trained.</p>
            )}
          </div>
        )}
        {step === 2 && (
          <div>
            <div className="viz-label">Consensus rule</div>
            <div className="votes">
              {Array.from({ length: (config?.consensus_threshold ?? 2) + 1 }).map((_, i) => (
                <span key={i} className={`vote ${i < (config?.consensus_threshold ?? 2) ? 'up' : 'down'}`}>
                  {i < (config?.consensus_threshold ?? 2) ? <ShieldAlert size={18} aria-hidden="true" /> : <ShieldCheck size={18} aria-hidden="true" />}
                </span>
              ))}
            </div>
            <p className="muted" style={{ fontSize: 14, margin: '14px 0 18px' }}>
              Confirmed once net votes reach {config?.consensus_threshold ?? 2}. Confirmed URLs override the model and retrain it after{' '}
              {config?.auto_retrain_every ?? 25} new confirmations.
            </p>
            {ti && (
              <div className="viz-stats">
                <div>
                  <strong>{num(ti.confirmed_phishing)}</strong>
                  <span>confirmed phishing</span>
                </div>
                <div>
                  <strong>{num(ti.confirmed_safe)}</strong>
                  <span>confirmed safe</span>
                </div>
                <div>
                  <strong>{num(ti.pending)}</strong>
                  <span>pending</span>
                </div>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  )
}

const STEPS = [
  {
    k: '01',
    title: 'Feature extraction',
    body: 'The URL is normalised and broken into lexical, structural and domain signals: length and entropy, IP hosts, subdomain depth, abused TLDs, brand names out of place, credential keywords, shorteners and more.',
  },
  {
    k: '02',
    title: 'ML classification',
    body: 'Random Forest, XGBoost and Logistic Regression are trained on the same features and compared on accuracy, precision, recall, F1 and ROC-AUC. The winner scores every check; well-known domains get a reputation discount.',
  },
  {
    k: '03',
    title: 'Crowdsourced intelligence',
    body: 'People report URLs as phishing or safe. Once consensus is reached the verdict overrides the model immediately - closing the zero-day gap - and the confirmed URLs feed the next retraining run.',
  },
]

function HowItWorks() {
  const section = useRef(null)
  const visual = useRef(null)
  const copy = useRef(null)
  const [step, setStep] = useState(0)
  const { metrics, config, ti } = useStats()
  const wide = useMediaQuery('(min-width: 900px)')

  useLayoutEffect(() => {
    if (!wide) return undefined
    const ctx = gsap.context(() => {
      const mm = gsap.matchMedia()
      // pin the visual while the copy scrolls past (motion users only; others get a sticky fallback in CSS)
      mm.add('(prefers-reduced-motion: no-preference)', () => {
        ScrollTrigger.create({
          trigger: copy.current,
          start: 'top 18%',
          end: () => `bottom ${visual.current.offsetHeight + window.innerHeight * 0.18}px`,
          pin: visual.current,
          pinSpacing: false,
          invalidateOnRefresh: true,
        })
        gsap.utils.toArray('.how-step').forEach((el) => {
          gsap.fromTo(el, { opacity: 0.28 }, { opacity: 1, ease: 'none', scrollTrigger: { trigger: el, start: 'top 75%', end: 'top 45%', scrub: true } })
        })
      })
      gsap.utils.toArray('.how-step').forEach((el, i) => {
        ScrollTrigger.create({ trigger: el, start: 'top 55%', end: 'bottom 55%', onToggle: (self) => self.isActive && setStep(i) })
      })
      gsap.fromTo(
        '.how-progress i',
        { scaleY: 0 },
        { scaleY: 1, ease: 'none', scrollTrigger: { trigger: copy.current, start: 'top 55%', end: 'bottom 55%', scrub: true } },
      )
    }, section)
    return () => ctx.revert()
  }, [wide])

  // content above and inside this section changes height once live data arrives
  useEffect(() => {
    const t = setTimeout(() => ScrollTrigger.refresh(), 120)
    return () => clearTimeout(t)
  }, [config, metrics, ti])

  return (
    <section id="how" ref={section} className="how" aria-labelledby="how-title">
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">How it works</span>
          <h2 id="how-title">Three stages, one verdict in milliseconds.</h2>
        </Reveal>
        <div className="how-grid">
          {wide && (
            <div className="how-visual-col">
              <div ref={visual} className="how-visual">
                <Card className="how-card">
                  <div className="how-card-head">
                    <span className="mono faint">stage {STEPS[step].k} / 03</span>
                    <span className="dots" aria-hidden="true">
                      {STEPS.map((s, i) => (
                        <i key={s.k} className={i === step ? 'on' : ''} />
                      ))}
                    </span>
                  </div>
                  <StepVisual step={step} metrics={metrics} config={config} ti={ti} />
                </Card>
              </div>
            </div>
          )}
          <div ref={copy} className="how-copy">
            {wide && (
              <div className="how-progress" aria-hidden="true">
                <i />
              </div>
            )}
            {STEPS.map((s, i) => (
              <article key={s.k} className={`how-step ${i === step ? 'active' : ''}`}>
                <span className="how-num mono">{s.k}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
                {!wide && (
                  <Card className="how-card inline">
                    <StepVisual step={i} metrics={metrics} config={config} ti={ti} />
                  </Card>
                )}
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function SignalMarquee() {
  const { config } = useStats()
  // keep the strip's height reserved while config loads so scroll triggers below stay accurate
  if (!config) return <section className="signals signals-empty" aria-hidden="true" />
  const all = [...config.feature_groups.lexical, ...config.feature_groups.structural, ...config.feature_groups.domain]
  const half = Math.ceil(all.length / 2)
  return (
    <section className="signals" aria-label={`The ${all.length} URL features the classifier reads`}>
      <Marquee speed={70}>
        {all.slice(0, half).map((f) => (
          <span key={f} className="signal mono">
            {f}
          </span>
        ))}
      </Marquee>
      <Marquee speed={80} reverse>
        {all.slice(half).map((f) => (
          <span key={f} className="signal mono">
            {f}
          </span>
        ))}
      </Marquee>
    </section>
  )
}

function FeatureGrid() {
  return (
    <section id="features" className="l-section" aria-labelledby="features-title">
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">Features</span>
          <h2 id="features-title">Built for the links that slip past blocklists.</h2>
        </Reveal>
        <Stagger className="feature-cards" inView>
          {FEATURES.map((f) => (
            <Card key={f.title} className="feature-card">
              <span className="feature-icon">
                <f.icon size={20} aria-hidden="true" />
              </span>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </Card>
          ))}
        </Stagger>
      </div>
    </section>
  )
}

function Numbers() {
  const { ti, metrics, error } = useStats()
  const best = metrics?.models?.[metrics.best_model]
  const items = [
    { label: 'URLs checked', value: ti?.checks, format: (v) => Math.round(v).toLocaleString() },
    { label: 'Community reports', value: ti?.reports, format: (v) => Math.round(v).toLocaleString() },
    { label: 'Confirmed phishing URLs', value: ti?.confirmed_phishing, format: (v) => Math.round(v).toLocaleString() },
    { label: `${best ? modelLabel(metrics.best_model) : 'Model'} accuracy`, value: best ? best.accuracy * 100 : undefined, format: (v) => `${v.toFixed(1)}%` },
    { label: 'ROC-AUC', value: best?.roc_auc, format: (v) => v.toFixed(3) },
  ]
  return (
    <section id="numbers" className="numbers" aria-labelledby="numbers-title">
      <div className="l-wrap">
        <h2 id="numbers-title" className="sr-only">
          Live numbers
        </h2>
        {error ? (
          <p className="muted" role="status" style={{ textAlign: 'center' }}>
            Live numbers are unavailable - the backend on port 8103 is not reachable.
          </p>
        ) : (
          <div className="numbers-grid">
            {items.map((it) => (
              <div key={it.label} className="number">
                <strong>{it.value === undefined || it.value === null ? '-' : <CountUp value={it.value} format={it.format} duration={1.8} />}</strong>
                <span>{it.label}</span>
              </div>
            ))}
          </div>
        )}
        <p className="faint numbers-note">Live from this installation&apos;s threat-intelligence store and the held-out test set (metrics.json).</p>
      </div>
    </section>
  )
}

function CallToAction() {
  return (
    <section className="l-section cta" aria-labelledby="cta-title">
      <div className="l-wrap">
        <Reveal>
          <Card className="cta-card">
            <Parallax speed={0.2} className="cta-glow" />
            <h2 id="cta-title">Got a link you do not trust?</h2>
            <p>Check it in a second, see exactly why it looks dangerous, and warn everyone else with one report.</p>
            <div className="row" style={{ justifyContent: 'center', marginTop: 26 }}>
              <MagneticButton>
                <Button as={Link} to="/app/check" variant="primary" size="lg" icon={ScanSearch}>
                  Check a URL
                </Button>
              </MagneticButton>
              <Button as={Link} to="/app/report" size="lg" icon={Users}>
                Report a URL
              </Button>
            </div>
          </Card>
        </Reveal>
      </div>
    </section>
  )
}

function Footer() {
  const { metrics } = useStats()
  return (
    <footer className="l-footer">
      <div className="l-wrap l-footer-inner">
        <div>
          <Link to="/" className="brand" style={{ padding: 0 }}>
            <BrandMark />
            <span>PhishGuard</span>
          </Link>
          <p className="faint" style={{ marginTop: 10, maxWidth: '46ch' }}>
            A dynamic phishing URL detection system integrating machine learning and crowdsourced threat intelligence. Batch A3 · CSE (Data Science).
          </p>
        </div>
        <nav aria-label="Footer" className="l-footer-links">
          <Link to="/app/check">Check URL</Link>
          <Link to="/app/report">Report</Link>
          <Link to="/app/intel">Threat intelligence</Link>
          <Link to="/app/models">Models</Link>
          <Link to="/app/activity">Activity</Link>
        </nav>
      </div>
      <div className="l-wrap faint l-footer-base">
        Active model: {metrics ? `${modelLabel(metrics.best_model)} v${metrics.model_version}` : 'not trained'}
      </div>
    </footer>
  )
}

export default function Landing() {
  const reduced = useReducedMotion()
  useLenis(!reduced)
  useEffect(() => {
    document.title = 'PhishGuard · Dynamic phishing URL detection'
    // layout shifts after fonts / lazy chunks load - recompute trigger positions
    const t = setTimeout(() => ScrollTrigger.refresh(), 600)
    return () => clearTimeout(t)
  }, [])
  return (
    <div className="landing">
      <a href="#how" className="skip-link">
        Skip to content
      </a>
      <LandingNav />
      <main>
        <Hero />
        <SignalMarquee />
        <HowItWorks />
        <FeatureGrid />
        <Numbers />
        <CallToAction />
      </main>
      <Footer />
    </div>
  )
}
