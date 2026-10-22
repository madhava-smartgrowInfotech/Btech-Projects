import { AlertTriangle, BarChart3, Gauge, Target } from 'lucide-react'
import { Badge, Card, CardHeader, Container, EmptyState, ErrorState, KeyValueList, PageHeader, Skeleton, StatCard } from '../components/ui'
import { ChartCard, DonutChart, HBarChart, Legend, useChartColors } from '../components/charts'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { num1, when } from '../lib/format'
import { useAsync } from '../lib/useAsync'

const pctFmt = (v) => `${(v * 100).toFixed(1)}%`

function ConfusionMatrix({ labels, matrix }) {
  const max = Math.max(1, ...matrix.flat())
  return (
    <div>
      <div className="cm-wrap">
        <table className="cm" aria-label="Confusion matrix: rows are actual class, columns are predicted class">
          <thead>
            <tr>
              <th scope="col" />
              {labels.map((l) => (
                <th key={l} scope="col">
                  Predicted {l}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => {
              const total = row.reduce((a, b) => a + b, 0) || 1
              return (
                <tr key={labels[i]}>
                  <th scope="row">Actual {labels[i]}</th>
                  {row.map((n, j) => (
                    <td key={j} className={i === j ? 'diag' : undefined} style={{ '--heat': n / max }}>
                      {n}
                      <small>{((n / total) * 100).toFixed(0)}% of row</small>
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="cm-axis">Rows: actual class · Columns: predicted class · Highlighted diagonal: correct</p>
    </div>
  )
}

export default function Model() {
  const c = useChartColors()
  const { data: m, error, loading, reload } = useAsync(() => api.metrics(), [])
  const missing = m && (m.status === 'missing' || m.accuracy === undefined)

  const head = (
    <PageHeader
      crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'Model performance' }]}
      title="Model performance"
      description="Measured metrics from the trained paper-decision model. The historical decision signal is one input among many - it does not judge scientific correctness."
    />
  )

  if (loading) {
    return (
      <Container>
        {head}
        <div aria-busy="true" aria-label="Loading metrics">
          <div className="grid grid-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} height={112} radius="18px" />
            ))}
          </div>
          <Skeleton height={280} style={{ marginTop: 20 }} radius="18px" />
        </div>
      </Container>
    )
  }
  if (error) {
    return (
      <Container>
        {head}
        <ErrorState title="Could not load model metrics" error={error} onRetry={reload} />
      </Container>
    )
  }
  if (missing) {
    return (
      <Container>
        {head}
        <EmptyState icon={BarChart3} title="No trained model yet">
          {m?.note || 'No metrics file was found.'} Train one with <code>python scripts/prepare_dataset.py</code> then <code>python scripts/train_model.py</code>, and refresh this page.
        </EmptyState>
      </Container>
    )
  }

  const labels = m.labels || []
  const dist = Object.entries(m.class_distribution || {})
  const labelColor = (k) => c.label?.[k] || c.accent
  const donut = dist.map(([k, v]) => ({ name: k, value: v, color: labelColor(k) }))
  const totalRows = dist.reduce((a, [, v]) => a + v, 0)
  const bars = [
    { name: 'Accuracy', v: m.accuracy },
    { name: 'Precision (macro)', v: m.precision_macro },
    { name: 'Recall (macro)', v: m.recall_macro },
    { name: 'F1 (macro)', v: m.f1_macro },
    ...(m.roc_auc != null ? [{ name: 'ROC-AUC', v: m.roc_auc }] : []),
  ]
  const perClass = labels.map((l, i) => {
    const col = (m.confusion_matrix || []).reduce((a, r) => a + (r[i] || 0), 0)
    const row = (m.confusion_matrix?.[i] || []).reduce((a, b) => a + b, 0)
    const tp = m.confusion_matrix?.[i]?.[i] || 0
    return { label: l, precision: col ? tp / col : null, recall: row ? tp / row : null, support: row }
  })

  return (
    <Container>
      {head}
      {m.synthetic_fallback && (
        <div className="note warn" role="note" style={{ marginBottom: 18 }}>
          <AlertTriangle size={18} aria-hidden="true" />
          <span>
            <strong>Synthetic fallback data.</strong> No public peer-review dataset was available, so this model was trained on a clearly labelled synthetic set ({m.dataset_rows?.toLocaleString()} rows). These numbers are <strong>not</strong> a public benchmark result.
          </span>
        </div>
      )}
      <Stagger className="grid grid-4">
        <StatCard label="Accuracy" value={m.accuracy * 100} format={(v) => `${v.toFixed(1)}%`} icon={Target} />
        <StatCard label="Precision (macro)" value={m.precision_macro * 100} format={(v) => `${v.toFixed(1)}%`} icon={Gauge} tone="info" />
        <StatCard label="Recall (macro)" value={m.recall_macro * 100} format={(v) => `${v.toFixed(1)}%`} icon={Gauge} tone="info" />
        <StatCard label="F1 (macro)" value={m.f1_macro * 100} format={(v) => `${v.toFixed(1)}%`} icon={BarChart3} tone="warn" delta={m.roc_auc != null ? `ROC-AUC ${num1(m.roc_auc, 3)}` : undefined} />
      </Stagger>

      <div className="grid grid-2 mt">
        <ChartCard title="Metric overview" subtitle={`Held-out test set · ${m.test_samples} samples`} height={260}>
          <HBarChart data={bars} labelKey="name" valueKey="v" valueFormat={pctFmt} name="Score" labelWidth={140} domain={[0, 1]} />
        </ChartCard>
        <ChartCard
          title="Class distribution"
          subtitle={`${totalRows.toLocaleString()} labelled rows`}
          height={260}
          legend={<Legend items={donut.map((d) => ({ label: `${d.name} (${d.value})`, color: d.color }))} />}
        >
          <DonutChart data={donut} centerValue={totalRows.toLocaleString()} centerLabel="rows" />
        </ChartCard>
      </div>

      <div className="grid grid-2 mt">
        <Card>
          <CardHeader title="Confusion matrix" subtitle="Where the model agrees and disagrees with the labels" />
          <div className="card-body">
            <ConfusionMatrix labels={labels} matrix={m.confusion_matrix || []} />
          </div>
        </Card>
        <Card>
          <CardHeader title="Per-class results" subtitle="Derived from the confusion matrix" />
          <div className="card-body">
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Class</th>
                    <th scope="col" className="num">
                      Precision
                    </th>
                    <th scope="col" className="num">
                      Recall
                    </th>
                    <th scope="col" className="num">
                      Support
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {perClass.map((p) => (
                    <tr key={p.label}>
                      <td>
                        <Badge tone={p.label === 'accept' ? 'safe' : p.label === 'reject' ? 'danger' : 'warn'} dot>
                          {p.label}
                        </Badge>
                      </td>
                      <td className="num">{p.precision === null ? '-' : pctFmt(p.precision)}</td>
                      <td className="num">{p.recall === null ? '-' : pctFmt(p.recall)}</td>
                      <td className="num">{p.support}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      </div>

      <Card className="mt">
        <CardHeader title="Training details" />
        <div className="card-body">
          <KeyValueList
            items={[
              ['Model', m.model_type],
              ['Features', m.features],
              ['Dataset source', `${m.dataset_source}${m.synthetic_fallback ? ' (synthetic fallback)' : ''}`],
              ['Dataset rows', m.dataset_rows?.toLocaleString()],
              ['Test samples', m.test_samples],
              ['Random seed', m.random_seed],
              ['Trained', when(m.trained_at)],
            ]}
          />
        </div>
      </Card>
    </Container>
  )
}
