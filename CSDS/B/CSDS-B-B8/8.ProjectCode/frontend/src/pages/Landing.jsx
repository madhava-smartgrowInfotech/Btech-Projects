import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion, useScroll, useSpring } from 'framer-motion'
import Lenis from 'lenis'
import { ArrowRight, Bell, CalendarDays, Camera, EyeOff, Moon, PersonStanding, ScanLine, ShieldAlert, Sun } from 'lucide-react'
import { BrandMark, Button, Card, IconButton } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import HeroVisual from '../components/three/HeroVisual'
import { useAuth } from '../lib/auth'
import { useTheme } from '../lib/theme'
import { useReducedMotion } from '../lib/motion'

const FEATURES = [
  { icon: PersonStanding, title: 'Activity recognition', text: 'Walking, standing, sitting, lying, drinking water and picking things up - recognised live from body keypoints.' },
  { icon: ShieldAlert, title: 'Real-time fall detection', text: 'A rapid drop to the floor followed by stillness is confirmed over a 3 second window before anyone is disturbed.' },
  { icon: Bell, title: 'Instant alerts', text: "An on-screen 'I'm OK' countdown, then Telegram with a snapshot and an email to family." },
  { icon: EyeOff, title: 'Privacy first', text: 'The live view shows only a skeleton. No video is stored - a snapshot is kept only with an alert.' },
  { icon: Moon, title: 'Works in dim rooms', text: 'Automatic gamma and CLAHE enhancement keeps recognition going when the lights are low.' },
  { icon: CalendarDays, title: 'Daily report', text: 'Time spent per activity and long-inactivity warnings, day by day.' },
]

const ACTIVITIES = ['Walking', 'Standing', 'Sitting', 'Lying', 'Drinking water', 'Picking up objects', 'Fall detection', 'Low-light enhancement', 'Privacy mode', 'Telegram alerts', 'Email alerts', 'Daily report']

// Figures come from experiments/eval/metrics.json (held-out evaluation, see README).
const NUMBERS = [
  { value: 17, format: (v) => Math.round(v), label: 'body keypoints per frame (YOLO11n-pose)' },
  { value: 86.3, format: (v) => `${v.toFixed(1)}%`, label: 'activity accuracy, normal light' },
  { value: 92.3, format: (v) => `${v.toFixed(1)}%`, label: 'specificity - non-falls ignored' },
  { value: 65.4, format: (v) => `${v.toFixed(1)}%`, label: 'sensitivity - simulated falls caught' },
  { value: 24.2, format: (v) => `${v.toFixed(1)} s`, label: 'impact to alert sent, incl. 20 s countdown' },
]

const STEPS = [
  { n: '01', title: 'Point any camera at the room', text: 'A webcam, or an old Android phone running IP Webcam. Frames are processed on your own computer on the CPU - nothing is uploaded.' },
  { n: '02', title: 'Find the body, not the face', text: 'YOLO11n-pose locates 17 keypoints per frame in about 30 ms. In privacy mode the screen shows only that skeleton.' },
  { n: '03', title: 'Recognise activity, catch the fall', text: 'A random forest classifies 20-frame windows into six activities, while a separate rule watches for a rapid drop followed by stillness.' },
  { n: '04', title: 'Ask first, then alert', text: "A red 'I'm OK' countdown appears on every screen. If nobody cancels it, Telegram and email go out to family with a snapshot." },
]

const BARS = [
  ['Walking', 98.0], ['Picking up objects', 100], ['Standing', 90.4], ['Lying', 81.2], ['Drinking water', 76.8], ['Sitting', 71.2],
]

function PoseFigure() {
  return (
    <svg viewBox="0 0 220 260" role="img" aria-label="Skeleton drawn from 17 body keypoints" fill="none">
      <g stroke="var(--accent)" strokeWidth="3.5" strokeLinecap="round">
        <path d="M110 70v70M110 84l-42 26-6 44M110 84l42 26 6 44M110 140l-30 52-8 52M110 140l30 52 8 52" />
      </g>
      <circle cx="110" cy="44" r="22" stroke="var(--accent-2)" strokeWidth="3.5" />
      {[[110, 44], [110, 84], [68, 110], [62, 154], [152, 110], [158, 154], [110, 140], [80, 192], [72, 244], [140, 192], [148, 244]].map(([x, y]) => (
        <circle key={`${x}-${y}`} cx={x} cy={y} r="5" fill="var(--text)" />
      ))}
    </svg>
  )
}

