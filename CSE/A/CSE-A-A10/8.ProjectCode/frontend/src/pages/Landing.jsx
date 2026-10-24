import Lenis from 'lenis'
import { ArrowRight, Brain, Camera, Moon, Network, ShieldAlert, Siren, Sun, Waypoints, Workflow } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { CountUp, FadeIn, MagneticButton, Marquee, Reveal, Stagger } from '../components/motion'
import Backdrop from '../components/reactbits/Backdrop'
import TrafficMap from '../components/traffic/TrafficMap'
import { Logo } from '../components/ui/AppShell'
import { IconButton } from '../components/ui/controls'
import { Card, StatusDot } from '../components/ui/display'
import Typewriter from '../components/ui/Typewriter'
import { useAuth } from '../lib/auth'
import { useReducedMotion } from '../lib/reduced'
import { useTheme } from '../lib/theme'

const CAPS = [
  { icon: Camera, title: 'Detect', body: 'YOLOv8 counts cars, bikes, buses and trucks per approach lane and turns them into passenger-car-equivalent density.' },
  { icon: Siren, title: 'Prioritise', body: 'A red+blue light-bar detector spots emergency vehicles and pre-empts signals along their route as a green wave.' },
  { icon: Brain, title: 'Predict', body: 'A gradient-boosted model forecasts every approach queue 30 seconds ahead, so green goes where the build-up is coming.' },
  { icon: Network, title: 'Coordinate', body: 'Neighbouring junctions share platoon look-ahead and avoid spill-back instead of pushing the queue down the road.' },
  { icon: ShieldAlert, title: 'Enforce', body: 'Red-light jumping and wrong-way driving are flagged with a plate, a vehicle class and a detector confidence.' },
  { icon: Workflow, title: 'Validate', body: 'Four controllers run on identical traffic in a built-in simulator, so every claim has a fair baseline.' },
]
const STEPS = [
  ['01', 'Camera in', 'Junction frames arrive; vehicles are detected and counted.'],
  ['02', 'Density out', 'Counts become PCU density and a recommended green time.'],
  ['03', 'Forecast', 'The model predicts queues 30 s ahead for every approach.'],
  ['04', 'Retime', 'Pressure, fairness and emergency pre-emption set the next phase.'],
  ['05', 'Coordinate', 'Neighbours receive look-ahead and avoid spill-back.'],
]
const CHIPS = ['YOLOv8', 'Machine learning', 'Computer vision', 'Emergency priority', 'Inter-junction communication', 'Violation detection', 'Green wave', 'PCU density']
const LINE_COLOR = { sig: 'var(--ok)', emg: 'var(--alert)', vio: 'var(--warn)', sys: 'var(--cyan)' }

function useSmoothScroll() {
  const reduced = useReducedMotion()
  useEffect(() => {
    if (reduced) return undefined
    const lenis = new Lenis({ duration: 1.1 })
    let raf = 0
    const loop = (t) => { lenis.raf(t); raf = requestAnimationFrame(loop) }
    raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); lenis.destroy() }
  }, [reduced])
}

// Polls the public preview simulation (a real, separate Sim) once or twice a second.
function usePulse() {
  const [pulse, setPulse] = useState(null)
  const [offline, setOffline] = useState(false)
  const [lines, setLines] = useState([{ kind: 'sys', text: '$ flowsense attach --network 2x2 --controller advanced' }])
  useEffect(() => {
    let live = true
    let timer
    const tick = async () => {
      if (document.hidden) { timer = setTimeout(tick, 1500); return }
      try {
        const r = await api.get('/public/pulse', { silent: true })
        if (!live) return
        setPulse(r.data)
        setOffline(false)
        if (r.data.lines?.length) setLines((old) => [...old, ...r.data.lines].slice(-16))
        timer = setTimeout(tick, 1400)
      } catch {
        if (!live) return
        setOffline(true)
        timer = setTimeout(tick, 4000)
      }
    }
    tick()
    return () => { live = false; clearTimeout(timer) }
  }, [])
  return { pulse, offline, lines }
}

function Terminal({ lines, offline, clock }) {
  const box = useRef(null)
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight }, [lines])
  return (
    <div className="panel scan flex min-w-0 flex-col overflow-hidden">
      <div className="relative z-[1] flex items-center justify-between gap-2 border-b border-line px-3 py-2 font-mono text-[11px] text-muted">
        <span className="truncate">~/flowsense/junction-grid.log</span>
        <StatusDot tone={offline ? 'alert' : 'ok'} label={offline ? 'offline' : clock || 'live'} />
      </div>
      <div ref={box} role="log" aria-live="off" aria-label="Live junction events" tabIndex={0}
        className="relative z-[1] h-[148px] overflow-y-auto bg-bg/40 px-3 py-2 font-mono text-[11.5px] leading-[1.7]">
        {offline && <div className="text-alert">api unreachable - start the backend (run.bat) to see live events</div>}
        {lines.map((l, i) => (
          <div key={i} className="whitespace-nowrap" style={{ color: LINE_COLOR[l.kind] || 'var(--fg)' }}>{l.text}</div>
        ))}
        <div className="flex gap-2 text-ok"><span>$</span><span className="tw-caret" aria-hidden="true" /></div>
      </div>
    </div>
  )
}

