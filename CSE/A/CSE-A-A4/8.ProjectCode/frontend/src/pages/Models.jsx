import { useState } from 'react'
import { Atom, GitCompare, Grid3x3, LineChart as LineIcon, ListOrdered } from 'lucide-react'
import { api } from '../lib/api'
import { useApi } from '../lib/useApi'
import { fmtNum, fmtPoints } from '../lib/format'
import { MODES, MODE_CODE, MODE_COLOR, MODE_LABEL, MODE_TONE } from '../lib/labels'
import { BarCompare, ChartLegend, GroupedBars, LineCompare } from '../components/charts'
import { Badge, Button, Card, EmptyState, ErrorState, KeyValueList, PageHeader, Segmented, Skeleton, Table, Tabs } from '../components/ui'
import { SlideUp } from '../components/motion'
import Loadable from '../components/app/Loadable'
import Heatmap from '../components/app/Heatmap'

const TABS = [
  { id: 'compare', label: 'Comparison', icon: GitCompare },
  { id: 'curves', label: 'Training curves', icon: LineIcon },
  { id: 'features', label: 'Features', icon: ListOrdered },
  { id: 'qubo', label: 'QUBO matrix', icon: Grid3x3 },
]
const METRICS = [
  { value: 'f1', label: 'F1' },
  { value: 'accuracy', label: 'Accuracy' },
  { value: 'precision', label: 'Precision' },
  { value: 'recall', label: 'Recall' },
  { value: 'loss', label: 'Loss' },
]

const load = () => Promise.all([api.comparison(), api.modelHistory(), api.featureImportance()])

function Comparison({ comparison, history }) {
  const untrained = Object.keys(history).length === 0
  const columns = [
    { key: 'Method', label: 'Model', render: (r) => <span><b>{MODE_LABEL[r.mode]}</b> <Badge tone={MODE_TONE[r.mode]}>{r.Method}</Badge></span>, sortValue: (r) => r.Method },
    { key: 'Accuracy', label: 'Accuracy', numeric: true, render: (r) => fmtPoints(r.Accuracy) },
    { key: 'Precision', label: 'Precision', numeric: true, render: (r) => fmtPoints(r.Precision) },
    { key: 'Recall', label: 'Recall', numeric: true, render: (r) => fmtPoints(r.Recall) },
    { key: 'F1-Score', label: 'F1', numeric: true, render: (r) => <b>{fmtPoints(r['F1-Score'])}</b> },
    { key: 'best_epoch', label: 'Best epoch', numeric: true },
    { key: 'TotalTime', label: 'Paper time', render: (r) => r.TotalTime },
    { key: 'measured', label: 'Measured here', numeric: true, render: (r) => (history[r.mode]?.elapsed_sec != null ? `${fmtNum(history[r.mode].elapsed_sec, 1)} s` : '–'), sortable: false },
  ]
  return (
    <div className="stack">
      {untrained && (
        <div className="notice warn" role="status">
          <span>No model has been trained on this machine, so these are the figures reported in the base paper. Train in the Model lab to see real results.</span>
        </div>
      )}
      <div className="grid-2 wide-left">
        <Card title="Metrics at each model's best epoch" subtitle="Percent, measured on the held-out 20% test split">
          <GroupedBars
            height={300}
            label="Grouped bars comparing accuracy, precision, recall and F1 for each model"
            valueFormat={(v) => `${v}%`}
            data={['Accuracy', 'Precision', 'Recall', 'F1-Score'].map((m) => ({
              x: m === 'F1-Score' ? 'F1' : m,
              ...Object.fromEntries(comparison.map((c) => [c.mode, c[m]])),
            }))}
            series={comparison.map((c) => ({ key: c.mode, name: `${MODE_LABEL[c.mode]} (${c.Method})`, color: MODE_COLOR[c.mode] }))}
          />
          <ChartLegend items={comparison.map((c) => ({ label: `${MODE_LABEL[c.mode]} (${c.Method})`, color: MODE_COLOR[c.mode] }))} />
        </Card>
        <Card title="How to read this" hover={false}>
          <KeyValueList
            items={[
              ['Classical (PCD)', 'Persistent contrastive divergence with Gibbs sampling'],
              ['Simulated annealing (SAS)', 'Annealing sweeps replace the Gibbs chain'],
              ['Quantum-inspired (QS)', 'Simulated quantum annealing with tunnelling; no quantum hardware is used'],
              ['Paper time', 'Training time reported in the base paper'],
              ['Measured here', 'Wall-clock seconds for the last run on this machine'],
            ]}
          />
        </Card>
      </div>
      <Card title="Model table">
        <Table columns={columns} rows={comparison} pageSize={0} cards caption="Model comparison" rowKey={(r) => r.mode} cardTitle={(r) => `${MODE_LABEL[r.mode]} (${r.Method})`} />
      </Card>
    </div>
  )
}

