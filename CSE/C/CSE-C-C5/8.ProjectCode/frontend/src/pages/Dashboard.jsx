import { Activity, GraduationCap, Percent, Trophy } from 'lucide-react'
import { useState } from 'react'
import { MonoBars } from '../components/charts/Bars'
import { PageHeader } from '../components/ui/AppShell'
import { Badge, Card, KeyValueList, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'
import { TabPanel, Tabs } from '../components/ui/nav'
import Table from '../components/ui/Table'
import { Stagger } from '../components/motion'
import { modelLabel, pct } from '../format'
import { useData } from '../lib/data'
import useFetch from '../lib/useFetch'

const PLOT_TABS = [
  { id: 'models', label: 'Model table' },
  { id: 'shap', label: 'SHAP importance' },
  { id: 'pca', label: 'PCA errors' },
  { id: 'prob_hist', label: 'Probabilities' },
]
const PLOT_INFO = {
  shap: ['SHAP feature importance', 'Which features push placement probability up or down - the explainability the placement officer asks for.'],
  pca: ['PCA: errors = borderline cases', 'Misclassified students sit among borderline-probability profiles, which is what the kNN residual step targets.'],
  prob_hist: ['Predicted probability distribution', 'Calibrated probabilities; the [0.4, 0.6] band is where the kNN residual refinement blends in.'],
}
const HYBRID = 'hybrid_xgb_knn'

function Plot({ name }) {
  const [failed, setFailed] = useState(false)
  const [title, body] = PLOT_INFO[name]
  return (
    <div>
      <p className="mb-3 text-sm text-muted">{body}</p>
      {failed ? (
        <ErrorState error={{ message: `Could not load the ${title} image.`, hint: 'Generate it with: python src/hybrid_model.py' }} />
      ) : (
        <div className="overflow-hidden rounded-[6px] border border-line bg-white p-2">
          <img src={`/api/plots/${name}`} alt={`${title} chart produced by the training pipeline`} className="mx-auto max-h-[560px] w-full object-contain" onError={() => setFailed(true)} />
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const { stats, error: dataError, reload } = useData()
  const m = useFetch('/metrics')
  const [tab, setTab] = useState('models')

  const results = m.data?.results
  const rows = results ? Object.entries(results).map(([k, v]) => ({ id: k, ...v })) : null
  const best = rows && rows.reduce((a, b) => (b.roc_auc > a.roc_auc ? b : a))
  const branchRows = stats && Object.entries(stats.by_branch).map(([branch, rate]) => ({ branch, rate })).sort((a, b) => b.rate - a.rate)
  const chart = rows && rows.map((r) => ({ name: modelLabel(r.id), id: r.id, auc: r.roc_auc, f1: r.f1, accuracy: r.accuracy }))
  const failed = m.error || dataError

  const cols = [
    { key: 'id', label: 'Model', sortable: true, defaultDir: 'asc', sortValue: (r) => modelLabel(r.id),
      render: (r) => <span className="inline-flex items-center gap-2 font-medium text-fg">{modelLabel(r.id)}{r.id === HYBRID && <Badge tone="ok">proposed</Badge>}{r.id === best?.id && r.id !== HYBRID && <Badge tone="info">best auc</Badge>}</span> },
    ...[['accuracy', 'Acc'], ['roc_auc', 'AUC'], ['f1', 'F1'], ['precision', 'Prec'], ['recall', 'Rec']].map(([key, label]) => ({
      key, label, sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => r[key].toFixed(4),
    })),
  ]

  return (
    <div>
      <PageHeader eyebrow="Placement officer" title="Officer dashboard"
        subtitle="Model quality, explainability and placement statistics from the trained pipeline and the campus dataset." />

      {failed && !m.data && !stats ? <ErrorState error={failed} onRetry={() => { reload(); m.reload() }} title="Could not load dashboard data" /> : (
        <div className="space-y-5">
          <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard label="Students in dataset" icon={GraduationCap} value={stats ? stats.total : '…'} live tone="ok" sub="historical placement records" />
            <StatCard label="Placed rate" icon={Percent} value={stats ? stats.placed_rate * 100 : '…'} format={(v) => `${v.toFixed(1)}%`} tone="cyan" sub={stats ? `avg CGPA ${stats.avg_cgpa}` : undefined} />
            <StatCard label="Hybrid XGB+kNN AUC" icon={Trophy} value={results?.[HYBRID] ? results[HYBRID].roc_auc : '…'} format={(v) => v.toFixed(4)} tone="info" sub={results ? `accuracy ${pct(results[HYBRID].accuracy)}` : undefined} />
            <StatCard label="9-fold CV (XGB)" icon={Activity} value={m.data ? m.data.cv_xgb_9fold : '…'} format={(v) => v.toFixed(4)} tone="warn" sub={m.data ? `Brier ${m.data.brier_platt} · residual ${pct(m.data.residual_rate)}` : undefined} />
          </Stagger>

          <div className="grid gap-5 lg:grid-cols-5">
            <Card title="Model comparison" eyebrow="test set · ROC AUC / F1" className="lg:col-span-3">
              {!chart ? <Skeleton className="h-[300px]" /> : (
                <MonoBars data={chart} xKey="name" series={[{ key: 'auc', label: 'ROC AUC', tone: 'ok' }, { key: 'f1', label: 'F1', tone: 'cyan' }]}
                  domain={[0.6, 1]} valueFormat={(v) => v.toFixed(2)} angle={-30} height={300} highlight={modelLabel(HYBRID)} label="Bar chart comparing ROC AUC and F1 of nine models" />
              )}
            </Card>
            <Card title="Placed rate by branch" eyebrow="dataset" className="lg:col-span-2">
              {!branchRows ? <Skeleton className="h-[300px]" /> : (
                <MonoBars data={branchRows} xKey="branch" series={[{ key: 'rate', label: 'Placed rate', tone: 'warn' }]} domain={[0, 1]}
                  valueFormat={(v) => pct(v, 0)} height={300} label="Bar chart of placed rate for each branch" />
              )}
            </Card>
          </div>

          <Card bodyClass="p-4">
            <Tabs id="dash" tabs={PLOT_TABS} value={tab} onChange={setTab} label="Dashboard detail" />
            <TabPanel tabsId="dash" value={tab} className="pt-4">
              {tab === 'models' ? (
                <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
                  {m.error ? <ErrorState error={m.error} onRetry={m.reload} title="Could not load metrics" /> : (
                    <Table columns={cols} rows={rows} loading={m.loading} rowKey={(r) => r.id} caption="Model metrics on the held-out test set"
                      initialSort={{ key: 'roc_auc', dir: 'desc' }}
                      empty={<EmptyState title="No metrics yet" body="Train the models first: python src/generate_dataset.py, src/preprocess.py, src/hybrid_model.py." />} />
                  )}
                  <div>
                    <h3 className="mb-1 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">Pipeline diagnostics</h3>
                    {m.data ? (
                      <KeyValueList items={[['9-fold CV (XGB)', m.data.cv_xgb_9fold], ['Brier (Platt)', m.data.brier_platt], ['Residual rate', m.data.residual_rate], ['Test set size', m.data.test_size]]} />
                    ) : <Skeleton className="h-28" />}
                  </div>
                </div>
              ) : <Plot name={tab} />}
            </TabPanel>
          </Card>
        </div>
      )}
    </div>
  )
}
