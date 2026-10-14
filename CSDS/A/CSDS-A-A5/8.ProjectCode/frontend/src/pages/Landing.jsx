import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'
import { ArrowRight, Brain, FileText, Moon, Network, Radar, Scale, Sun, Target } from 'lucide-react'
import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, SlideUp } from '../components/motion'
import Backdrop from '../components/reactbits/Backdrop'
import Logo from '../components/ui/Logo'
import { IconButton } from '../components/ui/controls'
import { StatusDot } from '../components/ui/display'
import Typewriter from '../components/ui/Typewriter'
import { inr, num } from '../format'
import { useAuth } from '../lib/auth'
import { useReducedMotion } from '../lib/reduced'
import { useTheme } from '../lib/theme'

gsap.registerPlugin(ScrollTrigger)

const FEATURES = [
  { icon: Brain, title: 'Learns normal GST behaviour', text: 'A self-supervised JEPA encoder learns what a normal taxpayer-month looks like from unlabelled invoices and returns. No fraud labels needed.' },
  { icon: Network, title: 'Finds fraud rings', text: 'Graph analytics trace circular-trading loops and clusters of registrations sharing an address or contact number.' },
  { icon: Target, title: 'Multi-layer risk', text: 'Invoice, return-behaviour and network signals combine into one ranked risk score per taxpayer and per invoice chain.' },
  { icon: FileText, title: 'Explains every flag', text: 'Gemini turns the evidence into an investigator-style case note, citing each fact it uses.' },
  { icon: Radar, title: 'Four patterns covered', text: 'Fake invoices, circular trading, shell entities and abnormal spikes in ITC claims.' },
  { icon: Scale, title: 'Measured, not assumed', text: 'Precision@k, recall and F1 against ground truth, side by side with a rule-based baseline.' },
]
const STEPS = [
  ['Generate the ecosystem', 'Load or generate a GST ecosystem: taxpayers, invoices and GSTR-1 / 2B / 3B returns from a seeded generator.'],
  ['Build three feature layers', 'Invoice, return-behaviour and buyer-seller network features for every taxpayer-month.'],
  ['Score deviation + trace rings', 'The JEPA encoder scores how far each month drifts from learned normal; graph analytics trace loops and shell clusters.'],
  ['Rank, drill in, explain', 'Ranked taxpayers and invoice chains, drill-down to evidence, and a written case note that cites every fact.'],
]
const TICKER = ['fake invoices', 'circular trading', 'shell entities', 'ITC spikes', 'JEPA encoder', 'GSTR-1 / 2B / 3B', 'invoice chains', 'precision@k', 'cited case notes']

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

