import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Lenis from 'lenis'
import { motion } from 'framer-motion'
import { ArrowRight, BarChart3, Layers, Network, Radar, ScanSearch, ShieldCheck, Sparkles, Users } from 'lucide-react'
import { Brand, Button, Container, ThemeToggle } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'
import { useAuth } from '../lib/auth'
import { api } from '../lib/api'
import { fmtInt } from '../lib/format'

const FEATURES = [
  { icon: Network, tone: 'var(--sky)', title: 'A graph, not a list', text: 'Accounts become nodes and follows, likes and comments become edges, so the model sees who an account moves with.', where: 'Graph & features' },
  { icon: ScanSearch, tone: 'var(--mint)', title: 'A score with reasons', text: 'Every account gets a fake-probability, the profile and behaviour traits behind it, and a map of its neighbourhood.', where: 'Accounts' },
  { icon: Radar, tone: 'var(--rose)', title: 'Botnets surface as clusters', text: 'Community detection over the learned embeddings groups coordinated accounts, with their size, shared posting hour and tie density.', where: 'Botnet clusters' },
  { icon: ShieldCheck, tone: 'var(--lavender)', title: 'Moderators stay in charge', text: 'Confirm or dismiss an account or a whole cluster. Decisions are logged and feed the next training run.', where: 'Moderator queue' },
  { icon: BarChart3, tone: 'var(--peach)', title: 'Three architectures, compared', text: 'GCN, GAT and GraphSAGE against a feature-only baseline on the same split, with precision, recall and F1.', where: 'Models & scale' },
  { icon: Layers, tone: 'var(--butter)', title: 'Scale measured, not assumed', text: 'Training and inference time are charted as the graph grows from thousands to tens of thousands of accounts.', where: 'Models & scale' },
]

const STEPS = [
  { icon: Network, tone: 'var(--sky)', title: 'Build the graph', text: 'Real social topology plus labelled profile and posting data become one graph.' },
  { icon: Layers, tone: 'var(--lavender)', title: 'Engineer features', text: 'Profile metadata, posting behaviour, timing and interaction frequency per account.' },
  { icon: Sparkles, tone: 'var(--mint)', title: 'Train and compare', text: 'GCN, GAT and GraphSAGE learn from neighbourhoods; a no-graph model is the yardstick.' },
  { icon: Radar, tone: 'var(--peach)', title: 'Find botnets', text: 'Louvain communities over the embeddings expose coordinated groups.' },
  { icon: ShieldCheck, tone: 'var(--rose)', title: 'Review and learn', text: 'Moderator decisions are logged and used when the model is retrained.' },
]

const CAPS = ['GCN', 'GAT', 'GraphSAGE', 'Message passing', 'Sparse tensors', 'Louvain communities', 'Embedding similarity', 'Class-weighted loss', 'Precision', 'Recall', 'F1-score', 'ROC-AUC', 'PR-AUC', 'Gradient x input', 'Scalability sweep', 'Moderator feedback']

function Illustration() {
  // A schematic of the idea: a tight coordinated cluster (rose) pushing into an ordinary network (mint / sky).
  const bots = [[96, 74], [132, 52], [160, 88], [124, 112], [88, 118], [174, 56]]
  const humans = [[250, 60], [286, 104], [240, 138], [210, 172], [300, 160], [60, 168], [36, 100], [190, 30]]
  const links = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0], [0, 3], [1, 3], [1, 5], [5, 2]]
  const out = [[2, 0], [5, 7], [3, 2], [4, 5], [0, 6]]
  return (
    <svg viewBox="0 0 340 200" role="img" aria-label="Illustration: a tightly connected group of fake accounts reaching into a network of ordinary accounts" width="100%">
      {humans.map((h, i) => humans.slice(i + 1, i + 3).map((g, j) => <line key={`h${i}-${j}`} x1={h[0]} y1={h[1]} x2={g[0]} y2={g[1]} stroke="var(--border-strong)" strokeWidth="1.4" />))}
      {out.map(([b, h]) => (
        <line key={`o${b}-${h}`} x1={bots[b][0]} y1={bots[b][1]} x2={humans[h][0]} y2={humans[h][1]} stroke="var(--rose)" strokeWidth="1.6" strokeDasharray="4 4" />
      ))}
      {links.map(([a, b]) => (
        <line key={`b${a}-${b}`} x1={bots[a][0]} y1={bots[a][1]} x2={bots[b][0]} y2={bots[b][1]} stroke="var(--rose)" strokeWidth="2" />
      ))}
      {humans.map((h, i) => (
        <circle key={`hn${i}`} cx={h[0]} cy={h[1]} r="8" fill={i % 2 ? 'var(--sky)' : 'var(--mint)'} stroke="var(--surface)" strokeWidth="2.5" />
      ))}
      {bots.map((b, i) => (
        <motion.circle key={`bn${i}`} cx={b[0]} cy={b[1]} r="10" fill="var(--rose)" stroke="var(--surface)" strokeWidth="3" animate={{ scale: [1, 1.12, 1] }} transition={{ duration: 3 + i * 0.4, repeat: Infinity, ease: 'easeInOut' }} style={{ transformBox: 'fill-box', transformOrigin: 'center' }} />
      ))}
    </svg>
  )
}

