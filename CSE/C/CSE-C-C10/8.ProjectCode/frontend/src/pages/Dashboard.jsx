import { Activity, Boxes, CheckCircle2, Rocket, TrendingUp, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useApi } from '../api'
import { Bars, Donut } from '../components/charts/Charts'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Badge, Card, KeyValueList, StatCard } from '../components/ui/display'
import { ErrorState, PageSkeleton } from '../components/ui/feedback'
import { fixed, meanStd, num, pct } from '../format'
import { useTheme } from '../lib/theme'

const STEPS = [
  'Enter structured signals (funding, rounds, milestones, relationships, industry, investors) plus a business description.',
  'VenturePulse builds a fused representation: scaled structured features (weight 0.5) + a transformer text embedding, compared with cosine similarity.',
  'It retrieves comparable historical startups and predicts with the best validated classifier.',
  'You see the estimated outcome, confidence, evidence cases and the key contributing features.',
]

export default function Dashboard() {
  const metrics = useApi('/model-metrics')
  const insights = useApi('/insights')
  const config = useApi('/config')
  const { tokens } = useTheme()

  const error = metrics.error || insights.error || config.error
  const loading = metrics.loading || insights.loading || config.loading
  if (error) return <><PageHeader title="Dashboard" eyebrow="overview" /><ErrorState error={error} title="Could not load the dashboard" onRetry={() => { metrics.reload(); insights.reload(); config.reload() }} /></>
  if (loading || !metrics.data || !insights.data || !config.data) return <PageSkeleton />

  const m = metrics.data
  const i = insights.data
  const cfg = config.data
  const best = m.models[m.best_model]
  const compare = Object.entries(m.models).map(([name, v]) => ({ name, bal: v.balanced_accuracy.mean }))

  return (
    <>
      <PageHeader title="Dashboard" eyebrow="overview"
        subtitle="Estimate early-stage startup outcomes from historical patterns: structured company signals plus a natural-language description, matched against comparable startups."
        actions={<Link to="/app/analyze"><Button icon={Rocket}>Analyze a startup</Button></Link>} />

      {cfg.dataset?.synthetic_fallback && (
        <div className="mb-5 rounded-[6px] border border-warn/40 bg-warn/[0.07] p-3 text-sm text-muted" role="note">
          <b className="font-mono text-[11px] uppercase tracking-wider text-warn">Data note · </b>
          the public Kaggle download was unavailable, so VenturePulse is running on a realistic synthetic dataset with the same schema. Predictions reflect that dataset.
        </div>
      )}

      <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Historical startups" value={i.total} icon={Boxes} sub="in the training set" />
        <StatCard label="Successful" value={i.success} icon={CheckCircle2} tone="ok" sub="acquired / success" />
        <StatCard label="Failed" value={i.failure} icon={XCircle} tone="alert" sub="closed / failure" />
        <StatCard label="Success rate" value={i.success_rate * 100} format={(v) => `${v.toFixed(1)}%`} icon={TrendingUp} tone="info" sub="share of all startups" />
      </Stagger>

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card title="Best validated model" eyebrow="serving" className="lg:col-span-1" action={<Badge tone="ok" dot>selected</Badge>}>
          <div className="font-mono text-xl font-semibold text-fg">{m.best_model}</div>
          <div className="mt-1 text-xs text-muted">5 repeated stratified 80/20 splits · {num(cfg.n_train)} historical startups</div>
          <div className="mt-4">
            <KeyValueList items={[
              ['Balanced accuracy', meanStd(best.balanced_accuracy)],
              ['Accuracy', meanStd(best.accuracy)],
              ['Precision', meanStd(best.precision)],
              ['Recall', meanStd(best.recall)],
              ['F1-score', meanStd(best.f1)],
            ]} />
          </div>
        </Card>

        <Card title="Class distribution" eyebrow="dataset" className="lg:col-span-1">
          <Donut label="Class distribution: successful versus failed startups" height={230}
            data={[{ name: 'SUCCESS', value: i.success, color: tokens.ok }, { name: 'FAILURE', value: i.failure, color: tokens.alert }]}
            center={<div><div className="font-mono text-2xl font-semibold text-fg">{pct(i.success_rate, 1)}</div><div className="font-mono text-[10px] uppercase tracking-wider text-muted">success</div></div>} />
        </Card>

        <Card title="Model comparison" eyebrow="balanced accuracy" className="lg:col-span-1"
          action={<Link to="/app/performance" className="font-mono text-[11px] uppercase tracking-wider text-ok hover:underline">details</Link>}>
          <Bars data={compare} xKey="name" layout="horizontal" height={230} xWidth={108} valueFormat={(v) => fixed(v, 2)} domain={[0, 1]}
            label="Balanced accuracy of each model" series={[{ key: 'bal', label: 'Balanced accuracy', color: tokens.info }]}
            colorBy={(r) => (r.name === m.best_model ? tokens.ok : tokens.info)} legend={false} />
        </Card>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card title="How VenturePulse works" eyebrow="method" className="lg:col-span-2">
          <ol className="space-y-3">
            {STEPS.map((s, idx) => (
              <li key={s} className="flex gap-3 text-sm text-muted">
                <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-[4px] border border-ok/40 bg-ok/10 font-mono text-[11px] text-ok">{idx + 1}</span>
                {s}
              </li>
            ))}
          </ol>
        </Card>
        <Card title="Pipeline" eyebrow="configuration" action={<Activity size={14} className="text-ok" aria-hidden="true" />}>
          <KeyValueList items={[
            ['Text embedding', `${cfg.embedding_dim}-d · ${cfg.embedding_backend || 'n/a'}`],
            ['Structured weight α', fixed(cfg.alpha, 1)],
            ['Default comparable cases', cfg.default_k],
            ['Class balance', `${cfg.class_counts.SUCCESS} / ${cfg.class_counts.FAILURE}`],
            ['Dataset', cfg.dataset?.synthetic_fallback ? 'synthetic fallback' : 'Kaggle public'],
          ]} />
        </Card>
      </div>
      <p className="mt-6 font-mono text-[11px] text-dim">Estimated startup outcome. This prediction is an analytical estimate, not a guarantee of future performance.</p>
    </>
  )
}

