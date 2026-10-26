import { useEffect, useState } from 'react'
import { ArrowRight, Cpu, Download, Gauge } from 'lucide-react'
import { Alert, Button, Card, Checkbox, KeyValueList, PageHeader, Skeleton } from '../components/ui'
import { ActionError, ComparisonPanel, Gate, MetricTiles, useAction } from '../components/app/common'
import { api } from '../lib/api'
import { fmtInt } from '../lib/format'
import { usePipeline } from '../lib/pipeline'

const pct = (f) => `${Math.round(f * 100)}%`

function SplitSummary({ split }) {
  return (
    <div className="two-col">
      <Card tone="lime" flat title="Train">
        <p className="mono small">
          {split.train_start} → {split.train_end}
        </p>
        <p className="display-sm" style={{ marginTop: 6 }}>
          {fmtInt(split.train_rows)} rows
        </p>
      </Card>
      <Card tone="coral" flat title="Test">
        <p className="mono small">
          {split.test_start} → {split.test_end}
        </p>
        <p className="display-sm" style={{ marginTop: 6 }}>
          {fmtInt(split.test_rows)} rows
        </p>
      </Card>
    </div>
  )
}

export default function Training() {
  const { state, refresh } = usePipeline()
  const baseline = useAction()
  const xgb = useAction()
  const loader = useAction()
  const [fraction, setFraction] = useState(0.8)
  const [split, setSplit] = useState(null)
  const [splitError, setSplitError] = useState(null)
  const [tune, setTune] = useState(false)
  const [lastRun, setLastRun] = useState(null) // {model, metrics, best_params}
  const [comparison, setComparison] = useState(null)

  const ready = Boolean(state?.features_ready)

  // The split summary follows the slider (debounced).
  useEffect(() => {
    if (!ready) return undefined
    const t = setTimeout(() => {
      api(`/api/training/split?train_fraction=${fraction}`)
        .then((s) => {
          setSplit(s)
          setSplitError(null)
        })
        .catch((e) => setSplitError(e))
    }, 250)
    return () => clearTimeout(t)
  }, [fraction, ready])

  useEffect(() => {
    if (!ready) return
    api('/api/training/results')
      .then((r) => setComparison(r.comparison))
      .catch(() => {})
  }, [ready])

  const runBaseline = async () => {
    const out = await baseline.run(() => api('/api/training/baseline', { method: 'POST', body: { train_fraction: fraction } }), {
      success: 'Moving-average baseline evaluated.',
    })
    if (out) {
      setLastRun({ model: 'Moving Average', metrics: out.metrics })
      setComparison(out.comparison)
    }
  }
  const runXgb = async () => {
    const out = await xgb.run(() => api('/api/training/xgboost', { method: 'POST', body: { train_fraction: fraction, tune } }), {
      success: tune ? 'XGBoost tuned and trained.' : 'XGBoost trained.',
    })
    if (out) {
      setLastRun({ model: 'XGBoost', metrics: out.metrics, best_params: out.best_params })
      setComparison(out.comparison)
    }
  }
  const loadSaved = async () => {
    const out = await loader.run(() => api('/api/training/load', { method: 'POST' }), { success: 'Loaded the saved XGBoost model.' })
    if (out) refresh()
  }

  const busy = baseline.loading || xgb.loading

  return (
    <>
      <PageHeader
        eyebrow="05 · Model training"
        title="Train models"
        description="A chronological split, a moving-average baseline, and XGBoost with optional hyperparameter tuning."
      />
      <Gate ok={ready} loading={!state} title="Build the feature table first" to="/app/features" cta="Go to Feature engineering">
        <div className="page-stack">
          <Card title="Chronological train / test split">
            <p className="muted" style={{ maxWidth: '68ch' }}>
              The split is by date, not random: the model trains on earlier dates and is tested on later ones, the way it would be used in production. A random
              split would leak future information into training and give misleadingly good metrics.
            </p>
            <div style={{ margin: '18px 0 6px' }}>
              <label htmlFor="frac" className="field-label">
                Training data fraction <strong className="mono">{pct(fraction)}</strong>
              </label>
              <input
                id="frac"
                className="range"
                type="range"
                min="0.5"
                max="0.95"
                step="0.05"
                value={fraction}
                onChange={(e) => setFraction(Number(e.target.value))}
                aria-valuetext={`${pct(fraction)} train, ${pct(1 - fraction)} test`}
              />
              <div className="row-between tiny mono muted">
                <span>50%</span>
                <span>95%</span>
              </div>
            </div>
            {splitError ? <Alert tone="error">{splitError.message}</Alert> : split ? <SplitSummary split={split} /> : <Skeleton height={96} />}
          </Card>

          <div className="two-col">
            <Card title="Baseline: moving average">
              <p className="muted">Predicts each test row as the product’s average over its last 7 training days. Any real model should beat this.</p>
              <div style={{ marginTop: 16 }}>
                <Button icon={Gauge} loading={baseline.loading} disabled={busy} onClick={runBaseline}>
                  Run moving-average baseline
                </Button>
              </div>
              <ActionError error={baseline.error} />
            </Card>
            <Card title="XGBoost">
              <p className="muted">Gradient-boosted trees on the engineered features. Tuning searches 10 settings with time-ordered cross-validation.</p>
              <div className="stack" style={{ marginTop: 16 }}>
                <Checkbox label="Run hyperparameter tuning (slower, more accurate)" checked={tune} onChange={setTune} disabled={busy} />
                <div className="row">
                  <Button variant="primary" icon={Cpu} loading={xgb.loading} disabled={busy} onClick={runXgb}>
                    {xgb.loading && tune ? 'Tuning and training…' : xgb.loading ? 'Training…' : 'Train XGBoost'}
                  </Button>
                  <Button icon={Download} loading={loader.loading} disabled={busy || !state?.saved_model_exists} onClick={loadSaved}>
                    Load saved model
                  </Button>
                </div>
                {!state?.saved_model_exists && <span className="small muted">No saved model yet. Train one and it is saved to models/.</span>}
                {xgb.loading && tune && <span className="small muted">Tuning fits many models; this can take a few minutes.</span>}
              </div>
              <ActionError error={xgb.error || loader.error} />
            </Card>
          </div>

          {lastRun && (
            <section aria-label={`${lastRun.model} results`} className="page-stack">
              <h2 className="display-sm">{lastRun.model}: test metrics</h2>
              <MetricTiles metrics={lastRun.metrics} />
              {lastRun.best_params && (
                <Card title="Best parameters found">
                  <KeyValueList items={Object.entries(lastRun.best_params).map(([k, v]) => ({ label: k, value: String(v) }))} />
                </Card>
              )}
            </section>
          )}

          {comparison?.length > 0 ? (
            <ComparisonPanel rows={comparison} />
          ) : (
            <Card flat>
              <p className="muted">No models evaluated yet. Run the baseline and train XGBoost to compare them here.</p>
            </Card>
          )}

          {state?.xgboost_trained && (
            <div className="row">
              <Button variant="primary" to="/app/domain" iconRight={ArrowRight}>
                Continue to domain adaptation
              </Button>
              <Button to="/app/evaluation">Model evaluation</Button>
            </div>
          )}
        </div>
      </Gate>
    </>
  )
}
