import { BarChart3, Crosshair, Gauge, Percent, Target } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Tooltip as RTooltip, XAxis, YAxis } from 'recharts'
import api, { describeError } from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Stagger } from '../components/motion'
import { Button } from '../components/ui/controls'
import { Badge, Card, KeyValueList, StatCard } from '../components/ui/display'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../components/ui/charts'
import { EmptyState, ErrorState, PageSkeleton } from '../components/ui/feedback'
import { num, pct } from '../format'

function Confusion({ m }) {
  const [[tn, fp], [fn, tp]] = m.confusion_matrix
  const [neg, pos] = m.confusion_labels || ['normal', 'attack']
  const total = tn + fp + fn + tp
  const cell = (v, tone, name) => (
    <div className="rounded-[6px] border p-3 text-center" style={{ borderColor: `color-mix(in oklab, var(--${tone}) 45%, transparent)`, background: `color-mix(in oklab, var(--${tone}) 9%, transparent)` }}>
      <div className="font-mono text-2xl font-semibold tabular-nums" style={{ color: `var(--${tone})` }}>{num(v)}</div>
      <div className="mt-0.5 font-mono text-[10px] uppercase tracking-wider text-muted">{name}</div>
      <div className="font-mono text-[10px] text-dim">{pct(v / total)}</div>
    </div>
  )
  return (
    <div role="table" aria-label="Confusion matrix" className="space-y-2">
      <div className="grid grid-cols-[auto_1fr_1fr] items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-dim">
        <span />
        <span className="text-center">Predicted {neg}</span>
        <span className="text-center">Predicted {pos}</span>
      </div>
      <div className="grid grid-cols-[auto_1fr_1fr] items-stretch gap-2">
        <span className="flex items-center font-mono text-[10px] uppercase tracking-wider text-dim [writing-mode:vertical-rl] rotate-180">Actual {neg}</span>
        {cell(tn, 'ok', 'true negative')}{cell(fp, 'warn', 'false positive')}
        <span className="flex items-center font-mono text-[10px] uppercase tracking-wider text-dim [writing-mode:vertical-rl] rotate-180">Actual {pos}</span>
        {cell(fn, 'hot', 'false negative')}{cell(tp, 'ok', 'true positive')}
      </div>
    </div>
  )
}

