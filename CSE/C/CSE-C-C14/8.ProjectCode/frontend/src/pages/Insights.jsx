import { BarChart3, Info, Target } from 'lucide-react'
import { api } from '../lib/api'
import { useDocTitle, useLoad } from '../lib/hooks'
import { fmtInt, fmtPct } from '../lib/format'
import { CONDITION_NAMES, MODEL_NAMES, isDemoData } from '../lib/labels'
import { Button, Card, EmptyState, ErrorState, KeyValueList, PageHeader, PageSkeleton, StatCard, Table } from '../components/ui'
import { BarCompare, ChartLegend, GroupedBars } from '../components/charts'
import { SlideUp, Stagger } from '../components/motion'
import { useChartTheme } from '../lib/palette'

function ConfusionGrid({ matrix }) {
  const cells = [
    ['True real', 'Predicted real', matrix[0][0], 'mint'],
    ['True real', 'Predicted AI', matrix[0][1], 'rose'],
    ['True AI', 'Predicted real', matrix[1][0], 'rose'],
    ['True AI', 'Predicted AI', matrix[1][1], 'mint'],
  ]
  return (
    <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: 10 }} role="table" aria-label="Confusion matrix counts">
      {cells.map(([t, p, v, tone]) => (
        <div key={t + p} role="cell" className={`card tint-${tone}`} style={{ padding: 16, textAlign: 'center' }}>
          <div className="stat-value num">{fmtInt(v)}</div>
          <div className="tiny muted">{t} · {p}</div>
        </div>
      ))}
    </div>
  )
}

export default function Insights() {
  useDocTitle('Model insights · VeriVision AI')
  const { data, error, loading, reload } = useLoad((s) => api.insights(s), [])
  const t = useChartTheme()

  const header = (
    <PageHeader
      eyebrow="Evaluation"
      icon={BarChart3}
      title="Model insights"
      lead="Measured held-out test performance. Every number is read from the evaluation artifacts written by scripts/evaluate.py - never typed in by hand."
    />
  )
  if (loading) return <div className="stack">{header}<PageSkeleton kpis={6} blocks={2} /></div>
  if (error) return <div className="stack">{header}<ErrorState title="Could not load the evaluation results" error={error} onRetry={reload} /></div>
  if (!data.available) {
    return (
      <div className="stack">
        {header}
        <EmptyState
          icon={Target}
          title="Model evaluation unavailable until training is completed"
          message="Run the training workflow described in HOW_TO_RUN.md (the last step is scripts/evaluate.py) to generate evaluation artifacts, then reload this page."
          action={<Button variant="secondary" onClick={reload}>Reload</Button>}
        />
      </div>
    )
  }

  const e = data.ensemble
  const demo = isDemoData(e.dataset)
  const kpis = [
    ['Accuracy', e.accuracy, 'lavender'],
    ['Precision', e.precision, 'mint'],
    ['Recall', e.recall, 'peach'],
    ['F1-score', e.f1, 'sky'],
    ['ROC-AUC', e.roc_auc, 'lavender'],
    ['Balanced accuracy', e.balanced_accuracy, 'mint'],
  ]
  const modelRows = Object.entries(data.models || {}).map(([key, m]) => ({ key, name: MODEL_NAMES[key] || key, ...m }))
  const modelCols = [
    { key: 'name', label: 'Model', render: (m) => <strong>{m.name}</strong> },
    { key: 'resolution', label: 'Input', numeric: true, render: (m) => `${m.resolution}px` },
    { key: 'accuracy', label: 'Accuracy', numeric: true, render: (m) => fmtPct(m.accuracy) },
    { key: 'f1', label: 'F1', numeric: true, render: (m) => fmtPct(m.f1) },
    { key: 'roc_auc', label: 'ROC-AUC', numeric: true, render: (m) => fmtPct(m.roc_auc) },
  ]
  const robust = Object.entries(data.robustness || {}).map(([k, m]) => ({
    name: CONDITION_NAMES[k] || k,
    value: m.accuracy,
    color: k === 'clean' ? t.mint : m.accuracy < 0.7 ? t.rose : m.accuracy < 0.95 ? t.peach : t.sky,
  }))
  const modelBars = modelRows.map((m) => ({ x: m.name, accuracy: m.accuracy, f1: m.f1, auc: m.roc_auc }))

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      {header}

      {demo && (
        <SlideUp>
          <div className="card tint-peach" role="note" style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <Info size={20} aria-hidden="true" style={{ color: 'var(--peach-ink)', flex: 'none', marginTop: 2 }} />
            <div>
              <strong>These metrics come from synthetic demo data.</strong> The public CIFAKE download was unavailable when the models were trained, so the
              scores below describe the demo dataset only - not real-world accuracy. The robustness rows show how quickly that performance degrades.
            </div>
          </div>
        </SlideUp>
      )}

      <Stagger className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: 16 }}>
        {kpis.map(([label, v, tone]) => (
          <Stagger.Item key={label}>
            <StatCard label={label} value={v * 100} format={(x) => `${x.toFixed(2)}%`} tone={tone} icon={Target} foot={`${fmtInt(e.n_samples)} test images`} />
          </Stagger.Item>
        ))}
      </Stagger>

      <div className="grid-2">
        <Card title="Confusion matrix" subtitle="Ensemble on the held-out test split." hover={false}>
          <div className="stack" style={{ '--gap': '16px' }}>
            <ConfusionGrid matrix={e.confusion_matrix} />
            {data.confusion_exists && (
              <details>
                <summary className="small" style={{ cursor: 'pointer', fontWeight: 600 }}>Show the rendered figure from evaluate.py</summary>
                <img
                  src="/artifacts/confusion_matrix.png"
                  alt="Confusion matrix figure produced by the evaluation script"
                  loading="lazy"
                  style={{ width: '100%', maxWidth: 420, margin: '12px auto 0', display: 'block', borderRadius: 16, background: '#fff', border: '1px solid var(--border)' }}
                />
              </details>
            )}
            <KeyValueList items={[['Dataset', e.dataset], ['Random seed', e.seed], ['Test samples', fmtInt(e.n_samples)]]} />
          </div>
        </Card>

        <Card title="Clean vs degraded (ensemble accuracy)" subtitle="The same test images after JPEG, resampling, blur and noise." hover={false}>
          <BarCompare data={robust} valueFormat={(v) => fmtPct(v, 0)} height={300} name="Accuracy" label="Ensemble accuracy under distortions" />
          <p className="small muted" style={{ marginTop: 10 }}>
            Accuracy falls sharply under resampling and blur - a reminder to read the per-image robustness check on every result.
          </p>
        </Card>
      </div>

      <Card title="Per-model comparison" subtitle="Each branch evaluated on its own." hover={false}>
        <div className="stack" style={{ '--gap': '18px' }}>
          <Table columns={modelCols} rows={modelRows} rowKey={(m) => m.key} pageSize={0} caption="Per-model metrics" cardTitle={(m) => m.name} />
          <ChartLegend items={[{ label: 'Accuracy', color: t.lavender }, { label: 'F1', color: t.sky }, { label: 'ROC-AUC', color: t.mint }]} />
          <GroupedBars
            data={modelBars}
            series={[{ key: 'accuracy', name: 'Accuracy', color: t.lavender }, { key: 'f1', name: 'F1', color: t.sky }, { key: 'auc', name: 'ROC-AUC', color: t.mint }]}
            valueFormat={(v) => fmtPct(v, 0)}
            height={260}
            label="Accuracy, F1 and ROC-AUC per model"
          />
        </div>
      </Card>
    </div>
  )
}
