import { Suspense, lazy, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Lenis from 'lenis'
import { ArrowRight, Brain, Dna, FileText, Fingerprint, Layers, Moon, ScanLine, Sparkles, Sun, TestTubes } from 'lucide-react'
import { useTheme } from '../lib/theme'
import { useHealth } from '../lib/health'
import { useAuth } from '../lib/auth'
import { useMediaQuery, useReducedMotion } from '../lib/motion'
import { BrandMark, Button, Card, IconButton, Tooltip } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, ScrollTrigger, SlideUp, Stagger, gsap } from '../components/motion'
import '../styles/landing.css'

const HeroVisual = lazy(() => import('../components/three/HeroVisual'))

const SIGNALS = [
  'JEPA pre-training',
  'masked patch-block prediction',
  'no masks needed to pre-train',
  'ViT encoder',
  'fine-tune on 10% of masks',
  'U-Net baseline',
  'MAE baseline',
  'Dice and IoU',
  'tumour area in mm²',
  'k-mer tokens',
  'repeat-type classifier',
  'exact tandem-repeat scan',
  '20 CODIS core loci',
  'theta-corrected likelihood ratios',
  'NIST allele frequencies',
  'structured Gemini reports',
]

const FEATURES = [
  { icon: Brain, title: 'JEPA pre-training', body: 'A small ViT learns by predicting the features of masked patch blocks in brain-MRI slices. No expert masks are used at this stage.' },
  { icon: ScanLine, title: 'Few-label segmentation', body: 'A light decoder fine-tuned on only 10% of the masks outlines the tumour and reports its area in px and mm², its share of the brain and its location.' },
  { icon: Layers, title: 'Label-efficiency comparison', body: 'Dice and IoU at 10% and 100% of the masks, side by side with a supervised U-Net, an MAE-pre-trained ViT and a ViT from scratch.' },
  { icon: Dna, title: 'DNA encoder', body: 'k-mer tokens and the same latent-prediction objective classify STR repeat type and organism class, alongside an exact tandem-repeat scan.' },
  { icon: Fingerprint, title: 'STR profile matching', body: 'A genotype over the 20 CODIS core loci is ranked against reference profiles with theta-corrected likelihood ratios and a per-locus breakdown.' },
  { icon: FileText, title: 'Structured reports', body: 'Gemini writes a summary, findings, measurements, interpretation, limitations and recommendation from the real model output, never from invented numbers.' },
]

const NUMBERS = [
  { label: 'CODIS core loci', value: 20 },
  { label: 'Reference STR profiles', value: 1000 },
  { label: 'Segmentation models', value: 3 },
  { label: 'Repeat-type classes', value: 5 },
  { label: 'Report sections', value: 6 },
]

// 8x8 patch grid: the highlighted blocks are the ones the predictor has to describe.
const MASKED = new Set([9, 10, 11, 17, 18, 19, 28, 29, 36, 37, 6, 7, 14, 15, 50, 51, 58, 59])

function useLenis(enabled) {
  useEffect(() => {
    if (!enabled) return undefined
    const lenis = new Lenis({ duration: 1.15, smoothWheel: true })
    lenis.on('scroll', ScrollTrigger.update)
    const raf = (t) => lenis.raf(t * 1000)
    gsap.ticker.add(raf)
    gsap.ticker.lagSmoothing(0)
    return () => {
      gsap.ticker.remove(raf)
      lenis.destroy()
    }
  }, [enabled])
}

function LandingNav() {
  const { theme, toggle } = useTheme()
  const { user } = useAuth()
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])
  const dark = theme === 'dark'
  return (
    <header className={`l-nav ${scrolled ? 'scrolled' : ''}`}>
      <div className="l-wrap l-nav-inner">
        <Link to="/" className="brand" aria-label="BioSight home">
          <BrandMark />
          <span>BioSight</span>
        </Link>
        <nav aria-label="Landing sections" className="l-nav-links">
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
          <a href="#numbers">In this build</a>
        </nav>
        <div className="row" style={{ gap: 6 }}>
          <Tooltip label={dark ? 'Light mode' : 'Dark mode'} placement="bottom">
            <IconButton icon={dark ? Sun : Moon} label={dark ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
          </Tooltip>
          <Button as={Link} to={user ? '/app/mri' : '/login'} variant="primary" size="sm" iconRight={ArrowRight}>
            {user ? 'Open app' : 'Sign in'}
          </Button>
        </div>
      </div>
    </header>
  )
}

