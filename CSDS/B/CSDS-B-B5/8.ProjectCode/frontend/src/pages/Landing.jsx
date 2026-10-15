import Lenis from 'lenis'
import { ArrowRight, Captions, Gauge, Hand, MessagesSquare, Moon, Sun, Volume2, WifiOff } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import Backdrop from '../components/reactbits/Backdrop'
import Logo from '../components/ui/Logo'
import Typewriter from '../components/ui/Typewriter'
import { Button, IconButton } from '../components/ui/controls'
import { Badge, Card, StatCard, StatusDot } from '../components/ui/display'
import { Skeleton } from '../components/ui/feedback'
import { label as pretty, pct } from '../format'
import { useAuth } from '../lib/auth'
import { useReducedMotion } from '../lib/reduced'
import { useTheme } from '../lib/theme'

const FEATURES = [
  { icon: Hand, title: 'Live sign recognition', text: '50 everyday ISL words plus fingerspelling A-Z and 1-9, with a confidence score for every sign.' },
  { icon: MessagesSquare, title: 'Signs become sentences', text: 'A pause closes the sentence. Rules work offline; when online, the wording is polished automatically.' },
  { icon: Volume2, title: 'Spoken aloud', text: 'Each sentence is read out with on-device text-to-speech so the hearing person just listens.' },
  { icon: Captions, title: 'Live subtitles', text: 'The hearing person speaks; large subtitles appear for the signer, recognised on this computer.' },
  { icon: WifiOff, title: 'Works offline', text: 'Camera, recognition, speech and subtitles all run locally, with FPS and latency always visible.' },
  { icon: Gauge, title: 'Measured', text: 'Accuracy, confusion matrices and latency are published on the performance page.' },
]

const PIPELINE = [
  ['$', 'signbridge start --offline', 'text-ok'],
  ['camera', 'webcam frame → MediaPipe hand landmarks', 'text-cyan'],
  ['model', 'ONNX word + letter classifiers on CPU', 'text-cyan'],
  ['gloss', 'recognised signs, each with a confidence', 'text-cyan'],
  ['nlp', 'grammar rules → sentence (Gemini polish when online)', 'text-info'],
  ['tts', 'sentence spoken aloud, offline', 'text-info'],
  ['stt', 'faster-whisper → live subtitles for the signer', 'text-warn'],
]

function useSmoothScroll() {
  const reduced = useReducedMotion()
  useEffect(() => {
    if (reduced) return
    const lenis = new Lenis({ lerp: 0.12 })
    let raf = requestAnimationFrame(function loop(t) { lenis.raf(t); raf = requestAnimationFrame(loop) })
    return () => { cancelAnimationFrame(raf); lenis.destroy() }
  }, [reduced])
}

