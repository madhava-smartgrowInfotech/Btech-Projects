import { Suspense, lazy, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BookOpen,
  Code2,
  Mic,
  Moon,
  Network,
  Sparkles,
  Store,
  Sun,
  Target,
  Trophy,
  Users,
} from 'lucide-react'
import Lenis from 'lenis'
import { Button, IconButton } from '../components/ui'
import { BrandMark } from '../components/ui/layout'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, SlideUp, Stagger } from '../components/motion'
import { useTheme } from '../lib/theme'
import { useAuth } from '../lib/auth'
import { api } from '../lib/api'
import { homeFor } from '../components/ui/layout'
import { prefersReducedMotion } from '../lib/motion'
import { useAsync } from '../lib/useAsync'

const HeroVisual = lazy(() => import('../components/three/HeroVisual'))

const FEATURES = [
  { icon: Network, title: 'Knowledge graph', text: 'Your curriculum as a directed prerequisite graph. See what is completed, strong, weak, recommended or still locked.' },
  { icon: BookOpen, title: 'AI learning roadmap', text: 'Prerequisite-aware steps toward your career goal, with the reason behind every recommendation.' },
  { icon: Target, title: 'Career matching', text: 'Cosine-similarity matching of your skills against real roles, with the exact skill gaps to close.' },
  { icon: Store, title: 'Learn & earn marketplace', text: 'Buy and sell notes, projects and courses with an in-app wallet. Nothing real is charged.' },
  { icon: Users, title: 'Peer mentorship', text: 'Mentors ranked by skill, domain, experience and rating. Send a request and track your sessions.' },
  { icon: Mic, title: 'Mock interviews', text: 'Role-specific questions scored locally on keyword coverage and semantic similarity, with a full report.' },
  { icon: Code2, title: 'Sandboxed coding', text: 'Solve problems in Python. Submissions run in an isolated process with a hard timeout.' },
  { icon: Trophy, title: 'XP, levels and badges', text: 'Every assessment, interview and solved problem earns XP, streaks and badges.' },
]

