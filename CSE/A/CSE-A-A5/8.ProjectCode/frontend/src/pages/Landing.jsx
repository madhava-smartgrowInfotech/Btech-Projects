import { ArrowRight, BarChart3, Bell, BookOpen, Lock, Moon, Radar, Sun, TerminalSquare } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { CountUp, MagneticButton, Marquee, Reveal } from '../components/motion'
import { Container } from '../components/ui/AppShell'
import { StatusDot } from '../components/ui/display'
import Logo from '../components/ui/Logo'
import Typewriter from '../components/ui/Typewriter'
import Backdrop from '../components/three/LazyBackdrop'
import { clock } from '../format'
import { useTheme } from '../lib/theme'
import useHealth from '../lib/useHealth'

const TECH = ['AES-256-GCM', 'ECDH P-256', 'HKDF-SHA256', 'XGBoost', '1D CNN', 'Logistic stacking', 'UNSW-NB15', 'FastAPI', 'PyTorch']

const STEPS = [
  { n: '01', title: 'ECDH P-256 handshake', body: 'Every message gets a fresh ephemeral key pair, agreed against the cloud public key. Nothing is reused.' },
  { n: '02', title: 'HKDF-SHA256 key', body: 'The shared secret is stretched into a 256-bit session key that exists for one transfer only.' },
  { n: '03', title: 'AES-256-GCM seal', body: 'A 12-byte random nonce and a 16-byte tag. Change one bit in transit and decryption is rejected.' },
  { n: '04', title: 'ThreatSense verdict', body: 'XGBoost and a 1D CNN score each flow; logistic regression stacks them into one attack probability.' },
]

const FEATURES = [
  { to: '/app', icon: Radar, title: 'Live scoring', body: 'Score one flow or a 10,000-row CSV and watch verdicts, confidence and severity stream in.' },
  { to: '/app/secure', icon: Lock, title: 'Secure transfer', body: 'Encrypt text or files, inspect ciphertext, nonce and tag, then verify or tamper at the mock cloud.' },
  { to: '/app/alerts', icon: Bell, title: 'Alerts', body: 'Every detected intrusion, filterable by severity, with per-model scores.' },
  { to: '/app/performance', icon: BarChart3, title: 'Model performance', body: 'Accuracy, precision, recall, F1, ROC-AUC and the confusion matrix from the held-out test set.' },
]

// Runs three real GET requests and prints what came back, like a terminal session.
function LiveTerminal() {
  const [lines, setLines] = useState([])
  useEffect(() => {
    let live = true
    const acc = [] // local to this run, so a StrictMode re-mount replaces the lines instead of duplicating them
    const add = (l) => { acc.push({ ...l, t: Date.now() }); if (live) setLines([...acc]) }
    ;(async () => {
      for (const [path, fmt] of [
        ['/health', (d) => `status=${d.status} engine_loaded=${d.engine_loaded} version=${d.version}`],
        ['/metrics', (d) => `accuracy=${d.accuracy.toFixed(4)} f1=${d.f1.toFixed(4)} roc_auc=${d.roc_auc.toFixed(4)} test_rows=${d.splits.test}`],
        ['/alerts', (d) => `alerts_logged=${d.total}`],
      ]) {
        add({ cmd: `GET /api${path}` })
        try {
          const r = await api.get(path, { silent: true })
          add({ out: fmt(r.data), tone: 'ok' })
        } catch (e) {
          add({ out: e.response ? `HTTP ${e.response.status}: ${e.response.data?.detail ?? 'error'}` : 'no response - is the backend running on :8305?', tone: 'alert' })
        }
      }
    })()
    return () => { live = false }
  }, [])
  return (
    <div className="panel scan overflow-hidden" aria-label="Live API terminal">
      <div className="relative z-[1] flex items-center gap-2 border-b border-line px-3 py-2 font-mono text-[11px] text-muted">
        <TerminalSquare size={14} className="text-ok" aria-hidden="true" /><span>~/cipherguard/live-api.log</span><StatusDot tone="ok" />
      </div>
      <div role="log" aria-live="polite" className="relative z-[1] min-h-[168px] space-y-1 bg-bg/40 p-4 font-mono text-[12px] leading-relaxed">
        {lines.map((l, i) => (
          l.cmd
            ? <div key={i} className="text-fg"><span className="text-dim">{clock(l.t)} </span><span className="text-ok">$</span> {l.cmd}</div>
            : <div key={i} className="break-words pl-4" style={{ color: `var(--${l.tone})` }}>{l.out}</div>
        ))}
        <div className="flex gap-2 text-ok"><span>$</span><span className="tw-caret" aria-hidden="true" /></div>
      </div>
    </div>
  )
}