// Real readout from the public health endpoint (+ overview when signed in).
function LiveReadout({ user }) {
  const [health, setHealth] = useState(null)
  const [down, setDown] = useState(false)
  const [stats, setStats] = useState(null)
  useEffect(() => {
    api.get('/health').then((r) => setHealth(r.data)).catch(() => setDown(true))
    if (user) api.get('/overview').then((r) => setStats(r.data.stats)).catch(() => {})
  }, [user])
  const line = (k, v, tone = 'fg') => (
    <div className="flex justify-between gap-4"><span className="text-dim">{k}</span><span style={{ color: `var(--${tone})` }}>{v}</span></div>
  )
  return (
    <div className="panel scan w-full max-w-md overflow-hidden font-mono text-[12px]">
      <div className="relative z-[1] flex items-center gap-1.5 border-b border-line px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-alert/70" /><span className="h-2 w-2 rounded-full bg-warn/70" /><span className="h-2 w-2 rounded-full bg-ok/70" />
        <span className="ml-2 text-[11px] text-dim">taxsentinel — live</span>
      </div>
      <div className="relative z-[1] space-y-1 p-4 leading-relaxed">
        <div className="text-ok">$ curl :8105/api/health</div>
        {down ? line('status', 'unreachable - start run.bat', 'alert') : !health ? <div className="text-dim">connecting…</div> : (
          <>
            {line('status', health.status, 'ok')}
            {line('pipeline_ready', String(health.pipeline_ready), health.pipeline_ready ? 'ok' : 'warn')}
            {line('gemini_configured', String(health.gemini_configured), health.gemini_configured ? 'ok' : 'warn')}
          </>
        )}
        {stats && (
          <>
            <div className="pt-2 text-ok">$ curl :8105/api/overview</div>
            {line('taxpayers', num(stats.taxpayers))}
            {line('invoices', num(stats.invoices))}
            {line('flagged', num(stats.flagged), 'alert')}
            {line('itc_at_risk', inr(stats.itc_at_risk), 'warn')}
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
        <h2 className="mt-3 font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">From raw returns to a cited case note in four passes.</h2>
        <p className="mt-4 max-w-md text-muted">Every pass runs on your machine against the current ecosystem. Generate a new one from the control room and the whole analysis re-runs in under a minute.</p>
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

function StatsStrip({ user }) {
  const [stats, setStats] = useState(null)
  useEffect(() => {
    if (user) api.get('/overview').then((r) => setStats(r.data.stats)).catch(() => {})
  }, [user])
  const items = stats
    ? [[stats.taxpayers, 'taxpayers analysed', num], [stats.invoices, 'invoices scored', num], [stats.flagged, 'taxpayers flagged', num], [stats.itc_at_risk, 'ITC at risk', inr]]
    : [[4, 'fraud patterns covered', num], [3, 'evidence layers fused', num], [5, 'baseline rules (R1-R5) compared', num], [3, 'return types reconciled', num]]
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
        {stats ? <><StatusDot tone="ok" className="mr-1.5" /> live from the current ecosystem</> : 'sign in to see the live ecosystem counts'}
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

      {/* hero */}
      <section className="relative">
        <Backdrop className="absolute inset-0 fade-mask" />
        <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-4 pb-20 pt-16 sm:px-6 sm:pt-24 lg:grid-cols-[1.25fr_1fr]">
          <div>
            <SlideUp className="inline-flex items-center gap-2 rounded-full border border-ok/30 bg-ok/5 px-3 py-1 font-mono text-[11px] uppercase tracking-[0.14em] text-ok">
              <StatusDot tone="ok" /> GST input-tax-credit fraud analytics
            </SlideUp>
            <Typewriter as="h1" speed={22} delay={250} keepCaret
              text="Find the fake invoices, circular trades and shell firms behind suspicious ITC claims."
              className="mt-6 font-mono text-3xl font-semibold leading-[1.15] tracking-tight text-fg sm:text-5xl" />
            <SlideUp delay={0.35}>
              <p className="mt-6 max-w-xl text-lg text-muted">
                TaxSentinel learns how normal businesses file and trade, ranks taxpayers and invoice chains by how far they
                deviate, and writes a plain-language case note that cites the evidence.
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
            <SlideUp delay={0.6} className="w-full max-w-md"><LiveReadout user={user} /></SlideUp>
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
        <h2 className="mt-3 max-w-2xl font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">Built for investigators, forensic accountants and compliance teams.</h2>
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

      <StatsStrip user={user} />

      <section className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <Reveal className="panel scan relative overflow-hidden p-8 sm:p-12">
          <Backdrop intensity={1.4} className="absolute inset-0 opacity-60 fade-mask" />
          <div className="relative z-[1] max-w-2xl">
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-ok">// ready</div>
            <h2 className="mt-3 font-mono text-2xl font-semibold tracking-tight text-fg sm:text-4xl">Open the control room and start with the highest-risk taxpayer.</h2>
            <p className="mt-4 text-muted">Sign in with the demo account or create your own. The bundled ecosystem is already analysed.</p>
            <div className="mt-8">
              <MagneticButton>
                <Link to={user ? '/app' : '/login?demo=1'} className="inline-flex h-11 items-center gap-2 rounded-[6px] bg-ok px-5 text-sm font-semibold text-on-ok hover:brightness-110">
                  {user ? 'Open dashboard' : 'Sign in with the demo account'} <ArrowRight size={16} />
                </Link>
              </MagneticButton>
            </div>
          </div>
        </Reveal>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-8 sm:px-6">
          <Logo />
          <p className="font-mono text-[11px] text-dim">The bundled ecosystem is synthetic sample data produced by a seeded generator. Risk scores are indications for review, not findings.</p>
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