function StepVisual({ step }) {
  if (step === 0) {
    return (
      <>
        <div className="viz-label">Camera sources</div>
        <ul className="anatomy-list">
          <li><span className="anatomy-tag">0</span> This computer&apos;s webcam</li>
          <li><span className="anatomy-tag">http://…/video</span> A phone running IP Webcam</li>
          <li><span className="anatomy-tag">video file</span> A recorded clip for demos</li>
        </ul>
        <div className="viz-foot">Nothing leaves your machine except alerts you chose to send.</div>
      </>
    )
  }
  if (step === 1) {
    return (
      <>
        <div className="viz-label">17 keypoints</div>
        <div className="step-pose"><PoseFigure /></div>
        <div className="viz-foot">Privacy mode draws this and nothing else.</div>
      </>
    )
  }
  if (step === 2) {
    return (
      <>
        <div className="viz-label">Accuracy per activity (normal light)</div>
        <div className="viz-bars">
          {BARS.map(([name, v], i) => (
            <div className={`viz-bar${i === 0 ? ' best' : ''}`} key={name}>
              <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'nowrap' }}>
                <span>{name}</span>
                <strong>{v.toFixed(1)}%</strong>
              </div>
              <div className="viz-track"><i style={{ width: `${v}%` }} /></div>
            </div>
          ))}
        </div>
        <div className="viz-foot">Held-out images, seeded motion windows. Sitting is the weakest activity.</div>
      </>
    )
  }
  return (
    <>
      <div className="viz-label">Possible fall detected</div>
      <div className="mini-fall">
        <div className="mini-count" aria-hidden="true">20</div>
        <div className="viz-stats">
          <div><strong>Telegram</strong><span>with snapshot</span></div>
          <div><strong>Email</strong><span>Gmail SMTP</span></div>
          <div><strong>I&apos;m OK</strong><span>cancels it</span></div>
        </div>
      </div>
      <div className="viz-foot">Countdown is configurable from 5 to 300 seconds.</div>
    </>
  )
}

