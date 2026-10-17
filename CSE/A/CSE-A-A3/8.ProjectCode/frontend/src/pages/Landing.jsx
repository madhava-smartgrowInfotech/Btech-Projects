import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion, useScroll, useSpring } from 'framer-motion'
import Lenis from 'lenis'
import { ArrowRight, Moon, Sun, Trophy } from 'lucide-react'
import { BrandMark, Button, Card, ErrorState, IconButton, Skeleton } from '../components/ui'
import { CountUp, Marquee, MagneticButton, Reveal, SlideUp, Stagger } from '../components/motion'
import HeroVisual from '../components/three/HeroVisual'
import { useTheme } from '../lib/theme'
import { prefersReducedMotion } from '../lib/motion'
import { api } from '../lib/api'
import { ICON } from '../lib/diseases'
import { DISEASE_NAME, pct, titleize } from '../lib/format'
import { useAsync } from '../lib/useAsync'

function useLenis() {
  useEffect(() => {
    if (prefersReducedMotion()) return undefined
    const lenis = new Lenis({ lerp: 0.1 })
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
  }, [])
}

function LandingNav() {
  const { theme, toggle } = useTheme()
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])
  const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
  return (
    <header className={`l-nav${scrolled ? ' scrolled' : ''}`}>
      <div className="l-wrap l-nav-inner">
        <Link to="/" className="brand">
          <BrandMark />
          <span>
            Health Assistant
            <small>Multi-disease prediction</small>
          </span>
        </Link>
        <nav className="l-nav-links" aria-label="Page sections">
          <a href="#how">How it works</a>
          <a href="#conditions">Conditions</a>
          <a href="#numbers">By the numbers</a>
        </nav>
        <div className="row" style={{ flexWrap: 'nowrap' }}>
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={label} onClick={toggle} />
          <Button as={Link} to="/app" variant="primary" iconRight={ArrowRight}>
            Open app
          </Button>
        </div>
      </div>
    </header>
  )
}

const STEPS = [
  { n: '01', title: 'Enter the clinical values', body: 'Pick a condition and fill in the patient indicators - glucose and BMI for diabetes, cholesterol and ECG for the heart, enzymes for the liver, creatinine for the kidney.' },
  { n: '02', title: 'Four algorithms compete', body: 'Logistic Regression, Decision Tree, Random Forest and SVM are each trained per condition. The one with the best F1-score on held-out data is chosen to serve predictions.' },
  { n: '03', title: 'Get a risk class with confidence', body: 'The chosen model scales your input, predicts high or low risk, and reports how confident it is - alongside the accuracy it achieved on test data.' },
]