function Hero() {
  const { online } = useHealth()
  const { user } = useAuth()
  return (
    <section className="hero" aria-labelledby="hero-title">
      {/* depth layers: each moves at its own rate on scroll */}
      <Parallax speed={-0.35} className="hero-layer hero-grid" />
      <Parallax speed={0.55} className="hero-layer hero-orbs">
        <span className="orb orb-a" />
        <span className="orb orb-b" />
      </Parallax>
      <Parallax speed={0.18} className="hero-layer hero-visual">
        <Suspense fallback={<img className="hero-fallback" src="/hero-fallback.svg" alt="" aria-hidden="true" />}>
          <HeroVisual />
        </Suspense>
      </Parallax>

      <div className="l-wrap hero-inner">
        <div className="hero-copy">
          <SlideUp>
            <span className="eyebrow">
              <span className="pulse" aria-hidden="true" /> Self-supervised JEPA · medical imaging · DNA fingerprinting
            </span>
          </SlideUp>
          <SlideUp delay={0.08}>
            <h1 id="hero-title">
              See the tumour. Read the profile. <span className="text-grad">With a fraction of the labels.</span>
            </h1>
          </SlideUp>
          <SlideUp delay={0.16}>
            <p className="hero-sub">
              BioSight pre-trains on unlabelled brain-MRI slices and DNA sequences by predicting meaning instead of pixels, then segments tumours from only 10% of the masks, classifies
              STR repeats and ranks STR profiles with likelihood ratios, each with a structured report.
            </p>
          </SlideUp>
          <SlideUp delay={0.24}>
            <div className="row" style={{ marginTop: 32, gap: 12 }}>
              <MagneticButton>
                <Button as={Link} to={user ? '/app/mri' : '/login'} variant="primary" size="lg" iconRight={ArrowRight}>
                  {user ? 'Open the workspace' : 'Try the demo'}
                </Button>
              </MagneticButton>
              <Button as="a" href="#how" size="lg">
                How it works
              </Button>
            </div>
          </SlideUp>
          <SlideUp delay={0.32}>
            <div className="hero-meta">
              <span>
                <Sparkles size={15} aria-hidden="true" /> {online === undefined ? 'Checking the API…' : online ? 'API online' : 'API offline - run.bat starts it'}
              </span>
              <span>Decision support only, not a clinical or forensic device</span>
            </div>
          </SlideUp>
        </div>
      </div>
      <a href="#how" className="scroll-cue" aria-label="Scroll to how it works">
        <span />
      </a>
    </section>
  )
}

const STEPS = [
  {
    k: '01',
    title: 'Pre-train without labels',
    body: 'A ViT encoder sees the visible patches of an MRI slice and a predictor describes, in feature space, the blocks that were hidden. Because it predicts meaning rather than pixels, no expert masks are needed. The same idea runs on DNA, with 4-mer tokens.',
  },
  {
    k: '02',
    title: 'Fine-tune on few labels',
    body: 'A light decoder is fine-tuned on a small share of the masks and compared with a supervised U-Net, an MAE-pre-trained ViT and a ViT from scratch at 10% and 100% of the labels. You get the overlay, area in mm², share of the brain and Dice against the expert mask.',
  },
  {
    k: '03',
    title: 'Match, classify, report',
    body: 'DNA windows are classified for STR repeat type and organism class, an exact scan lists tandem repeats, and STR genotypes are ranked against the reference database with likelihood ratios. Every result gets a structured report written from the real numbers.',
  },
]

