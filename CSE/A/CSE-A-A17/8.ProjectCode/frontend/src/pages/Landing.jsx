import { Link } from 'react-router-dom'
import { ArrowRight, BarChart3, FileSpreadsheet, Gauge, Shuffle, ShieldCheck, Sparkles, TrendingUp, UploadCloud } from 'lucide-react'
import { Button, Card, Container } from '../components/ui'
import { CountUp, InkRule, MagneticButton, MaskHeadline, Marquee, PageTransition, Parallax, Reveal, Stagger } from '../components/motion'

// Every figure below is a constant of the pipeline in src/ (feature_engineering.py, domain_adaptation.py, evaluation.py).
const FACTS = [
  ['Model', 'XGBoost', 'reg:squarederror'],
  ['Split', 'By date', 'first 80% train, last 20% test'],
  ['Lags', '1 · 7 · 14 · 28', 'days, per product'],
  ['Rolling', '7 · 14 · 28', 'mean, plus std on 7 and 28'],
  ['Weights', 'p / (1 − p)', 'clipped at 20'],
  ['MAPE', 'Safe', 'zero-demand rows excluded'],
]

const TICKER = [
  { label: 'Lag features', value: '1·7·14·28' },
  { label: 'Rolling windows', value: '7·14·28' },
  { label: 'Train / test', value: 'By date' },
  { label: 'Tuning', value: 'TimeSeriesSplit' },
  { label: 'Metrics', value: 'RMSE·MAE·MAPE·R²' },
  { label: 'Adaptation', value: 'Importance-weighted' },
]

const STEPS = [
  ['Upload', 'Bring transactions_train.csv and articles.csv (customers.csv is optional). Files are validated, cleaned and merged, and a data-quality report shows what changed.'],
  ['Explore', 'Daily, weekly and monthly demand, the top products, department, colour and sales-channel mix, and the price distribution.'],
  ['Aggregate', 'Transactions become units sold per product per day. Only same-day rows are counted, so no future information leaks in.'],
  ['Engineer', 'Calendar and cyclical features, plus lag and rolling features computed with a strict shift so a day never sees its own demand.'],
  ['Train', 'A moving-average baseline against XGBoost, optionally tuned with RandomizedSearchCV on time-ordered folds.'],
  ['Adapt', 'Pick a source and a target domain, measure the shift with a domain classifier, then re-weight the source rows that look like the target.'],
  ['Evaluate', 'RMSE, MAE, safe MAPE and R² for every model, before versus after adaptation, with real percentage changes.'],
  ['Forecast', 'Choose a product and a 7, 14 or 30 day horizon. Lags roll forward on the model’s own predictions.'],
]

const FEATURES = [
  [UploadCloud, 'Your data, not a demo', 'Nothing is hard-coded. Every chart, metric and forecast is computed from the files you upload.'],
  [ShieldCheck, 'No data leakage', 'Chronological split, shifted lags, TimeSeriesSplit tuning, and the domain column kept out of the features.'],
  [Shuffle, 'Domain adaptation', 'Instance weights from a logistic-regression domain classifier, applied through XGBoost sample weights.'],
  [Gauge, 'Honest metrics', 'Safe MAPE reports how many zero-demand rows it skipped. Improvements are shown as measured, up or down.'],
  [TrendingUp, 'Recursive forecasts', 'Seven, fourteen or thirty days ahead for any product with enough history.'],
  [Sparkles, 'Optional AI notes', 'Gemini explains the results in plain language from aggregated numbers only. Raw rows are never sent.'],
]

const COUNTS = [
  ['Calendar features', 14],
  ['Lag features', 4],
  ['Rolling statistics', 5],
  ['Evaluation metrics', 4],
]

