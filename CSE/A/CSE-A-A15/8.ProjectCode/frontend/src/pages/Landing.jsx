import { useNavigate } from 'react-router-dom'
import { EyeOff, FileLock2, ImageIcon, KeyRound, ShieldCheck } from 'lucide-react'
import { getToken } from '../api'
import Backdrop from '../components/reactbits/Backdrop'
import Logo from '../components/ui/Logo'
import Typewriter from '../components/ui/Typewriter'
import { Button } from '../components/ui/controls'
import { Card, StatusDot } from '../components/ui/display'
import { CountUp, MagneticButton, Marquee, Reveal, Stagger } from '../components/motion'

// Figures are the measured results in README.md (ml/eval.py: 6 covers, RSA-3072, 22 round trips).
const FACTS = [
  { value: 22, format: (v) => `${Math.round(v)}`, label: 'round trips byte-exact', sub: 'of 22 run, oversized ones blocked' },
  { value: 61.7, format: (v) => v.toFixed(1), label: 'mean PSNR, dB', sub: 'minimum 52.5 dB' },
  { value: 0.999, format: (v) => v.toFixed(4), label: 'mean SSIM', sub: 'minimum 0.9958' },
  { value: 3.0, format: (v) => v.toFixed(1), label: 'bits per pixel', sub: '14.6 KiB to 337.5 KiB per cover' },
  { value: 86, format: (v) => `${Math.round(v)} ms`, label: 'median unwrap + decrypt', sub: 'RSA-3072 key' },
]

const STEPS = [
  [FileLock2, '01 · Encrypt', 'AES-256-GCM seals the file with a fresh session key for every message. Any tampering is detected.'],
  [KeyRound, '02 · Wrap', "The session key is locked with the receiver's RSA public key (OAEP). Only their private key can open it."],
  [ImageIcon, '03 · Hide', 'The sealed bundle is written into the lowest bits of an ordinary-looking PNG. Nothing looks unusual.'],
]

const TERMS = ['AES-256-GCM', 'RSA-OAEP', 'LSB steganography', 'PNG only', 'PSNR · SSIM', 'byte-exact restore']

export default function Landing() {
  const nav = useNavigate()
  const signedIn = !!getToken()

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Backdrop intensity={0.6} className="fixed inset-x-0 top-0 z-0 h-[80vh] fade-mask-bottom opacity-80" />

      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
        <Logo />
        <Button variant="secondary" size="sm" onClick={() => nav(signedIn ? '/send' : '/login')}>
          {signedIn ? 'Open app' : 'Sign in'}
        </Button>
      </header>

      <section className="relative z-10 mx-auto max-w-6xl px-4 pb-16 pt-10 sm:px-6 sm:pt-16">
        <div className="mb-4 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">
          <StatusDot tone="ok" /> hybrid encryption · steganography
        </div>
        <Typewriter as="h1" text="Two layers of protection. One ordinary-looking image."
          className="max-w-3xl font-mono text-3xl font-semibold leading-tight tracking-tight text-fg sm:text-5xl" />
        <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted">
          Encryption tells an eavesdropper that something secret is moving. Hiding alone protects nothing once it is found.
          CipherVeil does both: the file is encrypted, then hidden where nobody thinks to look.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <MagneticButton>
            <Button size="lg" icon={ShieldCheck} onClick={() => nav(signedIn ? '/send' : '/login')}>
              {signedIn ? 'Open the app' : 'Get started'}
            </Button>
          </MagneticButton>
          <a href="#how" className="inline-flex h-11 items-center rounded-[6px] border border-line-strong px-5 text-sm text-fg hover:border-ok/60 hover:text-ok">
            How it works
          </a>
        </div>
      </section>

      <div className="relative z-10 border-y border-line bg-panel/60 py-3 backdrop-blur-sm">
        <Marquee duration={36} className="font-mono text-xs uppercase tracking-[0.14em] text-muted">
          {TERMS.map((t) => <span key={t} className="mx-6 whitespace-nowrap">{t} <span className="text-ok">/</span></span>)}
        </Marquee>
      </div>

      <section aria-labelledby="facts" className="relative z-10 mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <h2 id="facts" className="mb-2 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">Measured results</h2>
        <p className="mb-6 max-w-2xl text-sm text-muted">From the evaluation in this repository, not from marketing.</p>
        <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          {FACTS.map((f) => (
            <div key={f.label} className="panel scan p-4">
              <div className="font-mono text-2xl font-semibold tracking-tight text-fg sm:text-[28px]">
                <CountUp value={f.value} format={f.format} />
              </div>
              <div className="mt-1 text-sm text-fg">{f.label}</div>
              <div className="mt-1 font-mono text-[11px] text-dim">{f.sub}</div>
            </div>
          ))}
        </Stagger>
      </section>

      <section id="how" aria-labelledby="how-title" className="relative z-10 mx-auto max-w-6xl px-4 pb-14 sm:px-6">
        <h2 id="how-title" className="mb-6 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">How it works</h2>
        <Reveal stagger={0.12} className="grid gap-4 md:grid-cols-3">
          {STEPS.map(([Icon, title, text]) => (
            <Card key={title} title={title} bodyClass="space-y-3 p-5">
              <Icon className="h-5 w-5 text-ok" aria-hidden="true" />
              <p className="text-sm leading-relaxed text-muted">{text}</p>
            </Card>
          ))}
        </Reveal>
      </section>

      <section aria-labelledby="honest" className="relative z-10 mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <Reveal>
          <Card title="Measured, not promised" bodyClass="space-y-3 p-5">
            <div className="flex items-start gap-3">
              <EyeOff className="mt-0.5 h-5 w-5 shrink-0 text-ok" aria-hidden="true" />
              <p className="text-sm leading-relaxed text-muted">
                Every message reports PSNR and SSIM against the original cover, histograms and bit planes before and after, how much of the image was used, and timings.
                The robustness test is blunt: lossless handling keeps the payload, while JPEG recompression, noise or resizing destroys it.
                <b className="text-fg"> Send the result as a PNG.</b>
              </p>
            </div>
          </Card>
        </Reveal>
      </section>
    </div>
  )
}
