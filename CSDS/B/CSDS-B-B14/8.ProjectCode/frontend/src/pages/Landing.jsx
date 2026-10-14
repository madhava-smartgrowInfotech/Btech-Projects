import { Link } from 'react-router-dom'
import { Activity, ArrowRight, FlaskConical, Gauge, LayoutDashboard, LogIn, MapPinned, ShieldAlert, TrendingUp, Waves } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { Badge, Brand, Button } from '../components/ui'
import { MagneticButton, Reveal, SlideUp, Stagger } from '../components/motion'
import Blobs from '../components/reactbits/Blobs.jsx'

const FEATURES = [
  { icon: FlaskConical, tone: 'var(--lavender)', title: 'Water-quality prediction', text: 'A stacked ensemble of four models, with SHAP reasons and guideline-limit checks for every lab sample.', to: '/quality', go: 'Check a sample' },
  { icon: MapPinned, tone: 'var(--mint)', title: 'Digital twin of the network', text: 'A hydraulic model of zones, pipes, tanks and pumps that recomputes pressures and flows for every scenario.', to: '/network', go: 'Open the map' },
  { icon: TrendingUp, tone: 'var(--sky)', title: '7-day demand forecast', text: 'Per-zone forecasts from consumption history and live weather, so hot days are planned for.', to: '/forecast', go: 'See the forecast' },
  { icon: ShieldAlert, tone: 'var(--peach)', title: 'Leak detection and localisation', text: 'Pressure and inflow residuals against the twin flag a leak and rank the most likely pipes on the map.', to: '/leaks', go: 'Run a scenario' },
  { icon: Gauge, tone: 'var(--butter)', title: 'Distribution equity', text: 'Supply against demand per zone, an equity score, and a rebalancing plan tested on the twin before anyone touches a valve.', to: '/network', go: 'Review imbalance' },
  { icon: Activity, tone: 'var(--rose)', title: 'Abnormal consumption', text: 'An IsolationForest over customer meters finds bursts, continuous night flow and suspected theft.', to: '/leaks', go: 'Review meters' },
]

const STEPS = [
  { title: 'Feed in what you already have', text: 'Lab results, zone meters, a few pressure loggers and the customer meters you already read.' },
  { title: 'The twin simulates the network', text: 'A hydraulic model of the city recomputes pressures and flows for every scenario.' },
  { title: 'Models flag and rank', text: 'Leaks, abnormal meters and quality failures come with the likely pipe or the drivers behind them.' },
  { title: 'Test the fix before touching a valve', text: 'Rebalancing and pump changes are simulated on the twin first.' },
]

// Network facts from the project README (WNTR / EPANET model and sensor set).
const FACTS = [
  ['5', 'supply zones'],
  ['85', 'pipes in the network model'],
  ['16', 'pressure loggers'],
  ['150', 'customer meters analysed'],
]