function Counter({ label, value, suffix = '', format }) {
  return (
    <div className="min-w-0 border-l border-line-strong pl-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-dim">{label}</div>
      <div className="font-mono text-2xl font-semibold text-fg">
        {typeof value === 'number' ? <CountUp value={value} duration={0.6} format={format} /> : <span>-</span>}{suffix}
      </div>
    </div>
  )
}

export default function Landing() {
  useSmoothScroll()
  const { user } = useAuth()
  const { theme, toggle } = useTheme()
  const { pulse, offline, lines } = usePulse()
  const k = pulse?.kpis
  const h = pulse?.headline
  const cta = user ? '/app' : '/login'
  const ctaLabel = user ? 'Open control room' : 'Sign in to the control room'

  return (
    <div className="relative overflow-x-clip">
      <header className="sticky top-0 z-40 border-b border-line bg-bg/75 backdrop-blur-md">
        <div className="mx-auto flex h-14 w-full max-w-[1280px] items-center gap-3 px-4 sm:px-6">
          <Link to="/" aria-label="FlowSense home"><Logo /></Link>
          <nav aria-label="Sections" className="ml-6 hidden items-center gap-5 font-mono text-xs uppercase tracking-wider text-muted md:flex">
            <a href="#capabilities" className="hover:text-ok">Capabilities</a>
            <a href="#pipeline" className="hover:text-ok">Pipeline</a>
            <a href="#results" className="hover:text-ok">Results</a>
          </nav>
          <div className="flex-1" />
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
          <Link to={cta} className="inline-flex h-9 items-center gap-2 rounded-[6px] bg-ok px-3.5 text-sm font-medium text-on-ok hover:brightness-110">
            {user ? 'Open app' : 'Sign in'} <ArrowRight size={15} aria-hidden="true" />
          </Link>
        </div>
      </header>

      <section className="relative">
        <Backdrop className="absolute inset-x-0 top-0 h-[780px] fade-mask-bottom" />
        <div className="relative mx-auto grid w-full max-w-[1280px] gap-10 px-4 pb-20 pt-14 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:pt-24">
          <div className="min-w-0">
            <FadeIn>
              <div className="mb-4 inline-flex items-center gap-2 rounded-[4px] border border-ok/40 bg-ok/10 px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">
                <StatusDot tone="ok" blink /> camera to signal head
              </div>
            </FadeIn>
            <h1 className="font-mono text-4xl font-semibold leading-[1.08] tracking-tight text-fg sm:text-5xl lg:text-[56px]">
              <Typewriter text="Detect. Predict." speed={45} caret={false} />
              <span className="text-ok"><Typewriter text="Adapt. Coordinate." speed={45} delay={750} keepCaret /></span>
            </h1>
            <FadeIn delay={0.5}>
              <p className="mt-6 max-w-xl text-base leading-relaxed text-muted">
                FlowSense watches junction cameras, measures density on every approach lane, retimes the signals automatically and
                clears a path for emergency vehicles - across a whole grid, not one junction at a time.
              </p>
            </FadeIn>
            <FadeIn delay={0.7}>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <MagneticButton>
                  <Link to={cta} className="inline-flex h-11 items-center gap-2 rounded-[6px] bg-ok px-5 text-sm font-medium text-on-ok shadow-[0_0_0_1px_var(--ok),0_0_26px_-8px_var(--ok)] hover:brightness-110">
                    {ctaLabel} <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                </MagneticButton>
                <a href="#pipeline" className="inline-flex h-11 items-center gap-2 rounded-[6px] border border-line-strong px-5 text-sm text-fg hover:border-ok/60 hover:text-ok">How it works</a>
              </div>
            </FadeIn>
            <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-4" aria-label="Live preview counters">
              <Counter label="In network" value={k?.in_network} />
              <Counter label="Queued" value={k?.queued} />
              <Counter label="Avg delay" value={k?.avg_delay} suffix=" s" format={(v) => Math.round(v).toString()} />
              <Counter label="Completed" value={k?.throughput} />
            </div>
          </div>

          <FadeIn delay={0.35} className="min-w-0">
            <div className="space-y-3">
              <Card title="Live preview · advanced controller" action={<span className="font-mono text-[11px] text-dim">2 × 2 grid · {pulse?.clock || '--:--:--'}</span>}>
                <div className="rounded-[6px] bg-bg/60 p-2">
                  {pulse ? <TrafficMap map={pulse.map} compact label="Live preview of the junction grid" /> : (
                    <div className="grid h-[300px] place-items-center font-mono text-xs text-dim" aria-busy="true">{offline ? 'api unreachable - start the backend' : 'attaching to the simulator…'}</div>
                  )}
                </div>
              </Card>
              <Terminal lines={lines} offline={offline} clock={pulse?.clock} />
            </div>
          </FadeIn>
        </div>
      </section>

      <div className="border-y border-line bg-panel/60 py-3 font-mono text-xs uppercase tracking-[0.16em] text-muted">
        <Marquee duration={50}>
          {CHIPS.map((c) => <span key={c} className="mx-6 inline-flex items-center gap-2"><span className="h-1.5 w-1.5 bg-ok" aria-hidden="true" />{c}</span>)}
        </Marquee>
      </div>

      <section id="capabilities" className="mx-auto w-full max-w-[1280px] scroll-mt-16 px-4 py-20 sm:px-6">
        <Reveal>
          <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">capabilities</div>
          <h2 className="max-w-2xl font-mono text-2xl font-semibold tracking-tight sm:text-3xl">One pipeline instead of six separate tools</h2>
        </Reveal>
        <Reveal stagger={0.08} className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CAPS.map(({ icon: Icon, title, body }) => (
            <div key={title} className="panel scan p-5 transition-colors hover:border-ok/40">
              <div className="relative z-[1]">
                <div className="mb-3 grid h-9 w-9 place-items-center rounded-[6px] border border-line-strong text-ok"><Icon size={17} aria-hidden="true" /></div>
                <h3 className="font-mono text-sm font-semibold uppercase tracking-wider text-fg">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
              </div>
            </div>
          ))}
        </Reveal>
      </section>

      <section id="pipeline" className="scroll-mt-16 border-y border-line bg-panel/40">
        <div className="mx-auto w-full max-w-[1280px] px-4 py-20 sm:px-6">
          <Reveal>
            <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">pipeline</div>
            <h2 className="max-w-2xl font-mono text-2xl font-semibold tracking-tight sm:text-3xl">From a camera frame to the next green phase</h2>
          </Reveal>
          <Reveal stagger={0.08} className="mt-8 grid gap-3 md:grid-cols-5">
            {STEPS.map(([n, t, b]) => (
              <div key={n} className="rounded-[6px] border border-line bg-panel p-4">
                <div className="font-mono text-xs text-ok">{n}</div>
                <div className="mt-1 font-mono text-sm font-semibold text-fg">{t}</div>
                <p className="mt-1.5 text-xs leading-relaxed text-muted">{b}</p>
              </div>
            ))}
          </Reveal>
        </div>
      </section>

      <section id="results" className="mx-auto w-full max-w-[1280px] scroll-mt-16 px-4 py-20 sm:px-6">
        <Reveal>
          <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">results</div>
          <h2 className="max-w-2xl font-mono text-2xl font-semibold tracking-tight sm:text-3xl">Measured against fixed-time signals on the same traffic</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            A 15-minute morning-peak run on the 2 × 2 grid, computed by the simulator when the backend started - not a stored number.
          </p>
        </Reveal>
        <Reveal stagger={0.1} className="mt-8 grid gap-4 sm:grid-cols-3">
          {[
            ['Fixed-time avg delay', h?.fixed_delay, ' s', 'var(--dim)'],
            ['Advanced avg delay', h?.advanced_delay, ' s', 'var(--ok)'],
            ['Delay reduction', h?.cut_pct, '%', 'var(--cyan)'],
          ].map(([l, v, s, c]) => (
            <div key={l} className="panel scan p-5">
              <div className="relative z-[1]">
                <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted">{l}</div>
                <div className="mt-2 font-mono text-4xl font-semibold" style={{ color: c }}>
                  {typeof v === 'number' ? <CountUp value={v} format={(x) => (l.includes('reduction') ? Math.round(x) : x.toFixed(1))} /> : <span className="text-dim">…</span>}{typeof v === 'number' ? s : ''}
                </div>
              </div>
            </div>
          ))}
        </Reveal>
        {!h && <p className="mt-3 font-mono text-xs text-dim">{offline ? 'Start the backend to compute these numbers.' : 'Computing once the prediction model has trained…'}</p>}
      </section>

      <section className="border-t border-line">
        <div className="mx-auto flex w-full max-w-[1280px] flex-col items-start gap-5 px-4 py-16 sm:px-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="font-mono text-2xl font-semibold tracking-tight">Run the whole grid from one screen.</h2>
            <p className="mt-1.5 text-sm text-muted">Live control, benchmark, vision, prediction and violations - all on the same simulation.</p>
          </div>
          <Link to={cta} className="inline-flex h-11 items-center gap-2 rounded-[6px] bg-ok px-5 text-sm font-medium text-on-ok hover:brightness-110">
            {ctaLabel} <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </div>
        <div className="border-t border-line py-5 text-center font-mono text-[11px] text-dim">
          <Waypoints className="mr-1.5 inline" size={12} aria-hidden="true" />FlowSense · adaptive traffic control
        </div>
      </section>
    </div>
  )
}