function Counter({ label, children, tone = 'ok' }) {
  return (
    <div className="panel scan p-4">
      <div className="relative z-[1] font-mono text-[10px] uppercase tracking-[0.14em] text-muted">{label}</div>
      <div className="relative z-[1] mt-1 font-mono text-2xl font-semibold tracking-tight sm:text-[28px]" style={{ color: `var(--${tone})` }}>{children}</div>
    </div>
  )
}

export default function Landing() {
  const { theme, toggle } = useTheme()
  const { state, info } = useHealth(15000)
  const [m, setM] = useState(null)
  useEffect(() => {
    let live = true
    api.get('/metrics', { silent: true }).then((r) => live && setM(r.data)).catch(() => live && setM(null))
    return () => { live = false }
  }, [])

  const engine = { ok: ['engine ready', 'ok'], loading: ['engine idle', 'warn'], down: ['api offline', 'alert'] }[state] || ['checking...', 'warn']

  return (
    <div className="relative min-h-screen overflow-x-clip">
      <a href="#content" className="sr-only z-50 rounded bg-ok px-3 py-2 text-on-ok focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
      <header className="absolute inset-x-0 top-0 z-20">
        <Container className="flex h-16 items-center justify-between">
          <Link to="/" aria-label="CipherGuard Shield home"><Logo /></Link>
          <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-3">
            <a href="/docs" target="_blank" rel="noreferrer" className="hidden items-center gap-1.5 px-2 py-1.5 font-mono text-xs text-muted hover:text-fg sm:inline-flex"><BookOpen size={14} aria-hidden="true" />API docs</a>
            <button type="button" onClick={toggle} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              className="grid h-9 w-9 place-items-center rounded-[6px] text-muted hover:bg-panel-2 hover:text-fg">
              {theme === 'dark' ? <Sun size={17} aria-hidden="true" /> : <Moon size={17} aria-hidden="true" />}
            </button>
            <Link to="/app" className="inline-flex h-9 items-center gap-2 rounded-[6px] border border-line-strong bg-panel-2 px-3 font-mono text-xs text-fg hover:border-ok/60 hover:text-ok">Open console<ArrowRight size={14} aria-hidden="true" /></Link>
          </nav>
        </Container>
      </header>

      <main id="content">
        <section className="relative isolate overflow-hidden pb-16 pt-28 sm:pt-36">
          <Backdrop intensity={1} className="absolute inset-x-0 top-0 -z-10 h-full" />
          <Container>
            <div className="mb-5 inline-flex items-center gap-2 rounded-[6px] border border-line-strong bg-panel/80 px-2.5 py-1 font-mono text-[11px] text-muted backdrop-blur">
              <StatusDot tone={engine[1]} ring={state === 'ok'} /><span className="uppercase tracking-[0.14em]">{engine[0]}</span>
              {info && <span className="text-dim">v{info.version}</span>}
            </div>
            <Typewriter as="h1" text="Encrypt every byte. Flag every intrusion." speed={34} keepCaret
              className="max-w-4xl font-mono text-3xl font-semibold leading-[1.1] tracking-tight text-fg sm:text-5xl lg:text-6xl" />
            <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
              CipherGuard Shield seals data with ECDH P-256, HKDF-SHA256 and AES-256-GCM before it reaches the cloud, and watches the traffic with an
              XGBoost + 1D CNN intrusion detector - one console for both.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <MagneticButton>
                <Link to="/app" className="inline-flex h-11 items-center gap-2 rounded-[6px] bg-ok px-5 text-sm font-medium text-on-ok shadow-[0_0_0_1px_var(--ok),0_0_22px_-8px_var(--ok)] hover:brightness-110">
                  Open the console<ArrowRight size={16} aria-hidden="true" />
                </Link>
              </MagneticButton>
              <MagneticButton>
                <Link to="/app/secure" className="inline-flex h-11 items-center gap-2 rounded-[6px] border border-line-strong bg-panel-2 px-5 text-sm font-medium text-fg hover:border-ok/60 hover:text-ok">
                  <Lock size={16} aria-hidden="true" />Try secure transfer
                </Link>
              </MagneticButton>
            </div>

            <div className="mt-12 grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Counter label="Test accuracy" tone="ok">{m ? <CountUp value={m.accuracy * 100} format={(v) => `${v.toFixed(2)}%`} /> : '-'}</Counter>
              <Counter label="ROC-AUC" tone="cyan">{m ? <CountUp value={m.roc_auc} format={(v) => v.toFixed(4)} /> : '-'}</Counter>
              <Counter label="Held-out test flows" tone="info">{m ? <CountUp value={m.splits.test} /> : '-'}</Counter>
              <Counter label="Input features" tone="warn">{m ? <CountUp value={m.input_dim} /> : '-'}</Counter>
            </div>
            {!m && state === 'down' && <p className="mt-3 font-mono text-xs text-alert">Live numbers need the backend - start it with run.bat.</p>}
          </Container>
        </section>

        <section aria-labelledby="how" className="py-14">
          <Container>
            <h2 id="how" className="mb-8 font-mono text-xs uppercase tracking-[0.16em] text-ok">// how a transfer is protected</h2>
            <Reveal stagger={0.1} className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              {STEPS.map((s) => (
                <div key={s.n} className="panel scan p-5">
                  <div className="relative z-[1]">
                    <div className="font-mono text-3xl font-semibold text-ok/70">{s.n}</div>
                    <h3 className="mt-3 font-mono text-sm font-semibold text-fg">{s.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
                  </div>
                </div>
              ))}
            </Reveal>
          </Container>
        </section>

        <section aria-label="Technology" className="border-y border-line bg-panel/50 py-4">
          <Marquee duration={36}>
            {TECH.map((t) => <span key={t} className="mx-6 font-mono text-sm uppercase tracking-[0.16em] text-dim">{t}<span className="ml-12 text-ok" aria-hidden="true">/</span></span>)}
          </Marquee>
        </section>

        <section aria-labelledby="live" className="py-14">
          <Container className="grid grid-cols-1 items-start gap-8 lg:grid-cols-2">
            <Reveal>
              <h2 id="live" className="mb-3 font-mono text-xs uppercase tracking-[0.16em] text-ok">// talking to the real API</h2>
              <p className="max-w-md text-sm leading-relaxed text-muted">
                This is not a mock-up. The console on the right is the actual response of the FastAPI backend as this page loaded: health, held-out metrics and the alert count.
              </p>
            </Reveal>
            <Reveal><LiveTerminal /></Reveal>
          </Container>
        </section>

        <section aria-labelledby="screens" className="pb-20">
          <Container>
            <h2 id="screens" className="mb-8 font-mono text-xs uppercase tracking-[0.16em] text-ok">// what is inside</h2>
            <Reveal stagger={0.08} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map(({ to, icon: Icon, title, body }) => (
                <Link key={to} to={to} className="panel scan group block p-5 transition-colors hover:border-ok/50">
                  <div className="relative z-[1]">
                    <Icon size={20} className="text-ok" aria-hidden="true" />
                    <h3 className="mt-4 flex items-center gap-2 font-mono text-sm font-semibold text-fg">{title}<ArrowRight size={14} className="text-dim transition-transform group-hover:translate-x-1 group-hover:text-ok" aria-hidden="true" /></h3>
                    <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
                  </div>
                </Link>
              ))}
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="border-t border-line py-6">
        <Container className="flex flex-wrap items-center justify-between gap-3 font-mono text-[11px] text-dim">
          <span>CipherGuard Shield - SecureChannel + ThreatSense Engine</span>
          <span>{m ? m.data_mode : 'UNSW-NB15 schema'}</span>
        </Container>
      </footer>
    </div>
  )
}
