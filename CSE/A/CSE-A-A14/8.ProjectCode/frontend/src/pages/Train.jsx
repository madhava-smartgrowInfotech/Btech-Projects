import { useEffect, useState } from 'react'
import { ArrowRight, BrainCircuit, Rocket, Save, Star } from 'lucide-react'
import { PageHeader, Badge, Button, Card, Checkbox, ErrorState, Segmented, Select, Skeleton, StatCard, Table, useToast } from '../components/ui'
import { Callout, Gate, Slider } from '../components/app'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { celebrate, useAppState } from '../lib/appstate'
import { useAsync } from '../lib/hooks'
import { fmtInt, fmtNum } from '../lib/format'

const IMBALANCE = [
  { value: 'class_weight', label: 'Class weights' },
  { value: 'smote', label: 'SMOTE' },
  { value: 'none', label: 'None' },
]
const METRICS = [
  { value: 'f1_score', label: 'F1-score (default)' },
  { value: 'roc_auc', label: 'ROC-AUC' },
  { value: 'recall', label: 'Recall' },
  { value: 'precision', label: 'Precision' },
  { value: 'accuracy', label: 'Accuracy' },
]
const ALL_MODELS = ['Logistic Regression', 'Decision Tree', 'Random Forest', 'Gradient Boosting', 'Hist Gradient Boosting']
const REQUIRED = ALL_MODELS.slice(0, 3)

export default function Train() {
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Models"
        icon={BrainCircuit}
        title="Model training"
        lead="Train several classifiers on the same split so the comparison is fair, then save the one you want to use across the app. The best model is chosen on more than accuracy."
      />
      <Gate need="data">
        <TrainBody />
      </Gate>
    </div>
  )
}

