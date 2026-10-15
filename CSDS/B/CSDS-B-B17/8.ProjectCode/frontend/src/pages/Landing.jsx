import { useEffect, useState } from 'react'
import { ArrowRight, BarChart3, FileText, Gauge, HeartPulse, Mic, Tags } from 'lucide-react'
import api from '../api'
import { Badge, Button, Card, Container } from '../components/ui'
import { CountUp, InkRule, MagneticButton, MaskHeadline, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'

// Held-out evaluation figures from ml/train.py and ml/eval.py (see README "Evaluation results").
const EVAL = [
  { label: 'Intent accuracy', value: '99.8%' },
  { label: 'Intents', value: '27' },
  { label: 'Word error rate (real calls)', value: '4.7%' },
  { label: 'Speaker attribution', value: '100%' },
  { label: 'End-to-end intent (sample calls)', value: '80%' },
]

const FEATURES = [
  { icon: Mic, title: 'Every call, transcribed', text: 'Upload recordings in bulk or record from the microphone. faster-whisper transcribes on CPU and separates agent from customer.' },
  { icon: Tags, title: 'Intent, topic and keywords', text: 'A model trained on Bitext customer-support requests tags why the customer called and pulls out the key terms.' },
  { icon: HeartPulse, title: 'Emotion timeline', text: 'Text sentiment plus voice emotion per turn, drawn over the call, with escalation flags where it goes wrong.' },
  { icon: FileText, title: 'Summaries and action items', text: 'Gemini writes the reason for the call, the resolution and the follow-ups, so nobody has to listen back.' },
  { icon: Gauge, title: 'Agent scorecards', text: 'Greeting, empathy, talk and listen, silence, interruptions, resolution and sentiment change, each with its evidence.' },
  { icon: BarChart3, title: 'Live analytics', text: 'Volumes, top intents, sentiment trends and an agent leaderboard, with search across every transcript.' },
]

const STEPS = [
  ['01', 'Ingest', 'Upload files or record in the browser. Stereo is split by channel; mono gets a turn split.'],
  ['02', 'Transcribe', 'Timestamped transcript with agent and customer turns, produced on the CPU.'],
  ['03', 'Understand', 'Intent, topic, keywords, text sentiment and wav2vec2 voice emotion per turn.'],
  ['04', 'Score and summarise', 'A /100 agent scorecard with evidence, plus the Gemini summary and action items.'],
]

function useHealth() {
  const [state, setState] = useState({ status: 'loading' })
  useEffect(() => {
    let alive = true
    api
      .get('/health')
      .then((r) => alive && setState({ status: 'ok', ...r.data }))
      .catch(() => alive && setState({ status: 'down' }))
    return () => {
      alive = false
    }
  }, [])
  return state
}

export default function Landing() {
  const health = useHealth()
  const cell = (k, v) => (
    <div>
      <div className="k">{k}</div>
      <div className="v">{v}</div>
    </div>
  )
  return (
    <>
      <Container>
        <section className="hero">
          <div className="hero-grid">
            <div>
              <span className="eyebrow">Call intelligence for contact centres</span>
              <MaskHeadline as="h1" className="display-xl hero-title" lines={['Every call.', 'Analysed.']} />
              <p className="lead">
                CallSense turns call recordings into transcripts, intent, emotion, summaries and agent scorecards, so supervisors and QA teams see what
                customers feel <span className="hl">while it still matters</span>.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to="/login" iconRight={ArrowRight}>
                    Open the dashboard
                  </Button>
                </MagneticButton>
                <Button size="lg" href="#how">
                  How it works
                </Button>
              </div>
            </div>
            <SlideUp>
              <div className="checks-stack" aria-label="Service status">
                {cell('API', health.status === 'loading' ? '…' : health.status === 'ok' ? 'Online' : 'Offline')}
                {cell('Models', health.status === 'ok' ? (health.models_ready ? 'Ready' : 'Loading') : '—')}
                {cell('Gemini summaries', health.status === 'ok' ? (health.gemini_configured ? 'Configured' : 'No key') : '—')}
                {cell('Analysis queue', health.status === 'ok' ? `${health.queue} waiting` : '—')}
              </div>
              {health.status === 'down' && (
                <p className="small" style={{ marginTop: 12 }} role="status">
                  The API is not reachable. Start it with <code>run.bat</code>.
                </p>
              )}
            </SlideUp>
          </div>
        </section>
      </Container>

      <Marquee items={EVAL} variant="lime" label="Evaluation results" />

      <Container>
        <section className="section" aria-labelledby="features-h">
          <div className="section-head">
            <div>
              <span className="eyebrow">What it does</span>
              <h2 id="features-h" className="display-md" style={{ marginTop: 12 }}>
                Six things, no listening back.
              </h2>
            </div>
          </div>
          <Stagger className="feature-grid">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <Card key={title} hot className="feature-card" as="article">
                <div className="feature-icon" aria-hidden="true">
                  <Icon size={26} />
                </div>
                <h3 className="display-sm" style={{ marginBottom: 8 }}>
                  {title}
                </h3>
                <p className="muted">{text}</p>
              </Card>
            ))}
          </Stagger>
        </section>

        <InkRule thick />

        <section className="section" id="how" aria-labelledby="how-h">
          <div className="section-head">
            <div>
              <span className="eyebrow">The pipeline</span>
              <h2 id="how-h" className="display-md" style={{ marginTop: 12 }}>
                From audio to scorecard.
              </h2>
            </div>
          </div>
          <div>
            {STEPS.map(([n, t, d]) => (
              <Reveal key={n} className="how-step" y={28}>
                <span className="how-num" aria-hidden="true">
                  {n}
                </span>
                <div>
                  <h3 className="display-sm">{t}</h3>
                  <p className="muted" style={{ marginTop: 6, maxWidth: '60ch' }}>
                    {d}
                  </p>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="section" aria-labelledby="proof-h" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <span className="eyebrow">Measured, not promised</span>
              <h2 id="proof-h" className="display-md" style={{ marginTop: 12 }}>
                Held-out evaluation.
              </h2>
            </div>
            <Badge tone="info">from ml/train.py and ml/eval.py</Badge>
          </div>
          <div className="stats-strip">
            <div>
              <span className="stat-label">Intent accuracy</span>
              <div className="stat-value">
                <CountUp value={99.8} decimals={1} suffix="%" />
              </div>
              <p className="small muted">27 intents, 5,375 held-out utterances</p>
            </div>
            <div>
              <span className="stat-label">Word error rate</span>
              <div className="stat-value">
                <CountUp value={4.7} decimals={1} suffix="%" />
              </div>
              <p className="small muted">20 real call-centre recordings</p>
            </div>
            <div>
              <span className="stat-label">Speaker attribution</span>
              <div className="stat-value">
                <CountUp value={100} suffix="%" />
              </div>
              <p className="small muted">10 stereo sample calls</p>
            </div>
            <div>
              <span className="stat-label">Sentiment macro-F1</span>
              <div className="stat-value">
                <CountUp value={0.841} decimals={3} />
              </div>
              <p className="small muted">customer turns after transcription</p>
            </div>
          </div>
        </section>

        <section className="section" style={{ paddingTop: 0 }}>
          <Reveal className="cta-block">
            <h2 className="display-md">See your first call analysed.</h2>
            <p className="lead" style={{ margin: '14px 0 24px' }}>
              Sign in, press “Load sample calls”, and watch the emotion timeline, summary and scorecard appear.
            </p>
            <Button variant="secondary" size="lg" to="/login" iconRight={ArrowRight}>
              Sign in
            </Button>
          </Reveal>
        </section>
      </Container>

      <footer className="footer">
        <Container>
          <p>CallSense — call analytics for contact centres. Speech and text models run locally on CPU; summaries use Gemini.</p>
        </Container>
      </footer>
    </>
  )
}
