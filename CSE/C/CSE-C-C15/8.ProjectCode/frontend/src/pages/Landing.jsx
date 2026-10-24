import Lenis from 'lenis'
import { ArrowRight, Brain, Cpu, FlaskConical, Gauge, Moon, Network, ShieldCheck, Sun, Timer } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { CountUp, Marquee, MagneticButton, Reveal, SlideUp } from '../components/motion'
import Backdrop from '../components/reactbits/Backdrop'
import Logo from '../components/ui/Logo'
import Typewriter from '../components/ui/Typewriter'
import { Button, IconButton } from '../components/ui/controls'
import { Badge, StatusDot } from '../components/ui/display'
import { FEATURE_LABEL, fmt } from '../format'
import { useAuth } from '../lib/auth'
import { prefersReducedMotion } from '../lib/reduced'
import { useTheme } from '../lib/theme'

const STAGES = [
  ['capture', 'Scapy sniff or the software simulator produces packets.'],
  ['aggregate', 'Rolling windows become 10 directional traffic features.'],
  ['classify', 'A 200-tree Random Forest labels each window Benign or Attack.'],
  ['score', 'Distributed-risk and an explainable severity are computed.'],
  ['mitigate', 'High and critical windows quarantine top sources, then auto-recover.'],
]

const FEATURES = [
  [Brain, 'Random Forest detection', 'Every window is classified with its confidence shown next to the verdict.'],
  [Network, 'Carpet-bombing aware', 'Source and destination spread feed a distributed-risk score, not just raw volume.'],
  [Gauge, 'Explainable severity', 'Low to Critical, with every contributing factor listed. No black box.'],
  [ShieldCheck, 'Adaptive mitigation', 'Application-level quarantine with automatic expiry. The OS firewall is never touched.'],
  [Cpu, 'Host health', 'CPU, memory and interface throughput sampled alongside the traffic.'],
  [FlaskConical, 'Simulation mode', 'Flood, carpet-bombing and slow attacks generated in software. Clearly labelled, nothing is sent.'],
]

function useSmoothScroll() {
  useEffect(() => {
    if (prefersReducedMotion()) return undefined
    const lenis = new Lenis({ duration: 1.1 })
    let raf = 0
    const loop = (t) => { lenis.raf(t); raf = requestAnimationFrame(loop) }
    raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); lenis.destroy() }
  }, [])
}

