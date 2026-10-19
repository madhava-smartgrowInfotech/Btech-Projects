import { useEffect, useMemo } from 'react'
import { ArrowDownRight, ArrowRight, ArrowUpRight, BarChart3, BrainCircuit, CalendarClock, Database, MessageSquareText, Network, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react'
import { Badge, Brand, Button, Container, ErrorState, Skeleton, ThemeToggle } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import { ForecastChart } from '../components/charts'
import Blobs from '../components/reactbits/Blobs'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { allModels, buildSeries, companyOf } from '../lib/market'
import { dateLabel, fmtInt, fmtUSD } from '../lib/format'

const FEATURES = [
  { icon: TrendingUp, tone: 'var(--mint)', title: 'Forecasts with honest bands', text: 'Five-day and thirty-day closing-price forecasts, drawn with a confidence band so uncertainty is part of the picture.', to: '/app/forecast', cta: 'Open forecasts' },
  { icon: BarChart3, tone: 'var(--sky)', title: 'Every model on the table', text: 'The hybrid deep model is scored against ARIMA, SARIMAX, Prophet, Random Forest and SVR on the same held-out data.', to: '/app/models', cta: 'Compare models' },
  { icon: MessageSquareText, tone: 'var(--peach)', title: 'News tone, scored by FinBERT', text: 'Headlines are scored for sentiment and fed to the model as an extra channel. You can read the headlines yourself.', to: '/app/sentiment', cta: 'See sentiment' },
  { icon: Network, tone: 'var(--lavender)', title: 'Federated training', text: 'Each ticker trains locally and the weights are averaged with FedAvg. The rounds and loss curves are all visible.', to: '/app/models?tab=training', cta: 'View training' },
  { icon: Database, tone: 'var(--rose)', title: 'Clear about its data', text: 'Every series says whether it is live, bundled or synthetic, and the news source is always labelled.', to: '/app/about', cta: 'Method and data' },
  { icon: ShieldCheck, tone: 'var(--butter)', title: 'Built for learning', text: 'A research and education tool. Nothing here is financial advice, and the app says so.', to: '/app/about', cta: 'Read the notes' },
]

const STEPS = [
  { n: '01', icon: Database, tone: 'var(--sky)', title: 'Ingest', text: 'Daily prices for the ticker universe plus financial headlines.' },
  { n: '02', icon: BrainCircuit, tone: 'var(--lavender)', title: 'Model', text: 'Baselines, an LSTM, attention, sentiment and a federated hybrid.' },
  { n: '03', icon: CalendarClock, tone: 'var(--mint)', title: 'Forecast', text: 'Five- and thirty-day closes with confidence bands and a trend call.' },
  { n: '04', icon: Sparkles, tone: 'var(--peach)', title: 'Explain', text: 'Side-by-side accuracy, training curves and the headlines behind the tone.' },
]

export default function Landing() {
  const live = useAsync(async (signal) => {
    const [tickers, metrics] = await Promise.all([api.tickers({ signal }), api.metrics({ signal })])
    const first = tickers.tickers[0]?.ticker
    const hist = first ? await api.history(first, 250, { signal }) : null
    return { tickers: tickers.tickers, metrics, hist, first }
  }, [])

  useEffect(() => {
    document.title = 'QuantPulse · Stock trend forecasting'
  }, [])

  const stats = useMemo(() => {
    const d = live.data
    if (!d) return null
    const ms = Object.values(d.metrics)
    return {
      tickers: d.tickers.length,
      up: d.tickers.filter((t) => t.trend === 'up').length,
      models: ms[0] ? allModels(ms[0]).length : 0,
      headlines: ms.reduce((a, m) => a + (m.sentiment?.n_headlines || 0), 0),
    }
  }, [live.data])

  const preview = useMemo(() => {
    const d = live.data
    const m = d?.metrics[d.first]
    if (!d?.hist?.history.length || !m?.forecast_short?.length) return null
    const s = buildSeries(d.hist.history, m.forecast_short, m.last_close, 70)
    return { ...s, base: m.last_close, end: s.rows[s.rows.length - 1] }
  }, [live.data])

  const heroMetrics = live.data ? live.data.metrics[live.data.first] : null

  return (
    <div className="landing">
      <a className="skip-link" href="#top">Skip to content</a>
      <header className="l-nav">
        <Container>
          <Brand />
          <nav className="l-nav-links" aria-label="Sections">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#universe">Tickers</a>
          </nav>
          <span style={{ flex: 1 }} />
          <ThemeToggle />
          <Button to="/app" icon={ArrowRight} className="btn-open-app" size="sm">
            <span>Open app</span>
          </Button>
        </Container>
      </header>

      <main id="top" tabIndex={-1}>
        <section className="hero">
          <Blobs preset="hero" />
          <Container>
            <div className="hero-grid">
              <div>
                <SlideUp>
                  <Badge tone="lavender" icon={Sparkles}>5-day and 30-day stock trend forecasts</Badge>
                </SlideUp>
                <SlideUp delay={0.08}>
                  <h1 style={{ marginTop: 18 }}>
                    Stock forecasts you can <span className="hl">actually read</span>
                  </h1>
                </SlideUp>
                <SlideUp delay={0.16}>
                  <p className="hero-lead">
                    QuantPulse turns price history and news tone into short-term forecasts with confidence bands, then shows exactly how each model scored against the classics.
                  </p>
                </SlideUp>
                <SlideUp delay={0.24} className="hero-cta">
                  <MagneticButton>
                    <Button to="/app" size="lg" icon={TrendingUp}>Open the dashboard</Button>
                  </MagneticButton>
                  <Button to="/app/models" size="lg" variant="secondary" icon={BarChart3}>Compare the models</Button>
                </SlideUp>
                <SlideUp delay={0.32} className="hero-note">
                  <Badge tone="mint" dot>Research and education tool</Badge>
                  <Badge tone="sky" dot>{live.data ? `${stats.tickers} tickers modelled` : 'Live from the API'}</Badge>
                </SlideUp>
              </div>

              <SlideUp delay={0.2} className="hero-visual">
                <div className="hero-card">
                  <div className="hero-preview-head">
                    <div>
                      <b>{live.data?.first || 'Forecast preview'}</b>
                      <div className="small muted">{live.data ? companyOf(live.data.first) : 'Loading'}</div>
                    </div>
                    {heroMetrics && (
                      <Badge tone={heroMetrics.trend === 'up' ? 'mint' : 'rose'} icon={heroMetrics.trend === 'up' ? ArrowUpRight : ArrowDownRight}>
                        {heroMetrics.trend === 'up' ? 'Trend up' : 'Trend down'}
                      </Badge>
                    )}
                  </div>
                  {live.loading && !live.data && <Skeleton height={260} radius={18} />}
                  {live.error && <ErrorState compact title="API not reachable" error={live.error} onRetry={live.reload} />}
                  {preview && (
                    <ForecastChart
                      height={260}
                      data={preview.data}
                      splitAt={preview.anchored ? preview.cutoff : undefined}
                      valueFormat={(v) => fmtUSD(v, 0)}
                      xFormat={(v, long) => dateLabel(v, long)}
                      label={`${live.data.first} recent closes with a five-day forecast`}
                    />
                  )}
                  {preview && (
                    <>
                      <div className="hero-float b">
                        <div>
                          <b>{fmtUSD(preview.base)}</b>
                          <span>close at forecast</span>
                        </div>
                      </div>
                      <div className="hero-float a">
                        <div>
                          <b>{fmtUSD(preview.end.predicted_close)}</b>
                          <span>forecast, day {preview.end.day}</span>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </SlideUp>
            </div>
          </Container>
        </section>

        {stats && (
          <section className="section" style={{ paddingTop: 0 }} aria-label="QuantPulse in numbers">
            <Container>
              <Reveal>
                <div className="stats-strip">
                  <div className="s"><b><CountUp value={stats.tickers} format={fmtInt} /></b><span>tickers modelled</span></div>
                  <div className="s"><b><CountUp value={stats.models} format={fmtInt} /></b><span>models scored per ticker</span></div>
                  <div className="s"><b><CountUp value={stats.headlines} format={fmtInt} /></b><span>headlines scored</span></div>
                  <div className="s"><b><CountUp value={stats.up} format={fmtInt} /> of {stats.tickers}</b><span>trending up</span></div>
                </div>
              </Reveal>
            </Container>
          </section>
        )}

        <section className="section" id="features">
          <Container>
            <Reveal className="section-head">
              <Badge tone="mint">What you get</Badge>
              <h2>Clear forecasts, plainly explained</h2>
              <p>Every number on screen comes straight from the trained models, with the working shown.</p>
            </Reveal>
            <Stagger className="features" inView>
              {FEATURES.map((f) => (
                <Stagger.Item key={f.title}>
                  <article className="feature">
                    <span className="ico" style={{ background: f.tone }}><f.icon size={24} aria-hidden="true" /></span>
                    <h3>{f.title}</h3>
                    <p>{f.text}</p>
                    <div className="where"><Button to={f.to} variant="ghost" size="sm" iconRight={ArrowRight}>{f.cta}</Button></div>
                  </article>
                </Stagger.Item>
              ))}
            </Stagger>
          </Container>
        </section>

        <section className="section" id="how" style={{ background: 'var(--bg-tint)' }}>
          <Container>
            <Reveal className="section-head">
              <Badge tone="sky">How it works</Badge>
              <h2>From raw prices to a forecast you can check</h2>
            </Reveal>
            <Reveal>
              <div className="steps-line" aria-hidden="true"><div /></div>
              <div className="steps">
                {STEPS.map((s) => (
                  <div key={s.n} className="step-card">
                    <span className="n">{s.n}</span>
                    <h3>{s.title}</h3>
                    <p>{s.text}</p>
                    <span className="ico" style={{ background: s.tone }}><s.icon size={22} aria-hidden="true" /></span>
                  </div>
                ))}
              </div>
            </Reveal>
          </Container>
        </section>

        <section className="section" id="universe">
          <Container>
            <Reveal className="section-head">
              <Badge tone="peach">The universe</Badge>
              <h2>The closes the models forecast from</h2>
              <p>One chip per ticker, with its trend. Hover to pause, and open the dashboard for each outlook.</p>
            </Reveal>
            {live.loading && !live.data && <Skeleton height={48} radius={999} />}
            {live.data && (
              <Marquee speed={45}>
                {live.data.tickers.map((t) => (
                  <span key={t.ticker} className="chip">
                    <b>{t.ticker}</b>
                    {fmtUSD(t.last_close)}
                    {t.trend === 'up' ? <ArrowUpRight size={15} color="var(--mint-ink)" aria-label="trend up" /> : <ArrowDownRight size={15} color="var(--rose-ink)" aria-label="trend down" />}
                  </span>
                ))}
              </Marquee>
            )}
          </Container>
        </section>

        <section className="section" style={{ paddingTop: 0 }}>
          <Container>
            <Reveal>
              <div className="cta">
                <Blobs preset="cta" />
                <h2>See what the models see</h2>
                <p>Open the dashboard, pick a ticker and compare the hybrid model with the classics. No sign-up needed.</p>
                <MagneticButton>
                  <Button to="/app" size="lg" variant="mint" iconRight={ArrowRight}>Open QuantPulse</Button>
                </MagneticButton>
              </div>
            </Reveal>
          </Container>
        </section>
      </main>

      <footer className="footer">
        <Container>
          <span>QuantPulse · short-term stock forecasting for research and education.</span>
          <span>Not financial advice.</span>
        </Container>
      </footer>
    </div>
  )
}
