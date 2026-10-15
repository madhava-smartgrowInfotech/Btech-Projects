import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Download, Eraser, FileText, Gauge, Layers, ScanSearch, SlidersHorizontal, Sparkles, Target, UploadCloud, Waves } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge, Brand, Button, Container, ThemeToggle, modelLabel } from '../components/ui'
import { CountUp, FadeIn, MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'
import { api } from '../lib/api'
import { fmtInt } from '../lib/format'
import { useHealth } from '../lib/health'
import { HOW_IT_WORKS, OBJECTIVES, OVERVIEW, PROBLEM, TECH_STACK } from '../content'

const STEP_ICONS = [UploadCloud, SlidersHorizontal, ScanSearch, Target, FileText]
const TONES = ['lavender', 'mint', 'peach', 'sky', 'rose', 'butter']
const OBJECTIVE_ICONS = [Layers, Eraser, Sparkles, Target, UploadCloud, Gauge]

/** An illustration (not data): a stylised sea with two dashed boxes, like the app draws on real images. */
function Scene() {
  return (
    <svg className="scene" viewBox="0 0 480 340" role="img" aria-label="Illustration of an ocean scene with two floating plastic items outlined by detection boxes">
      <defs>
        <linearGradient id="sea" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" style={{ stopColor: 'var(--sky-soft)' }} />
          <stop offset="1" style={{ stopColor: 'var(--sky)' }} />
        </linearGradient>
      </defs>
      <rect width="480" height="340" style={{ fill: 'url(#sea)' }} />
      <circle cx="384" cy="70" r="30" style={{ fill: 'var(--butter)' }} />
      <path d="M0 190c40-16 80-16 120 0s80 16 120 0 80-16 120 0 80 16 120 0v150H0z" style={{ fill: 'var(--lavender)', opacity: 0.45 }} />
      <path d="M0 230c40-16 80-16 120 0s80 16 120 0 80-16 120 0 80 16 120 0v110H0z" style={{ fill: 'var(--sky)', opacity: 0.7 }} />
      <path d="M0 280c40-14 80-14 120 0s80 14 120 0 80-14 120 0 80 14 120 0v60H0z" style={{ fill: 'var(--mint)', opacity: 0.55 }} />
      {/* bottle */}
      <g transform="rotate(-18 150 215)">
        <rect x="132" y="190" width="38" height="62" rx="12" style={{ fill: '#fff', opacity: 0.9 }} />
        <rect x="143" y="176" width="16" height="18" rx="4" style={{ fill: 'var(--peach)' }} />
      </g>
      <rect className="box" x="104" y="162" width="98" height="104" rx="12" style={{ fill: 'none', stroke: 'var(--lavender-ink)', strokeWidth: 3 }} />
      <rect x="104" y="140" width="70" height="22" rx="8" style={{ fill: 'var(--lavender-ink)' }} />
      <text x="114" y="156" style={{ fill: '#fff', font: '600 12px Inter, sans-serif' }}>plastic</text>
      {/* bag */}
      <path d="M310 222c14-18 40-18 54 0l10 36c2 8-4 14-12 14h-50c-8 0-14-6-12-14z" style={{ fill: '#fff', opacity: 0.88 }} />
      <rect className="box" x="292" y="196" width="96" height="86" rx="12" style={{ fill: 'none', stroke: 'var(--mint-ink)', strokeWidth: 3 }} />
      <rect x="292" y="174" width="70" height="22" rx="8" style={{ fill: 'var(--mint-ink)' }} />
      <text x="302" y="190" style={{ fill: '#fff', font: '600 12px Inter, sans-serif' }}>plastic</text>
    </svg>
  )
}

function useHistory() {
  const [rows, setRows] = useState(null)
  useEffect(() => {
    let alive = true
    api
      .history()
      .then((r) => alive && setRows(r))
      .catch(() => alive && setRows(null))
    return () => {
      alive = false
    }
  }, [])
  return rows
}

export default function Landing() {
  const health = useHealth()
  const rows = useHistory()
  useEffect(() => {
    document.title = 'PlastiScan - Ocean plastic detection'
  }, [])

  const stats = useMemo(() => {
    if (!rows || !rows.length) return null
    return {
      runs: rows.length,
      objects: rows.reduce((a, r) => a + r.object_count, 0),
      avg: (rows.reduce((a, r) => a + r.avg_confidence, 0) / rows.length) * 100,
    }
  }, [rows])

  const label = modelLabel(health.data)

  return (
    <div className="landing">
      <a className="skip-link" href="#top">
        Skip to content
      </a>
      <header className="l-nav">
        <Container>
          <Brand />
          <nav className="l-nav-links" aria-label="Page sections">
            <a href="#how">How it works</a>
            <a href="#problem">Problem</a>
            <a href="#objectives">Objectives</a>
            <a href="#stack">Technology</a>
          </nav>
          <div className="l-nav-right">
            <ThemeToggle />
            <Button to="/app/detect" size="sm" iconRight={ArrowRight} className="btn-open-app">
              <span>Open the app</span>
            </Button>
          </div>
        </Container>
      </header>

      <main id="top" tabIndex={-1}>
        <section className="hero">
          <Blobs preset="hero" />
          <Container>
            <div className="hero-grid">
              <div>
                <SlideUp>
                  <Badge tone="lavender" icon={Waves}>
                    AI for cleaner oceans
                  </Badge>
                </SlideUp>
                <SlideUp delay={0.06}>
                  <h1 style={{ marginTop: 18 }}>
                    Spot plastic in ocean images, <span className="hl">one box at a time</span>
                  </h1>
                </SlideUp>
                <SlideUp delay={0.12}>
                  <p className="hero-lead">
                    Upload an ocean photo and PlastiScan finds each piece of plastic waste, draws a box around it and tells you how sure the model is.
                  </p>
                </SlideUp>
                <SlideUp delay={0.18} className="hero-cta">
                  <MagneticButton>
                    <Button to="/app/detect" size="lg" iconRight={ArrowRight}>
                      Try a detection
                    </Button>
                  </MagneticButton>
                  <Button href="#how" size="lg" variant="secondary" onClick={(e) => (e.preventDefault(), document.getElementById('how')?.scrollIntoView({ behavior: 'smooth' }))}>
                    See how it works
                  </Button>
                </SlideUp>
                <FadeIn delay={0.35} className="hero-note">
                  <Badge tone="mint">YOLOv8 detector</Badge>
                  <Badge tone="sky">Underwater-aware preprocessing</Badge>
                  <Badge tone="peach">Downloadable reports</Badge>
                </FadeIn>
              </div>

              <motion.div className="hero-visual" initial={{ opacity: 0, y: 24, rotate: 1.5 }} animate={{ opacity: 1, y: 0, rotate: 0 }} transition={{ type: 'spring', stiffness: 120, damping: 18, delay: 0.15 }}>
                <div className="hero-card">
                  <Scene />
                </div>
                <motion.div className="hero-float b" animate={{ y: [0, -8, 0] }} transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}>
                  <Target size={22} aria-hidden="true" style={{ color: 'var(--lavender-ink)' }} />
                  <div>
                    <b>Bounding boxes</b>
                    <span>on every detected item</span>
                  </div>
                </motion.div>
                <motion.div className="hero-float a" animate={{ y: [0, 8, 0] }} transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}>
                  <Gauge size={22} aria-hidden="true" style={{ color: 'var(--mint-ink)' }} />
                  <div>
                    <b>Confidence score</b>
                    <span>for each detection</span>
                  </div>
                </motion.div>
              </motion.div>
            </div>
          </Container>
        </section>

        {stats && (
          <Container>
            <Reveal>
              <div className="stats-strip" role="group" aria-label="Live totals from your detection history">
                <div className="s">
                  <b>
                    <CountUp value={stats.runs} format={fmtInt} />
                  </b>
                  <span>images analysed</span>
                </div>
                <div className="s">
                  <b>
                    <CountUp value={stats.objects} format={fmtInt} />
                  </b>
                  <span>plastic objects detected</span>
                </div>
                <div className="s">
                  <b>
                    <CountUp value={stats.avg} format={(v) => `${v.toFixed(1)}%`} />
                  </b>
                  <span>average confidence</span>
                </div>
                {label && (
                  <div className="s">
                    <b style={{ fontSize: 20 }}>{label}</b>
                    <span>current model</span>
                  </div>
                )}
              </div>
            </Reveal>
          </Container>
        )}

        <section className="section" id="how" style={{ scrollMarginTop: 80 }}>
          <Container>
            <Reveal className="section-head">
              <Badge tone="sky">How the system works</Badge>
              <h2>From a photo to a report in five steps</h2>
              <p>Every step is a real stage of the detection pipeline in this project.</p>
            </Reveal>
            <div className="steps-line" aria-hidden="true">
              <motion.div initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }} transition={{ duration: 1.1, ease: 'easeOut' }} />
            </div>
            <Stagger className="steps" inView as="ol" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {HOW_IT_WORKS.map((s, i) => {
                const Icon = STEP_ICONS[i]
                return (
                  <Stagger.Item as="li" key={s.title} className="step-card">
                    <span className="n">Step {i + 1}</span>
                    <h3>{s.title}</h3>
                    <p>{s.text}</p>
                    <span className="ico" style={{ background: `var(--${TONES[i]})` }}>
                      <Icon size={24} aria-hidden="true" />
                    </span>
                  </Stagger.Item>
                )
              })}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="problem" style={{ scrollMarginTop: 80, paddingTop: 8 }}>
          <Container>
            <Stagger className="features" inView>
              <Stagger.Item className="feature">
                <span className="ico" style={{ background: 'var(--lavender)' }}>
                  <Waves size={26} aria-hidden="true" />
                </span>
                <h3>Project overview</h3>
                <p>{OVERVIEW}</p>
              </Stagger.Item>
              <Stagger.Item className="feature">
                <span className="ico" style={{ background: 'var(--peach)' }}>
                  <Target size={26} aria-hidden="true" />
                </span>
                <h3>The problem</h3>
                <p>{PROBLEM}</p>
              </Stagger.Item>
            </Stagger>
          </Container>
        </section>

        <section className="section" id="objectives" style={{ scrollMarginTop: 80, paddingTop: 8 }}>
          <Container>
            <Reveal className="section-head">
              <Badge tone="mint">Project objectives</Badge>
              <h2>What the project sets out to do</h2>
            </Reveal>
            <Stagger className="features" inView as="ol" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {OBJECTIVES.map((o, i) => {
                const Icon = OBJECTIVE_ICONS[i]
                return (
                  <Stagger.Item as="li" key={o} className="feature">
                    <span className="ico" style={{ background: `var(--${TONES[i]})` }}>
                      <Icon size={26} aria-hidden="true" />
                    </span>
                    <h3>Objective {i + 1}</h3>
                    <p>{o}</p>
                  </Stagger.Item>
                )
              })}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="stack" style={{ scrollMarginTop: 80, paddingTop: 8 }}>
          <Container>
            <Reveal className="section-head">
              <Badge tone="peach">Technology stack</Badge>
              <h2>Built with familiar, open tools</h2>
            </Reveal>
            <Reveal>
              <Marquee>
                {TECH_STACK.flatMap((g) => g.items).map((t) => (
                  <span className="chip" key={t}>
                    {t}
                  </span>
                ))}
              </Marquee>
            </Reveal>
            <Reveal style={{ marginTop: 34 }}>
              <div className="tech-groups">
                {TECH_STACK.map((g) => (
                  <div className="card" key={g.group}>
                    <h3>{g.group}</h3>
                    <div className="row">
                      {g.items.map((t) => (
                        <Badge key={t} tone="neutral">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Reveal>
          </Container>
        </section>

        <section className="section" style={{ paddingTop: 8 }}>
          <Container>
            <Reveal>
              <div className="cta">
                <Blobs preset="cta" />
                <h2>Ready to scan an image?</h2>
                <p>Drop in an ocean photo, adjust the confidence threshold, and download the annotated image and a JSON report.</p>
                <div className="row" style={{ justifyContent: 'center' }}>
                  <MagneticButton>
                    <Button to="/app/detect" size="lg" iconRight={ArrowRight}>
                      Open detection
                    </Button>
                  </MagneticButton>
                  <Button to="/app/about" size="lg" variant="secondary">
                    About the project
                  </Button>
                </div>
                <p className="small" style={{ marginTop: 22, marginBottom: 0 }}>
                  Use the app menu to move between <strong>Detection</strong>, <strong>Dashboard</strong>, <strong>Evaluation</strong> and <strong>About</strong>.
                </p>
              </div>
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="footer">
        <Container>
          <span>PlastiScan · Automated Plastic Waste Detection in Oceans Using Artificial Intelligence</span>
          <span>
            <Link to="/app/detect">Detection</Link> · <Link to="/app/dashboard">Dashboard</Link> · <Link to="/app/evaluation">Evaluation</Link> · <Link to="/app/about">About</Link>
          </span>
        </Container>
      </footer>
    </div>
  )
}