function TrainBody() {
  const toast = useToast()
  const { state, refresh, hasTrial } = useAppState()
  const overview = useAsync(() => api.dashboard(), [])
  const cfg = useAsync(() => api.dataConfig(), [])
  const saved = useAsync(() => api.results(), [], { enabled: hasTrial })

  const [testSize, setTestSize] = useState(0.2)
  const [strategy, setStrategy] = useState('class_weight')
  const [models, setModels] = useState(REQUIRED)
  const [metric, setMetric] = useState('f1_score')
  const [training, setTraining] = useState(false)
  const [res, setRes] = useState(null)
  const [pick, setPick] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (saved.data) setRes(saved.data)
  }, [saved.data])
  useEffect(() => {
    if (res) setPick((p) => (res.rows.some((r) => r.model === p) ? p : res.recommended))
  }, [res])

  const k = overview.data?.kpis
  const dist = overview.data?.distribution
  const imbalanceRatio = dist ? (Math.max(...dist.map((x) => x.value)) / Math.max(Math.min(...dist.map((x) => x.value)), 1)).toFixed(2) : null

  const toggleModel = (m, on) => setModels((cur) => (on ? [...cur, m] : cur.filter((x) => x !== m)))
  const missingRequired = REQUIRED.filter((m) => !models.includes(m))

  const train = async () => {
    setTraining(true)
    try {
      const r = await api.train({ test_size: testSize, imbalance_strategy: strategy, models, selection_metric: metric })
      setRes(r)
      await refresh()
      toast({ kind: 'success', title: `Trained ${r.rows.length} model${r.rows.length === 1 ? '' : 's'}`, message: `Recommended on ${metric.replace('_', ' ')}: ${r.recommended}.` })
      if (r.note) toast({ kind: 'info', title: 'Heads up', message: r.note })
    } catch (e) {
      toast({ kind: 'error', title: 'Training failed', message: e.message })
    } finally {
      setTraining(false)
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      await api.saveModel(pick)
      const r = await api.results()
      setRes(r)
      await refresh()
      celebrate()
      toast({ kind: 'success', title: `${pick} is now active`, message: 'Risk, Customer 360, Explain, What-if, Retention and Batch use it.' })
    } catch (e) {
      toast({ kind: 'error', title: 'Could not save the model', message: e.message })
    } finally {
      setSaving(false)
    }
  }

  const metricCol = (key, label) => ({ key, label, numeric: true, render: (r) => fmtNum(r[key], 4) })

  return (
    <>
      <Card title="Dataset summary" subtitle={state?.dataset?.name}>
        {overview.error || cfg.error ? (
          <ErrorState compact title="Summary unavailable" error={overview.error || cfg.error} onRetry={() => { overview.reload(); cfg.reload() }} />
        ) : !k || !cfg.data ? (
          <Skeleton height={100} radius={18} />
        ) : (
          <div className="stack">
            <Stagger className="grid-kpi">
              <Stagger.Item><StatCard label="Dataset size" value={k.total_customers} format={fmtInt} tone="lavender" /></Stagger.Item>
              <Stagger.Item><StatCard label="Total features" value={cfg.data.numeric_cols.length + cfg.data.categorical_cols.length} format={fmtInt} tone="sky" /></Stagger.Item>
              <Stagger.Item><StatCard label="Numeric features" value={cfg.data.numeric_cols.length} format={fmtInt} tone="mint" /></Stagger.Item>
              <Stagger.Item><StatCard label="Categorical features" value={cfg.data.categorical_cols.length} format={fmtInt} tone="peach" /></Stagger.Item>
            </Stagger>
            <p className="small">
              <strong>Class distribution:</strong> Retained = {fmtInt(k.retained_customers)} ({fmtNum(100 - k.churn_rate_pct, 1)}%), Churned = {fmtInt(k.churned_customers)} ({fmtNum(k.churn_rate_pct, 1)}%). Imbalance ratio about {imbalanceRatio}:1.
            </p>
          </div>
        )}
      </Card>

      <Card title="Training configuration">
        <div className="grid-2">
          <div className="stack" style={{ '--gap': '22px' }}>
            <Slider id="test-size" label="Test set size" value={testSize} min={0.1} max={0.4} step={0.05} onChange={setTestSize} format={(v) => `${Math.round(v * 100)}%`} hint="Share of customers held back to measure the models." />
            <Segmented label="Class imbalance handling" name="imbalance" value={strategy} onChange={setStrategy} options={IMBALANCE} />
            <Select id="metric" label="Metric used to recommend the best model" value={metric} onChange={(e) => setMetric(e.target.value)} options={METRICS} hint="Accuracy alone is a poor guide on imbalanced churn data." />
          </div>
          <fieldset className="stack" style={{ border: 0, padding: 0, margin: 0, '--gap': '6px' }}>
            <legend className="field-label" style={{ marginBottom: 6 }}>Models to train</legend>
            {ALL_MODELS.map((m) => (
              <Checkbox key={m} label={<span>{m} {REQUIRED.includes(m) && <Badge tone="lavender">required</Badge>}</span>} checked={models.includes(m)} onChange={(on) => toggleModel(m, on)} />
            ))}
            {missingRequired.length > 0 && <Callout tone="info">The project spec compares {REQUIRED.join(', ')}. Add the missing ones for a complete comparison.</Callout>}
          </fieldset>
        </div>
        <div className="row" style={{ marginTop: 22 }}>
          <Button icon={Rocket} size="lg" onClick={train} loading={training} disabled={!models.length}>
            {training ? 'Training…' : 'Train models'}
          </Button>
          {!models.length && <span className="small muted">Pick at least one model.</span>}
        </div>
      </Card>

      {saved.error && !res && <ErrorState compact title="Could not check earlier results" error={saved.error} onRetry={saved.reload} />}

      {res && (
        <Card title="Model comparison" subtitle={`Held-out ${Math.round(res.test_size * 100)}% test split · imbalance: ${res.strategy.replace('_', ' ')}`}>
          <div className="stack">
            <Callout tone="success" title={`Recommended on ${res.metric.replace('_', ' ')}: ${res.recommended}`}>
              Sorted by F1-score. The recommendation follows the metric you chose; you can save any model below.
            </Callout>
            <Table
              caption="Model comparison"
              pageSize={0}
              rowKey={(r) => r.model}
              highlight={(r) => r.model === res.recommended}
              initialSort={{ key: 'f1_score', dir: 'desc' }}
              columns={[
                {
                  key: 'model',
                  label: 'Model',
                  render: (r) => (
                    <span className="row" style={{ '--gap': '8px' }}>
                      {r.model}
                      {r.model === res.recommended && <Badge tone="lavender" icon={Star}>recommended</Badge>}
                      {r.model === res.active && <Badge tone="mint">active</Badge>}
                    </span>
                  ),
                },
                metricCol('accuracy', 'Accuracy'),
                metricCol('precision', 'Precision'),
                metricCol('recall', 'Recall'),
                metricCol('f1_score', 'F1-score'),
                metricCol('roc_auc', 'ROC-AUC'),
              ]}
              rows={res.rows}
            />
            <div className="tool-row" style={{ marginTop: 6 }}>
              <Select id="save-pick" label="Model to save as the active model" value={pick} onChange={(e) => setPick(e.target.value)} options={res.rows.map((r) => r.model)} />
              <Button icon={Save} onClick={save} loading={saving} disabled={!pick}>
                Save as active model
              </Button>
              <Button variant="secondary" to="/app/evaluation" iconRight={ArrowRight}>
                See curves
              </Button>
            </div>
          </div>
        </Card>
      )}
    </>
  )
}