export default function Landing() {
  useSmoothScroll()
  const { theme, toggle } = useTheme()
  const { user } = useAuth()
  const [metrics, setMetrics] = useState(null)
  const [totals, setTotals] = useState(null)
  const [offline, setOffline] = useState(false)

  useEffect(() => {
    let off = false
    api.get('/model/metrics', { silent: true }).then((r) => { if (!off) setMetrics(r.data.trained ? r.data.metrics : null) }).catch(() => { if (!off) setOffline(true) })
    api.get('/detections', { silent: true, params: { limit: 1 } }).then((r) => { if (!off) setTotals(r.data) }).catch(() => { if (!off) setOffline(true) })
    return () => { off = true }
  }, [])

  const attacks = totals?.by_prediction?.Attack ?? null
  const benign = totals?.by_prediction?.Benign ?? null
  const cta = user ? '/app' : '/login'

  return (
    <div className="relative overflow-x-clip">
      <header className="sticky top-0 z-30 border-b border-line bg-bg/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 w-full max-w-[1200px] items-center gap-3 px-4 sm:px-6">
          <Link to="/" aria-label="SentinelFlow home"><Logo /></Link>
          <nav aria-label="Sections" className="ml-6 hidden gap-5 font-mono text-xs uppercase tracking-wider text-muted md:flex">
            <a href="#pipeline" className="hover:text-ok">Pipeline</a>
            <a href="#features" className="hover:text-ok">Features</a>
            <a href="#evidence" className="hover:text-ok">Evidence</a>
          </nav>
          <div className="flex-1" />
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
          <Link to={cta}><Button size="sm">{user ? 'Open console' : 'Sign in'}</Button></Link>
        </div>
      </header>

      <section className="relative">
        <Backdrop className="absolute inset-x-0 top-0 h-[560px] fade-mask-bottom opacity-80" />
        <div className="relative z-[1] mx-auto w-full max-w-[1200px] px-4 pb-20 pt-16 sm:px-6 sm:pt-24">
          <SlideUp>
            <Badge tone="ok" dot>real-time ddos defence</Badge>
          </SlideUp>
          <Typewriter as="h1" text="Detect the flood. Contain it. Recover." speed={34} keepCaret
            className="mt-5 block max-w-4xl font-mono text-3xl font-semibold leading-tight tracking-tight text-fg sm:text-5xl" />
          <SlideUp delay={0.3}>
            <p className="mt-5 max-w-2xl text-base text-muted sm:text-lg">
              SentinelFlow classifies every rolling traffic window with a Random Forest, scores how distributed the attack is,
              explains its severity and quarantines the worst sources automatically, then lets them recover.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <MagneticButton><Link to={cta}><Button size="lg" icon={ArrowRight}>{user ? 'Open the console' : 'Enter the console'}</Button></Link></MagneticButton>
              <a href="#pipeline"><Button size="lg" variant="secondary">How it works</Button></a>
            </div>
          </SlideUp>

          <SlideUp delay={0.45} className="mt-12">
            <div className="panel scan max-w-3xl overflow-hidden">
              <div className="relative z-[1] flex items-center justify-between border-b border-line px-3 py-2 font-mono text-[11px] text-muted">
                <span>~/sentinelflow/status</span>
                <StatusDot tone={offline ? 'alert' : 'ok'} label={offline ? 'api offline' : 'api online'} />
              </div>
              <dl className="relative z-[1] grid grid-cols-2 gap-px bg-line sm:grid-cols-4">
                {[
                  ['Attack windows', attacks, 'alert'],
                  ['Benign windows', benign, 'ok'],
                  ['F1 score', metrics ? metrics.f1 * 100 : null, 'cyan', (v) => `${v.toFixed(2)}%`],
                  ['ROC-AUC', metrics?.roc_auc != null ? metrics.roc_auc * 100 : null, 'info', (v) => `${v.toFixed(2)}%`],
                ].map(([label, value, tone, format]) => (
                  <div key={label} className="bg-panel p-4">
                    <dt className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted">{label}</dt>
                    <dd className="mt-1 font-mono text-2xl font-semibold" style={{ color: `var(--${tone})` }}>
                      {typeof value === 'number' ? <CountUp value={value} format={format} /> : <span className="text-dim">{offline ? 'offline' : '...'}</span>}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
            {offline && <p className="mt-2 text-xs text-muted">The backend is not reachable, so live counters are blank. Start it with run.bat.</p>}
          </SlideUp>
        </div>
      </section>

      <section id="pipeline" className="mx-auto w-full max-w-[1200px] scroll-mt-16 px-4 py-16 sm:px-6">
        <Reveal>
          <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ok">pipeline</div>
          <h2 className="mt-2 font-mono text-2xl font-semibold text-fg sm:text-3xl">From packet to decision in five stages</h2>
        </Reveal>
        <Reveal stagger={0.08} as="ol" className="mt-8 grid gap-3 md:grid-cols-5">
          {STAGES.map(([name, text], i) => (
            <li key={name} className="panel scan p-4">
              <div className="relative z-[1]">
                <div className="font-mono text-[11px] text-ok">0{i + 1} / {name}</div>
                <p className="mt-2 text-sm text-muted">{text}</p>
              </div>
            </li>
          ))}
        </Reveal>
      </section>

      <section id="features" className="mx-auto w-full max-w-[1200px] scroll-mt-16 px-4 py-12 sm:px-6">
        <Reveal>
          <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ok">features</div>
          <h2 className="mt-2 font-mono text-2xl font-semibold text-fg sm:text-3xl">Built for a defender, not a demo reel</h2>
        </Reveal>
        <Reveal stagger={0.07} className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(([Icon, title, text]) => (
            <article key={title} className="panel scan p-5">
              <div className="relative z-[1]">
                <Icon size={20} className="text-ok" aria-hidden="true" />
                <h3 className="mt-3 font-mono text-sm font-semibold text-fg">{title}</h3>
                <p className="mt-1.5 text-sm text-muted">{text}</p>
              </div>
            </article>
          ))}
        </Reveal>
      </section>

      <section className="border-y border-line py-4" aria-label="Model input features">
        <Marquee duration={50}>
          {Object.values(FEATURE_LABEL).map((l) => (
            <span key={l} className="mx-5 whitespace-nowrap font-mono text-xs uppercase tracking-[0.14em] text-dim">{l} <span className="text-ok">/</span></span>
          ))}
        </Marquee>
      </section>

      <section id="evidence" className="mx-auto w-full max-w-[1200px] scroll-mt-16 px-4 py-16 sm:px-6">
        <Reveal>
          <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ok">evidence</div>
          <h2 className="mt-2 font-mono text-2xl font-semibold text-fg sm:text-3xl">Numbers from the trained model, not slides</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Metrics are read live from the artifacts written at training time.
            {metrics?.is_synthetic && ' They describe the synthetic fallback dataset, and the console says so on every screen that shows them.'}
          </p>
        </Reveal>
        <Reveal stagger={0.08} className="mt-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {metrics ? [
            ['Accuracy', metrics.accuracy * 100, (v) => `${v.toFixed(2)}%`], ['Precision', metrics.precision * 100, (v) => `${v.toFixed(2)}%`],
            ['Recall', metrics.recall * 100, (v) => `${v.toFixed(2)}%`], ['Test windows', metrics.test_samples, (v) => fmt(v)],
          ].map(([l, v, f]) => (
            <div key={l} className="panel p-5">
              <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted">{l}</div>
              <div className="mt-1 font-mono text-3xl font-semibold text-fg"><CountUp value={v} format={f} /></div>
            </div>
          )) : [0, 1, 2, 3].map((i) => (
            <div key={i} className="panel p-5">
              <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted">{['Accuracy', 'Precision', 'Recall', 'Test windows'][i]}</div>
              <div className="mt-1 font-mono text-3xl text-dim">{offline ? 'offline' : '...'}</div>
            </div>
          ))}
        </Reveal>
      </section>

      <section className="mx-auto w-full max-w-[1200px] px-4 pb-24 sm:px-6">
        <Reveal className="panel scan p-8 text-center sm:p-12">
          <div className="relative z-[1]">
            <Timer size={22} className="mx-auto text-ok" aria-hidden="true" />
            <h2 className="mt-3 font-mono text-2xl font-semibold text-fg sm:text-3xl">See a flood get contained in under a minute</h2>
            <p className="mx-auto mt-2 max-w-xl text-sm text-muted">Start a simulation from the console: no capture rights, no hardware, the same model and the same mitigation logic.</p>
            <Link to={cta} className="mt-6 inline-block"><Button size="lg" icon={ArrowRight}>{user ? 'Open the console' : 'Enter the console'}</Button></Link>
          </div>
        </Reveal>
      </section>

      <footer className="border-t border-line py-6 text-center font-mono text-[11px] text-dim">
        SentinelFlow · defensive network monitoring · localhost only
      </footer>
    </div>
  )
}
