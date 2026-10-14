import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BedDouble, BrainCircuit, Gauge, HeartPulse, LayoutDashboard, LogIn, Users, Workflow } from 'lucide-react'
import api, { errorMessage } from '../api'
import { useAuth } from '../lib/auth'
import { PublicShell } from '../components/ui/Layout'
import { Button } from '../components/ui/Button'
import { Alert, SkeletonBlock } from '../components/ui/Feedback'
import { Card } from '../components/ui/Display'
import { CountUp, FadeIn, InkRule, MagneticButton, MaskHeadline, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'

const MARQUEE = [
  { label: 'Length of stay', value: 'with reasons' },
  { label: 'Ward census', value: '14 days' },
  { label: 'ICU', value: 'early warning' },
  { label: 'Staff and equipment', value: 'per shift' },
  { label: 'Allocation', value: 'optimised' },
]

const FACTS = [
  ['Facilities', 'A to E'],
  ['Forecast window', '14 days'],
  ['Ward types', '5, incl. ICU'],
  ['Every number', 'explained'],
]

const FEATURES = [
  { icon: BrainCircuit, title: 'Length-of-stay prediction', text: 'Expected days and short or long stay at admission, with the clinical factors behind every estimate.' },
  { icon: BedDouble, title: 'Occupancy forecast', text: '14-day bed occupancy per ward, from current patients, their predicted stays and forecast admissions, with 90% bands.' },
  { icon: HeartPulse, title: 'ICU early warning', text: 'Expected ICU beds needed per facility, and a warning on the first day demand can pass capacity.' },
  { icon: Users, title: 'Staff and equipment demand', text: 'Nurses per shift at safe ratios, plus ventilators, monitors, infusion pumps and dialysis machines.' },
  { icon: Workflow, title: 'Allocation recommendations', text: 'An optimiser proposes bed conversions, diversions, nurse floats, extra shifts and equipment moves, and explains the trade-off.' },
  { icon: Gauge, title: 'Measured accuracy', text: 'Prediction error, forecast error against naive baselines, and the gain over a static allocation.' },
]

const STEPS = [
  ['Admit', 'A clinician enters the admission. The model returns expected days, an 80% range and the factors behind the estimate.'],
  ['Forecast', 'Current patients, their predicted stays and forecast admissions give the 14-day census for every ward, with 90% bands.'],
  ['Warn', 'The first day that a ward or the ICU can pass capacity raises an early warning, before the bed is needed.'],
  ['Plan', 'The optimiser recommends bed, nurse and equipment moves. An administrator accepts the plan or edits it first.'],
]

export default function Landing() {
  const { user } = useAuth()
  const [metrics, setMetrics] = useState(null)
  const [metricsError, setMetricsError] = useState('')
  const target = user ? '/dashboard' : '/login'

  useEffect(() => {
    if (!user) return undefined
    let live = true
    api
      .get('/metrics')
      .then(({ data }) => live && setMetrics(data))
      .catch((err) => live && setMetricsError(errorMessage(err)))
    return () => {
      live = false
    }
  }, [user])

  const ev = metrics?.evaluation
  const los = ev?.length_of_stay
  const cf = ev?.census_forecast
  const ru = ev?.resource_use

  return (
    <PublicShell>
      <section className="hero container">
        <div className="hero-grid">
          <div>
            <FadeIn>
              <span className="eyebrow">Hospital capacity, decision support</span>
            </FadeIn>
            <MaskHeadline as="h1" className="hero-title display-xl" lines={['Know the beds', 'before they', 'run out.']} />
            <SlideUp delay={0.3}>
              <p className="lead">
                HospiSense predicts each patient&apos;s length of stay, forecasts ward and ICU occupancy for the next 14 days, and recommends how to allocate
                beds, nurses and equipment, with the reasons behind every number.
              </p>
            </SlideUp>
            <div className="hero-actions">
              <MagneticButton>
                <Button variant="primary" size="lg" to={target} icon={user ? LayoutDashboard : LogIn}>
                  {user ? 'Open dashboard' : 'Sign in to HospiSense'}
                </Button>
              </MagneticButton>
              <Button size="lg" href="#how">
                How it works
              </Button>
            </div>
          </div>
          <SlideUp delay={0.2}>
            <div className="checks-stack">
              {FACTS.map(([k, v]) => (
                <div key={k}>
                  <div className="k">{k}</div>
                  <div className="v">{v}</div>
                </div>
              ))}
            </div>
          </SlideUp>
        </div>
      </section>

      <Marquee items={MARQUEE} />

      <section id="features" className="section container">
        <Reveal>
          <div className="section-head">
            <h2 className="display-md">Built for bed managers, doctors and planners</h2>
            <p className="lead">Each screen answers one question: how many beds, who is admitted, what to move, and how well the model has done.</p>
          </div>
        </Reveal>
        <Stagger className="grid grid-3" style={{ '--gap': '20px' }}>
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <Card key={title} hot className="feature-card">
              <span className="feature-icon" aria-hidden="true">
                <Icon size={26} />
              </span>
              <h3 className="display-sm" style={{ fontSize: '1.45rem' }}>
                {title}
              </h3>
              <p className="small" style={{ marginTop: 10 }}>
                {text}
              </p>
            </Card>
          ))}
        </Stagger>
      </section>

      <section id="how" className="section container">
        <InkRule thick />
        <Reveal>
          <div className="section-head" style={{ marginTop: 40 }}>
            <h2 className="display-md">From admission to plan</h2>
          </div>
        </Reveal>
        {STEPS.map(([title, text], i) => (
          <Reveal key={title} y={24}>
            <div className="how-step">
              <span className="how-num" aria-hidden="true">
                {String(i + 1).padStart(2, '0')}
              </span>
              <div style={{ minWidth: 0 }}>
                <h3 className="display-sm">{title}</h3>
                <p className="lead" style={{ marginTop: 8 }}>
                  {text}
                </p>
              </div>
            </div>
          </Reveal>
        ))}
      </section>

      <section className="section container" aria-labelledby="accuracy-title">
        <Reveal>
          <div className="section-head">
            <div>
              <h2 id="accuracy-title" className="display-md">
                Measured accuracy
              </h2>
              <p className="small muted" style={{ marginTop: 10 }}>
                Held-out records, never used in training.
              </p>
            </div>
          </div>
        </Reveal>
        {!user && (
          <p className="lead">
            <Link to="/login">Sign in</Link> to see the measured accuracy from the evaluation run.
          </p>
        )}
        {user && metricsError && <Alert tone="error">Could not load the measured accuracy. {metricsError}</Alert>}
        {user && !metricsError && !metrics && <SkeletonBlock rows={2} label="Loading measured accuracy" />}
        {user && metrics && !ev && (
          <Alert tone="warning">Evaluation results are not in the project yet. Run ml\eval.py to produce them.</Alert>
        )}
        {user && ev && (
          <div className="stats-strip">
            <div>
              <div className="stat-label">Length-of-stay error</div>
              <div className="stat-value">
                <CountUp value={los.mae_days} decimals={2} /> d
              </div>
              <p className="tiny muted">Mean absolute error per stay</p>
            </div>
            <div>
              <div className="stat-label">Stays within 1 day</div>
              <div className="stat-value">
                <CountUp value={los.within_1_day * 100} decimals={1} />%
              </div>
              <p className="tiny muted">Share of held-out predictions</p>
            </div>
            <div>
              <div className="stat-label">Census error</div>
              <div className="stat-value">
                <CountUp value={cf.mae_overall.model} decimals={2} />
              </div>
              <p className="tiny muted">Beds per ward, averaged over 1 to 14 days</p>
            </div>
            <div>
              <div className="stat-label">Patient-days without a bed</div>
              <div className="stat-value">
                <CountUp value={ru.reduction.patient_days_without_bed * 100} decimals={1} />%
              </div>
              <p className="tiny muted">Fewer than the static allocation</p>
            </div>
          </div>
        )}
      </section>

      <section className="section container">
        <div className="cta-block">
          <h2 className="display-md">Ready for the next admission?</h2>
          <p className="lead" style={{ marginTop: 12 }}>
            Sign in, predict the stay, then check the forecast for the coming fortnight.
          </p>
          <div className="hero-actions">
            <Button variant="secondary" size="lg" to={target} icon={user ? LayoutDashboard : LogIn}>
              {user ? 'Open dashboard' : 'Sign in'}
            </Button>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container footer-grid">
          <div>
            <h4>HospiSense</h4>
            <p className="small">
              Decision support only. Every prediction and recommendation supports, and does not replace, qualified clinical and operational judgement.
            </p>
          </div>
          <div>
            <h4>Screens</h4>
            <ul>
              <li>
                <Link to="/dashboard">Dashboard</Link>
              </li>
              <li>
                <Link to="/admissions">Admissions</Link>
              </li>
              <li>
                <Link to="/forecasts">Forecasts</Link>
              </li>
              <li>
                <Link to="/allocation">Allocation</Link>
              </li>
              <li>
                <Link to="/performance">Model performance</Link>
              </li>
            </ul>
          </div>
        </div>
      </footer>
    </PublicShell>
  )
}
