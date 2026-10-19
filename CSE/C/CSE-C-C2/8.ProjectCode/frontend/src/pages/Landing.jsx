import { AudioLines, BarChart3, Globe2, Library, Lock, Mic, PenLine, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui'
import { CountUp, InkRule, MagneticButton, Marquee, MaskHeadline, Reveal, SmoothScroll, Stagger } from '../components/motion'
import { Brand, Container } from '../components/ui/Layout'
import { useMeta } from '../lib/meta'

const STEPS = [
  { n: '01', title: 'Say the idea', text: 'Type anything up to 2,000 characters, in any of the supported languages. Pick a style and a length.' },
  { n: '02', title: 'A model writes it', text: 'A pretrained instruction model drafts an original story with a title, shaped by your style and length.' },
  { n: '03', title: 'A voice reads it', text: 'A per-language speech model narrates the story. Play it in the browser or download the WAV file.' },
]

const FEATURES = [
  { icon: Globe2, title: 'Multilingual', text: 'Stories and narration across all the languages the speech models cover, listed live from the server.' },
  { icon: PenLine, title: 'Styles and lengths', text: 'Adventure to bedtime to mystery, in short, medium or long form.' },
  { icon: Mic, title: 'Natural narration', text: 'Play in the browser, download WAV, or regenerate a fresh take.' },
  { icon: Library, title: 'Your library', text: 'Every story and its audio is kept in history: replay, download, or delete.' },
  { icon: BarChart3, title: 'Honest metrics', text: 'WER, CER, similarity, latency and real-time factor, computed on real outputs. Never pre-filled.' },
  { icon: Lock, title: 'Local-first', text: 'Stories, audio and evaluations stay on this machine. No analytics, no uploads.' },
]

export default function Landing() {
  const { languages, styles, lengths, meta } = useMeta()
  const ticker = languages.map((l) => ({ label: l.code.toUpperCase(), value: l.name }))

  return (
    <SmoothScroll>
      <Container>
        <section className="hero">
          <span className="eyebrow">Multilingual story generation + speech</span>
          <MaskHeadline className="hero-title" lines={['Say the idea.', 'Hear the story.']} />
          <div className="hero-grid">
            <div>
              <p className="lead">
                StoryVox writes an original story from a single sentence, then narrates it aloud in your language. It all runs on your own computer.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to="/studio" icon={Sparkles}>
                    Write a story
                  </Button>
                </MagneticButton>
                <Button size="lg" to="/stories" icon={Library}>
                  Open history
                </Button>
              </div>
            </div>
            <div className="checks-stack" aria-label="What this server offers">
              <div>
                <div className="k">Languages</div>
                <div className="v">{languages.length ? <CountUp value={languages.length} /> : '—'}</div>
              </div>
              <div>
                <div className="k">Styles</div>
                <div className="v">{styles.length ? <CountUp value={styles.length} /> : '—'}</div>
              </div>
              <div>
                <div className="k">Lengths</div>
                <div className="v">{lengths.length ? <CountUp value={lengths.length} /> : '—'}</div>
              </div>
              <div>
                <div className="k">Story model</div>
                <div className="v" style={{ fontSize: '1rem', overflowWrap: 'anywhere' }}>{meta?.story_model || '—'}</div>
              </div>
            </div>
          </div>
        </section>
      </Container>

      <Marquee items={ticker} variant="lime" label="Supported languages" />

      <Container>
        <section className="section" id="how">
          <Reveal className="section-head">
            <div>
              <span className="eyebrow">How it works</span>
              <h2 className="display-lg" style={{ marginTop: 12 }}>Three steps</h2>
            </div>
          </Reveal>
          {STEPS.map((s) => (
            <Reveal key={s.n} className="how-step">
              <span className="how-num" aria-hidden="true">{s.n}</span>
              <div>
                <h3 className="display-sm">{s.title}</h3>
                <p className="muted" style={{ marginTop: 8, maxWidth: '60ch' }}>{s.text}</p>
              </div>
            </Reveal>
          ))}
        </section>

        <InkRule thick />

        <section className="section">
          <Reveal className="section-head">
            <div>
              <span className="eyebrow">What you get</span>
              <h2 className="display-lg" style={{ marginTop: 12 }}>Everything on one desk</h2>
            </div>
          </Reveal>
          <Stagger className="grid feature-grid">
            {FEATURES.map((f) => (
              <div className="card feature-card" key={f.title} style={{ height: '100%' }}>
                <div className="feature-icon"><f.icon size={26} aria-hidden="true" /></div>
                <h3 className="display-sm">{f.title}</h3>
                <p className="muted" style={{ marginTop: 8 }}>{f.text}</p>
              </div>
            ))}
          </Stagger>
        </section>

        {languages.length > 0 && (
          <section className="section" style={{ paddingTop: 0 }}>
            <Reveal>
              <span className="eyebrow">Narration languages</span>
              <ul className="lang-cloud" style={{ listStyle: 'none', padding: 0, margin: '16px 0 0' }}>
                {languages.map((l) => (
                  <li className="lang-chip" key={l.code}>{l.name}<i>{l.code}</i></li>
                ))}
              </ul>
            </Reveal>
          </section>
        )}

        <Reveal>
          <div className="cta-block">
            <h2 className="display-lg">Your story is one sentence away.</h2>
            <p style={{ margin: '16px 0 24px', maxWidth: '52ch' }}>Open the studio, type an idea and press generate.</p>
            <Button variant="secondary" size="lg" to="/studio" icon={AudioLines}>
              Open the studio
            </Button>
          </div>
        </Reveal>
      </Container>

      <footer className="footer">
        <Container>
          <div className="footer-grid">
            <div>
              <Brand />
              <p className="small" style={{ marginTop: 12, maxWidth: '36ch' }}>Local-first multilingual storytelling with spoken narration.</p>
            </div>
            <div>
              <h4>Screens</h4>
              <ul>
                <li><Link to="/studio">Studio</Link></li>
                <li><Link to="/stories">History</Link></li>
                <li><Link to="/evaluation">Evaluation</Link></li>
              </ul>
            </div>
            <div>
              <h4>Privacy</h4>
              <p className="small">Stories, audio and evaluation files stay on this computer. Nothing is uploaded.</p>
            </div>
          </div>
        </Container>
      </footer>
    </SmoothScroll>
  )
}
