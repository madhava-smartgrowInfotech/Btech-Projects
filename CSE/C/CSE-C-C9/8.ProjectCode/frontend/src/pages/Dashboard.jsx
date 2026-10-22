import { ArrowRight, Brain, ClipboardList, FlaskConical, Gauge, LineChart, ShieldCheck, Target, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { fmtPct, modelLabel } from '../lib/format'
import { Badge, Button, Card, PageHeader, StatCard, Skeleton } from '../components/ui'
import { Stagger, SlideUp } from '../components/motion'
import { BarCompare } from '../components/charts'
import Async from '../components/Async'
import { Disclaimer } from '../components/Common'

const CAPS = [
  { icon: ClipboardList, tone: 'mint', title: 'Financial profiling', to: '/app/assess', text: 'Classifies your profile as Emerging, Developing or Established with a confidence score and a Low / Moderate / High risk band.' },
  { icon: Brain, tone: 'peach', title: 'Explainable AI', to: '/app/explain', text: 'SHAP-based global importance and per-person explanations show which factors pushed your score up or down.' },
  { icon: TrendingUp, tone: 'sky', title: 'Forecasting', to: '/app/forecast', text: 'A Holt-Winters economic-indicator forecast with history, 12-month outlook, intervals and trend interpretation.' },
  { icon: FlaskConical, tone: 'rose', title: 'What-if scenarios', to: '/app/whatif', text: 'Adjust gains, losses, hours or education and re-run the model to compare baseline against scenario.' },
  { icon: Gauge, tone: 'butter', title: 'Validated properly', to: '/app/performance', text: 'Stratified 5-fold cross-validation with leakage-safe pipelines. Every metric comes from an actual run.' },
  { icon: ShieldCheck, tone: 'lavender', title: 'Responsible by design', to: '/app/about', text: 'Informational insights only - never loan approval, credit decisions or guaranteed returns.' },
]

function DashSkeleton() {
  return (
    <div className="stack" role="status" aria-label="Loading dashboard">
      <div className="grid-kpi">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="card">
            <Skeleton width="50%" height={14} />
            <Skeleton width="65%" height={30} style={{ marginTop: 14 }} />
            <Skeleton width="40%" height={12} style={{ marginTop: 14 }} />
          </div>
        ))}
      </div>
      <div className="grid-2">
        <div className="card"><Skeleton width="45%" height={18} /><Skeleton height={230} radius={18} style={{ marginTop: 18 }} /></div>
        <div className="card"><Skeleton width="45%" height={18} /><Skeleton height={230} radius={18} style={{ marginTop: 18 }} /></div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const state = useAsync(api.dashboard)
  return (
    <div className="stack" style={{ '--gap': '26px' }}>
      <PageHeader
        eyebrow="Dashboard"
        icon={Target}
        title="Understand your financial profile"
        lead="FinSight AI analyses demographic and financial factors to identify a financial profile, assess risk, explain the drivers and project economic trends."
        actions={<Button to="/app/assess" icon={ClipboardList}>Start assessment</Button>}
      />
      <Async state={state} skeleton={<DashSkeleton />} title="Could not load the dashboard">
        {(d) => {
          const m = d.metrics || {}
          const pct = (v) => `${(v * 100).toFixed(1)}%`
          const hasMetrics = m.accuracy != null
          const drivers = (d.shap_top || []).map((f, i) => ({ name: f.label, value: f.mean_abs_shap, highlight: i === 0 }))
          return (
            <>
              {hasMetrics ? (
                <Stagger className="grid-kpi">
                  <Stagger.Item><StatCard label="Serving model" display={modelLabel(d.model)} icon={Brain} tone="lavender" foot="Best by ROC-AUC" /></Stagger.Item>
                  <Stagger.Item><StatCard label="Accuracy" value={m.accuracy} format={pct} icon={Target} tone="mint" foot="Held-out test set" /></Stagger.Item>
                  <Stagger.Item><StatCard label="ROC-AUC" value={m.roc_auc} format={(v) => v.toFixed(3)} icon={LineChart} tone="sky" foot={`CV ${m.cv_roc_auc_mean?.toFixed(3)} ± ${m.cv_roc_auc_std?.toFixed(3)}`} /></Stagger.Item>
                  <Stagger.Item><StatCard label="F1 score" value={m.f1} format={(v) => v.toFixed(3)} icon={Gauge} tone="peach" foot={`Precision ${fmtPct(m.precision, 0)} · recall ${fmtPct(m.recall, 0)}`} /></Stagger.Item>
                </Stagger>
              ) : (
                <Card tint="peach">
                  <p>Model metrics are not available yet. Run <code>python scripts/train.py</code> to generate real results.</p>
                </Card>
              )}

              <div className="grid-2">
                <Card title="Top drivers in the trained model" subtitle="Mean absolute SHAP value across a training sample (global explanation)." actions={<Button to="/app/explain" variant="ghost" size="sm" iconRight={ArrowRight}>Open explainability</Button>}>
                  {drivers.length ? (
                    <BarCompare data={drivers} horizontal height={270} yWidth={190} valueFormat={(v) => Number(v).toFixed(2)} name="Mean |SHAP|" label="Top five model drivers by mean absolute SHAP value" />
                  ) : (
                    <p className="muted">Global SHAP data is not available.</p>
                  )}
                </Card>
                <Card title="Economic outlook" subtitle="Household Financial Conditions Index - 12-month Holt-Winters forecast." tint="sky" actions={d.outlook?.trend_direction && <Badge tone="mint">Trend: {d.outlook.trend_direction}</Badge>}>
                  {d.outlook?.interpretation ? (
                    <SlideUp className="stack" style={{ '--gap': '14px' }}>
                      <p>{d.outlook.interpretation}</p>
                      <div><Button to="/app/forecast" variant="secondary" iconRight={ArrowRight}>Explore the forecast</Button></div>
                    </SlideUp>
                  ) : (
                    <p className="muted">Forecast data is unavailable.</p>
                  )}
                </Card>
              </div>

              <section aria-labelledby="caps">
                <h2 id="caps" style={{ marginBottom: 14 }}>What you can do here</h2>
                <Stagger className="features" inView>
                  {CAPS.map((c) => (
                    <Stagger.Item key={c.title}>
                      <Link to={c.to} className="feature" style={{ display: 'block', textDecoration: 'none' }}>
                        <span className="ico" style={{ background: `var(--${c.tone})` }}><c.icon size={24} aria-hidden="true" /></span>
                        <h3>{c.title}</h3>
                        <p>{c.text}</p>
                      </Link>
                    </Stagger.Item>
                  ))}
                </Stagger>
              </section>
              <Disclaimer />
            </>
          )
        }}
      </Async>
    </div>
  )
}
