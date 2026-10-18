import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import Lenis from 'lenis'
import {
  ArrowRight,
  BrainCircuit,
  FlaskConical,
  Lightbulb,
  Package,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Target,
  Upload,
  UserSearch,
} from 'lucide-react'
import { Brand, Button, Container, ThemeToggle } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'
import { useAuth } from '../lib/auth'

const FEATURES = [
  { icon: Target, tone: 'var(--lavender)', title: 'Who and how likely', text: 'Churn probability from 0 to 100% for every customer, from Logistic Regression, Decision Tree, Random Forest and boosting models you compare side by side.', where: 'Model training · Evaluation' },
  { icon: Sparkles, tone: 'var(--mint)', title: 'Why they might leave', text: 'Global drivers across the whole base and a local explanation for each customer, with SHAP when installed and a safe fallback when it is not.', where: 'Explainable AI · Customer 360' },
  { icon: ShieldAlert, tone: 'var(--rose)', title: 'Risk bands you control', text: 'Low, Medium, High and Critical bands with thresholds you set yourself, a filterable at-risk table and one-click CSV export.', where: 'Customer risk' },
  { icon: FlaskConical, tone: 'var(--sky)', title: 'What-if scenarios', text: 'Change a contract, a charge or a tenure and watch the predicted probability move. Clearly labelled as model-based, never a promise.', where: 'What-if' },
  { icon: Lightbulb, tone: 'var(--butter)', title: 'Suggested actions', text: 'Plain IF/THEN retention rules turn risk into next steps your team can read, challenge and explain. No external AI service involved.', where: 'Retention actions' },
  { icon: Package, tone: 'var(--peach)', title: 'Batch and monitoring', text: 'Score a new CSV in one go, then check it for drift, unseen categories and missing columns before trusting the numbers.', where: 'Batch · Monitoring' },
]

const STEPS = [
  { icon: Upload, tone: 'var(--mint)', title: 'Load data', text: 'Upload a customer CSV or start from the built-in sample. Columns are detected for you.' },
  { icon: BrainCircuit, tone: 'var(--lavender)', title: 'Train and compare', text: 'Pick imbalance handling and models. The best one is chosen on F1, not accuracy alone.' },
  { icon: ShieldAlert, tone: 'var(--rose)', title: 'Score and segment', text: 'Every customer lands in a risk band with a probability you can sort and filter.' },
  { icon: UserSearch, tone: 'var(--sky)', title: 'Explain', text: 'See the factors pushing each customer toward or away from churn.' },
  { icon: Lightbulb, tone: 'var(--peach)', title: 'Act', text: 'Review suggested retention actions and test them with what-if scenarios.' },
]

const CAPS = ['Logistic Regression', 'Decision Tree', 'Random Forest', 'Gradient Boosting', 'Hist Gradient Boosting', 'SMOTE', 'Class weights', 'ROC-AUC', 'Precision-Recall', 'F1-score', 'Permutation importance', 'SHAP', 'Risk segmentation', 'What-if analysis', 'Batch scoring', 'Drift check']

const FACTS = [
  { value: 13, label: 'Workspaces in one app' },
  { value: 5, label: 'Model families to compare' },
  { value: 4, label: 'Configurable risk bands' },
  { value: 0, label: 'External AI services called' },
]

