import { useEffect, useState } from 'react'
import { ArrowRight, BarChart3, FileScan, HeartPulse, ListOrdered, ScanSearch, ShieldCheck, Stethoscope } from 'lucide-react'
import { Button, Card, Container, Skeleton } from '../components/ui'
import { InkRule, MagneticButton, Marquee, MaskHeadline, Reveal, SlideUp } from '../components/motion'
import { PriorityBlock } from '../components/athena/bits'
import { useAuth } from '../lib/auth'
import { api } from '../lib/api'
import { fmtPct, PRIORITY_NAME } from '../lib/format'

const SCALE = {
  1: 'Immediate life threat. Seen now.',
  2: 'High risk or severe distress. Seen within minutes.',
  3: 'Stable but needs several resources. Seen in order.',
  4: 'One resource needed. Can wait safely.',
  5: 'No resources needed. Advice or a prescription.',
}

const STEPS = [
  ['Read the report', 'Upload a scanned PDF or photo. ATHENA reads every page and pulls out symptoms, findings, history and lab values, each tagged with the page it came from.'],
  ['Enter the vitals', 'Age, heart rate, blood pressure, SpO2, temperature, respiratory rate and how the patient arrived.'],
  ['Fuse and score', 'Report features and vitals become one record. A gradient-boosted model assigns a priority from 1 to 5 with a calibrated confidence.'],
  ['See why, then decide', 'SHAP shows which findings and vitals pushed the priority, strongest first. The clinician accepts or changes it, and the reason is stored.'],
]

const FEATURES = [
  [FileScan, 'Report intake', 'PDF or scan in, structured findings out, with page references.'],
  [HeartPulse, 'Vitals entry', 'Seven vitals plus arrival mode, validated as you type.'],
  [ScanSearch, 'Fused record', 'Report features and vitals side by side in one patient record.'],
  [Stethoscope, 'Triage model', 'Priority 1 to 5, a risk level and a calibrated confidence.'],
  [ShieldCheck, 'Clinician override', 'Accept or change with a reason. Every override is kept as feedback.'],
  [ListOrdered, 'Live queue', 'Patients ordered by priority and arrival, refreshed automatically.'],
  [BarChart3, 'Performance page', 'Accuracy, per-priority recall and seconds per patient.'],
]