export default function Landing() {
  return (
    <PageTransition>
      <section className="hero">
        <Container>
          <span className="eyebrow">Fashion demand · XGBoost · domain adaptation</span>
          <MaskHeadline as="h1" className="display-xl hero-title" lines={['Know what', 'sells next.']} />
          <div className="hero-grid">
            <div style={{ minWidth: 0 }}>
              <p className="lead" style={{ marginTop: 8 }}>
                TrendCast forecasts <span className="hl">daily product demand</span> from H&amp;M-style sales data, then shows how a model trained on one
                sales channel can be <span className="hl">adapted</span> to a shifted one, with every number measured on your own upload.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to="/app/upload" iconRight={ArrowRight}>
                    Upload your data
                  </Button>
                </MagneticButton>
                <MagneticButton>
                  <Button size="lg" to="/about" icon={FileSpreadsheet}>
                    How it works
                  </Button>
                </MagneticButton>
              </div>
            </div>
            <div style={{ position: 'relative', minWidth: 0 }}>
              <Parallax speed={0.25} style={{ position: 'absolute', right: -10, top: -34, zIndex: 0 }}>
                <div aria-hidden="true" style={{ width: 90, height: 90, background: 'var(--coral)', border: '3px solid var(--ink)' }} />
              </Parallax>
              <div className="checks-stack" style={{ position: 'relative', zIndex: 1 }} role="list" aria-label="Pipeline settings">
                {FACTS.map(([k, v, s]) => (
                  <div key={k} role="listitem">
                    <div className="k">{k}</div>
                    <div className="v">{v}</div>
                    <div className="tiny muted">{s}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Container>
      </section>

      <Marquee items={TICKER} label="Pipeline facts" />

      <section className="section" aria-labelledby="how">
        <Container>
          <div className="section-head">
            <MaskHeadline as="h2" className="display-lg" lines={['From CSV', 'to forecast']} scroll />
            <p className="lead muted" id="how">
              Eight steps, in order. Each one unlocks the next, and the app tells you what is missing.
            </p>
          </div>
          <div>
            {STEPS.map(([title, body], i) => (
              <Reveal key={title} className="how-step" y={36}>
                <span className="how-num" aria-hidden="true">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div>
                  <h3 className="display-sm">{title}</h3>
                  <p className="muted" style={{ marginTop: 8, maxWidth: '62ch' }}>
                    {body}
                  </p>
                </div>
              </Reveal>
            ))}
          </div>
        </Container>
      </section>

      <Container>
        <InkRule thick />
      </Container>

      <section className="section" aria-labelledby="features">
        <Container>
          <div className="section-head">
            <MaskHeadline as="h2" className="display-lg" lines={['Built to be', 'trusted']} scroll />
            <p className="lead muted" id="features">
              The project’s objectives, implemented end to end.
            </p>
          </div>
          <Stagger className="grid grid-3">
            {FEATURES.map(([Icon, title, body]) => (
              <Card key={title} hot className="feature-card" style={{ height: '100%' }}>
                <div className="feature-icon" aria-hidden="true">
                  <Icon size={26} />
                </div>
                <h3 className="card-title">{title}</h3>
                <p className="muted" style={{ marginTop: 8 }}>
                  {body}
                </p>
              </Card>
            ))}
          </Stagger>
        </Container>
      </section>

      <Container>
        <InkRule thick />
      </Container>

      <section className="section" aria-labelledby="numbers">
        <Container>
          <div className="section-head">
            <h2 className="display-lg" id="numbers">
              Inside the model
            </h2>
            <p className="muted small mono">Fixed by the pipeline code in src/feature_engineering.py and src/evaluation.py.</p>
          </div>
          <Reveal className="stats-strip">
            {COUNTS.map(([k, v]) => (
              <div key={k} className="stat">
                <span className="stat-label">{k}</span>
                <CountUp className="stat-value" value={v} />
              </div>
            ))}
          </Reveal>
        </Container>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <Container>
          <Reveal className="cta-block">
            <h2 className="display-lg" style={{ color: 'var(--ink)' }}>
              Bring your CSVs.
            </h2>
            <p className="lead" style={{ margin: '16px 0 28px' }}>
              Start with transactions and articles. The app walks you from cleaning to a 30-day forecast.
            </p>
            <div className="hero-actions" style={{ marginTop: 0 }}>
              <Button variant="secondary" size="lg" to="/app/upload" iconRight={ArrowRight}>
                Start now
              </Button>
              <Button size="lg" to="/app" icon={BarChart3}>
                Open the dashboard
              </Button>
            </div>
          </Reveal>
        </Container>
      </section>

      <footer className="footer">
        <Container>
          <div className="footer-grid">
            <div>
              <h4>TrendCast</h4>
              <p className="footer-note">Fashion Demand Forecasting Using Machine Learning and Domain Adaptation. CSE-A-A17.</p>
            </div>
            <div>
              <h4>Pipeline</h4>
              <ul>
                <li>
                  <Link to="/app/upload">Data upload</Link>
                </li>
                <li>
                  <Link to="/app/training">Model training</Link>
                </li>
                <li>
                  <Link to="/app/domain">Domain adaptation</Link>
                </li>
                <li>
                  <Link to="/app/forecast">Demand forecast</Link>
                </li>
              </ul>
            </div>
            <div>
              <h4>Project</h4>
              <ul>
                <li>
                  <Link to="/about">About</Link>
                </li>
              </ul>
            </div>
          </div>
        </Container>
      </footer>
    </PageTransition>
  )
}