function StepVisual({ step }) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={step}
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -12, scale: 0.98 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      >
        {step === 0 && (
          <div>
            <div className="viz-label">Masked patch blocks</div>
            <div className="patch-grid" role="img" aria-label="An 8 by 8 grid of image patches with several blocks highlighted as masked">
              {Array.from({ length: 64 }).map((_, i) => (
                <i key={i} className={MASKED.has(i) ? 'masked' : ''} />
              ))}
            </div>
            <div className="patch-legend">
              <span>
                <i /> context patches the encoder sees
              </span>
              <span>
                <i className="masked" /> blocks whose features are predicted
              </span>
            </div>
            <div className="viz-foot">The loss compares predicted and target features - no pixels are reconstructed.</div>
          </div>
        )}
        {step === 1 && (
          <div>
            <div className="viz-label">Share of masks used for fine-tuning</div>
            <div className="viz-bars">
              {[
                { name: 'ViT + JEPA pre-training', share: 10, best: true },
                { name: 'ViT + JEPA pre-training', share: 100 },
                { name: 'U-Net, supervised', share: 100 },
              ].map((b, i) => (
                <div key={i} className={`viz-bar ${b.best ? 'best' : ''}`}>
                  <div className="row" style={{ justifyContent: 'space-between' }}>
                    <span>{b.name}</span>
                    <strong>{b.share}%</strong>
                  </div>
                  <div className="viz-track">
                    <motion.i initial={{ width: 0 }} animate={{ width: `${b.share}%` }} transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="viz-foot">Dice and IoU for each setting are on the Label efficiency screen.</div>
          </div>
        )}
        {step === 2 && (
          <div>
            <div className="viz-label">From input to report</div>
            <ol className="flow">
              <li>
                <span className="flow-tag">DNA window</span> 99 bp, 96 4-mer tokens
              </li>
              <li>
                <span className="flow-tag">Classify</span> repeat type and organism class
              </li>
              <li>
                <span className="flow-tag">Scan</span> exact tandem repeats
              </li>
              <li>
                <span className="flow-tag">STR profile</span> 20 CODIS loci, theta-corrected LR
              </li>
              <li>
                <span className="flow-tag">Report</span> summary, findings, limitations
              </li>
            </ol>
            <div className="viz-foot">Reports are written only from the model output.</div>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  )
}

function HowItWorks() {
  const section = useRef(null)
  const visual = useRef(null)
  const copy = useRef(null)
  const [step, setStep] = useState(0)
  const wide = useMediaQuery('(min-width: 900px)')

  useLayoutEffect(() => {
    if (!wide) return undefined
    const ctx = gsap.context(() => {
      const mm = gsap.matchMedia()
      // pin the visual while the copy scrolls past (motion users only; others get a sticky fallback in CSS)
      mm.add('(prefers-reduced-motion: no-preference)', () => {
        ScrollTrigger.create({
          trigger: copy.current,
          start: 'top 18%',
          end: () => `bottom ${visual.current.offsetHeight + window.innerHeight * 0.18}px`,
          pin: visual.current,
          pinSpacing: false,
          invalidateOnRefresh: true,
        })
        gsap.utils.toArray('.how-step').forEach((el) => {
          gsap.fromTo(el, { opacity: 0.28 }, { opacity: 1, ease: 'none', scrollTrigger: { trigger: el, start: 'top 75%', end: 'top 45%', scrub: true } })
        })
      })
      gsap.utils.toArray('.how-step').forEach((el, i) => {
        ScrollTrigger.create({ trigger: el, start: 'top 55%', end: 'bottom 55%', onToggle: (self) => self.isActive && setStep(i) })
      })
      gsap.fromTo('.how-progress i', { scaleY: 0 }, { scaleY: 1, ease: 'none', scrollTrigger: { trigger: copy.current, start: 'top 55%', end: 'bottom 55%', scrub: true } })
    }, section)
    return () => ctx.revert()
  }, [wide])

  return (
    <section id="how" ref={section} className="how" aria-labelledby="how-title">
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">How it works</span>
          <h2 id="how-title">Learn from the data first. Ask for labels second.</h2>
        </Reveal>
        <div className="how-grid">
          {wide && (
            <div className="how-visual-col">
              <div ref={visual} className="how-visual">
                <Card className="how-card">
                  <div className="how-card-head">
                    <span className="mono faint">stage {STEPS[step].k} / 03</span>
                    <span className="dots" aria-hidden="true">
                      {STEPS.map((s, i) => (
                        <i key={s.k} className={i === step ? 'on' : ''} />
                      ))}
                    </span>
                  </div>
                  <StepVisual step={step} />
                </Card>
              </div>
            </div>
          )}
          <div ref={copy} className="how-copy">
            {wide && (
              <div className="how-progress" aria-hidden="true">
                <i />
              </div>
            )}
            {STEPS.map((s, i) => (
              <article key={s.k} className={`how-step ${i === step ? 'active' : ''}`}>
                <span className="how-num mono">{s.k}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
                {!wide && (
                  <Card className="how-card inline">
                    <StepVisual step={i} />
                  </Card>
                )}
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function SignalMarquee() {
  const half = Math.ceil(SIGNALS.length / 2)
  return (
    <section className="signals" aria-label="What BioSight does">
      <Marquee speed={70}>
        {SIGNALS.slice(0, half).map((f) => (
          <span key={f} className="signal mono">
            {f}
          </span>
        ))}
      </Marquee>
      <Marquee speed={80} reverse>
        {SIGNALS.slice(half).map((f) => (
          <span key={f} className="signal mono">
            {f}
          </span>
        ))}
      </Marquee>
    </section>
  )
}

function FeatureGrid() {
  return (
    <section id="features" className="l-section" aria-labelledby="features-title">
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">Features</span>
          <h2 id="features-title">One workspace for imaging and genomics.</h2>
        </Reveal>
        <Stagger className="feature-cards" inView>
          {FEATURES.map((f) => (
            <Card key={f.title} className="feature-card">
              <span className="feature-icon">
                <f.icon size={20} aria-hidden="true" />
              </span>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </Card>
          ))}
        </Stagger>
      </div>
    </section>
  )
}

function Numbers() {
  return (
    <section id="numbers" className="numbers" aria-labelledby="numbers-title">
      <div className="l-wrap">
        <h2 id="numbers-title" className="sr-only">
          What ships in this build
        </h2>
        <div className="numbers-grid">
          {NUMBERS.map((it) => (
            <div key={it.label} className="number">
              <strong>
                <CountUp value={it.value} duration={1.8} />
              </strong>
              <span>{it.label}</span>
            </div>
          ))}
        </div>
        <p className="faint numbers-note">What ships in this build. Measured Dice, IoU and accuracy are on the Label efficiency and Model performance screens.</p>
      </div>
    </section>
  )
}

function CallToAction() {
  const { user } = useAuth()
  return (
    <section className="l-section cta" aria-labelledby="cta-title">
      <div className="l-wrap">
        <Reveal>
          <Card className="cta-card">
            <Parallax speed={0.2} className="cta-glow" />
            <h2 id="cta-title">Try it on a real slice.</h2>
            <p>Pick a held-out brain-MRI sample, classify a DNA read or search an STR profile, and read the report that comes with it.</p>
            <div className="row" style={{ justifyContent: 'center', marginTop: 26 }}>
              <MagneticButton>
                <Button as={Link} to={user ? '/app/mri' : '/login'} variant="primary" size="lg" icon={Brain}>
                  {user ? 'Analyse an MRI slice' : 'Sign in with the demo'}
                </Button>
              </MagneticButton>
              <Button as={Link} to={user ? '/app/dna' : '/login'} size="lg" icon={TestTubes}>
                Classify DNA
              </Button>
            </div>
          </Card>
        </Reveal>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="l-footer">
      <div className="l-wrap l-footer-inner">
        <div>
          <Link to="/" className="brand" style={{ padding: 0 }}>
            <BrandMark />
            <span>BioSight</span>
          </Link>
          <p className="faint" style={{ marginTop: 10, maxWidth: '52ch' }}>
            JEPA LLM tuning framework for self-supervised medical-image segmentation and DNA fingerprinting analysis. Batch CSDS-A-A8.
          </p>
        </div>
        <nav aria-label="Footer" className="l-footer-links">
          <Link to="/app/mri">MRI analysis</Link>
          <Link to="/app/label-efficiency">Label efficiency</Link>
          <Link to="/app/dna">DNA analysis</Link>
          <Link to="/app/str">STR matching</Link>
          <Link to="/app/performance">Model performance</Link>
          <Link to="/app/history">History</Link>
        </nav>
      </div>
      <div className="l-wrap faint l-footer-base">Research prototype. Results are decision support and need review by a radiologist or a qualified DNA analyst.</div>
    </footer>
  )
}

export default function Landing() {
  const reduced = useReducedMotion()
  useLenis(!reduced)
  useEffect(() => {
    document.title = 'BioSight · JEPA imaging and DNA fingerprinting'
    // layout shifts after fonts / lazy chunks load - recompute trigger positions
    const t = setTimeout(() => ScrollTrigger.refresh(), 600)
    return () => clearTimeout(t)
  }, [])
  return (
    <div className="landing">
      <a href="#how" className="skip-link">
        Skip to content
      </a>
      <LandingNav />
      <main>
        <Hero />
        <SignalMarquee />
        <HowItWorks />
        <FeatureGrid />
        <Numbers />
        <CallToAction />
      </main>
      <Footer />
    </div>
  )
}