function HowVisual({ step, datasets, report }) {
  const ds = datasets?.find((d) => d.key === 'diabetes')
  const rep = report?.diabetes
  const algos = rep ? Object.entries(rep.all_results).sort((a, b) => b[1].f1 - a[1].f1) : []
  const best = rep?.all_results[rep.best_model]
  return (
    <div className="card how-card" aria-live="polite">
      <div className="how-card-head">
        <span className="viz-label" style={{ margin: 0 }}>
          Diabetes example
        </span>
        <span className="dots" aria-hidden="true">
          {STEPS.map((s, i) => (
            <i key={s.n} className={i === step ? 'on' : ''} />
          ))}
        </span>
      </div>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div key={step} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }}>
          {step === 0 && (
            <>
              <div className="viz-label">{ds ? `${ds.features.length} inputs` : 'Inputs'}</div>
              {ds ? (
                <ul className="anatomy-list" style={{ margin: 0 }}>
                  {ds.features.map((f) => (
                    <li key={f}>
                      <span className="anatomy-tag">Input</span>
                      <span>{titleize(f)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <Skeleton height={220} />
              )}
            </>
          )}
          {step === 1 && (
            <>
              <div className="viz-label">F1-score by algorithm</div>
              {rep ? (
                <div className="viz-bars">
                  {algos.map(([name, m]) => (
                    <div key={name} className={`viz-bar${name === rep.best_model ? ' best' : ''}`}>
                      <div className="row" style={{ justifyContent: 'space-between' }}>
                        <span>
                          {name} {name === rep.best_model && <Trophy size={13} aria-label="selected" style={{ display: 'inline', verticalAlign: '-2px' }} />}
                        </span>
                        <strong>{pct(m.f1)}</strong>
                      </div>
                      <div className="viz-track">
                        <i style={{ width: `${m.f1 * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <Skeleton height={220} />
              )}
            </>
          )}
          {step === 2 && (
            <>
              <div className="viz-label">Selected model · {rep ? rep.best_model : '...'}</div>
              {best ? (
                <div className="viz-stats">
                  <div>
                    <strong>{pct(best.accuracy)}</strong>
                    <span>Accuracy</span>
                  </div>
                  <div>
                    <strong>{pct(best.precision)}</strong>
                    <span>Precision</span>
                  </div>
                  <div>
                    <strong>{pct(best.recall)}</strong>
                    <span>Recall</span>
                  </div>
                </div>
              ) : (
                <Skeleton height={80} />
              )}
              <div className="viz-foot">Each prediction also returns a confidence percentage for the predicted class.</div>
            </>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

function HowItWorks({ datasets, report }) {
  const [step, setStep] = useState(0)
  const copy = useRef(null)
  const refs = useRef([])
  const { scrollYProgress } = useScroll({ target: copy, offset: ['start 70%', 'end 70%'] })
  const fill = useSpring(scrollYProgress, { stiffness: 120, damping: 30 })

  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setStep(Number(e.target.dataset.step))
      },
      { rootMargin: '-45% 0px -45% 0px' },
    )
    refs.current.forEach((el) => el && io.observe(el))
    return () => io.disconnect()
  }, [])

  return (
    <section className="how" id="how" aria-labelledby="how-h">
      <div className="l-wrap">
        <div className="section-head">
          <span className="eyebrow">How it works</span>
          <h2 id="how-h">From clinical values to a risk estimate in three steps</h2>
        </div>
        <div className="how-grid">
          <div className="how-copy" ref={copy}>
            <div className="how-progress" aria-hidden="true">
              <motion.i style={{ scaleY: fill }} />
            </div>
            {STEPS.map((s, i) => (
              <div key={s.n} className="how-step" data-step={i} ref={(el) => (refs.current[i] = el)}>
                <span className="how-num mono">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
          <div className="how-visual-col">
            <div className="how-visual">
              <HowVisual step={step} datasets={datasets} report={report} />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default function Landing() {
  useLenis()
  const diseases = useAsync(api.diseases)
  const report = useAsync(api.report)
  const datasets = useAsync(api.datasets)

  useEffect(() => {
    document.title = 'Health Assistant · Multi-disease prediction with machine learning'
  }, [])

  const list = diseases.data
  const rep = report.data
  const ds = datasets.data
  const apiError = diseases.error || report.error || datasets.error
  const retry = () => {
    diseases.reload()
    report.reload()
    datasets.reload()
  }
  const features = ds ? ds.flatMap((d) => d.features) : []
  const algos = rep ? Object.values(rep).reduce((n, d) => n + Object.keys(d.all_results).length, 0) : null
  const rows = ds ? ds.reduce((n, d) => n + d.rows, 0) : null
  const bestAcc = list ? Math.max(...list.map((d) => d.accuracy)) : null

  return (
    <div className="landing">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <LandingNav />
      <main id="main" tabIndex={-1}>
        <section className="hero" aria-labelledby="hero-h">
          <div className="hero-layer hero-grid" aria-hidden="true" />
          <div className="hero-layer hero-orbs" aria-hidden="true">
            <span className="orb orb-a" />
            <span className="orb orb-b" />
          </div>
          <div className="hero-layer hero-visual">
            <HeroVisual />
          </div>
          <div className="l-wrap hero-inner">
            <div className="hero-copy">
              <SlideUp>
                <span className="eyebrow">
                  <span className="pulse" aria-hidden="true" />
                  Machine-learning risk screening
                </span>
              </SlideUp>
              <SlideUp delay={0.08}>
                <h1 id="hero-h">
                  Four diseases. <span className="text-grad">One health assistant.</span>
                </h1>
              </SlideUp>
              <SlideUp delay={0.16}>
                <p className="hero-sub">
                  Enter a patient's clinical values and get an instant diabetes, heart, liver or kidney risk estimate - with the model's confidence and the accuracy behind it.
                </p>
              </SlideUp>
              <SlideUp delay={0.24}>
                <div className="landing-cta-row">
                  <MagneticButton>
                    <Button as={Link} to="/app/predict/diabetes" variant="primary" size="lg" iconRight={ArrowRight}>
                      Start a prediction
                    </Button>
                  </MagneticButton>
                  <Button as={Link} to="/app/models" size="lg">
                    Compare the models
                  </Button>
                </div>
              </SlideUp>
              <SlideUp delay={0.32}>
                <div className="hero-meta">
                  <span>Logistic Regression · Decision Tree · Random Forest · SVM</span>
                  <span>For education only - not medical advice</span>
                </div>
              </SlideUp>
            </div>
          </div>
          <div className="scroll-cue" aria-hidden="true">
            <span />
          </div>
        </section>

        <section className={`signals${ds ? '' : ' signals-empty'}`} aria-label="Clinical indicators the models use">
          {ds ? (
            <Marquee speed={90} label="Clinical indicators">
              {features.map((f, i) => (
                <span className="signal" key={`${f}-${i}`}>
                  {titleize(f)}
                </span>
              ))}
            </Marquee>
          ) : datasets.error ? (
            <p className="faint" style={{ textAlign: 'center' }}>
              Clinical indicators could not be loaded.
            </p>
          ) : (
            <Skeleton height={36} style={{ margin: '0 28px', width: 'auto' }} />
          )}
        </section>

        <HowItWorks datasets={ds} report={rep} />

        <section className="l-section" id="conditions" aria-labelledby="cond-h">
          <div className="l-wrap">
            <Reveal className="section-head">
              <span className="eyebrow">Conditions</span>
              <h2 id="cond-h">Choose what to screen for</h2>
            </Reveal>
            {apiError ? (
              <ErrorState title="Could not reach the prediction API" error={apiError} onRetry={retry} />
            ) : list ? (
              <Stagger className="feature-cards" inView>
                {list.map((d) => {
                  const Icon = ICON[d.key]
                  return (
                    <Card as={Link} to={`/app/predict/${d.key}`} key={d.key} className="feature-card disease-card" aria-label={`${DISEASE_NAME[d.key]} - ${d.best_model}, ${pct(d.accuracy)} accuracy`}>
                      <span className="feature-icon">
                        <Icon size={22} aria-hidden="true" />
                      </span>
                      <h3>{DISEASE_NAME[d.key]}</h3>
                      <p>{d.blurb}</p>
                      <p className="faint" style={{ marginTop: 14 }}>
                        {d.best_model} · {pct(d.accuracy)} accuracy · {d.n_features} inputs
                      </p>
                    </Card>
                  )
                })}
              </Stagger>
            ) : (
              <div className="feature-cards" aria-busy="true" aria-label="Loading conditions">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} height={200} radius={18} />
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="numbers" id="numbers" aria-label="Project numbers">
          <div className="l-wrap">
            <div className="numbers-grid">
              <div className="number">
                <strong>{list ? <CountUp value={list.length} /> : '-'}</strong>
                <span>Conditions</span>
              </div>
              <div className="number">
                <strong>{algos !== null ? <CountUp value={algos} /> : '-'}</strong>
                <span>Models trained</span>
              </div>
              <div className="number">
                <strong>{list ? <CountUp value={list.reduce((n, d) => n + d.n_features, 0)} /> : '-'}</strong>
                <span>Clinical inputs</span>
              </div>
              <div className="number">
                <strong>{rows !== null ? <CountUp value={rows} /> : '-'}</strong>
                <span>Training rows</span>
              </div>
              <div className="number">
                <strong>{bestAcc !== null ? <CountUp value={bestAcc * 100} format={(v) => `${v.toFixed(1)}%`} /> : '-'}</strong>
                <span>Best test accuracy</span>
              </div>
            </div>
            <p className="faint numbers-note">Training data is synthetically generated for demonstration; accuracies describe that data, not real patients.</p>
          </div>
        </section>

        <section className="l-section">
          <div className="l-wrap">
            <Reveal>
              <div className="card cta-card">
                <span className="cta-glow" aria-hidden="true" />
                <h2>Try a prediction now</h2>
                <p>Load a real record from the training data or type your own values - results appear instantly.</p>
                <div className="landing-cta-row" style={{ justifyContent: 'center' }}>
                  <Button as={Link} to="/app/predict/diabetes" variant="primary" size="lg" iconRight={ArrowRight}>
                    Open the app
                  </Button>
                </div>
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="l-footer">
        <div className="l-wrap">
          <div className="l-footer-inner">
            <Link to="/" className="brand">
              <BrandMark />
              <span>
                Health Assistant
                <small>Multi-disease prediction</small>
              </span>
            </Link>
            <nav className="l-footer-links" aria-label="Footer">
              <Link to="/app">Overview</Link>
              <Link to="/app/models">Models</Link>
              <Link to="/app/predict/diabetes">Predict</Link>
              <Link to="/app/about">About</Link>
            </nav>
          </div>
          <div className="l-footer-base faint">
            This tool provides a machine-learning based risk estimate for educational and demonstration purposes only. It is not a substitute for professional medical diagnosis.
            Please consult a qualified healthcare provider for any medical concerns.
          </div>
        </div>
      </footer>
    </div>
  )
}
