import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Bot, Bug, FileText, Gauge, ListChecks, Lock, ShieldCheck, Terminal } from 'lucide-react'
import api from '../api'
import { useAuth } from '../auth'
import { useAsync } from '../lib/useAsync'
import { BrandMark, Button, Card, Skeleton, Badge } from '../components/ui'
import { MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import HeroVisual from '../components/three/HeroVisual'

const FEATURES = [
  { icon: Bug, title: 'OWASP API Top 10 checks', body: 'BOLA/IDOR, broken authentication, excessive data exposure, mass assignment, missing rate limits, broken function-level authorisation, injection and misconfiguration.' },
  { icon: Bot, title: 'AI business-logic tests', body: 'Gemini reads your spec and proposes abuse tests such as negative amounts, foreign-account transfers and replayed payments. Without a key, a built-in generator is used.' },
  { icon: Gauge, title: 'Security score', body: 'A 0–100 score with a letter grade, weighted by finding severity.' },
  { icon: Terminal, title: 'Reproducible findings', body: 'Each finding includes evidence, a curl command that reproduces it, the OWASP mapping and a fix with a code snippet.' },
  { icon: FileText, title: 'HTML and PDF reports', body: 'Shareable reports with evidence, reproduction steps, OWASP mapping and fixes.' },
  { icon: ListChecks, title: 'Validation', body: 'Compare findings with a target’s known-vulnerability list for a detection rate and a false-positive count.' },
  { icon: Lock, title: 'Scope guard', body: 'Scans only run against allow-listed hosts (localhost by default), and only after you confirm you are authorised.' },
]

const STEPS = [
  { n: '01', title: 'Import the spec', body: 'Paste or upload an OpenAPI, Swagger or Postman file, and add auth profiles for two test users.' },
  { n: '02', title: 'Confirm scope', body: 'The host must be on the allow-list, and you confirm you are authorised to test it.' },
  { n: '03', title: 'Run the checks', body: 'OWASP checks and AI-generated business-logic tests run against the live target.' },
  { n: '04', title: 'Fix and re-test', body: 'Review the score, follow each finding’s fix, and share an HTML or PDF report.' },
]

// Shows a live value, a dash if the call failed, or a skeleton while it loads.
const pick = (state, fn) => (state.data ? fn(state.data) : state.error ? '–' : undefined)

function Fact({ value, label }) {
  return (
    <div className="number">
      <strong>{value ?? <Skeleton width={56} height={30} />}</strong>
      <span>{label}</span>
    </div>
  )
}

export default function Landing() {
  const { email } = useAuth()
  const cta = email ? '/app/targets' : '/login'
  const [scrolled, setScrolled] = useState(false)

  const owasp = useAsync(() => api.get('/owasp').then((r) => r.data), [])
  const config = useAsync(() => api.get('/config').then((r) => r.data), [])
  const health = useAsync(() => api.get('/health').then((r) => r.data), [])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const apiStatus = health.error ? (
    <Badge tone="danger" dot>API offline</Badge>
  ) : health.data ? (
    <Badge tone="safe" dot>API online</Badge>
  ) : (
    <Skeleton width={90} height={14} />
  )

  return (
    <div className="landing">
      <header className={`l-nav${scrolled ? ' scrolled' : ''}`}>
        <div className="l-wrap l-nav-inner">
          <Link to="/" className="brand" aria-label="APISentry home">
            <BrandMark />
            <span>APISentry</span>
          </Link>
          <nav className="l-nav-links" aria-label="Page sections">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
          </nav>
          <Button as={Link} to={cta} variant="primary" size="sm" iconRight={ArrowRight}>
            {email ? 'Open app' : 'Sign in'}
          </Button>
        </div>
      </header>

      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-layer hero-grid" aria-hidden="true" />
        <div className="hero-layer hero-orbs" aria-hidden="true">
          <span className="orb orb-a" />
          <span className="orb orb-b" />
        </div>
        <div className="hero-layer" aria-hidden="true">
          <div className="hero-visual" style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)' }}>
            <HeroVisual />
          </div>
        </div>

        <div className="l-wrap hero-inner">
          <div className="hero-copy">
            <SlideUp>
              <span className="eyebrow">
                <span className="pulse" aria-hidden="true" />
                Security testing for payment APIs
              </span>
            </SlideUp>
            <SlideUp delay={0.08}>
              <h1 id="hero-title">
                Find API vulnerabilities <span className="text-grad">before</span> you deploy.
              </h1>
            </SlideUp>
            <SlideUp delay={0.16}>
              <p className="hero-sub">
                APISentry imports your REST API spec, runs the OWASP API Top 10 plus AI-generated business-logic tests,
                then gives developers a security score and a clear fix for every finding.
              </p>
            </SlideUp>
            <SlideUp delay={0.24}>
              <div className="row" style={{ marginTop: 32, gap: 12, flexWrap: 'wrap' }}>
                <MagneticButton>
                  <Button as={Link} to={cta} variant="primary" size="lg" iconRight={ArrowRight}>
                    {email ? 'Open app' : 'Start scanning'}
                  </Button>
                </MagneticButton>
                <Button as="a" href="#features" variant="ghost" size="lg">
                  See features
                </Button>
              </div>
            </SlideUp>
            <div className="hero-meta">
              {apiStatus}
              <span>
                <ShieldCheck size={14} aria-hidden="true" />
                {owasp.data ? `${owasp.data.top10.length} OWASP API Top 10 categories` : <Skeleton width={180} height={14} />}
              </span>
              <span>
                Scans limited to{' '}
                {config.data ? config.data.scope_allowlist.join(', ') : <Skeleton width={120} height={14} />}
              </span>
            </div>
          </div>
        </div>
        <div className="scroll-cue" aria-hidden="true">
          <span />
        </div>
      </section>

      <div className="signals">
        {owasp.data ? (
          <Marquee label="OWASP API Top 10 categories" speed={48}>
            {owasp.data.top10.map((c) => (
              <span key={c.id} className="signal">
                {c.id} · {c.name}
              </span>
            ))}
          </Marquee>
        ) : (
          <div className="l-wrap" style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            {owasp.error ? (
              <span className="faint">Could not load the OWASP categories from the API.</span>
            ) : (
              [0, 1, 2].map((i) => <Skeleton key={i} width={220} height={32} radius={999} />)
            )}
          </div>
        )}
      </div>

      <section id="features" className="l-section">
        <div className="l-wrap">
          <Reveal className="section-head">
            <span className="eyebrow">Features</span>
            <h2>Everything a developer needs before a release.</h2>
          </Reveal>
          <Stagger className="feature-cards" inView>
            {FEATURES.map((f) => (
              <Card key={f.title} as="article" className="feature-card">
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

      <section className="numbers" aria-label="Key facts">
        <div className="l-wrap numbers-grid">
          <Fact value={pick(owasp, (d) => d.top10.length)} label="OWASP API Top 10 categories" />
          <Fact value={pick(owasp, (d) => Object.keys(d.severity_weights).length)} label="Severity levels" />
          <Fact value={pick(config, (d) => d.scope_allowlist.length)} label="Hosts allowed by default" />
          <Fact value="2" label="Report formats (HTML and PDF)" />
          <Fact value="0–100" label="Security score with a letter grade" />
        </div>
      </section>

      <section id="how" className="l-section">
        <div className="l-wrap">
          <Reveal className="section-head">
            <span className="eyebrow">How it works</span>
            <h2>From spec to score in one scan.</h2>
          </Reveal>
          <Stagger className="grid-4" inView>
            {STEPS.map((s) => (
              <Card key={s.n} as="article" className="feature-card">
                <span className="how-num">{s.n}</span>
                <h3 style={{ marginTop: 10 }}>{s.title}</h3>
                <p>{s.body}</p>
              </Card>
            ))}
          </Stagger>
        </div>
      </section>

      <section className="l-section" style={{ paddingTop: 0 }}>
        <div className="l-wrap">
          <Reveal>
            <div className="cta-card">
              <div className="cta-glow" aria-hidden="true" />
              <h2>Scan your staging API before it ships.</h2>
              <p>Only allow-listed hosts can be scanned, and each scan asks you to confirm you are authorised first.</p>
              <div className="row" style={{ justifyContent: 'center', marginTop: 28 }}>
                <Button as={Link} to={cta} variant="primary" size="lg" iconRight={ArrowRight}>
                  {email ? 'Open app' : 'Sign in'}
                </Button>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <footer className="l-footer">
        <div className="l-wrap l-footer-inner">
          <div className="brand">
            <BrandMark />
            <span>APISentry</span>
          </div>
          <nav className="l-footer-links" aria-label="Footer">
            <a href="#features">Features</a>
            <Link to={cta}>{email ? 'Open app' : 'Sign in'}</Link>
          </nav>
        </div>
        <div className="l-wrap l-footer-base faint" style={{ marginTop: 24 }}>
          Scans run only against allow-listed hosts. Only test systems you own or have permission to test.
        </div>
      </footer>
    </div>
  )
}
