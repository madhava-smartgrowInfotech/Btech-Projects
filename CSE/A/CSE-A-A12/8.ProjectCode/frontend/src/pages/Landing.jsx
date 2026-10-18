import { Link } from 'react-router-dom'
import { ArrowRight, Brain, Database, Flame, ImageUp, ScanLine, ShieldAlert, SlidersHorizontal } from 'lucide-react'
import { Alert, Button, Card, Container, Brand } from '../components/ui'
import { CountUp, InkRule, MagneticButton, MaskHeadline, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import { useAuth } from '../lib/auth'
import { useDocumentTitle, useHealth } from '../lib/hooks'
import { CLASS_COLOR } from '../lib/format'

const TICKER = [
  { label: 'Input', value: '224×224' },
  { label: 'Classes', value: '3' },
  { label: 'Enhancement', value: 'CLAHE' },
  { label: 'Explainability', value: 'Grad-CAM' },
  { label: 'Formats', value: 'JPG · PNG' },
  { label: 'Max upload', value: '8 MB' },
  { label: 'History', value: 'SQLite' },
]

const STEPS = [
  { icon: ImageUp, title: 'Upload', body: 'Drop in a chest X-ray as JPG or PNG, up to 8 MB. It is saved with a unique name so nothing is overwritten.' },
  { icon: SlidersHorizontal, title: 'Resize and enhance', body: 'The image is resized to 224×224, contrast-boosted with CLAHE, lightly denoised and normalised for the network.' },
  { icon: Brain, title: 'Classify', body: 'A convolutional network returns a probability for Normal, Bacterial Pneumonia and Viral Pneumonia.' },
  { icon: Flame, title: 'Explain with Grad-CAM', body: 'A heatmap overlay shows which lung regions pushed the prediction, so a reader can sanity-check it.' },
  { icon: Database, title: 'Keep a record', body: 'Every result is stored with its images and probabilities, and stays one click away in History.' },
]

const CLASSES = [
  {
    name: 'Normal',
    body: 'Clear lung fields with no focal opacity. The model returns Normal when neither pneumonia class outweighs it.',
  },
  {
    name: 'Bacterial Pneumonia',
    body: 'Often seen as a focal, dense consolidation in one lobe. The heatmap usually concentrates on that region.',
  },
  {
    name: 'Viral Pneumonia',
    body: 'Often a more diffuse, interstitial pattern across both lungs, which is harder to tell apart from bacterial cases.',
  },
]

export default function Landing() {
  useDocumentTitle(null)
  const { user } = useAuth()
  const health = useHealth()
  const cta = user ? '/app/detect' : '/login'

  return (
    <>
      <section className="hero">
        <Container>
          <span className="eyebrow">Chest X-ray screening support</span>
          <MaskHeadline className="display-xl hero-title hero-headline" lines={['Read the lungs.', 'Show the work.']} />
          <div className="hero-grid">
            <div>
              <p className="lead">
                Upload a chest X-ray. PneumoDetect classifies it as <span className="hl">Normal</span>, <span className="hl-coral">Bacterial</span> or{' '}
                <span className="hl">Viral</span> pneumonia and paints a Grad-CAM heatmap over the regions that drove the call.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to={cta} iconRight={ArrowRight}>
                    {user ? 'Start a scan' : 'Try the demo'}
                  </Button>
                </MagneticButton>
                <Button size="lg" href="#how">
                  How it works
                </Button>
              </div>
            </div>
            <Card tone="lime" className="hero-plate" aria-label="What you get">
              <div className="row-between">
                <strong className="mono">RESULT PREVIEW</strong>
                <ScanLine size={22} aria-hidden="true" />
              </div>
              <p className="display-sm">One image in. Three probabilities and a heatmap out.</p>
              <div className="stack" style={{ '--gap': '10px' }}>
                {Object.entries(CLASS_COLOR).map(([name, color]) => (
                  <div key={name} className="row" style={{ '--gap': '10px' }}>
                    <span className="class-chip" style={{ background: color, maxWidth: 28, height: 28 }} aria-hidden="true" />
                    <strong>{name}</strong>
                  </div>
                ))}
              </div>
              <p className="small">Every prediction is saved to your history with the original film and its overlay.</p>
            </Card>
          </div>
          {health?.demo_mode && (
            <div style={{ marginTop: 32 }}>
              <Alert tone="warning">
                <strong>Demo model.</strong> No trained weights are installed (<code>saved_models/pneumonia_model.h5</code>), so predictions come from an untrained
                network. The whole pipeline runs, but the labels are not clinically meaningful until the model is trained.
              </Alert>
            </div>
          )}
        </Container>
      </section>

      <Marquee items={TICKER} label="Pipeline facts" />

      <section className="section" id="how">
        <Container>
          <div className="section-head">
            <div>
              <span className="eyebrow">The pipeline</span>
              <h2 className="display-lg loose" style={{ marginTop: 12 }}>
                Five steps. <span className="hl">No black box.</span>
              </h2>
            </div>
          </div>
          <div>
            {STEPS.map((s, i) => (
              <Reveal key={s.title} y={28}>
                <div className="how-step">
                  <span className="how-num" aria-hidden="true">
                    0{i + 1}
                  </span>
                  <div className="stack" style={{ '--gap': '6px' }}>
                    <h3 className="display-sm row">
                      <s.icon size={24} aria-hidden="true" /> {s.title}
                    </h3>
                    <p style={{ maxWidth: '62ch' }}>{s.body}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </Container>
      </section>

      <InkRule thick />

      <section className="section" id="classes">
        <Container>
          <div className="section-head">
            <div>
              <span className="eyebrow">Three outcomes</span>
              <h2 className="display-lg loose" style={{ marginTop: 12 }}>
                What the model <span className="hl-coral">looks for</span>
              </h2>
            </div>
          </div>
          <Stagger className="grid grid-3">
            {CLASSES.map((c) => (
              <Card key={c.name} hot className="class-card">
                <span className="class-chip" style={{ background: CLASS_COLOR[c.name] }} aria-hidden="true" />
                <h3 className="display-sm">{c.name}</h3>
                <p>{c.body}</p>
              </Card>
            ))}
          </Stagger>
        </Container>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <Container>
          <SlideUp>
            <div className="stats-strip">
              <div>
                <div className="stat-value">
                  <CountUp value={3} />
                </div>
                <div className="stat-label">Classes</div>
              </div>
              <div>
                <div className="stat-value">
                  <CountUp value={224} />
                </div>
                <div className="stat-label">Pixel input size</div>
              </div>
              <div>
                <div className="stat-value">
                  <CountUp value={5} />
                </div>
                <div className="stat-label">Pipeline steps</div>
              </div>
              <div>
                <div className="stat-value">
                  <CountUp value={8} suffix=" MB" />
                </div>
                <div className="stat-label">Max upload</div>
              </div>
            </div>
          </SlideUp>
        </Container>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <Container>
          <SlideUp>
            <div className="cta-block stack">
              <h2 className="display-lg">Run a scan.</h2>
              <p className="lead">Sign in with the demo account and have a result, a heatmap and a saved record in under a minute.</p>
              <div>
                <Button variant="secondary" size="lg" to={cta} iconRight={ArrowRight}>
                  {user ? 'Start a scan' : 'Sign in to the demo'}
                </Button>
              </div>
            </div>
          </SlideUp>
        </Container>
      </section>

      <footer className="footer">
        <Container>
          <div className="footer-grid">
            <div className="stack" style={{ '--gap': '12px' }}>
              <Brand />
              <p className="small">Pneumonia Detection Using Deep Learning.</p>
            </div>
            <div>
              <h4>Explore</h4>
              <ul>
                <li>
                  <a href="#how">How it works</a>
                </li>
                <li>
                  <a href="#classes">Classes</a>
                </li>
                <li>
                  <Link to="/login">Sign in</Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="row" style={{ '--gap': '6px' }}>
                <ShieldAlert size={16} aria-hidden="true" /> Disclaimer
              </h4>
              <p className="small">
                An academic and research prototype for computer-aided screening support. It is not a certified medical device and must not be the sole basis for
                diagnosis or treatment.
              </p>
            </div>
          </div>
        </Container>
      </footer>
    </>
  )
}
