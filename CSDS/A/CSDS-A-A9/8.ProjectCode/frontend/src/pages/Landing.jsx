import { useEffect } from 'react'
import { ArrowRight, Eraser, Fingerprint, Network, ScrollText, ShieldCheck, Sparkles, Waves } from 'lucide-react'
import { Badge, Brand, Button, Container, ThemeToggle } from '../components/ui'
import { FadeIn, Marquee, MagneticButton, Reveal, SlideUp, Stagger, CountUp } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'
import { useLab } from '../lib/lab'
import { fmtNum } from '../lib/format'

const STEPS = [
  { icon: Network, tone: 'var(--lavender)', title: 'Federated training', text: 'Isolated clients train locally. Each update is L2-clipped before the coordinator sees it.' },
  { icon: Waves, tone: 'var(--sky)', title: 'Noisy aggregation', text: 'Gaussian noise gives a one-shot (ε, δ) differential-privacy bound on the released model.' },
  { icon: Eraser, tone: 'var(--peach)', title: 'Parameter-level unlearning', text: "A client's tracked update is subtracted and the retained clients are renormalised. No full retraining." },
  { icon: Fingerprint, tone: 'var(--mint)', title: 'Independent verification', text: 'Compared with a clean retained-only recomputation, then tested with a membership-inference attack.' },
  { icon: ScrollText, tone: 'var(--rose)', title: 'Tamper-evident audit', text: 'Every event is hash-chained with SHA-256 so edits to the ledger are detected.' },
]

const FEATURES = [
  { icon: Network, tone: 'var(--mint)', title: 'Federated training', text: 'Train the global model, see per-client clipped updates, epsilon, perplexity and accuracy.', to: '/app/training' },
  { icon: Eraser, tone: 'var(--peach)', title: 'Certified unlearning', text: 'Remove a client and get a downloadable certificate with residual influence and utility retained.', to: '/app/unlearning' },
  { icon: Sparkles, tone: 'var(--sky)', title: 'Model explorer', text: 'Sample the character language model before and after a deletion request.', to: '/app/explorer' },
  { icon: ScrollText, tone: 'var(--rose)', title: 'Compliance audit', text: 'Browse the hash-chained ledger and verify its integrity with one click.', to: '/app/audit' },
]

const TAGS = ['Federated learning', 'Differential privacy', 'Gradient clipping', 'Gaussian mechanism', 'Membership inference', 'Hash-chained audit', 'Right to be forgotten', 'Utility retention']