export default function Landing() {
  const { user } = useAuth()
  const cta = user ? '/dashboard' : '/login'
  return (
    <div className="landing">
      <header className="l-nav">
        <div className="container">
          <Brand />
          <nav className="l-nav-links" aria-label="Page sections">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
          </nav>
          <span style={{ flex: 1 }} />
          <Button size="sm" to={cta} icon={LogIn} className="btn-open-app">
            <span>{user ? 'Open dashboard' : 'Sign in'}</span>
          </Button>
        </div>
      </header>

      <section className="hero">
        <Blobs preset="landing" />
        <div className="container hero-grid">
          <SlideUp>
            <span className="eyebrow">
              <Waves size={14} aria-hidden="true" /> Water utility intelligence
            </span>
            <h1 style={{ marginTop: 18 }}>
              See leaks, imbalances and quality risks in your water network <span className="hl">early</span>.
            </h1>
            <p className="hero-lead">
              AquaVision predicts water quality and demand, and detects leaks, pressure imbalances and abnormal consumption on a digital twin of the city
              network. It works with a handful of pressure loggers and the meters you already read.
            </p>
            <div className="hero-cta">
              <MagneticButton>
                <Button size="lg" to={cta} iconRight={ArrowRight}>
                  {user ? 'Open dashboard' : 'Get started'}
                </Button>
              </MagneticButton>
              <a className="btn secondary lg" href="#features">
                See what it does
              </a>
            </div>
            <div className="hero-note">
              <Badge tone="lavender">Water quality</Badge>
              <Badge tone="mint">Digital twin</Badge>
              <Badge tone="sky">Demand forecast</Badge>
              <Badge tone="peach">Leak detection</Badge>
            </div>
          </SlideUp>

          <div className="hero-visual">
            <div className="hero-card">
              <div className="stack" style={{ '--gap': '14px' }}>
                {[
                  { icon: LayoutDashboard, tone: 'var(--lavender)', title: 'Operations dashboard', text: 'Water loss, pressure, quality and open alerts in one view' },
                  { icon: MapPinned, tone: 'var(--mint)', title: 'Network map', text: 'Pipes coloured by zone, with leak suspects ranked' },
                  { icon: Gauge, tone: 'var(--peach)', title: 'What-if on the twin', text: 'Simulate a pump change before it happens on site' },
                ].map((row) => (
                  <div key={row.title} className="row" style={{ '--gap': '14px', flexWrap: 'nowrap' }}>
                    <span className="stat-ico" style={{ background: row.tone }}>
                      <row.icon size={20} aria-hidden="true" />
                    </span>
                    <div style={{ minWidth: 0 }}>
                      <strong>{row.title}</strong>
                      <div className="small muted">{row.text}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="hero-float b">
              <span className="stat-ico" style={{ background: 'var(--mint)' }}>
                <ShieldAlert size={18} aria-hidden="true" />
              </span>
              <div>
                <b>Top-3</b>
                <span>likely leak pipes ranked</span>
              </div>
            </div>
            <div className="hero-float a">
              <span className="stat-ico" style={{ background: 'var(--sky)' }}>
                <Gauge size={18} aria-hidden="true" />
              </span>
              <div>
                <b>Equity</b>
                <span>zones compared on service</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Reveal className="container">
        <div className="stats-strip">
          {FACTS.map(([value, label]) => (
            <div key={label} className="s">
              <b>{value}</b>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </Reveal>

      <section id="features" className="section">
        <div className="container">
          <Reveal className="section-head">
            <span className="eyebrow">What it does</span>
            <h2>Everything the utility team needs, in one calm place</h2>
            <p>Each capability runs on the live API. Open a screen and the numbers you see are the model's own output.</p>
          </Reveal>
          <Stagger className="features" inView gap={0.09}>
            {FEATURES.map((f) => (
              <Stagger.Item key={f.title} className="feature">
                <span className="ico" style={{ background: f.tone }}>
                  <f.icon size={24} aria-hidden="true" />
                </span>
                <h3>{f.title}</h3>
                <p>{f.text}</p>
                <div className="where">
                  <Link className="btn ghost sm" to={f.to}>
                    {f.go} <ArrowRight size={15} aria-hidden="true" />
                  </Link>
                </div>
              </Stagger.Item>
            ))}
          </Stagger>
        </div>
      </section>

      <section id="how" className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <Reveal className="section-head">
            <span className="eyebrow">How it works</span>
            <h2>From raw readings to a decision you can test</h2>
          </Reveal>
          <Stagger className="steps" inView gap={0.1}>
            {STEPS.map((s, i) => (
              <Stagger.Item key={s.title} className="step-card">
                <span className="n">0{i + 1}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </Stagger.Item>
            ))}
          </Stagger>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <Reveal className="cta">
            <Blobs preset="cta" />
            <h2>Take a look at your network</h2>
            <p>Sign in with a demo account and walk through every screen. The engineer account can run leak scenarios; the manager account can run what-if plans.</p>
            <Button size="lg" to={cta} iconRight={ArrowRight}>
              {user ? 'Open dashboard' : 'Sign in'}
            </Button>
          </Reveal>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <span>AquaVision · decision support for water distribution</span>
          <Link to={cta}>{user ? 'Open dashboard' : 'Sign in'}</Link>
        </div>
      </footer>
    </div>
  )
}