export default function Performance() {
  const { tokens, animate, axis, grid } = useChartTheme()
  const [m, setM] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(() => {
    setLoading(true)
    api.get('/metrics')
      .then((r) => { setM(r.data); setError(null) })
      .catch((e) => setError(describeError(e)))
      .finally(() => setLoading(false))
  }, [])
  useEffect(() => { load() }, [load])

  if (loading && !m) return <div className="space-y-6"><PageHeader eyebrow="Held-out test set" title="Model performance" /><PageSkeleton /></div>

  const header = <PageHeader eyebrow="Held-out test set" title="Model performance"
    subtitle="Metrics computed by the training pipeline on data the models never saw, read straight from reports/metrics.json." />

  if (error || !m) {
    return (
      <div className="space-y-6">
        {header}
        <ErrorState error={error || 'No metrics returned.'} title="Metrics unavailable" onRetry={load} />
        <Card><EmptyState icon={BarChart3} title="No report to show" body="Train the model with python -m cipherguard.ids.train (run.bat does it on first start), then reload."
          action={<Button variant="secondary" size="sm" onClick={load}>Reload</Button>} /></Card>
      </div>
    )
  }

  const metricBars = [
    { name: 'Accuracy', value: m.accuracy, color: tokens.ok },
    { name: 'Precision', value: m.precision, color: tokens.cyan },
    { name: 'Recall', value: m.recall, color: tokens.warn },
    { name: 'F1', value: m.f1, color: tokens.info },
    { name: 'ROC-AUC', value: m.roc_auc, color: tokens.hot },
  ]
  const modelBars = [
    { name: 'XGBoost', value: m.xgb_accuracy, color: tokens.cyan },
    { name: '1D CNN', value: m.cnn_accuracy, color: tokens.info },
    { name: 'Stacked ensemble', value: m.accuracy, color: tokens.ok },
  ]
  const tech = m.technology || {}
  const synthetic = /synthetic/i.test(m.data_mode)
  const barChart = (data, label) => (
    <ChartFrame height={230} label={label}>
      {({ width, height }) => (
        <BarChart width={width} height={height} data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid vertical={false} {...grid} />
          <XAxis dataKey="name" {...axis} />
          <YAxis domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} {...axis} />
          <RTooltip cursor={{ fill: tokens.line }} content={<MonoTooltip valueFormat={(v) => v.toFixed(4)} />} />
          <Bar dataKey="value" name="Score" radius={[2, 2, 0, 0]} isAnimationActive={animate}>
            {data.map((d) => <Cell key={d.name} fill={d.color} />)}
          </Bar>
        </BarChart>
      )}
    </ChartFrame>
  )

  return (
    <div className="space-y-6">
      {header}
      {synthetic && (
        <div role="note" className="flex flex-wrap items-center gap-2 rounded-[6px] border border-warn/35 bg-warn/[0.07] p-3 text-sm text-fg">
          <Badge tone="warn">data mode</Badge>{m.data_mode}. Drop the real UNSW-NB15 CSVs into data/raw and retrain to replace these numbers.
        </div>
      )}
      <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatCard label="Accuracy" value={m.accuracy * 100} format={(v) => `${v.toFixed(2)}%`} icon={Target} tone="ok" />
        <StatCard label="Precision" value={m.precision * 100} format={(v) => `${v.toFixed(2)}%`} icon={Crosshair} tone="cyan" />
        <StatCard label="Recall" value={m.recall * 100} format={(v) => `${v.toFixed(2)}%`} icon={Percent} tone="warn" />
        <StatCard label="F1" value={m.f1 * 100} format={(v) => `${v.toFixed(2)}%`} icon={Gauge} tone="info" />
        <StatCard label="ROC-AUC" value={m.roc_auc} format={(v) => v.toFixed(4)} icon={BarChart3} tone="hot" />
      </Stagger>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Test metrics" eyebrow="ensemble">
          {barChart(metricBars, 'Bar chart of ensemble test metrics')}
          <ChartLegend items={metricBars.map((b) => ({ label: b.name, color: b.color }))} />
        </Card>
        <Card title="Confusion matrix" eyebrow={`${num(m.splits.test)} test records`}>
          <Confusion m={m} />
        </Card>
        <Card title="Model comparison" eyebrow="test accuracy">
          {barChart(modelBars, 'Bar chart comparing XGBoost, CNN and ensemble accuracy')}
          <p className="mt-2 text-xs text-muted">Each model and the stacked ensemble are scored on the same {num(m.splits.test)} held-out records.</p>
        </Card>
        <Card title="Training run" eyebrow="reports/metrics.json">
          <KeyValueList items={[
            ['Dataset rows', num(m.dataset_rows)],
            ['Train / val / test', `${num(m.splits.train)} / ${num(m.splits.val)} / ${num(m.splits.test)}`],
            ['Class balance (neg / pos)', m.class_balance ? `${num(m.class_balance.neg)} / ${num(m.class_balance.pos)}` : '-'],
            ['Input dimension', num(m.input_dim)],
            ['CNN backend', m.cnn_backend],
            ['Stacking weights (XGB, CNN)', (m.meta_coef?.[0] || []).map((c) => c.toFixed(3)).join(', ')],
            ['Stacking intercept', (m.meta_intercept || []).map((c) => c.toFixed(3)).join(', ')],
          ]} />
        </Card>
      </div>

      <Card title="Technology" eyebrow="what produced these numbers">
        <KeyValueList cols={2} items={[
          ['Model A', tech.model_a], ['Model B', tech.model_b], ['Fusion', tech.fusion], ['Dataset', tech.dataset], ['Crypto', tech.crypto],
        ].filter(([, v]) => v)} />
      </Card>
    </div>
  )
}