export default function Landing() {
  const { user } = useAuth()
  const [facts, setFacts] = useState(null)

  useEffect(() => {
    document.title = 'BotGraph · Fake-account and botnet detection'
    let alive = true
    api.health().then((d) => alive && setFacts(d)).catch(() => {})
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return () => { alive = false }
    const lenis = new Lenis({ lerp: 0.12 })
    let raf
    const loop = (t) => {
      lenis.raf(t)
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => {
      alive = false
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
                    <Sparkles size={14} aria-hidden="true" /> Graph neural networks for trust and safety
                  </span>
                </SlideUp>
                <SlideUp delay={0.08}>
                  <h1 style={{ marginTop: 18 }}>
                    Fake accounts hide alone. <span className="hl">Botnets</span> can&apos;t hide together.
                  </h1>
                </SlideUp>
                <SlideUp delay={0.16}>
                  <p className="hero-lead">
                    BotGraph scores every account from its relational context, then groups coordinated accounts into botnet clusters your moderators can review, confirm or dismiss.
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
                  <span className="badge mint">GCN · GAT · GraphSAGE</span>
                  <span className="badge lavender">Runs locally</span>
                  <span className="badge sky">Moderator in the loop</span>
                </SlideUp>
              </div>

              <SlideUp delay={0.2} className="hero-visual">
                <div className="hero-card">
                  <p className="tiny muted" style={{ marginBottom: 6 }}>
                    Schematic illustration
                  </p>
                  <Illustration />
                </div>
                {facts && (
                  <>
                    <div className="hero-float a">
                      <Users size={22} aria-hidden="true" />
                      <div>
                        <b>{fmtInt(facts.accounts)}</b>
                        <span>accounts in the graph</span>
                      </div>
                    </div>
                    <div className="hero-float b">
                      <Radar size={22} aria-hidden="true" />
                      <div>
                        <b>{facts.botnets} botnets</b>
                        <span>found by clustering</span>
                      </div>
                    </div>
                  </>
                )}
              </SlideUp>
            </div>
          </Container>
        </section>

        <section className="section" id="features">
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">What you get</span>
              <h2>From a single suspicious profile to a whole network</h2>
              <p>Seven workspaces covering the full path: graph, scores, clusters, review, evaluation.</p>
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
              <h2>Five steps from raw data to a reviewed botnet</h2>
              <p>Everything below is already run for you: sign in and the results are waiting.</p>
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
              <h2>Measured, not promised</h2>
              <p>These numbers are read live from the running service.</p>
            </Reveal>
            {facts ? (
              <Reveal>
                <div className="stats-strip">
                  <div className="s">
                    <b>
                      <CountUp value={facts.accounts} duration={1.2} />
                    </b>
                    <span>Accounts scored</span>
                  </div>
                  <div className="s">
                    <b>
                      <CountUp value={facts.edges} duration={1.2} />
                    </b>
                    <span>Ties between them</span>
                  </div>
                  <div className="s">
                    <b>
                      <CountUp value={(facts.best_f1 ?? 0) * 100} duration={1.2} format={(v) => `${v.toFixed(1)}%`} />
                    </b>
                    <span>F1 of {facts.model}</span>
                  </div>
                  <div className="s">
                    <b>
                      <CountUp value={(facts.baseline_f1 ?? 0) * 100} duration={1.2} format={(v) => `${v.toFixed(1)}%`} />
                    </b>
                    <span>F1 without the graph</span>
                  </div>
                </div>
              </Reveal>
            ) : (
              <p className="muted" style={{ textAlign: 'center' }}>
                Start the API (run.bat) to see live numbers here.
              </p>
            )}
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
                <h2>See a botnet get caught</h2>
                <p>Sign in with a demo account, open the top-scored account and follow its neighbourhood into a cluster.</p>
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
          <span>BotGraph · graph-based fake-profile and botnet detection. Graph topology and profile rows are real public datasets; injected botnets and timing features are seeded synthetic data.</span>
          <Link to="/login" className="link-cell">
            Sign in
          </Link>
        </Container>
      </footer>
    </div>
  )
}
