import { useMemo, useState } from 'react'
import { BarChart3, CheckCircle2, Clock, Gauge as GaugeIcon, History, Radar, Trophy } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { fmtCompact, fmtDateTime, fmtInt, fmtMetric, fmtPct, fmtSeconds } from '../lib/format'
import { Badge, Card, EmptyState, ErrorState, PageHeader, Skeleton, StatCard, Table, Tabs } from '../components/ui'
import { ChartLegend, GroupedBars, LineCompare } from '../components/charts'
import { Callout, Load } from '../components/app'
import { useChartTheme } from '../lib/palette'

const COLOR_KEYS = { baseline: 'peach', gcn: 'sky', gat: 'mint', sage: 'lavender' }

/** Resample each model's ROC curve onto a shared false-positive-rate grid so one chart can draw them all. */
function rocRows(models) {
  const grid = Array.from({ length: 41 }, (_, i) => i / 40)
  const interp = (roc, x) => {
    const { fpr, tpr } = roc
    for (let i = 1; i < fpr.length; i++) {
      if (fpr[i] >= x) {
        const span = fpr[i] - fpr[i - 1] || 1
        return tpr[i - 1] + ((tpr[i] - tpr[i - 1]) * (x - fpr[i - 1])) / span
      }
    }
    return tpr[tpr.length - 1]
  }
  return grid.map((x) => ({ x, ...Object.fromEntries(models.map((m) => [m.name, interp(m.roc, x)])) }))
}

