import { lazy, Suspense, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Lenis from 'lenis'
import { ArrowRight, Bot, FileSearch, Gauge, Hash, Moon, Radio, ShieldCheck, Sun, Workflow, Zap } from 'lucide-react'
import { useTheme } from '../lib/theme'
import { useAuth } from '../lib/auth'
import { useReducedMotion } from '../lib/motion'
import { BrandMark } from '../components/ui/layout'
import { Button, IconButton } from '../components/ui/controls'
import { Card } from '../components/ui/display'
import { CountUp, FadeIn, Marquee, MagneticButton, Parallax, Reveal, SlideUp, Stagger, gsap, ScrollTrigger } from '../components/motion'
import { CHECK_LABEL } from '../lib/format'

const HeroVisual = lazy(() => import('../components/three/HeroVisual'))

const SIGNALS = ['VOLTAGE_OVER', 'VOLTAGE_UNDER', 'LINE_OVERLOAD', 'TRANSFORMER_OVERLOAD', 'BATTERY_SOC_LIMIT', 'BATTERY_CHARGE_LIMIT', 'NODE_EXPORT_LIMIT', 'NODE_IMPORT_LIMIT', 'GRID_IMPORT_LIMIT', 'GRID_EXPORT_LIMIT', 'POWER_BALANCE_RESIDUAL', 'POWER_LIMIT_EXCEEDED', 'CURTAILMENT_EXCEEDS_GENERATION']

const AGENTS = [
  { id: 'prosumer_01', role: 'Residential prosumer', act: 'Charge battery', kw: '3.2 kW' },
  { id: 'ev_01', role: 'EV / storage node', act: 'Charge battery', kw: '7.4 kW' },
  { id: 'renewable_01', role: 'Renewable prosumer', act: 'Export power', kw: '1000 kW' },
]

const OUTCOMES = [
  { key: 'approved', label: 'Approved', tone: 'safe', text: 'Safe as requested. Executed unchanged.' },
  { key: 'projected', label: 'Projected', tone: 'warn', text: 'Power scaled to the largest value that passes every check, then re-verified.' },
  { key: 'rejected', label: 'Rejected', tone: 'danger', text: 'Malformed or unsafe at any size. Nothing is executed.' },
]

const STEPS = [
  { n: '01', title: 'Agents propose', text: 'Three agents - a residential prosumer, an EV and storage node, and a renewable prosumer - each read their own node and propose one structured action per step. They never touch the grid.' },
  { n: '02', title: 'The shield checks', text: 'Every proposal runs through ordered, deterministic checks: structure, limits, battery, power balance, and a trial AC power flow for voltage, line, transformer and grid limits.' },
  { n: '03', title: 'Approve, project or reject', text: 'Safe actions pass. Unsafe ones are scaled down to the largest verified-safe power, or rejected outright. Model text can never change this decision.' },
  { n: '04', title: 'Executed and audited', text: 'Only validated setpoints reach the grid. Every intervention lands in a SHA-256 hash-chained log, so later edits are detectable.' },
]

const FEATURES = [
  { icon: Bot, title: 'Decentralised agents', text: 'Each node has its own agent with its own context. Provider failures fall back to a labelled policy instead of silently guessing.' },
  { icon: ShieldCheck, title: 'Symbolic safety shield', text: 'A small deterministic layer that imports no LLM, agent or simulation code, so model output cannot influence it.' },
  { icon: Gauge, title: 'Verified by power flow', text: 'Voltage, line loading, transformer and grid limits are checked on a trial AC power flow before anything is committed.' },
  { icon: FileSearch, title: 'Explainable decisions', text: 'Inputs, decision factors, the action and the safety outcome are shown for every decision - no hidden chain-of-thought.' },
  { icon: Hash, title: 'Tamper-evident audit log', text: 'Every non-approved decision is chained with SHA-256. The console shows at a glance whether the chain is still valid.' },
  { icon: Radio, title: 'Live and reproducible', text: 'Seeded scenarios stream over WebSocket, with fault injection to show the shield working on demand.' },
]

function useStepScroll(count) {
  const [active, setActive] = useState(0)
  const root = useRef(null)
  const bar = useRef(null)
  const reduced = useReducedMotion()
  useLayoutEffect(() => {
    const el = root.current
    if (!el) return undefined
    const ctx = gsap.context(() => {
      el.querySelectorAll('.how-step').forEach((s, i) => {
        ScrollTrigger.create({ trigger: s, start: 'top 55%', end: 'bottom 55%', onToggle: (self) => self.isActive && setActive(i) })
      })
      if (bar.current && !reduced) {
        gsap.fromTo(bar.current, { scaleY: 0 }, { scaleY: 1, ease: 'none', scrollTrigger: { trigger: el.querySelector('.how-copy'), start: 'top 60%', end: 'bottom 60%', scrub: true } })
      }
    }, el)
    return () => ctx.revert()
  }, [count, reduced])
  return { active, root, bar }
}

function StepVisual({ step }) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div key={step} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.28 }}>
        {step === 0 && (
          <>
            <div className="viz-label">Example proposals this step</div>
            <ul className="viz-list">
              {AGENTS.map((a) => (
                <li key={a.id}>
                  <div><strong className="mono">{a.id}</strong><div className="faint">{a.role}</div></div>
                  <div className="viz-act"><span>{a.act}</span><strong>{a.kw}</strong></div>
                </li>
              ))}
            </ul>
            <div className="viz-foot">Illustrative values. Proposals are untrusted until the shield has decided.</div>
          </>
        )}
        {step === 1 && (
          <>
            <div className="viz-label">Checks run in order</div>
            <div className="checks big">
              {['STRUCTURE', 'POWER_LIMITS', 'BATTERY', 'NODE_LIMITS', 'POWER_BALANCE', 'POWER_FLOW', 'VOLTAGE', 'LINE_LOADING', 'TRANSFORMER', 'GRID_LIMITS'].map((c, i) => (
                <motion.span key={c} className="check-chip pass" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}>{CHECK_LABEL[c]}</motion.span>
              ))}
            </div>
            <div className="viz-foot">Same input, same grid state, same decision - every time.</div>
          </>
        )}
        {step === 2 && (
          <>
            <div className="viz-label">Three possible outcomes</div>
            <div className="outcomes">
              {OUTCOMES.map((o) => (
                <div key={o.key} className={`outcome ${o.key}`}>
                  <strong>{o.label}</strong>
                  <span>{o.text}</span>
                </div>
              ))}
            </div>
          </>
        )}
        {step === 3 && (
          <>
            <div className="viz-label">Hash-chained audit trail</div>
            <div className="chain">
              {['event #1', 'event #2', 'event #3'].map((e, i) => (
                <div key={e} className="chain-link">
                  <span className="mono">{e}</span>
                  <span className="faint mono">prev_hash → hash</span>
                </div>
              ))}
            </div>
            <div className="viz-foot">Edit one record and every later hash stops matching.</div>
          </>
        )}
      </motion.div>
    </AnimatePresence>
  )
}

