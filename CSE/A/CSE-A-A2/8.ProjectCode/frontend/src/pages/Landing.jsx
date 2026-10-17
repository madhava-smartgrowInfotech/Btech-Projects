import { useEffect, useState } from 'react'
import { ArrowRight, BrainCircuit, Gauge, Hospital, MapPinned, Radio, ShieldCheck, Timer } from 'lucide-react'
import { Button, Card, Container } from '../components/ui'
import { CountUp, InkRule, MagneticButton, MaskHeadline, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import { api } from '../lib/api'
import { EMERGENCY_CONTACTS } from '../lib/format'
import { useMonitor } from '../state/MonitorContext'

const STEPS = [
  { title: 'Sense', body: 'Accelerometer, gyroscope and speed readings stream in. This build simulates a phone so it runs anywhere.' },
  { title: 'Detect', body: 'A Random Forest classifier decides whether the spike looks like a crash and returns its probability.' },
  { title: 'Rate', body: 'A second model grades the impact: None, Minor, Moderate or Severe.' },
  { title: 'Confirm', body: 'On Moderate or Severe, a 15 second countdown lets the occupant cancel a false alarm.' },
  { title: 'Dispatch', body: 'Location is resolved, the nearest hospital is found and the emergency message is drafted.' },
]

const FEATURES = [
  { icon: Radio, title: 'Live sensor feed', body: 'Stream a fresh reading every 1.5 seconds and watch acceleration and rotation on a rolling chart.' },
  { icon: BrainCircuit, title: 'Two-stage models', body: 'Accident detection first, severity second. If the detector says no accident, severity is forced to None.' },
  { icon: Timer, title: 'False-alarm guard', body: 'Nothing is sent until the countdown ends or the occupant presses Send alert now.' },
  { icon: MapPinned, title: 'Nearest hospital', body: 'Great-circle distance picks the closest emergency hospitals and plots them next to the crash.' },
  { icon: Gauge, title: 'Manual override', body: 'Type your own sensor values to see exactly where the model draws the line.' },
  { icon: ShieldCheck, title: 'Honest fallback', body: 'If the trained models are missing, a rule-based fallback answers and the app says so.' },
]

export default function Landing() {
  const { health } = useMonitor()
  const [hospitalCount, setHospitalCount] = useState(null)
  useEffect(() => {
    let alive = true
    api
      .hospitals({ k: 100 })
      .then((d) => alive && setHospitalCount(d.hospitals.length))
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [])

  const modelLabel = health.status === 'ok' ? (health.models_loaded ? 'Trained ML' : 'Fallback') : health.status === 'error' ? 'Offline' : '…'
  const ticker = [
    { label: 'Confirmation window', value: '15 s' },
    { label: 'Severity levels', value: 'None / Minor / Moderate / Severe' },
    { label: 'Sensor features', value: '11' },
    { label: 'Ambulance', value: '108' },
    { label: 'National emergency', value: '112' },
    ...(hospitalCount ? [{ label: 'Hospitals in directory', value: String(hospitalCount) }] : []),
  ]

  return (
    <>
      <Container>
        <section className="hero">
          <div className="hero-grid">
            <div>
              <span className="eyebrow">AI accident detection and emergency response</span>
              <MaskHeadline className="display-xl hero-title" lines={['Detect.', 'Rate.', 'Dispatch.']} />
              <p className="lead">
                ResQAI reads vehicle sensor data, spots a crash, grades how bad it is and, if nobody answers, sends help to the right hospital with the right location.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to="/monitor" iconRight={ArrowRight}>
                    Open live monitor
                  </Button>
                </MagneticButton>
                <Button size="lg" to="/response" icon={Hospital}>
                  See response map
                </Button>
              </div>
            </div>
            <SlideUp delay={0.2}>
              <div className="checks-stack" aria-label="System status">
                <div>
                  <div className="k">API</div>
                  <div className="v">{health.status === 'ok' ? 'Online' : health.status === 'error' ? 'Offline' : 'Checking'}</div>
                </div>
                <div>
                  <div className="k">Model</div>
                  <div className="v">{modelLabel}</div>
                </div>
                <div>
                  <div className="k">Stages</div>
                  <div className="v">Detect + Rate</div>
                </div>
                <div>
                  <div className="k">Countdown</div>
                  <div className="v">15 s</div>
                </div>
              </div>
            </SlideUp>
          </div>
        </section>
      </Container>

      <Marquee items={ticker} label="ResQAI facts" />

      <Container>
        <section className="section">
          <Reveal className="section-head">
            <div>
              <span className="eyebrow">How it works</span>
              <h2 className="display-lg" style={{ marginTop: 12 }}>Five steps, no hand-offs</h2>
            </div>
          </Reveal>
          <InkRule thick />
          <ol style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {STEPS.map((s, i) => (
              <Reveal as="li" className="how-step" key={s.title} y={32}>
                <span className="how-num" aria-hidden="true">{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <h3 className="display-sm">{s.title}</h3>
                  <p className="muted" style={{ marginTop: 6, maxWidth: '60ch' }}>{s.body}</p>
                </div>
              </Reveal>
            ))}
          </ol>
        </section>
      </Container>

      <Container>
        <div className="stats-strip">
          <div>
            <span className="stat-label">Severity levels</span>
            <div className="stat-value"><CountUp value={4} /></div>
          </div>
          <div>
            <span className="stat-label">Sensor features</span>
            <div className="stat-value"><CountUp value={11} /></div>
          </div>
          <div>
            <span className="stat-label">Seconds to cancel</span>
            <div className="stat-value"><CountUp value={15} /></div>
          </div>
          <div>
            <span className="stat-label">Hospitals listed</span>
            <div className="stat-value">{hospitalCount === null ? '—' : <CountUp value={hospitalCount} />}</div>
          </div>
        </div>
      </Container>

      <Container>
        <section className="section">
          <Reveal className="section-head">
            <div>
              <span className="eyebrow">What is inside</span>
              <h2 className="display-lg" style={{ marginTop: 12 }}>Built for the worst minute</h2>
            </div>
          </Reveal>
          <Stagger className="grid grid-3">
            {FEATURES.map(({ icon: Icon, title, body }) => (
              <Card key={title} className="feature-card" hot>
                <div className="feature-icon"><Icon size={26} aria-hidden="true" /></div>
                <h3 className="display-sm" style={{ margin: '16px 0 8px' }}>{title}</h3>
                <p className="muted small">{body}</p>
              </Card>
            ))}
          </Stagger>
        </section>
      </Container>

      <Container>
        <Reveal>
          <div className="cta-block" style={{ padding: 'clamp(24px, 5vw, 56px)', marginBottom: 24 }}>
            <h2 className="display-lg">Crash it. Safely.</h2>
            <p className="lead" style={{ marginTop: 14 }}>Fire a severe crash scenario and watch the countdown, the alert and the map light up.</p>
            <div className="hero-actions">
              <Button variant="secondary" size="lg" to="/monitor" iconRight={ArrowRight}>Start the demo</Button>
            </div>
          </div>
        </Reveal>
      </Container>

      <footer className="footer">
        <Container>
          <div className="footer-grid">
            <div>
              <h4>ResQAI</h4>
              <p className="small">AI-Based Accident Detection, Severity Assessment and Intelligent Emergency Response System.</p>
            </div>
            <div>
              <h4>Emergency numbers</h4>
              <ul>
                {EMERGENCY_CONTACTS.map((c) => (
                  <li key={c.number}>
                    {c.label}: <a href={`tel:${c.number}`}>{c.number}</a>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Note</h4>
              <p className="small">Prototype trained on synthetic sensor data. Hospital data is a small demo directory. Alerts are drafted, not sent to real responders.</p>
            </div>
          </div>
        </Container>
      </footer>
    </>
  )
}