function Comparison({ d }) {
  const t = useChartTheme()
  const col = (n) => t[COLOR_KEYS[n]]
  const best = d.models.find((m) => m.is_best)
  const roc = useMemo(() => rocRows(d.models), [d.models])
  const cm = best.confusion
  const rec = d.cluster_recovery
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <div className="grid-kpi">
        <StatCard label="Best architecture" display={best.label} icon={Trophy} tone="lavender" foot={`chosen on validation F1, ${d.meta.config.seeds.length ? 'averaged over seeds' : ''}`} />
        <StatCard label="F1 of the best" value={best.f1.mean} format={(v) => fmtPct(v, 1)} icon={CheckCircle2} tone="mint" foot={`± ${fmtMetric(best.f1.std)} over seeds`} />
        <StatCard label="Lift over no graph" value={best.f1_lift * 100} format={(v) => `+${v.toFixed(1)} pts`} icon={BarChart3} tone="sky" foot="F1 vs the feature-only baseline" />
        <StatCard label="Botnets recovered" display={`${rec.recovered} / ${rec.botnets}`} icon={Radar} tone="rose" foot={`mean recall ${fmtPct(rec.mean_recall, 0)} · precision ${fmtPct(rec.mean_precision, 0)}`} />
      </div>

      <Card title="Architectures on the same split" subtitle={`Test set: ${d.split.test} accounts. Mean over ${d.models[0].per_seed.length} training seeds. Threshold tuned on the validation set.`}>
        <Table
          caption="Model comparison"
          rowKey={(r) => r.name}
          pageSize={0}
          highlight={(r) => r.is_best}
          cardTitle={(r) => r.label}
          initialSort={{ key: 'f1', dir: 'desc' }}
          columns={[
            {
              key: 'label',
              label: 'Model',
              render: (r) => (
                <span className="row" style={{ '--gap': '8px' }}>
                  {r.label}
                  {r.is_best && <Badge tone="lavender">best</Badge>}
                  {!r.uses_graph && <Badge tone="peach">no graph</Badge>}
                </span>
              ),
              sortValue: (r) => r.label,
            },
            { key: 'accuracy', label: 'Accuracy', numeric: true, render: (r) => fmtMetric(r.accuracy.mean), sortValue: (r) => r.accuracy.mean },
            { key: 'precision', label: 'Precision', numeric: true, render: (r) => fmtMetric(r.precision.mean), sortValue: (r) => r.precision.mean },
            { key: 'recall', label: 'Recall', numeric: true, render: (r) => fmtMetric(r.recall.mean), sortValue: (r) => r.recall.mean },
            { key: 'f1', label: 'F1', numeric: true, render: (r) => `${fmtMetric(r.f1.mean)} ± ${fmtMetric(r.f1.std)}`, sortValue: (r) => r.f1.mean },
            { key: 'roc_auc', label: 'ROC-AUC', numeric: true, render: (r) => fmtMetric(r.roc_auc.mean), sortValue: (r) => r.roc_auc.mean },
            { key: 'pr_auc', label: 'PR-AUC', numeric: true, render: (r) => fmtMetric(r.pr_auc.mean), sortValue: (r) => r.pr_auc.mean },
            { key: 'lift', label: 'F1 vs baseline', numeric: true, render: (r) => (r.uses_graph ? `${r.f1_lift >= 0 ? '+' : ''}${(r.f1_lift * 100).toFixed(1)} pts` : '–'), sortValue: (r) => r.f1_lift },
            { key: 'train_seconds', label: 'Train time', numeric: true, render: (r) => fmtSeconds(r.train_seconds), sortValue: (r) => r.train_seconds },
          ]}
          rows={d.models}
        />
      </Card>

      <div className="grid-2">
        <Card title="Precision, recall and F1" subtitle="On an imbalanced set, accuracy alone hides missed fakes.">
          <GroupedBars
            height={300}
            data={['precision', 'recall', 'f1'].map((k) => ({ x: k === 'f1' ? 'F1' : k[0].toUpperCase() + k.slice(1), ...Object.fromEntries(d.models.map((m) => [m.name, m[k].mean])) }))}
            series={d.models.map((m) => ({ key: m.name, name: m.label, color: col(m.name) }))}
            valueFormat={(v) => fmtMetric(v, 2)}
            label="Precision, recall and F1 per model"
          />
          <ChartLegend items={d.models.map((m) => ({ label: m.label, color: col(m.name) }))} />
        </Card>
        <Card title="ROC curves" subtitle="Higher and further left is better. The dashed diagonal is guessing.">
          <LineCompare
            height={300}
            data={[...roc, ...[]].map((r) => ({ ...r, chance: r.x }))}
            series={[...d.models.map((m) => ({ key: m.name, name: m.label, color: col(m.name) })), { key: 'chance', name: 'Chance', color: t.axis, dashed: true }]}
            xFormat={(v) => Number(v).toFixed(2)}
            valueFormat={(v) => Number(v).toFixed(3)}
            yFormat={(v) => Number(v).toFixed(1)}
            domain={[0, 1]}
            dots={false}
            label="ROC curves for each model"
          />
          <ChartLegend items={d.models.map((m) => ({ label: m.label, color: col(m.name) }))} />
        </Card>
      </div>

      <div className="grid-2">
        <Card title={`Confusion matrix · ${best.label}`} subtitle={`Test accounts at threshold ${fmtMetric(best.threshold, 2)}.`}>
          <div className="confusion" role="img" aria-label={`Confusion matrix: ${cm.tn} true negatives, ${cm.fp} false positives, ${cm.fn} false negatives, ${cm.tp} true positives`}>
            <span />
            <span className="head">Predicted genuine</span>
            <span className="head">Predicted fake</span>
            <span className="side">Genuine</span>
            <span className="cell" style={{ background: 'var(--mint-soft)' }}><b>{fmtInt(cm.tn)}</b>correct</span>
            <span className="cell" style={{ background: 'var(--peach-soft)' }}><b>{fmtInt(cm.fp)}</b>false alarm</span>
            <span className="side">Fake</span>
            <span className="cell" style={{ background: 'var(--rose-soft)' }}><b>{fmtInt(cm.fn)}</b>missed</span>
            <span className="cell" style={{ background: 'var(--mint-soft)' }}><b>{fmtInt(cm.tp)}</b>caught</span>
          </div>
        </Card>
        <Card title="Botnet recovery" subtitle="Each injected botnet against the best-matching detected cluster.">
          <Table
            caption="Botnet recovery"
            rowKey={(r) => r.botnet}
            pageSize={0}
            cards={false}
            columns={[
              { key: 'botnet', label: 'Injected botnet', render: (r) => `#${r.botnet + 1} · ${r.size} accounts`, sortValue: (r) => r.botnet },
              { key: 'recall', label: 'Recall', numeric: true, render: (r) => fmtPct(r.recall, 0) },
              { key: 'precision', label: 'Precision', numeric: true, render: (r) => fmtPct(r.precision, 0) },
              { key: 'recovered', label: 'Recovered', render: (r) => <Badge tone={r.recovered ? 'mint' : 'peach'}>{r.recovered ? 'one community' : 'partly'}</Badge>, sortable: false },
            ]}
            rows={rec.per_botnet}
          />
        </Card>
      </div>
    </div>
  )
}

