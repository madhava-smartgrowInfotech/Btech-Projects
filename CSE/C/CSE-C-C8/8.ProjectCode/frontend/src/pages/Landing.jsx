import { Suspense, lazy, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useScroll, useSpring } from 'framer-motion'
import Lenis from 'lenis'
import { ArrowRight, BookOpen, FileSearch, FileText, Gauge, Moon, ScanSearch, ShieldCheck, Sparkles, Sun, Users } from 'lucide-react'
import { BrandMark, Button, IconButton, Skeleton } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, SlideUp, Stagger } from '../components/motion'
import { useTheme } from '../lib/theme'
import { useReducedMotion } from '../lib/motion'
import { useStats } from '../lib/stats'
import { api } from '../lib/api'

// three.js is heavy: it loads after first paint, in its own chunk.
const HeroVisual = lazy(() => import('../components/three/HeroVisual'))

const SIGNALS = [
  'PDF text extraction',
  'Section detection',
  'TF-IDF + logistic regression decision signal',
  'Structural checks',
  'Local Qwen review (analyze → critique → synthesize)',
  'OpenAlex literature grounding',
  'Embedding similarity',
  'Conflict-of-interest terms',
  'Workload awareness',
  'JSON & PDF export',
]

const STEPS = [
  {
    title: 'Upload a PDF',
    body: 'Drop in a manuscript up to 20 MB. PeerScope extracts the text, detects the sections, parses the references and keeps page-anchored evidence - all locally.',
  },
  {
    title: 'Get a preliminary review',
    body: 'A trained decision signal, deterministic structural checks and a local AI critique produce strengths, major and minor concerns and concrete recommendations.',
  },
  {
    title: 'Match reviewers, transparently',
    body: 'Expertise similarity, topic and method overlap and availability rank your reviewers - with a conflict check and a full breakdown for every score.',
  },
  {
    title: 'Audit and export',
    body: 'Every analysis is stored. Reopen it later, inspect how each score was computed, and export the whole thing as JSON or PDF.',
  },
]

const FEATURES = [
  { icon: FileText, title: 'Local extraction', body: 'PyMuPDF text, section detection and reference parsing run on your machine. Scanned, image-only PDFs are flagged rather than guessed at.' },
  { icon: Gauge, title: 'Measured decision signal', body: 'The accept / borderline / reject signal comes with real held-out metrics, a confusion matrix and a clear note when the training data is synthetic.' },
  { icon: Sparkles, title: 'Honest AI review', body: 'A local Qwen model critiques the paper. If it cannot load, PeerScope says so and keeps the deterministic analysis visible - no fabricated text.' },
  { icon: BookOpen, title: 'Literature grounding', body: 'Related works are retrieved from OpenAlex and ranked by similarity. Treated as context, never as proof of novelty.' },
  { icon: Users, title: 'Auditable matching', body: 'Every recommendation shows its signal breakdown, matching terms, workload and conflict check. Reviewer CSV import and export included.' },
  { icon: ShieldCheck, title: 'Decision support only', body: 'Final editorial judgment remains with a qualified human. PeerScope never claims to replace reviewers or guarantee correctness.' },
]

function useLenis(enabled) {
  useEffect(() => {
    if (!enabled) return undefined
    const lenis = new Lenis({ lerp: 0.1, smoothWheel: true })
    let raf
    const tick = (t) => {
      lenis.raf(t)
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      lenis.destroy()
    }
  }, [enabled])
}

function Nav() {
  const { theme, toggle } = useTheme()
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])
  return (
    <header className={`l-nav${scrolled ? ' scrolled' : ''}`}>
      <div className="l-wrap l-nav-inner">
        <Link to="/" className="brand" aria-label="PeerScope home">
          <BrandMark />
          <span>PeerScope</span>
        </Link>
        <nav className="l-nav-links" aria-label="Page sections">
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
          <a href="#numbers">Live numbers</a>
        </nav>
        <div className="row">
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
          <Button as={Link} to="/app" variant="primary" size="sm" iconRight={ArrowRight}>
            Open app
          </Button>
        </div>
      </div>
    </header>
  )
}