export default function Landing() {
  const { user } = useAuth()

  useEffect(() => {
    document.title = 'ChurnIQ · Explainable churn prediction for telecom'
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
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
  }, [])

  return (
    <div className="landing">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="l-nav">
        <Container>
          <Brand />
          <nav className="l-nav-links" aria-label="Sections">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#stack">Under the hood</a>
          </nav>
          <div className="row-end">
            <ThemeToggle />
            {user ? (
              <Button to="/app" className="btn-open-app" iconRight={ArrowRight}>
                <span>Open app</span>
              </Button>
            ) : (
              <>
                <Button to="/login" variant="ghost">
                  Sign in
                </Button>
                <Button to="/login" className="btn-open-app" iconRight={ArrowRight}>
                  <span>Try the demo</span>
                </Button>
              </>
            )}
          </div>
        </Container>
      </header>

      <main id="main">
        <section className="hero">
          <Blobs preset="hero" />
          <Container>
            <div className="hero-grid">
              <div>
                <SlideUp>
                  <span className="eyebrow">
                    <Sparkles size={14} aria-hidden="true" /> Explainable AI for telecom retention
                  </span>
                </SlideUp>
                <SlideUp delay={0.08}>
                  <h1 style={{ marginTop: 18 }}>
                    Know who is about to leave, <span className="hl">why</span>, and what to do next.
                  </h1>
                </SlideUp>
                <SlideUp delay={0.16}>
                  <p className="hero-lead">
                    ChurnIQ turns a customer file into churn probabilities, plain-language reasons and suggested retention actions. Train, compare, explain and simulate, all on your own machine.
                  </p>
                </SlideUp>
                <SlideUp delay={0.24} className="hero-cta">
                  <MagneticButton>
                    <Button to={user ? '/app' : '/login'} size="lg" iconRight={ArrowRight}>
                      {user ? 'Open the app' : 'Try the live demo'}
                    </Button>
                  </MagneticButton>
                  <a className="btn secondary lg" href="#how">
                    See how it works
                  </a>
                </SlideUp>
                <SlideUp delay={0.32} className="hero-note">
                  <span className="badge mint">Runs locally</span>
                  <span className="badge lavender">No paid APIs</span>
                  <span className="badge sky">SHAP-ready</span>
                </SlideUp>
              </div>

              <SlideUp delay={0.2} className="hero-visual">
                <div className="hero-card" aria-hidden="true">
                  <div className="hero-pipeline">
                    {[
                      { i: Target, c: 'var(--lavender)', t: 'Predict', s: 'Probability for every customer' },
                      { i: Sparkles, c: 'var(--mint)', t: 'Explain', s: 'Drivers and protective factors' },
                      { i: ShieldAlert, c: 'var(--rose)', t: 'Segment', s: 'Low · Medium · High · Critical' },
                      { i: FlaskConical, c: 'var(--sky)', t: 'Simulate', s: 'What if the contract changed?' },
                      { i: Lightbulb, c: 'var(--butter)', t: 'Recommend', s: 'Readable retention actions' },
                    ].map((p) => (
                      <div className="pipe" key={p.t}>
                        <span className="ico" style={{ background: p.c }}>
                          <p.i size={20} />
                        </span>
                        <div>
                          <b>{p.t}</b>
                          <span>{p.s}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="hero-float a" aria-hidden="true">
                  <ShieldCheck size={22} />
                  <div>
                    <b>100% local</b>
                    <span>your data stays put</span>
                  </div>
                </div>
                <div className="hero-float b" aria-hidden="true">
                  <Stethoscope size={22} />
                  <div>
                    <b>Drift checks</b>
                    <span>before you trust it</span>
                  </div>
                </div>
              </SlideUp>
            </div>
          </Container>
        </section>

        <section className="section" id="features">
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">What you get</span>
              <h2>Four questions, answered in one place</h2>
              <p>Who will churn, how likely, why, and what could be done about it.</p>
            </Reveal>
            <Stagger className="features" inView>
              {FEATURES.map((f) => (
                <Stagger.Item key={f.title}>
                  <article className="feature">
                    <span className="ico" style={{ background: f.tone }}>
                      <f.icon size={24} aria-hidden="true" />
                    </span>
                    <h3>{f.title}</h3>
                    <p>{f.text}</p>
                    <div className="where">
                      <span className="badge neutral">{f.where}</span>
                    </div>
                  </article>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="how" style={{ background: 'var(--bg-tint)' }}>
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">How it works</span>
              <h2>From a CSV to a retention plan in five steps</h2>
              <p>The Quick start button on the dashboard runs steps one to three for you with sample data.</p>
            </Reveal>
            <Reveal>
              <div className="steps-line" aria-hidden="true">
                <div />
              </div>
            </Reveal>
            <Stagger className="steps" inView>
              {STEPS.map((s, i) => (
                <Stagger.Item key={s.title}>
                  <article className="step-card">
                    <span className="n">STEP {i + 1}</span>
                    <span className="ico" style={{ background: s.tone }}>
                      <s.icon size={24} aria-hidden="true" />
                    </span>
                    <h3>{s.title}</h3>
                    <p>{s.text}</p>
                  </article>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="stack">
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">Under the hood</span>
              <h2>Honest, local and inspectable</h2>
              <p>Everything below is real and ships in this project.</p>
            </Reveal>
            <Reveal>
              <div className="stats-strip">
                {FACTS.map((f) => (
                  <div className="s" key={f.label}>
                    <b>
                      <CountUp value={f.value} duration={1.2} />
                    </b>
                    <span>{f.label}</span>
                  </div>
                ))}
              </div>
            </Reveal>
            <Reveal delay={0.1} style={{ marginTop: 28 }}>
              <Marquee speed={46}>
                {CAPS.map((c) => (
                  <span className="chip" key={c}>
                    {c}
                  </span>
                ))}
              </Marquee>
            </Reveal>
          </Container>
        </section>

        <section className="section" style={{ paddingTop: 0 }}>
          <Container>
            <Reveal>
              <div className="cta">
                <Blobs preset="cta" />
                <h2>See your own retention story</h2>
                <p>Sign in with the demo account, press Quick start and have a trained, explained model in seconds.</p>
                <MagneticButton>
                  <Button to={user ? '/app' : '/login'} size="lg" variant="primary" iconRight={ArrowRight}>
                    {user ? 'Open the app' : 'Try the live demo'}
                  </Button>
                </MagneticButton>
              </div>
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="footer">
        <Container>
          <span>
            ChurnIQ · Explainable AI-Based Customer Churn Prediction and Intelligent Retention System. Base paper: <em>Explaining Customer Churn Through Unified Perturbation-Based XAI Soft Computing</em>, IEEE Access, 2026 (DOI 10.1109/ACCESS.2026.3663648).
          </span>
          <Link to="/login" className="link-cell">
            Sign in
          </Link>
        </Container>
      </footer>
    </div>
  )
}