export default function Landing() {
  const { theme, toggle } = useTheme()
  const { user } = useAuth()
  const reduced = useReducedMotion()
  const [scrolled, setScrolled] = useState(false)
  const { active, root, bar } = useStepScroll(STEPS.length)
  const cta = user ? { to: '/app', label: 'Open the console' } : { to: '/login', label: 'Open the console' }

  useEffect(() => {
    document.title = 'SafeGrid-AI · Let the agents propose, let the shield decide'
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    if (reduced) return undefined
    const lenis = new Lenis({ lerp: 0.1 })
    lenis.on('scroll', ScrollTrigger.update)
    const tick = (t) => lenis.raf(t * 1000)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)
    return () => {
      gsap.ticker.remove(tick)
      lenis.destroy()
    }
  }, [reduced])

  return (
    <div className="landing">
      <a href="#top" className="skip-link">Skip to content</a>
      <header className={`l-nav${scrolled ? ' scrolled' : ''}`}>
        <div className="l-wrap l-nav-inner">
          <Link to="/" className="brand">
            <BrandMark />
            <span>SafeGrid-AI</span>
          </Link>
          <nav className="l-nav-links" aria-label="Page sections">
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#numbers">At a glance</a>
          </nav>
          <div className="row" style={{ flexWrap: 'nowrap' }}>
            <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
            <Link className="btn btn-primary" to={cta.to}>{user ? 'Console' : 'Sign in'}</Link>
          </div>
        </div>
      </header>

      <main id="top">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-layer hero-grid" aria-hidden="true" />
          <div className="hero-layer hero-orbs" aria-hidden="true"><div className="orb orb-a" /><div className="orb orb-b" /></div>
          <div className="hero-layer hero-visual">
            <Suspense fallback={<img className="hero-fallback" src="/hero-fallback.svg" alt="" aria-hidden="true" />}>
              <HeroVisual />
            </Suspense>
          </div>
          <div className="l-wrap hero-inner">
            <div className="hero-copy">
              <FadeIn><span className="eyebrow"><span className="pulse" aria-hidden="true" />Explainable multi-agent power routing</span></FadeIn>
              <SlideUp delay={0.05}><h1 id="hero-title">Let the agents propose. <span className="text-grad">Let the shield decide.</span></h1></SlideUp>
              <SlideUp delay={0.12}>
                <p className="hero-sub">SafeGrid-AI routes power across a small smart grid with AI agents, and puts a deterministic Symbolic Safety Shield between every proposal and the grid. Watch what the AI wanted, what the shield allowed, and what actually ran.</p>
              </SlideUp>
              <SlideUp delay={0.2}>
                <div className="row hero-cta">
                  <MagneticButton><Link className="btn btn-primary btn-lg" to={cta.to}>{cta.label}<ArrowRight size={18} aria-hidden="true" /></Link></MagneticButton>
                  <a className="btn btn-lg" href="#how">See how it works</a>
                </div>
              </SlideUp>
              <FadeIn delay={0.4}>
                <div className="hero-meta">
                  <span><Zap size={14} aria-hidden="true" /> 3 agents</span>
                  <span>7 reproducible scenarios</span>
                  <span>Live over WebSocket</span>
                </div>
              </FadeIn>
            </div>
          </div>
          <div className="scroll-cue" aria-hidden="true"><span /></div>
        </section>

        <section className="signals" aria-label="Violations the shield guards against">
          <Marquee speed={60} label="Violation codes the shield checks for">
            {SIGNALS.map((s) => <span key={s} className="signal mono">{s}</span>)}
          </Marquee>
        </section>

        <section className="how l-section" id="how" ref={root} aria-labelledby="how-title">
          <div className="l-wrap">
            <Reveal className="section-head">
              <span className="eyebrow">How it works</span>
              <h2 id="how-title">Four steps between an idea and the grid</h2>
            </Reveal>
            <div className="how-grid">
              <div className="how-copy">
                <div className="how-progress" aria-hidden="true"><i ref={bar} /></div>
                {STEPS.map((s, i) => (
                  <div key={s.n} className="how-step">
                    <span className="how-num mono">{s.n}</span>
                    <h3>{s.title}</h3>
                    <p>{s.text}</p>
                    <Card className="how-card inline how-mobile" spotlight={false}><StepVisual step={i} /></Card>
                  </div>
                ))}
              </div>
              <div className="how-visual-col">
                <div className="how-visual how-desktop">
                  <Card className="how-card" spotlight={false}>
                    <div className="how-card-head">
                      <span className="eyebrow">Step {STEPS[active].n}</span>
                      <div className="dots" aria-hidden="true">{STEPS.map((s, i) => <i key={s.n} className={i === active ? 'on' : ''} />)}</div>
                    </div>
                    <StepVisual step={active} />
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="l-section" id="features" aria-labelledby="feat-title">
          <div className="l-wrap">
            <Reveal className="section-head">
              <span className="eyebrow">Built for trust</span>
              <h2 id="feat-title">Free to propose, impossible to bypass</h2>
            </Reveal>
            <Stagger className="feature-cards" inView>
              {FEATURES.map(({ icon: Icon, title, text }) => (
                <Card key={title} className="feature-card">
                  <span className="feature-icon"><Icon size={22} aria-hidden="true" /></span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </Card>
              ))}
            </Stagger>
          </div>
        </section>

        <section className="numbers" id="numbers" aria-label="SafeGrid-AI at a glance">
          <div className="l-wrap">
            <div className="numbers-grid">
              {[[3, 'Autonomous agents'], [7, 'Seeded scenarios'], [10, 'Ordered safety checks'], [3, 'Shield outcomes']].map(([v, l]) => (
                <div key={l} className="number"><strong><CountUp value={v} /></strong><span>{l}</span></div>
              ))}
              <div className="number"><strong>SHA-256</strong><span>Hash-chained audit log</span></div>
            </div>
            <p className="faint numbers-note">Everything runs on a simulated 3-node low-voltage feeder. It is not connected to, and must not be used to control, real equipment.</p>
          </div>
        </section>

        <section className="l-section" aria-labelledby="cta-title">
          <div className="l-wrap">
            <Parallax speed={0.1}>
              <Card className="cta-card" spotlight={false}>
                <div className="cta-glow" aria-hidden="true" />
                <h2 id="cta-title">See the shield in action</h2>
                <p>Pick the unsafe AI action scenario, press Start, and watch every unsafe proposal get scaled down or rejected in real time.</p>
                <div className="row" style={{ justifyContent: 'center', marginTop: 28 }}>
                  <Link className="btn btn-primary btn-lg" to={cta.to}>{cta.label}<ArrowRight size={18} aria-hidden="true" /></Link>
                </div>
              </Card>
            </Parallax>
          </div>
        </section>
      </main>

      <footer className="l-footer">
        <div className="l-wrap">
          <div className="l-footer-inner">
            <Link to="/" className="brand"><BrandMark /><span>SafeGrid-AI<small>Shielded multi-agent grid control</small></span></Link>
            <div className="l-footer-links">
              <a href="#how">How it works</a>
              <Link to="/login">Sign in</Link>
              <a href="#features">Features</a>
              <Link to="/app">Console</Link>
            </div>
          </div>
          <div className="l-footer-base faint">Simulated feeder for demonstration. Do not use to control real equipment.</div>
        </div>
      </footer>
    </div>
  )
}