function Hero() {
  const { health } = useStats()
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-layer hero-grid" aria-hidden="true" />
      <div className="hero-layer hero-orbs" aria-hidden="true">
        <span className="orb orb-a" />
        <span className="orb orb-b" />
      </div>
      <div className="hero-layer hero-visual" aria-hidden="true">
        <Suspense fallback={<img className="hero-fallback" src="/hero-fallback.svg" alt="" />}>
          <HeroVisual />
        </Suspense>
      </div>
      <div className="l-wrap hero-inner">
        <div className="hero-copy">
          <SlideUp>
            <span className="eyebrow">
              <span className="pulse" aria-hidden="true" /> AI-assisted · runs on your machine
            </span>
          </SlideUp>
          <SlideUp delay={0.08} as="h1" id="hero-title">
            Evaluate the paper.
            <br />
            <span className="text-grad">Match the right reviewers.</span>
          </SlideUp>
          <SlideUp delay={0.16} as="p" className="hero-sub">
            PeerScope turns a research-paper PDF into a structured preliminary assessment and a transparent, auditable ranking of reviewers - with every score explained.
          </SlideUp>
          <SlideUp delay={0.24} className="hero-actions">
            <MagneticButton>
              <Button as={Link} to="/app/analyze" variant="primary" size="lg" icon={ScanSearch}>
                Analyze a paper
              </Button>
            </MagneticButton>
            <Button as={Link} to="/app" size="lg" iconRight={ArrowRight}>
              Open dashboard
            </Button>
          </SlideUp>
          <SlideUp delay={0.32} className="hero-meta">
            <span>
              <FileSearch size={14} aria-hidden="true" /> {health ? `${health.reviewer_count} reviewers ready` : 'Local-first'}
            </span>
            <span>No paid APIs · no credentials</span>
            <span>Final judgment stays human</span>
          </SlideUp>
        </div>
      </div>
      <div className="scroll-cue" aria-hidden="true">
        <span />
      </div>
    </section>
  )
}

function VizUpload() {
  const parts = [
    ['Title', 'Detected from page 1'],
    ['Summary', 'Abstract or opening text'],
    ['Methodology', 'Section heading + word count'],
    ['Results', 'Experiments / evaluation'],
    ['References', 'Parsed and counted'],
  ]
  return (
    <div>
      <div className="viz-label">What gets extracted</div>
      <ul className="anatomy-list">
        {parts.map(([t, d], i) => (
          <li key={t}>
            <span className={`anatomy-tag${i === 2 ? ' hot' : ''}`}>{t}</span>
            {d}
          </li>
        ))}
      </ul>
      <div className="viz-foot">PDF · up to 20 MB · processed locally</div>
    </div>
  )
}

function VizReview() {
  const dims = ['Method', 'Evidence', 'Clarity', 'Reproducibility', 'Novelty', 'Limitations']
  return (
    <div>
      <div className="viz-label">Review dimensions</div>
      <div className="tag-row" style={{ gap: 10 }}>
        {dims.map((d) => (
          <span key={d} className="signal">
            {d}
          </span>
        ))}
      </div>
      <ul className="anatomy-list" style={{ marginTop: 22 }}>
        <li>
          <span className="anatomy-tag">Signal</span>accept / borderline / reject, with confidence
        </li>
        <li>
          <span className="anatomy-tag">Checks</span>structure, evidence, method, presentation
        </li>
        <li>
          <span className="anatomy-tag hot">Critique</span>strengths, concerns, next steps
        </li>
      </ul>
    </div>
  )
}