export default function Landing() {
  const { user } = useAuth()
  const [stats, setStats] = useState({ loading: true, data: null })

  useEffect(() => {
    let live = true
    api
      .publicStats()
      .then((d) => live && setStats({ loading: false, data: d.available ? d : null }))
      .catch(() => live && setStats({ loading: false, data: null }))
    return () => {
      live = false
    }
  }, [])

  const s = stats.data
  const ticker = s
    ? [
        { label: 'Hold-out accuracy', value: fmtPct(s.accuracy, 1) },
        { label: 'Within one priority', value: fmtPct(s.within_one_priority, 1) },
        { label: 'Macro F1', value: s.macro_f1.toFixed(2) },
        { label: 'Test cases', value: s.n_test.toLocaleString() },
        { label: 'Model time / patient', value: `${(s.model_seconds_per_patient * 1000).toFixed(2)} ms` },
      ]
    : []

  return (
    <div className="hero-clip">
      <Container>
        <section className="hero">
          <span className="eyebrow">Emergency triage assistant</span>
          <MaskHeadline
            className="display-xl hero-title"
            style={{ fontSize: 'clamp(2.4rem, 8vw, 6.5rem)' }}
            lines={['Every priority', 'shows its reasons.']}
          />
          <div className="hero-grid">
            <div>
              <p className="lead" style={{ maxWidth: '52ch' }}>
                ATHENA reads the scanned report, takes the vitals, assigns a triage priority from 1 to 5, and lists the findings behind it. The clinician always has the last word.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to={user ? '/app/queue' : '/login'} iconRight={ArrowRight}>
                    {user ? 'Open the queue' : 'Sign in to triage'}
                  </Button>
                </MagneticButton>
                <Button size="lg" href="#how">How it decides</Button>
              </div>
            </div>
            <div aria-live="polite">
              {stats.loading ? (
                <Skeleton height={230} />
              ) : s ? (
                <div className="checks-stack">
                  <div><div className="k">Hold-out accuracy</div><div className="v">{fmtPct(s.accuracy, 1)}</div></div>
                  <div><div className="k">Within one level</div><div className="v">{fmtPct(s.within_one_priority, 1)}</div></div>
                  <div><div className="k">Test cases</div><div className="v">{s.n_test.toLocaleString()}</div></div>
                  <div><div className="k">Model per patient</div><div className="v">{(s.model_seconds_per_patient * 1000).toFixed(2)} ms</div></div>
                  <div style={{ gridColumn: '1 / -1', borderBottom: 0, borderRight: 0 }}>
                    <div className="k">Measured on a seeded synthetic dataset, not patient data</div>
                  </div>
                </div>
              ) : (
                <Card flat><p className="small">Model numbers appear here once the model is trained. Run <code>python ml/train.py</code>.</p></Card>
              )}
            </div>
          </div>
        </section>
      </Container>

      {ticker.length > 0 && <Marquee items={ticker} label="Model evaluation figures" />}

      <Container>
        <section className="section" aria-labelledby="scale-h">
          <Reveal className="section-head">
            <h2 id="scale-h" className="display-lg">Five levels.<br />One queue.</h2>
            <p className="lead" style={{ maxWidth: '40ch' }}>The sickest patient is always at the top, and ties go to the earlier arrival.</p>
          </Reveal>
          <Card flat className="scale-list" style={{ padding: 0 }}>
            {[1, 2, 3, 4, 5].map((n) => (
              <div className="scale-row" key={n}>
                <PriorityBlock p={n} />
                <div>
                  <strong>{PRIORITY_NAME[n]}</strong>
                  <span>{SCALE[n]}</span>
                </div>
              </div>
            ))}
          </Card>
        </section>
        <InkRule thick />

        <section className="section" id="how" aria-labelledby="how-h">
          <Reveal className="section-head">
            <h2 id="how-h" className="display-lg">How it<br />decides</h2>
          </Reveal>
          {STEPS.map(([t, d], i) => (
            <SlideUp key={t} className="how-step">
              <span className="how-num" aria-hidden="true">{String(i + 1).padStart(2, '0')}</span>
              <div>
                <h3 className="display-sm">{t}</h3>
                <p style={{ marginTop: 8, maxWidth: '62ch' }}>{d}</p>
              </div>
            </SlideUp>
          ))}
        </section>

        <section className="section" aria-labelledby="feat-h" style={{ paddingTop: 0 }}>
          <Reveal className="section-head">
            <h2 id="feat-h" className="display-lg">What is<br />inside</h2>
          </Reveal>
          <div className="grid grid-3">
            {FEATURES.map(([Icon, t, d]) => (
              <SlideUp key={t} className="card feature-card hot">
                <div className="feature-icon"><Icon size={26} aria-hidden="true" /></div>
                <h3 className="display-sm">{t}</h3>
                <p className="small" style={{ marginTop: 8 }}>{d}</p>
              </SlideUp>
            ))}
          </div>
        </section>

        <section className="section" style={{ paddingTop: 0 }}>
          <Reveal>
            <div className="cta-block stack">
              <h2 className="display-lg">Triage the next<br />arrival.</h2>
              <p className="lead" style={{ maxWidth: '48ch' }}>Sign in with a demo account, upload a sample report and watch the priority and its reasons appear.</p>
              <div><Button variant="secondary" size="lg" to={user ? '/app/new' : '/login'} iconRight={ArrowRight}>{user ? 'New patient' : 'Sign in'}</Button></div>
            </div>
          </Reveal>
        </section>
      </Container>

      <footer className="footer">
        <Container>
          <div className="footer-grid">
            <div>
              <h4>ATHENA</h4>
              <p className="small">Autonomous Triage and Healthcare Electronic Neural Assistant. Decision support for emergency departments.</p>
            </div>
            <div>
              <h4>Product</h4>
              <ul>
                <li><a href="#how">How it decides</a></li>
                <li><a href="/login">Sign in</a></li>
              </ul>
            </div>
            <div>
              <h4>Note</h4>
              <p className="small">Decision support only. The treating clinician makes the final triage decision. Model figures use synthetic data.</p>
            </div>
          </div>
        </Container>
      </footer>
    </div>
  )
}
