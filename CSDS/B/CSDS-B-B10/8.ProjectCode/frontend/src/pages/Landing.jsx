import { ArrowRight, Gauge, Image as ImageIcon, Radio, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import Backdrop from '../components/reactbits/Backdrop'
import { FadeIn, Reveal, SlideUp, Stagger } from '../components/motion'
import { Button } from '../components/ui/controls'
import { StatCard, StatusDot } from '../components/ui/display'
import Logo from '../components/ui/Logo'
import Typewriter from '../components/ui/Typewriter'
import { useAuth } from '../lib/auth'

// Numbers from README "Evaluation results" (66 images, experiments/eval/metrics.json). Static, not live.
const EVIDENCE = [
  { label: 'Entropy, cipher', value: 7.9996, format: (v) => v.toFixed(4), sub: 'ideal 8' },
  { label: 'Correlation, adjacent', value: 0.0001, format: (v) => v.toFixed(4), sub: 'horizontal · ideal 0' },
  { label: 'NPCR, 1-pixel change', value: 99.61, format: (v) => `${v.toFixed(2)}%`, sub: 'ideal 99.61%' },
  { label: 'UACI, 1-pixel change', value: 33.46, format: (v) => `${v.toFixed(2)}%`, sub: 'ideal 33.46%' },
]

const FEATURES = [
  { icon: ImageIcon, title: 'Wavelet and chaos', body: 'Integer Haar wavelet, Henon-map permutation, logistic key streams and XOR diffusion with a key-dependent S-box. The key is 256 bits, with a public 128-bit nonce per image.' },
  { icon: ShieldCheck, title: 'Security lab', body: 'Entropy, chi-square, neighbour correlation, NPCR and UACI, key sensitivity, and attack tests on the cipher. Each report exports as HTML or JSON.' },
  { icon: Radio, title: 'Live UAV link', body: 'A sender streams encrypted drone frames over a WebSocket. The ground station decrypts with its own key and shows frame rate, latency and throughput.' },
  { icon: Gauge, title: 'Benchmark', body: 'Encryption and decryption time against AES-256-CTR and ChaCha20 on the same images, with the lossless check on every run.' },
]

export default function Landing() {
  const { user } = useAuth()
  const target = user ? '/studio' : '/login'

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Backdrop intensity={0.7} className="absolute inset-x-0 top-0 z-0 h-[95vh] fade-mask opacity-80" />

      <header className="relative z-10 mx-auto flex max-w-[1200px] items-center justify-between gap-4 px-4 py-5 sm:px-6">
        <Logo />
        <nav className="flex items-center gap-2" aria-label="Account">
          <Link to={target}><Button variant={user ? 'primary' : 'secondary'} size="sm">{user ? 'Open studio' : 'Sign in'}</Button></Link>
        </nav>
      </header>

      <section className="relative z-10 mx-auto max-w-[1200px] px-4 pb-16 pt-10 sm:px-6 sm:pt-16">
        <FadeIn>
          <div className="mb-4 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">
            <StatusDot tone="ok" ring /> SkyCipher · drone link encryption
          </div>
        </FadeIn>
        <h1 className="max-w-4xl font-mono text-3xl font-semibold leading-tight tracking-tight text-fg sm:text-5xl">
          <Typewriter text="Encrypt drone video before it leaves the aircraft." speed={22} />
        </h1>
        <SlideUp delay={0.15}>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
            Chaos-based image encryption built on a Haar wavelet transform and XOR diffusion. It is light enough for live
            transmission, and every decryption is checked bit for bit with SHA-256.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={target}>
              <Button size="lg" icon={ArrowRight}>{user ? 'Open the image studio' : 'Sign in to start'}</Button>
            </Link>
            <Link to="/live"><Button size="lg" variant="secondary" icon={Radio}>Live link</Button></Link>
          </div>
        </SlideUp>
      </section>

      <section className="relative z-10 mx-auto max-w-[1200px] px-4 pb-16 sm:px-6" aria-labelledby="evidence-title">
        <h2 id="evidence-title" className="mb-4 font-mono text-[11px] uppercase tracking-[0.16em] text-dim">
          Evaluation · 66 images · from the README
        </h2>
        <Reveal stagger={0.08} className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {EVIDENCE.map((e) => (
            <StatCard key={e.label} label={e.label} value={e.value} format={e.format} sub={e.sub} tone="ok" />
          ))}
        </Reveal>
        <p className="mt-3 font-mono text-[11px] text-dim">
          Decryption is bit-identical on all 66 images. Key space 2^256 plus a 128-bit nonce.
        </p>
      </section>

      <section className="relative z-10 mx-auto max-w-[1200px] px-4 pb-24 sm:px-6" aria-labelledby="features-title">
        <h2 id="features-title" className="mb-4 font-mono text-[11px] uppercase tracking-[0.16em] text-dim">What is in the app</h2>
        <Stagger className="grid gap-3 sm:grid-cols-2">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div key={title} className="panel scan h-full p-5">
              <div className="relative z-[1] flex items-center gap-2 font-mono text-sm text-fg">
                <Icon size={16} className="text-ok" aria-hidden="true" /> {title}
              </div>
              <p className="relative z-[1] mt-2 text-sm leading-relaxed text-muted">{body}</p>
            </div>
          ))}
        </Stagger>
      </section>

      <footer className="relative z-10 border-t border-line px-4 py-6 text-center font-mono text-[11px] text-dim sm:px-6">
        Sample images: VisDrone and USC-SIPI · demo account on the sign-in page
      </footer>
    </div>
  )
}