export default function Landing() {
  const { user } = useAuth()
  const { theme, toggle } = useTheme()
  const [metrics, setMetrics] = useState(undefined) // undefined loading, null failed
  const [vocab, setVocab] = useState(null)
  useSmoothScroll()

  useEffect(() => {
    api.get('/metrics', { silent: true }).then((r) => setMetrics(r.data.evaluation || null)).catch(() => setMetrics(null))
    api.get('/vocab', { silent: true }).then((r) => setVocab(r.data)).catch(() => {})
  }, [])

  const go = user ? '/app' : '/register'
  return (
    <div className="relative min-h-screen overflow-x-clip">
      <Backdrop intensity={0.8} className="absolute inset-x-0 top-0 z-0 h-[88vh] fade-mask-bottom" />
      <a href="#features" className="sr-only z-50 rounded bg-ok px-3 py-2 text-on-ok focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>

      <header className="relative z-10 mx-auto flex h-16 w-full max-w-6xl items-center gap-2 px-4 sm:px-6">
        <Link to="/" aria-label="SignBridge home"><Logo /></Link>
        <div className="ml-auto flex items-center gap-2">
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
          {user ? <Link to="/app"><Button>Open SignBridge</Button></Link> : (
            <>
              <Link to="/login" className="hidden sm:block"><Button variant="secondary">Sign in</Button></Link>
              <Link to="/register"><Button>Create account</Button></Link>
            </>
          )}
        </div>
      </header>

      <main className="relative z-10">
        <section className="mx-auto grid w-full max-w-6xl items-center gap-10 px-4 pb-16 pt-12 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:pt-20">
          <div>
            <SlideUp><Badge tone="ok" dot>Indian Sign Language ⇄ speech</Badge></SlideUp>
            <h1 className="mt-5 font-mono text-4xl font-semibold leading-[1.1] tracking-tight text-fg sm:text-5xl">
              <Typewriter text="Sign. Speak." delay={200} />
              <span className="block text-ok"><Typewriter text="One screen." delay={800} keepCaret /></span>
            </h1>
            <SlideUp delay={0.3}>
              <p className="mt-6 max-w-xl text-lg text-muted">
                SignBridge turns ISL signs into text and speech, and turns the hearing person's voice into live subtitles — in real time, on an ordinary laptop, without needing the internet.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <MagneticButton><Link to={go}><Button size="lg" icon={ArrowRight}>Start a conversation</Button></Link></MagneticButton>
                {!user && <Link to="/login"><Button size="lg" variant="secondary">Try the demo account</Button></Link>}
              </div>
            </SlideUp>
          </div>

          <SlideUp delay={0.2}>
            <div className="panel scan overflow-hidden">
              <div className="relative z-[1] flex items-center justify-between border-b border-line px-3 py-2 font-mono text-[11px] text-muted">
                <span>~/signbridge/pipeline.txt</span><StatusDot tone="ok" />
              </div>
              <div className="relative z-[1] space-y-1.5 bg-bg/40 p-4 font-mono text-[12.5px] leading-relaxed">
                {PIPELINE.map(([tag, text, color], i) => (
                  <div key={tag} className="flex gap-3">
                    <span className={`w-14 shrink-0 ${color}`}>{tag === '$' ? '$' : `[${tag}]`}</span>
                    <span className="min-w-0 text-fg/90"><Typewriter text={text} speed={14} delay={900 + i * 650} caret={false} /></span>
                  </div>
                ))}
                <div className="flex gap-3 text-ok"><span className="w-14">$</span><span className="tw-caret" aria-hidden="true" /></div>
              </div>
            </div>
          </SlideUp>
        </section>

        <section className="mx-auto w-full max-w-6xl px-4 pb-16 sm:px-6" aria-label="Measured results">
          <div className="mb-3 font-mono text-[11px] uppercase tracking-[0.16em] text-dim">measured on held-out data · live from the API</div>
          {metrics === undefined && <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>}
          {metrics === null && <p className="font-mono text-xs text-dim">Results unavailable — start the backend (run.bat) to see the measured accuracy and latency.</p>}
          {metrics && (
            <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <StatCard label="Word accuracy" value={metrics.words.accuracy * 100} format={(v) => `${v.toFixed(1)}%`} sub={`${metrics.words.labels.length} signs · ${metrics.words.n_test} test takes`} />
              <StatCard label="Fingerspelling" value={metrics.letters.accuracy * 100} format={(v) => `${v.toFixed(1)}%`} tone="cyan" sub={`A-Z, 1-9 · ${metrics.letters.n_test} images`} />
              {metrics.continuous && <StatCard label="Continuous signing" value={metrics.continuous.sign_accuracy * 100} format={(v) => `${v.toFixed(1)}%`} tone="info" sub={`word error rate ${pct(metrics.continuous.word_error_rate)}`} />}
              {metrics.latency?.frame_total_ms && <StatCard label="Per-frame latency" value={metrics.latency.frame_total_ms.mean} format={(v) => `${v.toFixed(0)} ms`} tone="warn" sub={`~${metrics.latency.max_fps} FPS on CPU`} />}
            </Stagger>
          )}
        </section>

        {vocab && (
          <section className="border-y border-line bg-panel/60 py-4" aria-label="Vocabulary">
            <Marquee duration={60}>
              {vocab.words.map((w) => (
                <span key={w.gloss} className="mx-3 inline-flex items-center gap-2 whitespace-nowrap font-mono text-sm uppercase tracking-wider text-muted">
                  <span className="h-1 w-1 bg-ok" aria-hidden="true" />{pretty(w.gloss)}
                </span>
              ))}
            </Marquee>
          </section>
        )}

        <section id="features" className="mx-auto w-full max-w-6xl scroll-mt-4 px-4 py-20 sm:px-6">
          <Reveal>
            <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-ok">what it does</div>
            <h2 className="mt-2 font-mono text-2xl font-semibold tracking-tight text-fg sm:text-3xl">Both directions of a conversation</h2>
          </Reveal>
          <Reveal stagger={0.08} className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <Card key={title} bodyClass="p-5">
                <div className="mb-3 grid h-9 w-9 place-items-center rounded-[6px] border border-ok/40 bg-ok/10 text-ok"><Icon size={18} aria-hidden="true" /></div>
                <h3 className="font-mono text-sm font-semibold text-fg">{title}</h3>
                <p className="mt-1.5 text-sm text-muted">{text}</p>
              </Card>
            ))}
          </Reveal>
        </section>

        <section className="mx-auto w-full max-w-6xl px-4 pb-24 sm:px-6">
          <Reveal>
            <div className="panel scan flex flex-col items-start justify-between gap-5 p-6 sm:flex-row sm:items-center sm:p-8">
              <div className="relative z-[1]">
                <h2 className="font-mono text-xl font-semibold text-fg">Ready to talk?</h2>
                <p className="mt-1 text-sm text-muted">Demo login <span className="font-mono text-fg">demo@signbridge.app</span> / <span className="font-mono text-fg">demo1234</span> — or create your own account.</p>
              </div>
              <Link to={go} className="relative z-[1]"><Button size="lg" icon={ArrowRight}>{user ? 'Open SignBridge' : 'Get started'}</Button></Link>
            </div>
          </Reveal>
        </section>
      </main>

      <footer className="relative z-10 border-t border-line py-6 text-center font-mono text-[11px] text-dim">SignBridge · runs on your own computer</footer>
    </div>
  )
}
