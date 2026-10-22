import { Suspense, lazy, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Lenis from 'lenis'
import { ArrowRight, Check, FileLock2, Fingerprint, KeyRound, Lock, Moon, ScrollText, ShieldCheck, Sun, UsersRound, X } from 'lucide-react'
import { useTheme } from '../lib/theme'
import { useReducedMotion } from '../lib/motion'
import { useAuth } from '../lib/auth'
import { useAsync } from '../lib/useAsync'
import { api } from '../lib/api'
import { BrandMark, Badge, Button, IconButton } from '../components/ui'
import { CountUp, Marquee, MagneticButton, Parallax, Reveal, SlideUp, Stagger, ScrollTrigger, gsap } from '../components/motion'

const HeroVisual = lazy(() => import('../components/three/HeroVisual'))

const PRIMITIVES = ['AES-256-GCM', 'RSA-2048-OAEP', 'PBKDF2-HMAC-SHA-256', 'SHA-256 integrity', 'JWT sessions', 'bcrypt password hashes', 'Web Crypto API', 'Hash-chained audit log', 'Owner · Editor · Viewer', 'Ciphertext-only storage']

const STEPS = [
  {
    tag: 'AES-256-GCM',
    title: 'Encrypted before it leaves your browser',
    body: 'Each file gets its own random 256-bit key and a fresh 12-byte IV. The browser encrypts and hashes the file locally, so the server never sees plaintext.',
  },
  {
    tag: 'RSA-OAEP',
    title: 'The key is wrapped for you alone',
    body: 'The file key is sealed with your RSA-2048 public key. Your private key is itself encrypted with a PBKDF2-derived key from your password, so only you can open it.',
  },
  {
    tag: 'Ciphertext',
    title: 'The server stores only ciphertext',
    body: 'Storage holds encrypted bytes and wrapped keys. A leaked database or a curious admin sees nothing readable. Access is enforced server-side on every request.',
  },
  {
    tag: 'Re-wrap + verify',
    title: 'Share by re-wrapping, verify on download',
    body: 'Sharing re-wraps the file key for the recipient in your browser. On download, AES-GCM authentication and a SHA-256 check must both pass, or nothing is saved.',
  },
]

const FEATURES = [
  [FileLock2, 'Client-side encryption', 'AES-256-GCM in the Web Crypto API. Plaintext never touches the network.'],
  [KeyRound, 'Password-protected keys', 'Your RSA private key is wrapped with PBKDF2 (120,000 iterations) and unlocked only in memory.'],
  [UsersRound, 'Role-based sharing', 'Owner, Editor and Viewer roles, enforced by the backend. Revoke access any time.'],
  [Fingerprint, 'Integrity on every download', 'AES-GCM tag plus a stored SHA-256 digest. Tampered files are rejected, never saved.'],
  [ScrollText, 'Tamper-evident audit', 'Every sensitive action joins a hash chain. One click recomputes the chain and tells you if anything changed.'],
  [ShieldCheck, 'Honest by design', 'No recovery backdoor. Forget your password and the files stay sealed. That is the point.'],
]

const RBAC = [
  ['Read and download', true, true, true],
  ['Replace file content', true, true, false],
  ['Share and change roles', true, false, false],
  ['Revoke access', true, false, false],
  ['Delete file', true, false, false],
  ['View per-file audit history', true, false, false],
]

function Mark({ yes }) {
  return yes ? <Check size={17} className="yes" aria-label="Allowed" /> : <X size={17} className="no" aria-label="Not allowed" />
}

function HowItWorks() {
  const root = useRef(null)
  const [active, setActive] = useState(0)
  const reduced = useReducedMotion()

  useEffect(() => {
    const el = root.current
    if (!el) return undefined
    const ctx = gsap.context(() => {
      el.querySelectorAll('.how-step').forEach((step, i) => {
        ScrollTrigger.create({ trigger: step, start: 'top 55%', end: 'bottom 55%', onToggle: (self) => self.isActive && setActive(i) })
      })
      if (!reduced) {
        gsap.fromTo('.how-progress i', { scaleY: 0 }, { scaleY: 1, ease: 'none', scrollTrigger: { trigger: '.how-copy', start: 'top 60%', end: 'bottom 60%', scrub: true } })
      }
    }, el)
    return () => ctx.revert()
  }, [reduced])

  return (
    <section className="how" id="how" ref={root} aria-labelledby="how-h">
      <div className="l-wrap">
        <div className="section-head">
          <span className="eyebrow">How it works</span>
          <h2 id="how-h">Four steps between your file and anyone else.</h2>
        </div>
        <div className="how-grid">
          <div className="how-copy">
            <div className="how-progress" aria-hidden="true">
              <i style={reduced ? { transform: 'none' } : undefined} />
            </div>
            {STEPS.map((s, i) => (
              <div className="how-step" key={s.title}>
                <span className="how-num mono">STEP {String(i + 1).padStart(2, '0')}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
          <div className="how-visual-col">
            <div className="how-visual">
              <div className="card how-card">
                <div className="how-card-head">
                  <span className="viz-label" style={{ margin: 0 }}>
                    Live pipeline
                  </span>
                  <div className="dots" aria-hidden="true">
                    {STEPS.map((s, i) => (
                      <i key={s.tag} className={i === active ? 'on' : ''} />
                    ))}
                  </div>
                </div>
                <div className="crypto-flow" role="list">
                  {STEPS.map((s, i) => (
                    <div key={s.tag} role="listitem" className={`crypto-step${i === active ? ' active' : ''}`} aria-current={i === active ? 'step' : undefined}>
                      <span className="mono">{s.tag}</span>
                      <span>
                        <b>{['Your browser', 'Your browser', 'The server', 'Recipient browser'][i]}</b> · {['encrypt + hash', 'wrap the key', 'store ciphertext', 'unwrap, decrypt, verify'][i]}
                      </span>
                    </div>
                  ))}
                </div>
                <p className="viz-foot">The server is never on the trusted side of steps 1, 2 and 4.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default function Landing() {
  const { theme, toggle } = useTheme()
  const reduced = useReducedMotion()
  const { user } = useAuth()
  const { data: health } = useAsync(() => api.health(), [])
  const { data: cfg } = useAsync(() => api.config(), [])
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    document.title = 'CipherVault · Encrypted file storage'
  }, [])

  // Smooth scroll, kept in sync with GSAP ScrollTrigger. Skipped entirely for reduced motion.
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

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 20)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])

  const primary = user ? { to: '/app', label: 'Open my vault' } : { to: '/register', label: 'Create your vault' }

  return (
    <div className="landing">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className={`l-nav${scrolled ? ' scrolled' : ''}`}>
        <div className="l-wrap l-nav-inner">
          <Link to="/" className="brand">
            <BrandMark />
            <span>CipherVault</span>
          </Link>
          <nav className="l-nav-links" aria-label="Page sections">
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#roles">Access roles</a>
          </nav>
          <div className="landing-nav-actions">
            <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
            {!user && (
              <Link to="/login" className="btn btn-ghost hide-sm">
                Sign in
              </Link>
            )}
            <Link to={primary.to} className="btn btn-primary">
              {user ? primary.label : 'Get started'}
            </Link>
          </div>
        </div>
      </header>

      <main id="main">
        <section className="hero" aria-labelledby="hero-h">
          <div className="hero-layer hero-grid" aria-hidden="true" />
          <div className="hero-layer hero-orbs" aria-hidden="true">
            <span className="orb orb-a" />
            <span className="orb orb-b" />
          </div>
          <div className="hero-layer hero-visual">
            <Parallax speed={0.35}>
              <Suspense fallback={null}>
                <HeroVisual />
              </Suspense>
            </Parallax>
          </div>
          <div className="l-wrap hero-inner">
            <div className="hero-copy">
              <SlideUp>
                <span className="eyebrow">
                  <span className="pulse" aria-hidden="true" /> Zero-knowledge file storage
                </span>
              </SlideUp>
              <SlideUp delay={0.08}>
                <h1 id="hero-h">
                  Files sealed <span className="text-grad">before</span> they leave your browser.
                </h1>
              </SlideUp>
              <SlideUp delay={0.16}>
                <p className="hero-sub">
                  CipherVault encrypts every file on your device with AES-256-GCM and keeps the keys with you. Share with Owner, Editor and Viewer roles, and prove nothing was tampered with using a hash-chained audit log.
                </p>
              </SlideUp>
              <SlideUp delay={0.24}>
                <div className="hero-cta">
                  <MagneticButton>
                    <Link to={primary.to} className="btn btn-primary btn-lg">
                      {primary.label} <ArrowRight size={18} aria-hidden="true" />
                    </Link>
                  </MagneticButton>
                  {!user && (
                    <Link to="/login" className="btn btn-lg">
                      Try the demo
                    </Link>
                  )}
                </div>
              </SlideUp>
              <SlideUp delay={0.32}>
                <div className="hero-meta">
                  <span>
                    <Lock size={14} aria-hidden="true" /> Ciphertext-only server
                  </span>
                  <span>
                    <KeyRound size={14} aria-hidden="true" /> Keys never leave your device
                  </span>
                  {health ? (
                    <Badge tone="safe" dot>
                      API online
                    </Badge>
                  ) : (
                    <Badge dot>Checking API</Badge>
                  )}
                </div>
              </SlideUp>
            </div>
          </div>
          <div className="scroll-cue" aria-hidden="true">
            <span />
          </div>
        </section>

        <div className="signals" aria-label="Security primitives">
          <Marquee label="Cryptographic primitives used" speed={46}>
            {PRIMITIVES.map((p) => (
              <span className="signal" key={p}>
                {p}
              </span>
            ))}
          </Marquee>
        </div>

        <HowItWorks />

        <section className="l-section" id="features" aria-labelledby="feat-h">
          <div className="l-wrap">
            <Reveal className="section-head">
              <span className="eyebrow">Features</span>
              <h2 id="feat-h">Everything a private vault needs. Nothing it does not.</h2>
            </Reveal>
            <Stagger inView className="feature-cards">
              {FEATURES.map(([Icon, title, body]) => (
                <div className="card spot feature-card" key={title} onPointerMove={(e) => {
                  const r = e.currentTarget.getBoundingClientRect()
                  e.currentTarget.style.setProperty('--mx', `${e.clientX - r.left}px`)
                  e.currentTarget.style.setProperty('--my', `${e.clientY - r.top}px`)
                }}>
                  <span className="feature-icon">
                    <Icon size={20} aria-hidden="true" />
                  </span>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
              ))}
            </Stagger>
          </div>
        </section>

        <section className="numbers" aria-label="Key facts">
          <div className="l-wrap">
            <div className="numbers-grid">
              {[
                [256, 'AES-GCM key size, in bits', 'AES-GCM'],
                [2048, 'RSA key size, in bits', 'RSA-OAEP'],
                [120000, 'PBKDF2 iterations per password', 'password to key'],
                [12, 'random IV bytes per encryption', 'AES-GCM'],
                [cfg?.max_upload_mb ?? 25, 'MB upload limit (set by the server)', 'limit'],
              ].map(([n, label]) => (
                <div className="number" key={label}>
                  <strong>
                    <CountUp value={n} />
                  </strong>
                  <span>{label.trim()}</span>
                </div>
              ))}
            </div>
            <p className="numbers-note faint">These are the actual parameters used by this build, not marketing estimates.</p>
          </div>
        </section>

        <section className="l-section" id="roles" aria-labelledby="roles-h">
          <div className="l-wrap">
            <Reveal className="section-head">
              <span className="eyebrow">Access control</span>
              <h2 id="roles-h">Three roles. Enforced on the server.</h2>
            </Reveal>
            <Reveal>
              <div className="card" style={{ overflowX: 'auto' }}>
                <table className="rbac-table">
                  <thead>
                    <tr>
                      <th scope="col">Capability</th>
                      <th scope="col">Owner</th>
                      <th scope="col">Editor</th>
                      <th scope="col">Viewer</th>
                    </tr>
                  </thead>
                  <tbody>
                    {RBAC.map(([cap, ...cols]) => (
                      <tr key={cap}>
                        <td>{cap}</td>
                        {cols.map((c, i) => (
                          <td key={i}>
                            <Mark yes={c} />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Reveal>
          </div>
        </section>

        <section className="l-section" style={{ paddingTop: 0 }} aria-labelledby="cta-h">
          <div className="l-wrap">
            <Reveal>
              <div className="card cta-card">
                <span className="cta-glow" aria-hidden="true" />
                <h2 id="cta-h">Seal your first file in under a minute.</h2>
                <p>Create an account, upload a file, and watch the ciphertext land on the server. Or open the demo with synthetic data.</p>
                <div className="hero-cta" style={{ justifyContent: 'center' }}>
                  <Link to={primary.to} className="btn btn-primary btn-lg">
                    {primary.label}
                  </Link>
                  {!user && (
                    <Link to="/login" className="btn btn-lg">
                      Try the demo
                    </Link>
                  )}
                </div>
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="l-footer">
        <div className="l-wrap">
          <div className="l-footer-inner">
            <div>
              <Link to="/" className="brand" style={{ padding: 0 }}>
                <BrandMark />
                <span>CipherVault</span>
              </Link>
              <p className="faint" style={{ marginTop: 12, maxWidth: 360 }}>
                Secure file storage with client-side encryption and role-based access control.
              </p>
            </div>
            <nav className="l-footer-links" aria-label="Footer">
              <a href="#how">How it works</a>
              <Link to="/login">Sign in</Link>
              <a href="#features">Features</a>
              <Link to="/register">Create account</Link>
              <a href="#roles">Access roles</a>
              <a href="/docs">API docs</a>
            </nav>
          </div>
          <div className="l-footer-base faint">Endpoint security still matters: a compromised browser can read what you open. CipherVault protects data at rest and in transit to the server.</div>
        </div>
      </footer>
    </div>
  )
}
