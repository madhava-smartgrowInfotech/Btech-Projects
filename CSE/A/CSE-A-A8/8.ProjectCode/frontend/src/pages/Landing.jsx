import { Suspense, lazy, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Lenis from 'lenis'
import {
  ArrowRight,
  FileText,
  GitCompareArrows,
  LayoutDashboard,
  Lightbulb,
  Moon,
  ScanText,
  ShieldCheck,
  Sun,
  TrendingUp,
  UploadCloud,
  Waypoints,
} from 'lucide-react'
import { useAuth } from '../lib/auth'
import { useConfig } from '../lib/config'
import { useTheme } from '../lib/theme'
import { useMediaQuery, useReducedMotion } from '../lib/motion'
import { BrandMark, Button, Card, IconButton, Tooltip } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, ScrollTrigger, SlideUp, Stagger, gsap } from '../components/motion'
import { Disclaimer } from '../components/lab'
import '../styles/landing.css'

const HeroVisual = lazy(() => import('../components/three/HeroVisual'))

// Illustrative row, taken from the extraction module's own documentation example.
const ROW = [
  { part: 'Hemoglobin', tag: 'test name', note: 'snapped to the canonical spelling' },
  { part: ' 10.5', tag: 'value', note: 'numeric result', hot: true },
  { part: ' g/dL', tag: 'unit', note: 'unit token' },
  { part: ' 12.0 - 16.0', tag: 'reference range', note: 'two-sided or one-sided (<, >)', hot: true },
]

const FEATURES = [
  { icon: UploadCloud, title: 'Multi-format upload', body: 'PDF, JPG, JPEG and PNG lab reports, up to 15 MB, with clear errors when a file cannot be read.' },
  { icon: ScanText, title: 'OCR + AI extraction', body: 'The text layer is used when present; scans and photos go through OpenCV clean-up and Tesseract OCR.' },
  { icon: ShieldCheck, title: 'Transparent classification', body: 'Every value is compared with its own reference range - Low, Normal, High or Unknown - using simple, visible rules.' },
  { icon: TrendingUp, title: 'Trends over time', body: 'Pick any test and follow it across every report you have uploaded, against its reference band.' },
  { icon: GitCompareArrows, title: 'Compare two reports', body: 'See which tests changed between two check-ups, by how much, and in which direction.' },
  { icon: Lightbulb, title: 'Plain-language insights', body: 'Abnormal results get a general, non-diagnostic explanation, possible causes and a sensible next step.' },
]

const STEPS = [
  {
    k: '01',
    title: 'Extract the text',
    body: 'PDFs are read from their embedded text layer. Scanned PDFs and photos are rendered, de-noised, deskewed and passed through Tesseract OCR - so a phone photo of a printout still works.',
  },
  {
    k: '02',
    title: 'Structure every row',
    body: 'Each line is parsed into test name, value, unit and reference range. A TF-IDF matcher snaps noisy OCR names such as "Haemogl0bin" to a dictionary of common lab tests so trends stay consistent.',
  },
  {
    k: '03',
    title: 'Classify and explain',
    body: 'Values below the range are Low, above it High, inside it Normal. Anything abnormal gets a calm, educational explanation - never a diagnosis - and always a reminder to ask a doctor.',
  },
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
  const { user } = useAuth()
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
        <Link to="/" className="brand" aria-label="LabLens home">
          <BrandMark />
          <span>LabLens</span>
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
          <Button as={Link} to={user ? '/app' : '/login'} variant="primary" size="sm" iconRight={ArrowRight}>
            {user ? 'Open app' : 'Sign in'}
          </Button>
        </div>
      </div>
    </header>
  )
}