function Scalability() {
  const state = useAsync(() => api.scalability(), [])
  const t = useChartTheme()
  return (
    <Load state={state} title="Could not load the scalability sweep" skeleton={<Skeleton height={360} radius={20} />}>
      {(s) => {
        const names = ['baseline', 'gcn', 'gat', 'sage']
        const series = names.map((n) => ({ key: n, name: s.labels[n], color: t[COLOR_KEYS[n]] }))
        const rowsTrain = s.rows.map((r) => ({ x: r.nodes, edges: r.edges, ...Object.fromEntries(names.map((n) => [n, r.models[n].train_seconds_per_epoch])) }))
        const rowsInfer = s.rows.map((r) => ({ x: r.nodes, ...Object.fromEntries(names.map((n) => [n, r.models[n].inference_seconds])) }))
        const first = s.rows[0]
        const last = s.rows[s.rows.length - 1]
        return (
          <div className="stack" style={{ '--gap': '22px' }}>
            <Callout tone="info" title="How the sweep works">
              The account graph is copied {first.nodes === last.nodes ? '' : `1 to ${last.nodes / first.nodes} times`} as disjoint components, growing from {fmtInt(first.nodes)} to {fmtInt(last.nodes)} accounts and {fmtCompact(first.edges)} to {fmtCompact(last.edges)} ties. Training time is averaged over {s.epochs_timed} epochs, inference is the median of 3 forward passes, on CPU.
            </Callout>
            <div className="grid-2">
              <Card title="Training time per epoch" subtitle="Seconds, as the graph grows.">
                <LineCompare height={300} data={rowsTrain} series={series} xFormat={(v) => fmtCompact(v)} valueFormat={fmtSeconds} yFormat={(v) => `${Number(v).toFixed(1)}s`} label="Training time per epoch against number of accounts" />
                <ChartLegend items={series.map((x) => ({ label: x.name, color: x.color }))} />
              </Card>
              <Card title="Inference time" subtitle="One forward pass over every account.">
                <LineCompare height={300} data={rowsInfer} series={series} xFormat={(v) => fmtCompact(v)} valueFormat={fmtSeconds} yFormat={(v) => `${Number(v).toFixed(2)}s`} label="Inference time against number of accounts" />
                <ChartLegend items={series.map((x) => ({ label: x.name, color: x.color }))} />
              </Card>
            </div>
            <Card title="Measurements">
              <Table
                caption="Scalability measurements"
                rowKey={(r) => r.nodes}
                pageSize={0}
                cardTitle={(r) => `${fmtInt(r.nodes)} accounts`}
                columns={[
                  { key: 'nodes', label: 'Accounts', numeric: true, render: (r) => fmtInt(r.nodes) },
                  { key: 'edges', label: 'Ties', numeric: true, render: (r) => fmtInt(r.edges) },
                  ...names.map((n) => ({
                    key: n,
                    label: `${s.labels[n]} · train / infer`,
                    numeric: true,
                    sortValue: (r) => r.models[n].train_seconds_per_epoch,
                    render: (r) => `${fmtSeconds(r.models[n].train_seconds_per_epoch)} / ${fmtSeconds(r.models[n].inference_seconds)}`,
                  })),
                ]}
                rows={s.rows}
              />
            </Card>
          </div>
        )
      }}
    </Load>
  )
}

function Runs({ d }) {
  const runs = d.runs
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <Callout tone="info" title="Learning from moderators">
        Each retraining run adds your confirm and dismiss decisions to the training labels. The test split is never touched, so the before and after F1 below are measured on the same accounts (one training seed each).
      </Callout>
      <Card title="Retraining runs" subtitle="Newest first. Start a run from the moderator queue.">
        <Table
          caption="Retraining runs"
          rowKey={(r) => r.id}
          pageSize={0}
          cardTitle={(r) => `Run #${r.id}`}
          columns={[
            { key: 'id', label: 'Run', render: (r) => `#${r.id}`, sortValue: (r) => r.id },
            { key: 'started_at', label: 'Started', render: (r) => fmtDateTime(r.started_at), sortValue: (r) => r.started_at },
            { key: 'status', label: 'Status', render: (r) => <Badge tone={r.status === 'done' ? 'mint' : r.status === 'error' ? 'rose' : 'peach'}>{r.status}</Badge> },
            { key: 'feedback_labels', label: 'Labels used', numeric: true },
            { key: 'best', label: 'Best', render: (r) => r.best || '–' },
            ...['gcn', 'gat', 'sage'].map((m) => ({
              key: m,
              label: `${m === 'sage' ? 'GraphSAGE' : m.toUpperCase()} F1`,
              numeric: true,
              sortable: false,
              render: (r) => (r.f1_after?.[m] != null ? `${fmtMetric(r.f1_before?.[m])} → ${fmtMetric(r.f1_after[m])}` : '–'),
            })),
          ]}
          rows={runs}
          empty={<EmptyState icon={History} title="No retraining runs yet" message="Confirm or dismiss a few accounts in the moderator queue, then retrain." compact />}
        />
      </Card>
    </div>
  )
}

export default function Models() {
  const state = useAsync(() => api.models(), [])
  const [tab, setTab] = useState('compare')
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader eyebrow="Models & scale" icon={BarChart3} title="Which architecture, and does it scale?" lead="GCN, GAT and GraphSAGE against a feature-only baseline on one split, how the graph size affects speed, and what retraining on moderator decisions changed." />
      <Tabs
        name="models"
        label="Model sections"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: 'compare', label: 'Comparison', icon: Trophy },
          { id: 'scale', label: 'Scalability', icon: GaugeIcon },
          { id: 'runs', label: 'Retraining', icon: Clock },
        ]}
      />
      {tab === 'scale' ? (
        <Scalability />
      ) : (
        <Load state={state} title="Could not load model results" skeleton={<Skeleton height={420} radius={20} />}>
          {(d) => (tab === 'compare' ? <Comparison d={d} /> : <Runs d={d} />)}
        </Load>
      )}
      {state.error && state.data && <ErrorState compact title="Could not refresh" error={state.error} onRetry={state.reload} />}
    </div>
  )
}
