import { ArrowRight, Check } from 'lucide-react'
import { Alert, Badge, Button, Card, ErrorState, PageHeader, Skeleton, Stepper } from '../components/ui'
import { Stagger } from '../components/motion'
import { usePipeline } from '../lib/pipeline'
import { APP_NAV } from '../components/ui/Layout'

const COPY = {
  '/app/upload': 'Upload transactions and articles (customers optional). Validate, clean and merge them.',
  '/app/explore': 'Daily, weekly and monthly demand, top products, category and channel mix, prices.',
  '/app/demand': 'The aggregated daily demand table and a note on why it is leakage-free.',
  '/app/features': 'Build calendar, cyclical, lag, rolling and encoded product features.',
  '/app/training': 'Chronological split, moving-average baseline, XGBoost with optional tuning.',
  '/app/domain': 'Measure distribution shift and train an importance-weighted adapted model.',
  '/app/evaluation': 'Compare models, see before versus after adaptation, and feature importance.',
  '/app/forecast': 'Forecast 7, 14 or 30 days for any product with enough history.',
  '/app/insights': 'Optional Gemini explanations of the results, in plain language.',
}

const STEPS = ['Upload', 'Features', 'Train', 'Adapt', 'Forecast']

function currentStep(s) {
  if (!s) return 0
  if (s.forecast_done) return 5
  if (s.domain_done) return 4
  if (s.xgboost_trained) return 3
  if (s.features_ready) return 2
  if (s.data_loaded) return 1
  return 0
}

function nextAction(s) {
  if (!s.data_loaded) return ['/app/upload', 'Upload your CSVs', 'Nothing is loaded yet. Start by uploading transactions and articles.']
  if (!s.features_ready) return ['/app/features', 'Build the feature table', 'Data is loaded. Build the lag, rolling and calendar features next.']
  if (!s.xgboost_trained) return ['/app/training', 'Train the models', 'Features are ready. Run the baseline and train XGBoost.']
  if (!s.domain_done) return ['/app/domain', 'Run domain adaptation', 'XGBoost is trained. Measure the shift between two domains and adapt.']
  if (!s.forecast_done) return ['/app/forecast', 'Generate a forecast', 'Everything is trained. Forecast a product for the next 7 to 30 days.']
  return ['/app/evaluation', 'Review the evaluation', 'The pipeline is complete. Compare models and read the feature importance.']
}

export default function Overview() {
  const { state, error, refresh } = usePipeline()

  if (error) return <ErrorState title="The API is not reachable" error={error} onRetry={refresh} />
  if (!state) return <Skeleton height={240} />

  const [to, label, text] = nextAction(state)
  const steps = APP_NAV.filter((n) => n.step)
  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title="Pipeline"
        description="Move through the stages in order. Each one unlocks the next, and this page shows where you are."
      />
      <div className="page-stack">
        <Card tone="lime" title="Next step">
          <div className="row-between">
            <p style={{ maxWidth: '60ch', fontWeight: 600 }}>{text}</p>
            <Button variant="secondary" to={to} iconRight={ArrowRight}>
              {label}
            </Button>
          </div>
        </Card>

        <Card title="Progress">
          <Stepper steps={STEPS} current={currentStep(state)} label="Pipeline progress" />
        </Card>

        {!state.gemini_configured && (
          <Alert tone="info">AI Insights is optional and not configured. Add GEMINI_API_KEY to .env to enable it. Every other page works without it.</Alert>
        )}

        <Stagger className="grid grid-3">
          {steps.map((n) => {
            const done = n.done && state[n.done]
            const Icon = n.icon
            return (
              <Card key={n.to} className={`step-card ${done ? 'is-done' : ''}`} hot>
                <div className="row-between">
                  <span className="step-no" aria-hidden="true">
                    {n.step}
                  </span>
                  <Icon size={22} aria-hidden="true" />
                </div>
                <h3 className="card-title">{n.label}</h3>
                <p>{COPY[n.to]}</p>
                <div className="row-between">
                  {n.done ? (
                    done ? (
                      <Badge tone="pass">
                        <Check size={12} strokeWidth={3} aria-hidden="true" /> Done
                      </Badge>
                    ) : (
                      <Badge>To do</Badge>
                    )
                  ) : (
                    <Badge tone="info">Optional</Badge>
                  )}
                  <Button size="sm" to={n.to} iconRight={ArrowRight}>
                    Open
                  </Button>
                </div>
              </Card>
            )
          })}
        </Stagger>
      </div>
    </>
  )
}