function Curves({ history }) {
  const [metric, setMetric] = useState('f1')
  const modes = MODES.filter((m) => history[m])
  if (!modes.length) {
    return <EmptyState icon={LineIcon} title="No training history yet" message="Train a model in the Model lab and its per-epoch curves appear here." action={<Button to="/app/lab">Open the Model lab</Button>} />
  }
  const epochs = Math.max(...modes.map((m) => history[m][metric].length))
  const data = Array.from({ length: epochs }, (_, i) => ({ x: i + 1, ...Object.fromEntries(modes.map((m) => [m, history[m][metric][i]])) }))
  const isLoss = metric === 'loss'
  return (
    <Card title="Per-epoch training curves" subtitle="Evaluated on the test split after every epoch" actions={<Segmented name="curve-metric" value={metric} onChange={setMetric} options={METRICS} label="" />}>
      <LineCompare
        data={data}
        height={340}
        dots={epochs <= 25}
        label={`Line chart of ${metric} per epoch for each model`}
        xFormat={(x) => `Epoch ${x}`}
        yFormat={isLoss ? (v) => fmtNum(v, 2) : (v) => `${Math.round(v * 100)}%`}
        valueFormat={isLoss ? (v) => fmtNum(v, 3) : (v) => `${(v * 100).toFixed(1)}%`}
        domain={isLoss ? undefined : [0, 1]}
        series={modes.map((m) => ({ key: m, name: `${MODE_LABEL[m]} (${MODE_CODE[m]})`, color: MODE_COLOR[m] }))}
      />
      <ChartLegend items={modes.map((m) => ({ label: `${MODE_LABEL[m]} (${MODE_CODE[m]})`, color: MODE_COLOR[m] }))} />
    </Card>
  )
}

function Features({ fi }) {
  const top = fi.importance.slice(0, 18)
  return (
    <div className="grid-2 wide-left">
      <Card title="Feature importance" subtitle="Random-forest ranking after one-hot encoding. Lavender bars are the features the models use.">
        <BarCompare
          horizontal
          yWidth={225}
          height={Math.max(300, top.length * 30)}
          name="Importance"
          label="Bar chart of feature importance"
          valueFormat={(v) => fmtNum(v, 3)}
          data={top.map((f) => ({ name: f.feature, value: f.importance, highlight: f.selected }))}
        />
      </Card>
      <Card title="Pipeline in numbers" hover={false}>
        <KeyValueList
          items={[
            ['Features used', fi.columns.length],
            ['Training shape', fi.train_shape.join(' × ')],
            ['Test shape', fi.test_shape.join(' × ')],
            ['Dropped as correlated', fi.dropped_corr.length ? fi.dropped_corr.join(', ') : 'None'],
          ]}
        />
      </Card>
    </div>
  )
}

function Qubo({ trained }) {
  const available = MODES.filter((m) => trained.includes(m))
  const [mode, setMode] = useState(available[0] || 'classical')
  const state = useApi(() => api.qubo(mode), [mode])
  const q = state.data
  return (
    <Card
      title="QUBO matrix of the RBM"
      subtitle="The model's energy function written as a quadratic binary problem, the form an annealer or quantum sampler solves"
      actions={<Segmented name="qubo-mode" value={mode} onChange={setMode} options={MODES.map((m) => ({ value: m, label: MODE_CODE[m] }))} label="" />}
    >
      {state.loading && !q && <Skeleton height={360} radius={18} />}
      {state.error && (
        <ErrorState
          title={state.error.status === 404 ? 'This model has not been trained' : 'The matrix could not load'}
          error={state.error}
          hint={state.error.status === 404 ? 'Train it in the Model lab, then come back.' : undefined}
          onRetry={state.reload}
          compact
        />
      )}
      {q && (
        <div className="grid-2" style={{ alignItems: 'start' }}>
          <Heatmap matrix={q.Q} label={`QUBO matrix heatmap for the ${MODE_LABEL[mode]} model`} />
          <div className="stack">
            <KeyValueList
              items={[
                ['Full size', `${q.shape[0]} × ${q.shape[1]}`],
                ['Shown', `top-left ${q.display_size} × ${q.display_size}`],
                ['Minimum', fmtNum(q.stats.min, 4)],
                ['Maximum', fmtNum(q.stats.max, 4)],
                ['Mean', fmtNum(q.stats.mean, 5)],
              ]}
            />
            <div>
              <div className="heat-scale" aria-hidden="true" />
              <div className="row between small muted" style={{ maxWidth: 320, marginTop: 6 }}>
                <span>Negative</span>
                <span>0</span>
                <span>Positive</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

export default function Models() {
  const state = useApi(load)
  const [tab, setTab] = useState('compare')
  const [comparison, history, fi] = state.data || []
  const trained = history ? Object.keys(history) : []

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <PageHeader
        eyebrow="Under the hood"
        icon={Atom}
        title="Model comparison"
        lead="Three restricted Boltzmann machine classifiers trained with different samplers, side by side."
        actions={<Button to="/app/lab" variant="secondary">Retrain in the lab</Button>}
      />
      <Loadable state={state} kpis={0} title="Model details could not load">
        {state.data && (
          <>
            <Tabs tabs={TABS} value={tab} onChange={setTab} label="Model views" name="models" />
            <SlideUp key={tab}>
              {tab === 'compare' && (comparison.length ? <Comparison comparison={comparison} history={history} /> : <EmptyState icon={Atom} title="No models trained yet" message="Train at least one model to compare results." action={<Button to="/app/lab">Open the Model lab</Button>} />)}
              {tab === 'curves' && <Curves history={history} />}
              {tab === 'features' && <Features fi={fi} />}
              {tab === 'qubo' && <Qubo trained={trained} />}
            </SlideUp>
          </>
        )}
      </Loadable>
    </div>
  )
}
