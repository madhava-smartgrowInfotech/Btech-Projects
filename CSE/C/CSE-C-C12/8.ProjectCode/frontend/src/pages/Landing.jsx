import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Database, FileSearch, Lock, ShieldAlert, Stethoscope, Zap } from 'lucide-react'
import { Button, Card, Container } from '../components/ui'
import { CountUp, InkRule, MagneticButton, MaskHeadline, Marquee, Reveal, Stagger } from '../components/motion'
import { aboutApi } from '../lib/api'
import { useAuth } from '../lib/auth'

const STEPS = [
  ['Describe', 'Type your symptoms in your own words - no forms, no medical vocabulary needed.'],
  ['Retrieve', 'A hybrid FAISS + BM25 search over the knowledge base, reranked by a cross-encoder.'],
  ['Review', 'Get a grounded answer, possible conditions with evidence, and clear safety advice.'],
]

const FEATURES = [
  [FileSearch, 'Evidence, not guesses', 'Every answer lists the matching knowledge-base records with symptoms, guidance and a relevance score.'],
  [ShieldAlert, 'Safety escalation', 'Rule-based emergency detection puts urgent-care advice above everything else.'],
  [Lock, 'Private by design', 'Local SQLite storage, per-user history, deletion on demand, no trackers.'],
  [Stethoscope, 'Consultation history', 'Search, reopen and delete past consultations whenever you like.'],
]