function Hero() {
  const { config } = useConfig()
  const { user } = useAuth()
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
              <span className="pulse" aria-hidden="true" /> OCR + extraction + plain-language insights
            </span>
          </SlideUp>
          <SlideUp delay={0.08}>
            <h1 id="hero-title">
              Your lab report, <span className="text-grad">in plain language.</span>
            </h1>
          </SlideUp>
          <SlideUp delay={0.16}>
            <p className="hero-sub">
              Upload a PDF or a photo of a laboratory report. LabLens reads every test, flags what falls outside its reference range, tracks your results over time and explains them without the jargon.
            </p>
          </SlideUp>
          <SlideUp delay={0.24}>
            <div className="row" style={{ gap: 14, marginTop: 28 }}>
              <MagneticButton>
                <Button as={Link} to={user ? '/app/upload' : '/login'} variant="primary" size="lg" iconRight={ArrowRight}>
                  {user ? 'Upload a report' : 'Get started'}
                </Button>
              </MagneticButton>
              <Button as={Link} to="/app" size="lg" icon={LayoutDashboard}>
                See the dashboard
              </Button>
            </div>
          </SlideUp>
          <SlideUp delay={0.32}>
            <div className="hero-meta">
              <span>
                <FileText size={15} aria-hidden="true" /> {config ? config.supported_extensions.map((e) => e.slice(1).toUpperCase()).join(' · ') : 'PDF · JPG · JPEG · PNG'}
              </span>
              <span>Educational tool - not a medical device</span>
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

function StepVisual({ step }) {
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
          <div>
            <div className="viz-label">Two routes to the text</div>
            <ul className="anatomy-list">
              <li>
                <span className="anatomy-tag hot">text layer</span>
                <span>PDF with selectable text: read directly with PyMuPDF</span>
              </li>
              <li>
                <span className="anatomy-tag hot">OCR</span>
                <span>Scan or photo: grayscale, denoise, threshold, deskew, then Tesseract</span>
              </li>
            </ul>
            <div className="format-chips">
              {['PDF', 'JPG', 'JPEG', 'PNG'].map((f) => (
                <span key={f} className="anatomy-tag">
                  {f}
                </span>
              ))}
            </div>
            <div className="viz-foot">Up to 15 MB per file</div>
          </div>
        )}
        {step === 1 && (
          <div className="viz-anatomy">
            <div className="viz-label">One row, four fields</div>
            <div className="anatomy-url mono">
              {ROW.map((a) => (
                <span key={a.tag} className={a.hot ? 'hot' : ''}>
                  {a.part}
                </span>
              ))}
            </div>
            <ul className="anatomy-list">
              {ROW.map((a) => (
                <li key={a.tag}>
                  <span className={`anatomy-tag ${a.hot ? 'hot' : ''}`}>{a.tag}</span>
                  <span>{a.note}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {step === 2 && (
          <div>
            <div className="viz-label">Classification rules</div>
            <div className="viz-bars">
              {[
                ['Low', 'result below the lower limit', 18, 'var(--warn)'],
                ['Normal', 'inside the reference range', 100, 'var(--accent)'],
                ['High', 'result above the upper limit', 62, 'var(--danger)'],
              ].map(([name, note, w, color]) => (
                <div key={name} className="viz-bar">
                  <div className="row" style={{ justifyContent: 'space-between' }}>
                    <strong>{name}</strong>
                    <span className="faint">{note}</span>
                  </div>
                  <div className="viz-track">
                    <motion.i initial={{ width: 0 }} animate={{ width: `${w}%` }} transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }} style={{ background: color }} />
                  </div>
                </div>
              ))}
              <div className="viz-foot">No bound known on either side? The result is shown as Unknown, never guessed.</div>
            </div>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  )
}

function HowItWorks() {
  const section = useRef(null)
  const visual = useRef(null)
  const copy = useRef(null)
  const [step, setStep] = useState(0)
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
      gsap.fromTo('.how-progress i', { scaleY: 0 }, { scaleY: 1, ease: 'none', scrollTrigger: { trigger: copy.current, start: 'top 55%', end: 'bottom 55%', scrub: true } })
    }, section)
    return () => ctx.revert()
  }, [wide])

  return (
    <section id="how" ref={section} className="how" aria-labelledby="how-title">
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">How it works</span>
          <h2 id="how-title">From a scanned page to clear results in three stages.</h2>
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
                  <StepVisual step={step} />
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
                    <StepVisual step={i} />
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

function TestMarquee() {
  const { config } = useConfig()
  // keep the strip's height reserved while config loads so scroll triggers below stay accurate
  if (!config) return <section className="signals signals-empty" aria-hidden="true" />
  const all = config.known_tests
  const half = Math.ceil(all.length / 2)
  return (
    <section className="signals" aria-label={`${all.length} lab tests LabLens recognises by name`}>
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
          <h2 id="features-title">Everything you need to make sense of your labs.</h2>
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
  const { config, error } = useConfig()
  const items = config
    ? [
        { label: 'Lab tests recognised by name', value: config.known_tests.length },
        { label: 'Upload formats', value: config.supported_extensions.length },
        { label: 'Maximum file size (MB)', value: config.max_size_mb },
        { label: 'Result statuses', value: 4 },
      ]
    : []
  return (
    <section id="numbers" className="numbers" aria-labelledby="numbers-title">
      <div className="l-wrap">
        <h2 id="numbers-title" className="sr-only">
          Numbers
        </h2>
        {error ? (
          <p className="muted" role="status" style={{ textAlign: 'center' }}>
            Live numbers are unavailable - the backend on port 8308 is not reachable.
          </p>
        ) : (
          <div className="numbers-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))' }}>
            {items.map((it) => (
              <div key={it.label} className="number">
                <strong>
                  <CountUp value={it.value} duration={1.6} />
                </strong>
                <span>{it.label}</span>
              </div>
            ))}
          </div>
        )}
        <p className="faint numbers-note">Read live from this installation&apos;s extraction dictionary and upload limits.</p>
      </div>
    </section>
  )
}

function CallToAction() {
  const { user } = useAuth()
  return (
    <section className="l-section cta" aria-labelledby="cta-title">
      <div className="l-wrap">
        <Reveal>
          <Card className="cta-card">
            <Parallax speed={0.2} className="cta-glow" />
            <h2 id="cta-title">Got a lab report you cannot make sense of?</h2>
            <p>Upload it, see every result against its reference range, and get a calm explanation of anything unusual.</p>
            <div className="row" style={{ justifyContent: 'center', marginTop: 26 }}>
              <MagneticButton>
                <Button as={Link} to={user ? '/app/upload' : '/login'} variant="primary" size="lg" icon={UploadCloud}>
                  {user ? 'Upload a report' : 'Sign in to start'}
                </Button>
              </MagneticButton>
              <Button as={Link} to="/app/about" size="lg" icon={Waypoints}>
                How it is built
              </Button>
            </div>
          </Card>
        </Reveal>
        <div style={{ marginTop: 28 }}>
          <Disclaimer />
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="l-footer">
      <div className="l-wrap l-footer-inner">
        <div>
          <Link to="/" className="brand" style={{ padding: 0 }}>
            <BrandMark />
            <span>LabLens</span>
          </Link>
          <p className="faint" style={{ marginTop: 10, maxWidth: '46ch' }}>
            AI-powered medical lab report analysis and health insights. Batch A8 · CSE.
          </p>
        </div>
        <nav aria-label="Footer" className="l-footer-links">
          <Link to="/app/upload">Upload report</Link>
          <Link to="/app/reports">My reports</Link>
          <Link to="/app/trends">Health trends</Link>
          <Link to="/app/compare">Compare reports</Link>
          <Link to="/app/about">About</Link>
        </nav>
      </div>
      <div className="l-wrap faint l-footer-base">Educational tool only - not a medical device.</div>
    </footer>
  )
}

export default function Landing() {
  const reduced = useReducedMotion()
  useLenis(!reduced)
  useEffect(() => {
    document.title = 'LabLens · Lab report analysis in plain language'
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
        <TestMarquee />
        <HowItWorks />
        <FeatureGrid />
        <Numbers />
        <CallToAction />
      </main>
      <Footer />
    </div>
  )
}
