import { useState } from 'react'
import { Stethoscope, UploadCloud } from 'lucide-react'
import { PageHeader, Badge, Button, Card, EmptyState, ErrorState, FileDrop, PageSkeleton, StatCard, Table, useToast } from '../components/ui'
import { Callout } from '../components/app'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { useAppState } from '../lib/appstate'
import { useAsync } from '../lib/hooks'
import { fmtInt, fmtNum } from '../lib/format'

export default function Monitoring() {
  return (
    <div className="stack">
      <PageHeader eyebrow="Models" icon={Stethoscope} title="Model monitoring" lead="See which model is active and how it was trained, then compare a new file against the training data before you trust its predictions." />
      <Body />
    </div>
  )
}

function Body() {
  const { state, hasModel } = useAppState()
  const { data: m, error, reload } = useAsync(() => api.monitoring(), [state?.model?.saved_at], { enabled: hasModel })
  if (state && !hasModel) {
    return (
      <EmptyState
        icon={Stethoscope}
        tone="peach"
        title="No active model to monitor"
        message="Monitoring needs a saved model. Train the models and save one, then come back."
        action={<Button to="/app/train">Open Model training</Button>}
      />
    )
  }
  if (error && !m) return <ErrorState title="Monitoring could not load" error={error} onRetry={reload} />
  if (!m) return <PageSkeleton kpis={5} blocks={1} />

  const metrics = Object.entries(m.metrics || {})
  const METRIC_LABEL = { accuracy: 'Accuracy', precision: 'Precision', recall: 'Recall', f1_score: 'F1-score', roc_auc: 'ROC-AUC' }
  return (
    <>
      <Stagger className="grid-kpi">
        <Stagger.Item><StatCard label="Active model" display={m.name} tone="lavender" /></Stagger.Item>
        <Stagger.Item><StatCard label="Training dataset size" value={m.training_dataset_size} format={fmtInt} tone="sky" /></Stagger.Item>
        <Stagger.Item><StatCard label="Encoded features" value={m.feature_count} format={fmtInt} tone="mint" /></Stagger.Item>
        <Stagger.Item><StatCard label="Saved at" display={m.saved_at ? m.saved_at.replace('T', ' ') : '–'} tone="peach" /></Stagger.Item>
        <Stagger.Item><StatCard label="Imbalance strategy" display={(m.imbalance_strategy || '–').replace('_', ' ')} tone="rose" /></Stagger.Item>
      </Stagger>

      <Card title="Model metrics at save time">
        <Stagger className="grid-kpi">
          {metrics.map(([k, v]) => (
            <Stagger.Item key={k}>
              <StatCard label={k.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())} value={v} format={(x) => fmtNum(x, 4)} tone="lavender" />
            </Stagger.Item>
          ))}
        </Stagger>
      </Card>

      <Card title="Feature columns used by this model" subtitle={`${m.feature_cols.length} columns · target: ${m.target_col}`}>
        <div className="chip-list">
          {m.feature_cols.map((c) => (
            <span className="chip" key={c}>
              {c}
            </span>
          ))}
        </div>
      </Card>

      <Drift hasReference={m.has_reference} />
    </>
  )
}

function Drift({ hasReference }) {
  const toast = useToast()
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [r, setR] = useState(null)

  const run = async () => {
    setBusy(true)
    setErr('')
    try {
      setR(await api.drift(file))
      toast({ kind: 'success', title: 'Comparison finished' })
    } catch (e) {
      setR(null)
      setErr(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Data drift check" subtitle="Compare a new dataset’s structure and distributions with the training data.">
      <div className="stack">
        {!hasReference && (
          <Callout tone="info" title="No reference dataset in this session">
            Unseen-category and mean comparisons need the training dataset. Load and prepare it on the Data screen to enable them; column and missing-value checks still run.
          </Callout>
        )}
        <FileDrop
          accept=".csv,text/csv"
          label="Drop a dataset to compare"
          hint="CSV with the same columns as the training data."
          onFiles={(f) => {
            setFile(f[0] || null)
            setR(null)
            setErr('')
          }}
        />
        <div className="row">
          <Button icon={UploadCloud} onClick={run} loading={busy} disabled={!file}>
            Compare with training data
          </Button>
        </div>
        {err && (
          <Callout tone="error" title="Could not compare this file">
            {err}
          </Callout>
        )}
        {r && (
          <div className="stack">
            <p className="small muted">
              {r.filename} · {fmtInt(r.rows)} rows
            </p>
            {r.missing_columns.length > 0 ? (
              <Callout tone="error" title="Missing expected columns">
                {r.missing_columns.join(', ')}
              </Callout>
            ) : (
              <Callout tone="success">All expected feature columns are present.</Callout>
            )}
            {r.high_missing ? (
              <Callout tone="warn" title="High missing-value rate">
                {r.missing_pct}% of feature cells are empty in the new data.
              </Callout>
            ) : (
              <Callout tone="success">{r.missing_pct}% of feature cells are empty, which is within the normal range.</Callout>
            )}
            {r.has_reference &&
              (r.unexpected_categories.length ? (
                <Callout tone="warn" title="Categories not seen during training">
                  <ul>
                    {r.unexpected_categories.map((u) => (
                      <li key={u.column}>
                        <span className="code-pill">{u.column}</span>: {u.values.join(', ')}
                      </li>
                    ))}
                  </ul>
                </Callout>
              ) : (
                <Callout tone="success">No unexpected categorical values found.</Callout>
              ))}
            {r.mean_comparison.length > 0 && (
              <Table
                caption="Numeric feature means"
                pageSize={0}
                rowKey={(x) => x.feature}
                columns={[
                  { key: 'feature', label: 'Feature' },
                  { key: 'training_mean', label: 'Training mean', numeric: true, render: (x) => fmtNum(x.training_mean, 2) },
                  { key: 'new_mean', label: 'New data mean', numeric: true, render: (x) => fmtNum(x.new_mean, 2) },
                  {
                    key: 'delta',
                    label: 'Shift',
                    numeric: true,
                    sortValue: (x) => Math.abs(shift(x)),
                    render: (x) => {
                      const s = shift(x)
                      return <Badge tone={Math.abs(s) >= 25 ? 'rose' : Math.abs(s) >= 10 ? 'peach' : 'mint'}>{s > 0 ? '+' : ''}{fmtNum(s, 1)}%</Badge>
                    },
                  },
                ]}
                rows={r.mean_comparison}
              />
            )}
            {r.new_churn_rate != null && (
              <div className="grid-kpi">
                <StatCard label="Churn rate in new data" value={r.new_churn_rate} format={(v) => `${fmtNum(v, 1)}%`} tone="rose" />
              </div>
            )}
            {r.imbalance_warning && (
              <Callout tone="warn" title="Severe class imbalance">
                One class has fewer than 5 examples in the new data.
              </Callout>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

function shift(x) {
  return x.training_mean === 0 ? 0 : ((x.new_mean - x.training_mean) / Math.abs(x.training_mean)) * 100
}