export default function Landing() {
  const { user } = useAuth()
  const [m, setM] = useState(null)

  useEffect(() => {
    document.title = 'CareLens AI - Symptom Tracking Assistant'
    let alive = true
    aboutApi
      .metrics()
      .then((d) => alive && setM(d))
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [])

  const ticker = m
    ? [
        { label: 'Conditions covered', value: m.kb_conditions },
        { label: 'Knowledge records', value: m.kb_records },
        { label: 'Top-3 accuracy', value: `${Math.round(m.top3_accuracy * 100)}%` },
        { label: 'Mean latency', value: `${Math.round(m.mean_latency_ms)} ms` },
        { label: 'Data stays', value: 'local' },
      ]
    : [
        { label: 'Hybrid retrieval', value: 'FAISS + BM25' },
        { label: 'Reranker', value: 'cross-encoder' },
        { label: 'Storage', value: 'local SQLite' },
        { label: 'Not a diagnosis', value: 'ever' },
      ]

  return (
    <>
      <div className="legal-strip">
        <Container>Preliminary health information only - not a medical diagnosis. In an emergency call your local emergency number.</Container>
      </div>

      <Container>
        <section className="hero" aria-label="Introduction">
          <span className="eyebrow">Hybrid RAG symptom tracking</span>
          <MaskHeadline className="display-xl hero-title" lines={['Know your', 'symptoms.']} />
          <div className="hero-grid">
            <div>
              <p className="lead hero-sub">
                Describe how you feel. <span className="hl">CareLens AI</span> searches a curated medical knowledge base, shows the evidence behind every
                answer, and tells you plainly when to seek care.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to={user ? '/assistant' : '/register'} iconRight={ArrowRight}>
                    {user ? 'Open the assistant' : 'Create free account'}
                  </Button>
                </MagneticButton>
                {!user && (
                  <Button size="lg" to="/login" icon={Zap}>
                    Try the demo login
                  </Button>
                )}
              </div>
            </div>
            <div className="checks-stack" aria-label="Product facts">
              <div>
                <div className="k">Retrieval</div>
                <div className="v">FAISS + BM25</div>
              </div>
              <div>
                <div className="k">Rerank</div>
                <div className="v">Cross-encoder</div>
              </div>
              <div>
                <div className="k">Storage</div>
                <div className="v">100% local</div>
              </div>
              <div>
                <div className="k">Safety</div>
                <div className="v">Rule-based</div>
              </div>
            </div>
          </div>
        </section>
      </Container>

      <Marquee items={ticker} label="CareLens AI facts" />

      <Container>
        <section className="section" aria-labelledby="how-h">
          <div className="section-head">
            <h2 id="how-h" className="display-lg">
              How it <span className="hl">works</span>
            </h2>
          </div>
          <InkRule thick />
          {STEPS.map(([t, d], i) => (
            <Reveal key={t} className="how-step" delay={i * 0.05}>
              <span className="how-num" aria-hidden="true">
                0{i + 1}
              </span>
              <div>
                <h3 className="display-sm">{t}</h3>
                <p className="muted" style={{ marginTop: 8, maxWidth: '60ch' }}>
                  {d}
                </p>
              </div>
            </Reveal>
          ))}
        </section>

        <section className="section" style={{ paddingTop: 0 }} aria-labelledby="feat-h">
          <div className="section-head">
            <h2 id="feat-h" className="display-lg">
              Built to be <span className="hl-coral">careful</span>
            </h2>
          </div>
          <Stagger className="grid grid-2">
            {FEATURES.map(([Icon, t, d]) => (
              <Card key={t} className="feature-card" hot>
                <div className="feature-icon">
                  <Icon size={26} aria-hidden="true" />
                </div>
                <h3 className="display-sm">{t}</h3>
                <p className="muted" style={{ marginTop: 8 }}>
                  {d}
                </p>
              </Card>
            ))}
          </Stagger>
        </section>

        {m && (
          <section className="section" style={{ paddingTop: 0 }} aria-labelledby="num-h">
            <div className="section-head">
              <h2 id="num-h" className="display-lg">
                The <span className="hl">numbers</span>
              </h2>
              <span className="small muted" style={{ maxWidth: '40ch' }}>
                Measured on held-out queries from the bundled synthetic knowledge base.
              </span>
            </div>
            <div className="stats-strip">
              <div className="stat">
                <span className="stat-label">Top-1 accuracy</span>
                <span className="stat-value">
                  <CountUp value={m.top1_accuracy * 100} decimals={0} suffix="%" />
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Conditions</span>
                <span className="stat-value">
                  <CountUp value={m.kb_conditions} />
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Records</span>
                <span className="stat-value">
                  <CountUp value={m.kb_records} />
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Latency (ms)</span>
                <span className="stat-value">
                  <CountUp value={m.mean_latency_ms} />
                </span>
              </div>
            </div>
          </section>
        )}

        <section className="section" style={{ paddingTop: 0 }}>
          <Reveal>
            <div className="cta-block stack" style={{ '--gap': '18px' }}>
              <h2 className="display-lg">Ready when you are.</h2>
              <p className="lead">Create an account in seconds, or jump straight in with the demo login - it comes with sample consultations.</p>
              <div className="row">
                <Button variant="secondary" size="lg" to={user ? '/assistant' : '/register'} iconRight={ArrowRight}>
                  {user ? 'Open the assistant' : 'Get started'}
                </Button>
                <Button size="lg" to="/about" icon={Database}>
                  See the metrics
                </Button>
              </div>
            </div>
          </Reveal>
        </section>
      </Container>

      <footer className="footer">
        <Container>
          <div className="footer-grid">
            <div>
              <h4>CareLens AI</h4>
              <p className="small">Local symptom monitoring with grounded, preliminary health guidance.</p>
            </div>
            <div>
              <h4>Explore</h4>
              <ul>
                <li>
                  <Link to="/about">About &amp; metrics</Link>
                </li>
                <li>
                  <Link to="/login">Sign in</Link>
                </li>
                <li>
                  <Link to="/register">Create account</Link>
                </li>
              </ul>
            </div>
            <div>
              <h4>Important</h4>
              <p className="small">Not a medical diagnosis. Consult a qualified healthcare professional. In an emergency seek immediate care.</p>
            </div>
          </div>
        </Container>
      </footer>
    </>
  )
}