const STEPS = [
  {
    n: '01',
    title: 'Map what you know',
    text: 'Take short skill assessments. Each result updates your per-topic knowledge state across the prerequisite graph.',
    chain: ['Programming Fundamentals', 'Python', 'Data Structures', 'Machine Learning'],
    label: 'Prerequisite chain',
  },
  {
    n: '02',
    title: 'Find the weak links',
    text: 'The graph shows which prerequisite is blocking you, so you fix the foundation instead of guessing what to study next.',
    chain: ['Completed', 'Strong', 'Weak', 'Locked'],
    label: 'Topic status',
  },
  {
    n: '03',
    title: 'Follow a roadmap',
    text: 'Pick a career goal and get an ordered, prerequisite-respecting roadmap with resources and time estimates for each step.',
    chain: ['Step 1 · foundations', 'Step 2 · core skills', 'Step 3 · goal skills'],
    label: 'Your roadmap',
  },
  {
    n: '04',
    title: 'Practise, connect, earn',
    text: 'Rehearse interviews, solve coding problems, book a mentor and publish your own notes to the marketplace.',
    chain: ['Mock interview', 'Coding practice', 'Mentor session', 'Marketplace'],
    label: 'Keep growing',
  },
]

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
  const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
  return (
    <header className={`l-nav${scrolled ? ' scrolled' : ''}`}>
      <div className="l-wrap l-nav-inner">
        <Link to="/" className="brand" aria-label="SkillVerse home">
          <BrandMark />
          <span>SkillVerse</span>
        </Link>
        <nav className="l-nav-links" aria-label="Page sections">
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
          <a href="#numbers">Catalogue</a>
        </nav>
        <div className="row" style={{ flexWrap: 'nowrap' }}>
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={label} onClick={toggle} />
          {user ? (
            <Button as={Link} to={homeFor(user.role)} variant="primary" size="sm">
              Open app
            </Button>
          ) : (
            <>
              <Button as={Link} to="/login" variant="ghost" size="sm" className="hide-sm">
                Sign in
              </Button>
              <Button as={Link} to="/login?tab=register" variant="primary" size="sm">
                Get started
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

function Hero() {
  const { user } = useAuth()
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-layer hero-grid" aria-hidden="true" />
      <div className="hero-layer hero-orbs" aria-hidden="true">
        <span className="orb orb-a" />
        <span className="orb orb-b" />
      </div>
      <div className="hero-layer hero-visual">
        <Suspense fallback={<img className="hero-fallback" src="/hero-fallback.svg" alt="" aria-hidden="true" />}>
          <HeroVisual />
        </Suspense>
      </div>
      <div className="l-wrap hero-inner">
        <div className="hero-copy">
          <SlideUp>
            <span className="eyebrow">
              <span className="pulse" aria-hidden="true" />
              AI-driven learning and earning
            </span>
          </SlideUp>
          <SlideUp delay={0.08}>
            <h1 id="hero-title">
              Learn. Earn.
              <br />
              <span className="text-grad">Connect. Grow.</span>
            </h1>
          </SlideUp>
          <SlideUp delay={0.16}>
            <p className="hero-sub">
              SkillVerse turns your curriculum into a knowledge graph, builds a personal roadmap toward your career goal, and
              lets you practise interviews, solve code, find mentors and sell what you know.
            </p>
          </SlideUp>
          <SlideUp delay={0.24}>
            <div className="btn-row" style={{ marginTop: 32 }}>
              <MagneticButton>
                <Button as={Link} to={user ? homeFor(user.role) : '/login?tab=register'} variant="primary" size="lg" iconRight={ArrowRight}>
                  {user ? 'Open your workspace' : 'Create a free account'}
                </Button>
              </MagneticButton>
              {!user && (
                <Button as={Link} to="/login" size="lg">
                  Try a demo account
                </Button>
              )}
            </div>
          </SlideUp>
          <SlideUp delay={0.32}>
            <div className="hero-meta">
              <span>
                <Sparkles size={14} aria-hidden="true" /> Runs fully offline
              </span>
              <span>Based on IEEE Access 2026 · DOI 10.1109/ACCESS.2026.3662800</span>
            </div>
          </SlideUp>
        </div>
      </div>
      <div className="scroll-cue" aria-hidden="true">
        <span />
      </div>
    </section>
  )
}

function HowItWorks() {
  const [active, setActive] = useState(0)
  const refs = useRef([])
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(Number(e.target.dataset.i))
        })
      },
      { rootMargin: '-45% 0px -45% 0px' },
    )
    refs.current.forEach((el) => el && io.observe(el))
    return () => io.disconnect()
  }, [])
  const step = STEPS[active]
  return (
    <section className="how" id="how" aria-labelledby="how-title">
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">How it works</span>
          <h2 id="how-title">From “where am I?” to “what next?” in four steps</h2>
        </Reveal>
        <div className="how-grid">
          <div className="how-copy">
            <div className="how-progress" aria-hidden="true">
              <i style={{ transform: `scaleY(${(active + 1) / STEPS.length})`, transition: 'transform 500ms var(--ease-out)' }} />
            </div>
            {STEPS.map((s, i) => (
              <div key={s.n} className="how-step" data-i={i} ref={(el) => (refs.current[i] = el)}>
                <span className="how-num mono">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
                <div className="how-card inline card how-mobile-card" aria-hidden="true">
                  <StepVisual step={s} />
                </div>
              </div>
            ))}
          </div>
          <div className="how-visual-col">
            <div className="how-sticky">
              <div className="card how-card" aria-live="polite">
                <div className="how-card-head">
                  <span className="viz-label" style={{ margin: 0 }}>
                    {step.label}
                  </span>
                  <span className="dots" aria-hidden="true">
                    {STEPS.map((s, i) => (
                      <i key={s.n} className={i === active ? 'on' : ''} />
                    ))}
                  </span>
                </div>
                <StepVisual step={step} />
                <div className="viz-foot">
                  Step {active + 1} of {STEPS.length}: {step.title}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function StepVisual({ step }) {
  return (
    <ul className="anatomy-list" style={{ margin: 0 }}>
      {step.chain.map((c, i) => (
        <li key={c}>
          <span className={`anatomy-tag${i === step.chain.length - 1 ? '' : ''}`}>{String(i + 1).padStart(2, '0')}</span>
          <span style={{ color: 'var(--text)', fontWeight: 600 }}>{c}</span>
        </li>
      ))}
    </ul>
  )
}

function Features() {
  return (
    <section className="l-section" id="features" aria-labelledby="feat-title">
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">Everything in one place</span>
          <h2 id="feat-title">One ecosystem for the whole journey</h2>
        </Reveal>
        <Stagger className="feature-cards" inView>
          {FEATURES.map((f) => (
            <div key={f.title} className="card feature-card spot">
              <span className="feature-icon">
                <f.icon size={22} aria-hidden="true" />
              </span>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </div>
          ))}
        </Stagger>
      </div>
    </section>
  )
}

function Numbers() {
  const stats = useAsync(() => api.get('/auth/public/stats'), [])
  const s = stats.data
  const items = s
    ? [
        ['Learning topics in the graph', s.topics],
        ['Career roles', s.careers],
        ['Coding problems', s.problems],
        ['Interview questions', s.interview_questions],
        ['Marketplace resources', s.resources],
      ]
    : null
  return (
    <section className="numbers" id="numbers" aria-labelledby="num-title">
      <div className="l-wrap">
        <h2 id="num-title" className="sr-only">
          What is in the catalogue
        </h2>
        {items ? (
          <div className="numbers-grid">
            {items.map(([label, value]) => (
              <div className="number" key={label}>
                <strong>
                  <CountUp value={value} />
                </strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="numbers-note faint" role={stats.error ? 'status' : undefined}>
            {stats.loading ? 'Loading catalogue…' : 'Start the backend (run.bat) to see live catalogue numbers here.'}
          </p>
        )}
        {items && <p className="numbers-note faint">Live counts from the SkillVerse database.</p>}
      </div>
    </section>
  )
}

function Cta() {
  const { user } = useAuth()
  return (
    <section className="l-section">
      <div className="l-wrap">
        <Reveal>
          <div className="card cta-card" style={{ isolation: 'isolate' }}>
            <span className="cta-glow" aria-hidden="true" />
            <h2>Ready to see your knowledge graph?</h2>
            <p>Sign in with a seeded demo account and explore every screen, or create your own in under a minute.</p>
            <div className="btn-row" style={{ justifyContent: 'center', marginTop: 28 }}>
              <Button as={Link} to={user ? homeFor(user.role) : '/login'} variant="primary" size="lg" iconRight={ArrowRight}>
                {user ? 'Open your workspace' : 'Get started'}
              </Button>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

export default function Landing() {
  // smooth scrolling, skipped entirely for reduced-motion users
  useEffect(() => {
    if (prefersReducedMotion()) return undefined
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
  }, [])
  useEffect(() => {
    document.title = 'SkillVerse · Learn. Earn. Connect. Grow.'
  }, [])

  return (
    <div className="landing">
      <div className="grain" aria-hidden="true" />
      <a href="#how" className="skip-link">
        Skip to content
      </a>
      <LandingNav />
      <main>
        <Hero />
        <div className="signals" aria-label="Feature highlights">
          <Marquee speed={46} label="What SkillVerse includes">
            {FEATURES.map((f) => (
              <span className="signal" key={f.title}>
                {f.title}
              </span>
            ))}
          </Marquee>
        </div>
        <HowItWorks />
        <Parallax speed={0.1}>
          <Features />
        </Parallax>
        <Numbers />
        <Cta />
      </main>
      <footer className="l-footer">
        <div className="l-wrap">
          <div className="l-footer-inner">
            <div>
              <Link to="/" className="brand" style={{ padding: 0 }}>
                <BrandMark />
                <span>
                  SkillVerse
                  <small>AI-driven learning and earning ecosystem for knowledge engineers</small>
                </span>
              </Link>
            </div>
            <div className="l-footer-links">
              <Link to="/login">Sign in</Link>
              <Link to="/login?tab=register">Register</Link>
              <a href="#how">How it works</a>
              <a href="#features">Features</a>
            </div>
          </div>
          <div className="l-footer-base faint">
            Base paper: Enhancing Efficient Personalized Learning and Educational Management in Universities Using Graph Neural Networks in
            Intelligent Tutoring Systems. IEEE Access, 2026. Wallet payments are simulated; no real money is involved.
          </div>
        </div>
      </footer>
    </div>
  )
}
