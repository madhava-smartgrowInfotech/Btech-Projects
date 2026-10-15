import { Link } from 'react-router-dom'
import { ArrowRight, Brain, FileText, Languages, Layers, Lock, ScanLine } from 'lucide-react'
import { PublicShell, Container } from '../components/ui/Layout.jsx'
import { Alert, Button, Card } from '../components/ui/index.js'
import { MaskHeadline, Marquee, Reveal, SlideUp, Stagger } from '../components/motion/index.jsx'
import { useAuth } from '../lib/auth.jsx'

const FACTS = [
  { k: 'Modalities', v: 'X-ray + CT' },
  { k: 'Findings', v: '7 + normal' },
  { k: 'Reports', v: 'EN · HI · TE' },
  { k: 'Evidence', v: 'Grad-CAM' },
]

const MARQUEE = [
  { label: 'Input', value: 'PNG · JPG · DICOM' },
  { label: 'Checks', value: 'Modality + non-chest rejection' },
  { label: 'Explained by', value: 'Grad-CAM heatmap' },
  { label: 'Reports in', value: 'English · Hindi · Telugu' },
  { label: 'Decision', value: 'A qualified clinician confirms' },
]

const STEPS = [
  { title: 'Upload', text: 'PNG, JPG or DICOM, up to 25 MB, for a registered patient.' },
  { title: 'Modality check', text: 'Recognises chest X-ray or CT and rejects colour photos and non-chest images.' },
  { title: 'Preprocess and mask', text: 'Resize, denoise, contrast-enhance and normalise, with each step shown. A U-Net outlines the lungs on X-rays.' },
  { title: 'Classify and explain', text: 'EfficientNet-B0 with temperature-calibrated confidence and a Grad-CAM heatmap of the evidence.' },
  { title: 'Severity and assistant', text: 'Severity from the affected lung area. A clinical assistant answers follow-up questions for doctors.' },
  { title: 'Report', text: 'A PDF in English, Hindi or Telugu with a patient-friendly explanation.' },
]

const FEATURES = [
  { icon: ScanLine, title: 'X-ray and CT in one place', text: 'The modality check routes each chest image to the right model.' },
  { icon: Layers, title: 'Lung segmentation', text: 'Lung masks overlaid on the scan, next to every preprocessing step.' },
  { icon: Brain, title: 'Seven findings, two models', text: 'COVID-19, viral pneumonia, lung opacity and tuberculosis on X-ray; three lung cancer types on CT; plus normal.' },
  { icon: Layers, title: 'Explained, with severity', text: 'Grad-CAM shows what drove the result, with calibrated confidence and a severity estimate.' },
  { icon: Languages, title: 'Assistant and reports', text: 'Follow-up questions per scan, and PDF reports in three languages.' },
  { icon: Lock, title: 'Secure records', text: 'Encrypted patient data and images, doctor and technician roles, and a full audit log.' },
]

export default function Landing() {
  const { user } = useAuth()
  const start = user ? '/scan' : '/login'

  return (
    <PublicShell>
      <section className="hero">
        <Container>
          <div className="hero-grid">
            <div>
              <span className="eyebrow">Explainable chest screening</span>
              <MaskHeadline as="h1" className="display-lg hero-title" lines={['Read the lungs.', 'See the reason.']} />
              <p className="lead">
                Upload a chest X-ray or CT slice. PulmoVision segments the lungs, flags seven pulmonary conditions, shows the evidence as a
                Grad-CAM heatmap and writes a report in English, Hindi or Telugu.
              </p>
              <div className="hero-actions">
                <Button variant="primary" size="lg" to={start} iconRight={ArrowRight}>
                  Start a screening
                </Button>
                <Button size="lg" href="#how">
                  How it works
                </Button>
              </div>
            </div>
            <SlideUp>
              <dl className="checks-stack" style={{ margin: 0 }}>
                {FACTS.map((f) => (
                  <div key={f.k}>
                    <dt className="k">{f.k}</dt>
                    <dd className="v" style={{ margin: 0 }}>{f.v}</dd>
                  </div>
                ))}
              </dl>
            </SlideUp>
          </div>
        </Container>
      </section>

      <Marquee items={MARQUEE} label="Product facts" />

      <section className="section" id="how">
        <Container>
          <Reveal>
            <div className="section-head">
              <h2 className="display-md">From upload to report</h2>
              <p className="muted" style={{ maxWidth: '42ch' }}>Six steps, each one visible to the reviewing clinician.</p>
            </div>
          </Reveal>
          <Stagger>
            {STEPS.map((s, i) => (
              <div className="how-step" key={s.title}>
                <span className="how-num" aria-hidden="true">{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <h3 className="display-sm">{s.title}</h3>
                  <p className="muted" style={{ marginTop: 6 }}>{s.text}</p>
                </div>
              </div>
            ))}
          </Stagger>
        </Container>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <Container>
          <Reveal>
            <h2 className="display-md" style={{ marginBottom: 28 }}>Built for the reading room</h2>
          </Reveal>
          <Stagger style={{ display: 'grid', gap: 20, gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))' }}>
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <Card key={title} className="feature-card">
                <span className="feature-icon" aria-hidden="true">
                  <Icon size={24} />
                </span>
                <h3 className="card-title" style={{ marginTop: 14 }}>{title}</h3>
                <p className="muted" style={{ marginTop: 8 }}>{text}</p>
              </Card>
            ))}
          </Stagger>
          <div style={{ marginTop: 28 }}>
            <Alert tone="info">
              Every metric is measured on held-out test data. Signed-in users can read the full evaluation under{' '}
              <Link to={user ? '/performance' : '/login'}>Model performance</Link>.
            </Alert>
          </div>
        </Container>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <Container>
          <Reveal>
            <div className="cta-block">
              <h2 className="display-md">Ready to review a scan?</h2>
              <p className="lead" style={{ marginTop: 12 }}>Sign in with your clinic account to register a patient and upload a scan.</p>
              <div className="hero-actions">
                <Button variant="secondary" size="lg" to={start} icon={FileText}>
                  {user ? 'Open workspace' : 'Sign in'}
                </Button>
              </div>
            </div>
          </Reveal>
        </Container>
      </section>

      <footer className="footer">
        <Container>
          <div className="footer-grid">
            <div>
              <h4>PulmoVision</h4>
              <p className="small">
                Clinical decision support for radiologists and physicians. Every AI result is an aid for a qualified professional, not a diagnosis.
              </p>
            </div>
            <div>
              <h4>Explore</h4>
              <ul>
                <li><a href="#how">How it works</a></li>
                <li><Link to={start}>{user ? 'Workspace' : 'Sign in'}</Link></li>
              </ul>
            </div>
          </div>
        </Container>
      </footer>
    </PublicShell>
  )
}