function HowItWorks() {
  const copy = useRef(null)
  const [active, setActive] = useState(0)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: copy, offset: ['start 70%', 'end 70%'] })
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 28 })

  useEffect(() => {
    const nodes = copy.current?.querySelectorAll('[data-step]') || []
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(Number(e.target.dataset.step))),
      { rootMargin: '-45% 0px -45% 0px' },
    )
    nodes.forEach((n) => io.observe(n))
    return () => io.disconnect()
  }, [])

  return (
    <section className="how" id="how" aria-labelledby="how-title">
      <div className="l-wrap">
        <div className="section-head">
          <span className="eyebrow">How it works</span>
          <h2 id="how-title">From a camera frame to a message in family&apos;s pocket</h2>
        </div>
        <div className="how-grid">
          <div className="how-copy" ref={copy}>
            <div className="how-progress" aria-hidden="true">
              <motion.i style={{ scaleY: reduced ? 1 : progress }} />
            </div>
            {STEPS.map((s, i) => (
              <div className="how-step" data-step={i} key={s.n}>
                <span className="how-num mono">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
                <Card className="how-card inline how-inline" spotlight={false}>
                  <StepVisual step={i} />
                </Card>
              </div>
            ))}
          </div>
          <div className="how-visual-col">
            <div className="how-visual">
              <Card className="how-card" spotlight={false}>
                <div className="how-card-head">
                  <span className="faint mono">step {STEPS[active].n}</span>
                  <div className="dots" aria-hidden="true">
                    {STEPS.map((s, i) => <i key={s.n} className={i === active ? 'on' : ''} />)}
                  </div>
                </div>
                <AnimatePresence mode="wait" initial={false}>
                  <motion.div key={active} initial={{ opacity: 0, y: reduced ? 0 : 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: reduced ? 0 : -10 }} transition={{ duration: 0.28 }}>
                    <StepVisual step={active} />
                  </motion.div>
                </AnimatePresence>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default function Landing() {
  const { user } = useAuth()
  const { theme, toggle } = useTheme()
  const reduced = useReducedMotion()
  const [scrolled, setScrolled] = useState(false)
  const target = user ? '/app/monitor' : '/login'

  useEffect(() => {
    document.title = 'CareWatch · Fall detection and emergency alerts'
    const on = () => setScrolled(window.scrollY > 12)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])

  // smooth scrolling, off for people who prefer reduced motion
  useEffect(() => {
    if (reduced) return undefined
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
  }, [reduced])

  return (
    <div className="landing">
      <a href="#top" className="skip-link">Skip to content</a>
      <header className={`l-nav${scrolled ? ' scrolled' : ''}`}>
        <div className="l-wrap l-nav-inner">
          <Link to="/" className="brand" aria-label="CareWatch home">
            <BrandMark />
            <span>CareWatch</span>
          </Link>
          <nav className="l-nav-links" aria-label="Page sections">
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#numbers">Results</a>
          </nav>
          <div className="row nav-actions">
            <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
            <Button as={Link} to={target} variant="primary" size="sm">{user ? 'Open monitor' : 'Sign in'}</Button>
          </div>
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-layer hero-grid" aria-hidden="true" />
          <div className="hero-layer hero-orbs" aria-hidden="true"><span className="orb orb-a" /><span className="orb orb-b" /></div>
          <div className="hero-layer hero-visual"><HeroVisual /></div>
          <div className="l-wrap hero-inner">
            <div className="hero-copy">
              <SlideUp><span className="eyebrow"><span className="pulse" aria-hidden="true" /> Privacy-first home monitoring</span></SlideUp>
              <SlideUp delay={0.08}><h1>Peace of mind for people who <span className="text-grad">live alone</span></h1></SlideUp>
              <SlideUp delay={0.16}>
                <p className="hero-sub">
                  CareWatch turns a webcam or an old phone into a privacy-first carer. It recognises daily activities, detects falls in real time and alerts family instantly - showing only a skeleton, never the video.
                </p>
              </SlideUp>
              <SlideUp delay={0.24}>
                <div className="hero-cta">
                  <MagneticButton>
                    <Button as={Link} to={target} variant="primary" size="lg" iconRight={ArrowRight}>{user ? 'Open the monitor' : 'Get started'}</Button>
                  </MagneticButton>
                  <Button as="a" href="#how" size="lg" icon={ScanLine}>See how it works</Button>
                </div>
                <div className="hero-meta">
                  <span><Camera size={14} aria-hidden="true" /> Webcam or phone camera</span>
                  <span style={{ color: 'inherit', fontWeight: 400 }}><EyeOff size={14} aria-hidden="true" /> No video stored</span>
                  <span style={{ color: 'inherit', fontWeight: 400 }}><Bell size={14} aria-hidden="true" /> Telegram + email alerts</span>
                </div>
              </SlideUp>
            </div>
          </div>
          <div className="scroll-cue" aria-hidden="true"><span /></div>
        </section>

        <section className="signals" aria-label="What CareWatch does">
          <Marquee speed={46} label="Capabilities">
            {ACTIVITIES.map((a) => <span className="signal" key={a}>{a}</span>)}
          </Marquee>
        </section>

        <HowItWorks />

        <section className="l-section" id="features" aria-labelledby="features-title">
          <div className="l-wrap">
            <Reveal className="section-head">
              <span className="eyebrow">Features</span>
              <h2 id="features-title">Everything a quiet, careful watcher needs</h2>
            </Reveal>
            <Stagger className="feature-cards" inView gap={0.08}>
              {FEATURES.map(({ icon: Icon, title, text }) => (
                <Card className="feature-card" pad key={title}>
                  <span className="feature-icon"><Icon size={20} aria-hidden="true" /></span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </Card>
              ))}
            </Stagger>
          </div>
        </section>

        <section className="numbers" id="numbers" aria-labelledby="numbers-title">
          <div className="l-wrap">
            <h2 id="numbers-title" className="sr-only">Evaluation results</h2>
            <div className="numbers-grid">
              {NUMBERS.map((n) => (
                <div className="number" key={n.label}>
                  <strong><CountUp value={n.value} format={n.format} /></strong>
                  <span>{n.label}</span>
                </div>
              ))}
            </div>
            <p className="faint numbers-note">Measured on held-out images and simulated sequences - see the Model performance screen for the full breakdown and limitations.</p>
          </div>
        </section>

        <section className="l-section">
          <div className="l-wrap">
            <Reveal>
              <Card className="cta-card" spotlight={false}>
                <span className="cta-glow" aria-hidden="true" />
                <h2>Set it up in five minutes</h2>
                <p>Add your family as contacts, point a camera at the room and press start. Demo login: demo@carewatch.app</p>
                <div className="hero-cta" style={{ justifyContent: 'center' }}>
                  <Button as={Link} to={target} variant="primary" size="lg" iconRight={ArrowRight}>{user ? 'Open the monitor' : 'Sign in to CareWatch'}</Button>
                </div>
              </Card>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="l-footer">
        <div className="l-wrap">
          <div className="l-footer-inner">
            <div>
              <Link to="/" className="brand" style={{ padding: 0 }}><BrandMark /><span>CareWatch</span></Link>
              <p className="faint" style={{ marginTop: 12, maxWidth: '40ch' }}>Privacy-first activity recognition, fall detection and emergency alerts.</p>
            </div>
            <nav className="l-footer-links" aria-label="Footer">
              <a href="#how">How it works</a>
              <a href="#features">Features</a>
              <a href="#numbers">Results</a>
              <Link to={target}>{user ? 'Open monitor' : 'Sign in'}</Link>
            </nav>
          </div>
          <div className="l-footer-base faint">CareWatch is an assistive tool, not a certified medical device.</div>
        </div>
      </footer>
    </div>
  )
}