function VizMatch() {
  const w = [
    ['Expertise similarity', 55, true],
    ['Keyword overlap', 20],
    ['Method overlap', 15],
    ['Availability', 10],
  ]
  return (
    <div>
      <div className="viz-label">Default match weights</div>
      <div className="viz-bars">
        {w.map(([l, v, best]) => (
          <div key={l} className={`viz-bar${best ? ' best' : ''}`}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <span>{l}</span>
              <strong>{v}%</strong>
            </div>
            <div className="viz-track">
              <i style={{ width: `${v * 1.6}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="viz-foot">minus a conflict penalty · scaled 0-100</div>
    </div>
  )
}

function VizExport() {
  return (
    <div>
      <div className="viz-label">Every analysis is stored</div>
      <div className="viz-stats">
        <div>
          <strong>JSON</strong>
          <span>machine-readable</span>
        </div>
        <div>
          <strong>PDF</strong>
          <span>shareable report</span>
        </div>
        <div>
          <strong>Audit</strong>
          <span>per-score breakdown</span>
        </div>
      </div>
      <div className="viz-foot">Re-open any run from Analysis history</div>
    </div>
  )
}

const VIZ = [VizUpload, VizReview, VizMatch, VizExport]

function How() {
  const [active, setActive] = useState(0)
  const copyRef = useRef(null)
  const refs = useRef([])
  const { scrollYProgress } = useScroll({ target: copyRef, offset: ['start 60%', 'end 70%'] })
  const grow = useSpring(scrollYProgress, { stiffness: 120, damping: 30 })

  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(Number(e.target.dataset.i))
      },
      { rootMargin: '-45% 0px -45% 0px' },
    )
    refs.current.forEach((el) => el && io.observe(el))
    return () => io.disconnect()
  }, [])

  const Viz = VIZ[active]
  return (
    <section className="how" id="how" aria-labelledby="how-title">
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">How it works</span>
          <h2 id="how-title">From PDF to a defensible reviewer shortlist</h2>
        </Reveal>
        <div className="how-grid">
          <div className="how-copy" ref={copyRef}>
            <div className="how-progress" aria-hidden="true">
              <motion.i style={{ scaleY: grow }} />
            </div>
            {STEPS.map((s, i) => (
              <div key={s.title} className={`how-step${active === i ? ' on' : ''}`} data-i={i} ref={(el) => (refs.current[i] = el)}>
                <span className="how-num mono">STEP 0{i + 1}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
          <div className="how-visual-col">
            <div className="how-visual">
              <div className="card how-card" aria-live="polite">
                <div className="how-card-head">
                  <strong>{STEPS[active].title}</strong>
                  <div className="dots" aria-hidden="true">
                    {STEPS.map((_, i) => (
                      <i key={i} className={i === active ? 'on' : ''} />
                    ))}
                  </div>
                </div>
                <Viz />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Numbers() {
  const { health, metrics, error } = useStats()
  const [count, setCount] = useState(null)
  useEffect(() => {
    let alive = true
    api
      .analyses()
      .then((l) => alive && setCount(l.length))
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [])
  const acc = metrics && metrics.status !== 'missing' ? metrics.accuracy : null
  const items = [
    { label: 'reviewers in the directory', value: health?.reviewer_count, fmt: (v) => String(Math.round(v)) },
    { label: 'analyses stored', value: count, fmt: (v) => String(Math.round(v)) },
    { label: 'decision-model accuracy', value: acc === null ? null : acc * 100, fmt: (v) => `${v.toFixed(1)}%` },
    { label: 'held-out test samples', value: metrics?.test_samples, fmt: (v) => String(Math.round(v)) },
    { label: 'MB maximum upload', value: 20, fmt: (v) => String(Math.round(v)) },
  ]
  return (
    <section className="numbers" id="numbers" aria-label="Live numbers from the backend">
      <div className="l-wrap">
        <div className="numbers-grid">
          {items.map((it) => (
            <div className="number" key={it.label}>
              <strong>{it.value === undefined || it.value === null ? error ? '–' : <Skeleton width={70} height={34} /> : <CountUp value={it.value} format={it.fmt} />}</strong>
              <span>{it.label}</span>
            </div>
          ))}
        </div>
        <p className="faint numbers-note">
          {error ? 'The backend is offline, so live figures are unavailable.' : metrics?.synthetic_fallback ? 'Live from your PeerScope instance. The decision model was trained on a labelled synthetic fallback dataset.' : 'Live from your PeerScope instance.'}
        </p>
      </div>
    </section>
  )
}

export default function Landing() {
  const reduced = useReducedMotion()
  useLenis(!reduced)
  useEffect(() => {
    document.title = 'PeerScope · AI-assisted paper evaluation & reviewer matching'
  }, [])
  return (
    <div className="landing">
      <a href="#main-landing" className="skip-link">
        Skip to content
      </a>
      <Nav />
      <main id="main-landing">
        <Hero />

        <div className="signals" aria-label="Pipeline stages">
          <Marquee speed={55} label="Pipeline stages">
            {SIGNALS.map((s) => (
              <span className="signal" key={s}>
                {s}
              </span>
            ))}
          </Marquee>
        </div>

        <How />

        <section className="l-section" id="features" aria-labelledby="feat-title">
          <div className="l-wrap">
            <Reveal className="section-head">
              <span className="eyebrow">Features</span>
              <h2 id="feat-title">Built to be checked, not just believed</h2>
            </Reveal>
            <Parallax speed={0.08}>
              <Stagger className="feature-cards" inView>
                {FEATURES.map(({ icon: Icon, title, body }) => (
                  <div className="card spot feature-card" key={title}>
                    <span className="feature-icon">
                      <Icon size={20} aria-hidden="true" />
                    </span>
                    <h3>{title}</h3>
                    <p>{body}</p>
                  </div>
                ))}
              </Stagger>
            </Parallax>
          </div>
        </section>

        <Numbers />

        <section className="l-section" aria-labelledby="cta-title">
          <div className="l-wrap">
            <Reveal className="card cta-card">
              <span className="cta-glow" aria-hidden="true" />
              <h2 id="cta-title">Ready to evaluate your first paper?</h2>
              <p>Upload a PDF and get an auditable assessment and reviewer shortlist in one pass.</p>
              <div className="hero-actions" style={{ justifyContent: 'center' }}>
                <MagneticButton>
                  <Button as={Link} to="/app/analyze" variant="primary" size="lg" icon={ScanSearch}>
                    Analyze a paper
                  </Button>
                </MagneticButton>
                <Button as={Link} to="/app/reviewers" size="lg" icon={Users}>
                  Manage reviewers
                </Button>
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="l-footer">
        <div className="l-wrap">
          <div className="l-footer-inner">
            <Link to="/" className="brand">
              <BrandMark />
              <span>
                PeerScope<small>Paper evaluation &amp; reviewer matching</small>
              </span>
            </Link>
            <div className="l-footer-links">
              <Link to="/app">Dashboard</Link>
              <Link to="/app/analyze">Analyze paper</Link>
              <Link to="/app/reviewers">Reviewers</Link>
              <Link to="/app/model">Model performance</Link>
              <Link to="/app/history">History</Link>
              <Link to="/app/about">About &amp; responsible use</Link>
            </div>
          </div>
          <p className="faint l-footer-base">PeerScope provides AI-assisted analysis and reviewer matching for decision support. Final editorial judgment remains with a qualified human.</p>
        </div>
      </footer>
    </div>
  )
}
