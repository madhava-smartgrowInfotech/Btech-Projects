import { Link } from 'react-router-dom'
import { ArrowRight, Cpu, Eye, Flame, GitMerge, Layers, Lock, Moon, ScanSearch, ShieldCheck, Sun, Upload, Waves } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useDocTitle, useLoad } from '../lib/hooks'
import { useTheme } from '../lib/theme'
import { fmtPct } from '../lib/format'
import { isDemoData } from '../lib/labels'
import { Badge, Brand, Button, Container, Skeleton } from '../components/ui'
import { CountUp, FadeIn, MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs'

const STEPS = [
  { icon: Upload, tone: 'var(--lavender)', title: 'Upload', text: 'Drop in a PNG, JPG or WEBP. It is decoded and validated on your machine.' },
  { icon: Layers, tone: 'var(--sky)', title: 'Four detectors vote', text: 'Two EfficientNets, a ResNet50 and a MobileNetV3 each give their own verdict.' },
  { icon: GitMerge, tone: 'var(--mint)', title: 'Fusion with gates', text: 'Logits are fused with transparent weights; two gates handle outliers and consensus.' },
  { icon: Flame, tone: 'var(--peach)', title: 'See why', text: 'Grad-CAM heatmaps and a robustness check show where and how firmly it decided.' },
]

const FEATURES = [
  { icon: Layers, tone: 'var(--lavender)', title: '4-model heterogeneous ensemble', text: 'Different backbones, resolutions and losses, so one model’s blind spot is covered by another.' },
  { icon: Flame, tone: 'var(--peach)', title: 'Grad-CAM explanations', text: 'Heatmaps come from real model gradients, with a selector for each backbone.' },
  { icon: Waves, tone: 'var(--sky)', title: 'Robustness check', text: 'Every upload is re-tested after JPEG, resize and blur. Low consistency means: be careful.' },
  { icon: Lock, tone: 'var(--mint)', title: 'Runs locally', text: 'Inference stays on your computer. Nothing is uploaded to a cloud service.' },
  { icon: Cpu, tone: 'var(--rose)', title: 'CPU or GPU', text: 'The device is detected automatically; no GPU is required.' },
  { icon: ShieldCheck, tone: 'var(--butter)', title: 'Honest about limits', text: 'Results are estimates, not proof of origin, and the metrics page says exactly what they were measured on.' },
]

export default function Landing() {
  useDocTitle('VeriVision AI · Is this image real or AI-generated?')
  const { user } = useAuth()
  const { theme, toggle } = useTheme()
  const insights = useLoad((s) => api.insights(s), [])
  const cfg = useLoad((s) => api.config(s), [])
  const e = insights.data?.ensemble
  const cta = user ? '/app' : '/login'
  const weights = cfg.data
    ? cfg.data.branches.map((b) => ({ ...b, w: cfg.data.ensemble_weights[b.key] / Object.values(cfg.data.ensemble_weights).reduce((a, c) => a + c, 0) }))
    : null

  const maxW = weights ? Math.max(...weights.map((b) => b.w)) : 1

  return (
    <div className="landing">
      <a className="skip-link" href="#content">Skip to content</a>
      <header className="l-nav">
        <Container>
          <Brand />
          <nav className="l-nav-links" aria-label="Sections">
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#numbers">Numbers</a>
            <a href="#limits">Limits</a>
          </nav>
          <span style={{ flex: 1 }} />
          <button type="button" className="icon-btn" onClick={toggle} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} aria-pressed={theme === 'dark'}>
            {theme === 'dark' ? <Sun size={20} aria-hidden="true" /> : <Moon size={20} aria-hidden="true" />}
          </button>
          <Button to={cta} className="btn-open-app" icon={ScanSearch} aria-label={user ? 'Open analyzer' : 'Sign in'}><span>{user ? 'Open analyzer' : 'Sign in'}</span></Button>
        </Container>
      </header>

      <main id="content">
        <section className="hero" aria-labelledby="hero-title">
          <Blobs preset="hero" />
          <Container>
            <div className="hero-grid">
              <div>
                <SlideUp><span className="eyebrow"><Eye size={14} aria-hidden="true" /> AI-generated image detection</span></SlideUp>
                <SlideUp delay={0.05}>
                  <h1 id="hero-title" style={{ marginTop: 18 }}>
                    Is this image <span className="hl">real</span> or AI-generated?
                  </h1>
                </SlideUp>
                <SlideUp delay={0.1}>
                  <p className="hero-lead">
                    VeriVision AI checks your image with an ensemble of four deep-learning detectors and shows you <strong>why</strong> it decided, with
                    visual explanations, per-model votes and a robustness check.
                  </p>
                </SlideUp>
                <SlideUp delay={0.15}>
                  <div className="hero-cta">
                    <MagneticButton>
                      <Button to={cta} size="lg" iconRight={ArrowRight}>Analyze an image</Button>
                    </MagneticButton>
                    <Button size="lg" variant="secondary" onClick={(ev) => { ev.preventDefault(); document.getElementById('how')?.scrollIntoView({ behavior: 'smooth' }) }}>
                      See how it works
                    </Button>
                  </div>
                </SlideUp>
                <FadeIn delay={0.4}>
                  <div className="hero-note">
                    <Badge tone="mint" icon={Lock}>Runs locally</Badge>
                    <Badge tone="lavender" icon={Layers}>4-model ensemble</Badge>
                    <Badge tone="peach" icon={Flame}>Grad-CAM</Badge>
                  </div>
                </FadeIn>
              </div>

              <SlideUp delay={0.2} className="hero-visual">
                <div className="hero-card" aria-label="The four detectors and their fusion weights">
                  <h2 style={{ fontSize: 17, marginBottom: 4 }}>The ensemble</h2>
                  <p className="small muted" style={{ marginBottom: 16 }}>Live from the running API: four routes and their fusion weights.</p>
                  {weights ? (
                    <div className="stack" style={{ '--gap': '12px' }}>
                      {weights.map((b, i) => (
                        <div key={b.key}>
                          <div className="row between small" style={{ marginBottom: 6 }}>
                            <strong>{b.name}</strong>
                            <span className="muted num">{b.resolution}px · {fmtPct(b.w, 0)}</span>
                          </div>
                          <div className="progress" role="img" aria-label={`${b.name} weight ${fmtPct(b.w, 0)}`}>
                            <div className="progress-fill" style={{ width: `${(b.w / maxW) * 100}%`, background: ['var(--lavender)', 'var(--sky)', 'var(--peach)', 'var(--mint)'][i] }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : cfg.error ? (
                    <p className="small" role="status" style={{ color: 'var(--text-2)' }}>
                      Start the API (run.bat) to see the live ensemble here. The analyzer needs it as well.
                    </p>
                  ) : (
                    <div className="stack" style={{ '--gap': '14px' }} aria-label="Loading ensemble"><Skeleton height={22} /><Skeleton height={22} /><Skeleton height={22} /><Skeleton height={22} /></div>
                  )}
                </div>
                <div className="hero-float a"><Flame size={22} aria-hidden="true" style={{ color: 'var(--peach-ink)' }} /><div><b>Grad-CAM</b><span>shows where it looked</span></div></div>
                <div className="hero-float b"><ShieldCheck size={22} aria-hidden="true" style={{ color: 'var(--mint-ink)' }} /><div><b>On-device</b><span>nothing leaves your PC</span></div></div>
              </SlideUp>
            </div>
          </Container>
        </section>

        <section className="section" aria-label="Capabilities" style={{ paddingTop: 0 }}>
          <Marquee speed={46}>
            {['EfficientNet-B0 ×2', 'ResNet50 · 320px', 'MobileNetV3-Large', 'Focal loss', 'Logit-space fusion', 'Disagreement gating', 'Grad-CAM', 'JPEG / resize / blur re-test', 'Flip test-time augmentation'].map((c) => (
              <span className="chip" key={c}><span className="dot" style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--lavender)' }} aria-hidden="true" />{c}</span>
            ))}
          </Marquee>
        </section>

        <section className="section" id="how" aria-labelledby="how-title">
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">How it works</span>
              <h2 id="how-title">From upload to explanation in four steps</h2>
              <p>No black box: each stage is visible in the result you get back.</p>
            </Reveal>
            <Reveal>
              <div className="steps-line" aria-hidden="true"><div /></div>
            </Reveal>
            <Stagger className="steps" inView>
              {STEPS.map((s, i) => (
                <Stagger.Item key={s.title} className="step-card">
                  <span className="n">0{i + 1}</span>
                  <span className="ico" style={{ background: s.tone }}><s.icon size={24} aria-hidden="true" /></span>
                  <h3>{s.title}</h3>
                  <p>{s.text}</p>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="features" aria-labelledby="feat-title" style={{ background: 'var(--bg-tint)' }}>
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">Features</span>
              <h2 id="feat-title">Built to be trusted, not just fast</h2>
            </Reveal>
            <Stagger className="features" inView>
              {FEATURES.map((f) => (
                <Stagger.Item key={f.title}>
                  <article className="feature">
                    <span className="ico" style={{ background: f.tone }}><f.icon size={26} aria-hidden="true" /></span>
                    <h3>{f.title}</h3>
                    <p>{f.text}</p>
                  </article>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="numbers" aria-labelledby="num-title">
          <Container>
            <Reveal className="section-head">
              <span className="eyebrow">Measured results</span>
              <h2 id="num-title">Numbers read from the evaluation files</h2>
              <p>
                {e
                  ? isDemoData(e.dataset)
                    ? 'These were measured on synthetic demo data (the public dataset was unavailable at training time), so they show the pipeline works - not real-world accuracy.'
                    : `Held-out test split of ${e.dataset}, seed ${e.seed}.`
                  : 'Loaded live from the API.'}
              </p>
            </Reveal>
            {e ? (
              <Reveal>
                <div className="stats-strip">
                  {[['Ensemble accuracy', e.accuracy], ['F1-score', e.f1], ['ROC-AUC', e.roc_auc]].map(([l, v]) => (
                    <div className="s" key={l}><b><CountUp value={v * 100} format={(x) => `${x.toFixed(1)}%`} /></b><span>{l}</span></div>
                  ))}
                  <div className="s"><b><CountUp value={e.n_samples} /></b><span>held-out test images</span></div>
                  {insights.data.robustness?.resize && (
                    <div className="s"><b><CountUp value={insights.data.robustness.resize.accuracy * 100} format={(x) => `${x.toFixed(1)}%`} /></b><span>accuracy after a 2× resample</span></div>
                  )}
                </div>
              </Reveal>
            ) : insights.loading ? (
              <Skeleton height={120} radius={28} />
            ) : (
              <p className="small muted" style={{ textAlign: 'center' }} role="status">
                {insights.error ? 'Start the API (run.bat) to load the measured results.' : 'Evaluation artifacts are not available yet - run the training workflow first.'}
              </p>
            )}
          </Container>
        </section>

        <section className="section" id="limits" aria-labelledby="lim-title" style={{ paddingTop: 0 }}>
          <Container>
            <Reveal>
              <div className="card tint-peach" style={{ padding: 'clamp(22px, 4vw, 40px)' }}>
                <h2 id="lim-title">What it cannot do</h2>
                <ul className="stack" style={{ '--gap': '10px', paddingLeft: 20, margin: '14px 0 0' }}>
                  <li>It estimates likelihood. It does not prove where an image came from, and it cannot recognise every generator.</li>
                  <li>Heavily compressed, tiny or unusual images are harder - the per-image robustness check flags those.</li>
                  <li>A Grad-CAM heatmap is an explanation aid, not evidence of authenticity.</li>
                </ul>
              </div>
            </Reveal>
          </Container>
        </section>

        <section className="section" style={{ paddingTop: 0 }} aria-labelledby="cta-title">
          <Container>
            <Reveal>
              <div className="cta">
                <Blobs preset="cta" />
                <h2 id="cta-title">Check an image now</h2>
                <p>Sign in with the built-in demo account and run your first analysis in under a minute.</p>
                <MagneticButton><Button to={cta} size="lg" iconRight={ArrowRight}>{user ? 'Open the analyzer' : 'Try the demo'}</Button></MagneticButton>
              </div>
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="footer">
        <Container>
          <span>VeriVision AI - on-device image authenticity assessment. Results are AI-based estimates, not proof of image origin.</span>
          <span><Link to="/login">Sign in</Link></span>
        </Container>
      </footer>
    </div>
  )
}
