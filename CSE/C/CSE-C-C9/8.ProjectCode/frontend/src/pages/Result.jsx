import { lazy, Suspense } from 'react'
import { ArrowRight, Brain, ClipboardList, FlaskConical, Lightbulb, TrendingDown, TrendingUp } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { loadResult } from '../lib/baseline'
import { fmtSigned } from '../lib/format'
import { Button, Card, EmptyState, ErrorState, KeyValueList, PageHeader, ProgressBar, Skeleton } from '../components/ui'
import { CountUp, SlideUp, Stagger } from '../components/motion'
import { Disclaimer, FIELD_LABELS, ProfileBadge, RiskBadge } from '../components/Common'

const ForecastChart = lazy(() => import('../components/charts/ForecastChart'))

function FactorList({ items, max, tone }) {
  return (
    <ul className="stack" style={{ listStyle: 'none', padding: 0, margin: 0, '--gap': '14px' }}>
      {items.map((f) => (
        <li key={f.feature}>
          <div className="row between" style={{ '--gap': '8px', alignItems: 'baseline' }}>
            <strong>{f.label}</strong>
            <span className="num small" style={{ color: `var(--${tone}-ink)`, fontWeight: 700 }}>{fmtSigned(f.shap, 3, '')}</span>
          </div>
          <div className="progress" style={{ height: 8, marginTop: 6 }} aria-hidden="true">
            <div className="progress-fill" style={{ width: `${Math.max(4, (Math.abs(f.shap) / max) * 100)}%`, background: `var(--${tone})` }} />
          </div>
          <p className="small muted" style={{ marginTop: 6 }}>{f.sentence}</p>
        </li>
      ))}
    </ul>
  )
}

function MiniForecast() {
  const state = useAsync(api.forecast)
  if (state.loading) return <Skeleton height={280} radius={18} />
  if (state.error) return <ErrorState compact title="Forecast unavailable" error={state.error} onRetry={state.reload} />
  const f = state.data
  if (!f.available) return <p className="muted">{f.interpretation}</p>
  return (
    <div className="stack" style={{ '--gap': '14px' }}>
      <p>{f.interpretation}</p>
      <Suspense fallback={<Skeleton height={280} radius={18} />}>
        <ForecastChart history={f.history} forecast={f.forecast} sinceYear={2023} height={280} />
      </Suspense>
      <div><Button to="/app/forecast" variant="secondary" iconRight={ArrowRight}>Full forecast</Button></div>
    </div>
  )
}

export default function Result() {
  const r = loadResult()
  if (!r) {
    return (
      <div className="stack">
        <PageHeader eyebrow="Result" icon={ClipboardList} title="Your financial profile" />
        <EmptyState
          icon={ClipboardList}
          title="No assessment yet"
          message="Run an assessment first - your profile, risk band and the factors behind your score will appear here."
          action={<Button to="/app/assess" icon={ClipboardList}>Start assessment</Button>}
        />
      </div>
    )
  }
  const shap = r.shap || {}
  const all = [...(shap.positives || []), ...(shap.negatives || [])]
  const max = Math.max(0.001, ...all.map((f) => Math.abs(f.shap)))
  const tone = { Low: 'mint', Moderate: 'peach', High: 'rose' }[r.risk] || 'lavender'

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        crumbs={[{ label: 'Assessment', to: '/app/assess' }, { label: 'Result' }]}
        eyebrow="Result"
        icon={ClipboardList}
        title="Your financial profile"
        lead="A model-based estimate from the trained classifier. Use it as an informational pattern, not a judgement."
        actions={<Button to="/app/assess" variant="secondary" icon={ClipboardList}>Edit inputs</Button>}
      />

      <div className="grid-2">
        <SlideUp>
          <Card tint={tone} hover={false} title="Predicted profile" subtitle={`Model: ${r.model}`}>
            <div className="stack" style={{ '--gap': '14px' }}>
              <div className="row" style={{ '--gap': '10px' }}>
                <h2 style={{ fontSize: 'clamp(30px, 5vw, 42px)', fontWeight: 800 }}>{r.profile}</h2>
                <RiskBadge risk={r.risk} />
              </div>
              <div>
                <div className="row between" style={{ marginBottom: 8 }}>
                  <span className="small">Financial-strength score</span>
                  <strong className="stat-value" style={{ margin: 0, fontSize: 28 }}>
                    <CountUp value={r.strength_pct} format={(v) => `${v.toFixed(1)}%`} />
                  </strong>
                </div>
                <ProgressBar value={r.strength_pct} max={100} tone={tone} label="Financial-strength score" height={14} />
                <p className="small muted" style={{ marginTop: 8 }}>
                  Model confidence {r.proba}. Risk band: strength ≥ 60% → Low, 35–60% → Moderate, &lt; 35% → High.
                </p>
              </div>
              <div className="row">
                <Button to="/app/whatif" icon={FlaskConical}>Try a what-if scenario</Button>
                <Button to="/app/explain" variant="secondary" icon={Brain}>Why this result?</Button>
              </div>
            </div>
          </Card>
        </SlideUp>

        <SlideUp delay={0.08}>
          <Card hover={false} title="What shaped your score" subtitle="Live SHAP contributions for this profile. They show associations, not causation.">
            {shap.available ? (
              <div className="stack" style={{ '--gap': '20px' }}>
                {shap.positives?.length > 0 && (
                  <div>
                    <h3 className="row" style={{ '--gap': '8px', marginBottom: 12, color: 'var(--mint-ink)' }}><TrendingUp size={18} aria-hidden="true" />Strengthening factors</h3>
                    <FactorList items={shap.positives} max={max} tone="mint" />
                  </div>
                )}
                {shap.negatives?.length > 0 && (
                  <div>
                    <h3 className="row" style={{ '--gap': '8px', marginBottom: 12, color: 'var(--rose-ink)' }}><TrendingDown size={18} aria-hidden="true" />Weakening factors</h3>
                    <FactorList items={shap.negatives} max={max} tone="rose" />
                  </div>
                )}
              </div>
            ) : (
              <p className="muted">{shap.note || 'Local explanation unavailable.'}</p>
            )}
          </Card>
        </SlideUp>
      </div>

      <Card hover={false} title="Actionable insights" subtitle="Informational only.">
        <Stagger className="stack" style={{ '--gap': '12px' }}>
          {r.insights.map((tip) => (
            <Stagger.Item key={tip} className="row" style={{ '--gap': '12px', alignItems: 'flex-start', flexWrap: 'nowrap' }}>
              <span className="stat-ico" style={{ background: 'var(--butter)', width: 32, height: 32, borderRadius: 11 }}><Lightbulb size={16} aria-hidden="true" /></span>
              <p style={{ flex: 1 }}>{tip}</p>
            </Stagger.Item>
          ))}
        </Stagger>
      </Card>

      <div className="grid-2">
        <Card hover={false} title="Your inputs">
          <KeyValueList items={Object.entries(r.inputs).map(([k, v]) => [FIELD_LABELS[k] || k, typeof v === 'number' && k.startsWith('capital') ? `$${v.toLocaleString('en-US')}` : String(v)])} />
        </Card>
        <Card hover={false} tint="sky" title="Economic outlook" subtitle="12-month index forecast (illustrative Household Financial Conditions Index).">
          <MiniForecast />
        </Card>
      </div>
      <Disclaimer />
    </div>
  )
}