function LivePanel() {
  const { state, error } = useLab()
  const m = state?.metrics
  const rows = state
    ? [
        ['Session', state.trained ? 'Model trained' : 'Not trained yet'],
        ['Active clients', m ? `${m.active_clients} of ${state.contributions.length}` : `${state.contributions.length} registered`],
        ['Domains', [...new Set(state.contributions.map((c) => c.domain))].join(', ')],
        ['Audit ledger', state.audit.valid ? `${state.audit.records.length} record(s), chain valid` : 'Chain broken'],
      ]
    : null
  return (
    <div className="hero-card" style={{ padding: '48px 22px 84px' }}>
      <div className="row between" style={{ marginBottom: 14 }}>
        <strong style={{ fontFamily: 'var(--font-display)' }}>Live lab status</strong>
        <Badge tone={error ? 'rose' : state ? 'mint' : 'neutral'} dot>
          {error ? 'API offline' : state ? 'Connected' : 'Connecting'}
        </Badge>
      </div>
      {rows ? (
        <dl className="kv">
          {rows.map(([k, v]) => (
            <div key={k} style={{ display: 'contents' }}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="muted small">{error ? 'Start the API with run.bat to see live status.' : 'Checking the API…'}</p>
      )}
      <div className="hero-float b">
        <ShieldCheck size={22} aria-hidden="true" />
        <div>
          <b>{m ? `ε ${fmtNum(m.epsilon, 3)}` : 'ε · δ'}</b>
          <span>{m ? `δ = ${m.delta}` : 'DP guarantee'}</span>
        </div>
      </div>
      <div className="hero-float a" style={{ bottom: -24 }}>
        <Fingerprint size={22} aria-hidden="true" />
        <div>
          <b>SHA-256</b>
          <span>Hash-chained ledger</span>
        </div>
      </div>
    </div>
  )
}

export default function Landing() {
  const { state } = useLab()
  useEffect(() => {
    document.title = 'ForgetSafe · Certified right to be forgotten'
  }, [])
  return (
    <div className="landing">
      <a className="skip-link" href="#content">
        Skip to content
      </a>
      <header className="l-nav">
        <Container>
          <Brand />
          <nav className="l-nav-links" aria-label="Sections">
            <a href="#how">How it works</a>
            <a href="#screens">Screens</a>
            <a href="#live">Live</a>
          </nav>
          <span style={{ flex: 1 }} />
          <ThemeToggle />
          <Button to="/app" className="btn-open-app" iconRight={ArrowRight}>
            <span>Open the lab</span>
          </Button>
        </Container>
      </header>

      <main id="content">
        <section className="hero">
          <Blobs preset="hero" />
          <Container>
            <div className="hero-grid">
              <div>
                <FadeIn>
                  <Badge tone="lavender" icon={ShieldCheck}>
                    Federated LLM unlearning
                  </Badge>
                </FadeIn>
                <SlideUp delay={0.05}>
                  <h1 style={{ marginTop: 18 }}>
                    Forget a client, <span className="hl">prove it</span>, keep the model useful.
                  </h1>
                </SlideUp>
                <SlideUp delay={0.12}>
                  <p className="hero-lead">
                    ForgetSafe removes a client's contribution from a federated language model without full retraining, verifies the result against a clean recomputation, and records a tamper-evident certificate.
                  </p>
                </SlideUp>
                <SlideUp delay={0.18}>
                  <div className="hero-cta">
                    <MagneticButton>
                      <Button to="/app" size="lg" iconRight={ArrowRight}>
                        Open the lab
                      </Button>
                    </MagneticButton>
                    <Button to="/app/training" size="lg" variant="secondary" icon={Network}>
                      Train a model
                    </Button>
                  </div>
                </SlideUp>
                <div className="hero-note">
                  <Badge tone="mint">Differential privacy</Badge>
                  <Badge tone="sky">Membership-inference check</Badge>
                  <Badge tone="peach">Audit trail</Badge>
                </div>
              </div>
              <SlideUp delay={0.15} className="hero-visual">
                <LivePanel />
              </SlideUp>
            </div>
          </Container>
        </section>

        <section className="section" id="how">
          <Container>
            <Reveal>
              <div className="section-head">
                <Badge tone="sky">How it works</Badge>
                <h2>From training to a signed-off deletion</h2>
                <p>Five stages, each visible in the app and each backed by the real engine.</p>
              </div>
            </Reveal>
            <div className="steps-line" aria-hidden="true">
              <div />
            </div>
            <Stagger className="steps" inView>
              {STEPS.map((s, i) => (
                <Stagger.Item key={s.title} className="step-card">
                  <span className="n">0{i + 1}</span>
                  <span className="ico" style={{ background: s.tone }}>
                    <s.icon size={24} aria-hidden="true" />
                  </span>
                  <h3>{s.title}</h3>
                  <p>{s.text}</p>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="screens">
          <Container>
            <Reveal>
              <div className="section-head">
                <Badge tone="peach">Inside the lab</Badge>
                <h2>Four screens, one workflow</h2>
              </div>
            </Reveal>
            <Stagger className="features" inView style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 235px), 1fr))' }}>
              {FEATURES.map((f) => (
                <Stagger.Item key={f.title} className="feature">
                  <span className="ico" style={{ background: f.tone }}>
                    <f.icon size={26} aria-hidden="true" />
                  </span>
                  <h3>{f.title}</h3>
                  <p>{f.text}</p>
                  <div className="where">
                    <Button to={f.to} variant="ghost" size="sm" iconRight={ArrowRight}>
                      Open
                    </Button>
                  </div>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="live">
          <Container>
            <Reveal>
              <div className="stats-strip">
                <div className="s">
                  <b>{state ? <CountUp value={state.contributions.length} /> : '–'}</b>
                  <span>Federated clients</span>
                </div>
                <div className="s">
                  <b>{state ? <CountUp value={new Set(state.contributions.map((c) => c.domain)).size} /> : '–'}</b>
                  <span>Data domains</span>
                </div>
                <div className="s">
                  <b>{state ? <CountUp value={state.audit.records.length} /> : '–'}</b>
                  <span>Audit records</span>
                </div>
                <div className="s">
                  <b>{state ? (state.audit.valid ? 'Valid' : 'Broken') : '–'}</b>
                  <span>Hash chain</span>
                </div>
              </div>
            </Reveal>
            <div style={{ marginTop: 32 }}>
              <Marquee>
                {TAGS.map((t) => (
                  <span key={t} className="chip">
                    <ShieldCheck size={15} aria-hidden="true" /> {t}
                  </span>
                ))}
              </Marquee>
            </div>
          </Container>
        </section>

        <section className="section">
          <Container>
            <Reveal>
              <div className="cta">
                <Blobs preset="cta" />
                <h2>Ready to exercise the right to be forgotten?</h2>
                <p>Train the demonstrator, remove a client, and download the certificate in under a minute.</p>
                <MagneticButton>
                  <Button to="/app" size="lg" variant="mint" iconRight={ArrowRight}>
                    Open the lab
                  </Button>
                </MagneticButton>
              </div>
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="footer">
        <Container>
          <span>ForgetSafe · Privacy-preserving machine unlearning in federated LLMs</span>
          <span>A research demonstrator, not a legal compliance product.</span>
        </Container>
      </footer>
    </div>
  )
}
