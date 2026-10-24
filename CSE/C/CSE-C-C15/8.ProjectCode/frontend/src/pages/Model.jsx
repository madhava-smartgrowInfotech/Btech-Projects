import { AlertTriangle, Brain } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import api, { describeError } from '../api'
import { ImportanceBars } from '../components/app/Charts'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Badge, Card, KeyValueList, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton, Skeleton } from '../components/ui/feedback'
import { TabPanel, Tabs } from '../components/ui/nav'
import { FEATURE_LABEL, fmt, pct } from '../format'

function Confusion({ cm }) {
  const [labels, m] = [cm.labels, cm.matrix]
  const max = Math.max(...m.flat(), 1)
  return (
    <div role="table" aria-label="Confusion matrix" className="mx-auto max-w-sm font-mono text-xs">
      <div className="mb-1 grid grid-cols-[72px_1fr_1fr] gap-1 text-center text-[10px] uppercase tracking-wider text-dim">
        <span />
        {labels.map((l) => <span key={l}>pred {l}</span>)}
      </div>
      {m.map((row, i) => (
        <div key={labels[i]} role="row" className="mb-1 grid grid-cols-[72px_1fr_1fr] gap-1">
          <span className="grid place-items-center text-[10px] uppercase tracking-wider text-dim">true {labels[i]}</span>
          {row.map((v, j) => {
            const correct = i === j
            const tone = correct ? 'var(--ok)' : 'var(--alert)'
            return (
              <div key={j} role="cell" className="grid aspect-[4/3] place-items-center rounded-[4px] border border-line-strong"
                style={{ background: `color-mix(in oklab, ${tone} ${Math.max(8, (v / max) * 55)}%, transparent)` }}>
                <div className="text-center"><div className="text-lg font-semibold tabular-nums text-fg">{fmt(v)}</div>
                  <div className="text-[10px] text-muted">{correct ? 'correct' : 'error'}</div></div>
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

export default function Model() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('cm')

  const load = useCallback(() => {
    setError(null)
    api.get('/model/metrics').then((r) => setData(r.data)).catch((e) => setError(describeError(e)))
  }, [])
  useEffect(() => { load() }, [load])

  if (error) {
    return (
      <div className="space-y-5">
        <PageHeader eyebrow="console / model" title="Model performance" />
        <ErrorState error={error} title="Model metrics unavailable" onRetry={load} />
      </div>
    )
  }
  if (!data) return <PageSkeleton />

  if (!data.trained) {
    return (
      <div className="space-y-5">
        <PageHeader eyebrow="console / model" title="Model performance" />
        <Card title="Random Forest">
          <EmptyState icon={Brain} title="Model not trained yet" body={data.message || 'Train the model, then reload this page.'}
            action={<Button variant="secondary" onClick={load}>Check again</Button>} />
        </Card>
      </div>
    )
  }

  const m = data.metrics
  const importance = Object.entries(data.feature_importance || {})
    .map(([k, v]) => ({ name: FEATURE_LABEL[k] || k, value: v })).sort((a, b) => b.value - a.value)

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="console / model" title="Model performance"
        subtitle="Held-out test metrics for the Random Forest classifier, read from the artifacts written by ml/train_model.py."
        actions={<Badge tone={m.is_synthetic ? 'warn' : 'ok'} dot>{m.is_synthetic ? 'synthetic training data' : 'real training data'}</Badge>} />
      {m.is_synthetic && (
        <div role="note" className="flex items-start gap-3 rounded-[6px] border border-warn/40 bg-warn/10 p-3 text-sm text-warn">
          <AlertTriangle size={17} className="mt-0.5 shrink-0" aria-hidden="true" />
          <span>These numbers describe the synthetic fallback dataset, not real CICIDS2017 captures. Retrain on labelled local captures before relying on them in production.</span>
        </div>
      )}
      <Stagger className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Accuracy" value={m.accuracy * 100} format={(v) => `${v.toFixed(2)}%`} />
        <StatCard label="Precision" value={m.precision * 100} format={(v) => `${v.toFixed(2)}%`} />
        <StatCard label="Recall" value={m.recall * 100} format={(v) => `${v.toFixed(2)}%`} />
        <StatCard label="F1 score" value={m.f1 * 100} format={(v) => `${v.toFixed(2)}%`} />
        <StatCard label="ROC-AUC" tone="cyan" value={m.roc_auc === null || m.roc_auc === undefined ? 'n/a' : m.roc_auc * 100} format={(v) => `${v.toFixed(2)}%`} />
        <StatCard label="Test samples" tone="info" value={m.test_samples} />
      </Stagger>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Confusion matrix">{data.confusion_matrix ? <Confusion cm={data.confusion_matrix} /> : <EmptyState title="No confusion matrix" body="results/confusion_matrix.json is missing." />}</Card>
        <Card title="Feature importance">
          {importance.length ? <ImportanceBars data={importance} /> : <EmptyState title="No feature importance" body="results/feature_importance.json is missing." />}
        </Card>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Training run">
          <KeyValueList items={[
            ['Model', m.model], ['Train samples', fmt(m.train_samples)], ['Test samples', fmt(m.test_samples)],
            ['Benign / attack total', `${fmt(m.benign_total)} / ${fmt(m.attack_total)}`], ['Training time', m.training_seconds ? `${m.training_seconds}s` : '-'],
            ['Misclassified', data.confusion_matrix ? fmt(data.confusion_matrix.matrix[0][1] + data.confusion_matrix.matrix[1][0]) : '-'],
            ['False-alarm rate', data.confusion_matrix ? pct(data.confusion_matrix.matrix[0][1] / (data.confusion_matrix.matrix[0][0] + data.confusion_matrix.matrix[0][1]), 2) : '-'],
          ]} />
          <p className="mt-3 break-words text-xs leading-relaxed text-muted"><b className="text-fg">Provenance: </b>{m.dataset_provenance}</p>
        </Card>
        <Card title="Evaluation plots">
          <Tabs id="plots" tabs={[{ id: 'cm', label: 'Confusion' }, { id: 'roc', label: 'ROC' }, { id: 'fi', label: 'Importance' }]} value={tab} onChange={setTab} label="Evaluation plots" />
          <TabPanel tabsId="plots" value={tab} className="pt-4">
            <PlotImage key={tab} src={{ cm: 'confusion_matrix', roc: 'roc_curve', fi: 'feature_importance' }[tab]} alt={{ cm: 'Confusion matrix plot', roc: 'ROC curve plot', fi: 'Feature importance plot' }[tab]} />
          </TabPanel>
        </Card>
      </div>
    </div>
  )
}

function PlotImage({ src, alt }) {
  const [state, setState] = useState('loading')
  return (
    <div className="relative overflow-hidden rounded-[6px] border border-line bg-white">
      {state === 'loading' && <Skeleton className="absolute inset-0" />}
      {state === 'error' && <div className="p-6"><ErrorState compact title="Plot missing" error="The PNG was not found in results/." /></div>}
      <img src={`/static/results/${src}.png`} alt={alt} className={`mx-auto max-h-[420px] w-full object-contain ${state === 'error' ? 'hidden' : ''}`}
        onLoad={() => setState('ok')} onError={() => setState('error')} />
    </div>
  )
}
