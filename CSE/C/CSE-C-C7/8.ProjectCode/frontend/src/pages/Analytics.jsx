import { useState } from 'react'
import { BarChart3, Database, Layers, Scale, ShieldCheck, Sigma } from 'lucide-react'
import { Alert, Badge, Card, EmptyState, ErrorState, KeyValueList, PageHeader, SkeletonBlock, StatCard, Table, Tabs } from '../components/ui'
import { BarBlocks, PALETTE } from '../components/ui/Charts'
import { Stagger } from '../components/motion'
import { get } from '../lib/api'
import { useApi } from '../lib/useApi'
import { fmtInt, fmtNum, fmtPct } from '../lib/format'

const MODEL_LABEL = { logistic_regression: 'Logistic regression', random_forest: 'Random forest', xgboost: 'XGBoost' }
const FEATURE_LABEL = {
  cum_clicks: 'Total clicks',
  recent_clicks: 'Recent clicks',
  quiz_count: 'Quizzes',
  forum_count: 'Discussions',
  completions: 'Completions',
  engagement: 'Engagement',
  weekly_hours: 'Weekly hours',
  skill_code: 'Skill level',
}
const label = (k) => MODEL_LABEL[k] || k

function load() {
  return Promise.all([get('/api/metrics'), get('/api/fairness')]).then(([metrics, fair]) => ({ metrics, fair }))
}

function ConfusionMatrix({ name, m, selected }) {
  const [[tn, fp], [fn, tp]] = m
  return (
    <Card flat title={label(name)} actions={selected && <Badge tone="pass">Selected</Badge>}>
      <div className="cm" role="table" aria-label={`${label(name)} confusion matrix`}>
        <div className="hd" />
        <div className="hd">Pred. 0</div>
        <div className="hd">Pred. 1</div>
        <div className="hd">Actual 0</div>
        <div className="cell ok">{fmtInt(tn)}</div>
        <div className="cell bad">{fmtInt(fp)}</div>
        <div className="hd">Actual 1</div>
        <div className="cell bad">{fmtInt(fn)}</div>
        <div className="cell ok">{fmtInt(tp)}</div>
      </div>
    </Card>
  )
}

function Models({ m }) {
  const rows = Object.entries(m.models).map(([k, v]) => ({ id: k, name: label(k), ...v }))
  const colsNum = [
    ['roc_auc', 'ROC AUC'],
    ['accuracy', 'Accuracy'],
    ['precision', 'Precision'],
    ['recall', 'Recall'],
    ['f1', 'F1'],
    ['brier', 'Brier'],
  ]
  const columns = [
    {
      key: 'name',
      label: 'Model',
      render: (r) => (
        <span className="row" style={{ '--gap': '8px' }}>
          <strong>{r.name}</strong>
          {r.id === m.selected_model && <Badge tone="pass">Selected</Badge>}
        </span>
      ),
    },
    ...colsNum.map(([key, lab]) => ({ key, label: lab, numeric: true, render: (r) => fmtNum(r[key], 3) })),
  ]
  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <Table caption="Held-out test metrics per model" columns={columns} rows={rows} pageSize={10} />
      <Card title="ROC AUC by model">
        <BarBlocks
          data={rows.map((r) => ({ name: r.name, auc: r.roc_auc }))}
          xKey="name"
          yKey="auc"
          name="ROC AUC"
          decimals={2}
          height={260}
          colorFn={(d) => (d.name === label(m.selected_model) ? PALETTE.lime : PALETTE.sky)}
        />
        <p className="small muted" style={{ marginTop: 10 }}>
          Selected by validation AUC. Metrics come from the local training run on <strong>{m.dataset_source}</strong>; lower is better for Brier.
        </p>
      </Card>
    </div>
  )
}

function Diagnostics({ m }) {
  const importance = Object.entries(m.feature_importance || {}).map(([k, v]) => ({ name: FEATURE_LABEL[k] || k, value: v }))
  const [plotFailed, setPlotFailed] = useState(false)
  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <div className="grid grid-3">
        {Object.entries(m.models).map(([k, v]) => (
          <ConfusionMatrix key={k} name={k} m={v.confusion_matrix} selected={k === m.selected_model} />
        ))}
      </div>
      <div className="two-col">
        <Card title="Feature importance">
          {importance.length ? (
            <BarBlocks data={importance} xKey="name" yKey="value" name="Importance" decimals={2} color={PALETTE.amber} height={300} />
          ) : (
            <p className="muted">No feature importance was recorded.</p>
          )}
        </Card>
        <Card title="ROC curve">
          {plotFailed ? (
            <Alert tone="warning">The ROC plot is missing. Run python scripts/train_pipeline.py to generate it.</Alert>
          ) : (
            <div className="plot-frame">
              <img src="/static/roc_curve.png" alt="ROC curve of the selected model on the held-out test set" onError={() => setPlotFailed(true)} />
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

function Policy({ m }) {
  const p = m.policy_evaluation || {}
  const available = [p.ips, p.snips, p.doubly_robust].some((v) => v !== null && v !== undefined)
  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <Alert tone="info">Offline policy evaluation on logged data only. It is not a live A/B test result.</Alert>
      <Stagger className="grid grid-3" inView={false}>
        <StatCard label="IPS" value={fmtNum(p.ips, 3)} icon={Sigma} hint="Inverse propensity scoring" />
        <StatCard label="SNIPS" value={fmtNum(p.snips, 3)} icon={Sigma} hint="Self-normalised IPS" />
        <StatCard label="Doubly robust" value={fmtNum(p.doubly_robust, 3)} icon={Sigma} hint="IPS + outcome model" />
      </Stagger>
      {!available && (
        <Alert tone="warning">
          Not available in the current training run{p.reason ? `: ${p.reason}` : '.'} Fix the cause and re-run scripts/train_pipeline.py to populate these values.
        </Alert>
      )}
      {p.limitation && <Alert tone="warning">{p.limitation}</Alert>}
    </div>
  )
}

function Fairness({ fair }) {
  const groups = [
    ['age_band', 'By age band'],
    ['gender', 'By gender'],
  ]
  const cols = [
    { key: 'group', label: 'Group' },
    { key: 'n', label: 'Learners', numeric: true, render: (r) => fmtInt(r.n) },
    { key: 'success_rate', label: 'Success rate', numeric: true, render: (r) => fmtPct(r.success_rate, 1) },
    { key: 'avg_predicted', label: 'Avg predicted', numeric: true, render: (r) => fmtPct(r.avg_predicted, 1) },
    { key: 'f1', label: 'F1', numeric: true, render: (r) => fmtNum(r.f1, 3) },
  ]
  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <Alert tone="info">{fair.note}</Alert>
      {groups.map(([key, title]) => {
        const rows = Object.entries(fair.fairness?.[key] || {}).map(([group, v]) => ({ group, ...v }))
        return (
          <Card key={key} title={title}>
            {rows.length ? <Table caption={title} columns={cols} rows={rows} pageSize={10} /> : <p className="muted">No data recorded for this group.</p>}
          </Card>
        )
      })}
    </div>
  )
}

export default function Analytics() {
  const q = useApi(load, [])
  const [tab, setTab] = useState('models')
  return (
    <div className="container" style={{ paddingTop: 36, paddingBottom: 64 }}>
      <PageHeader
        eyebrow="Model analytics"
        title="Nothing hidden"
        description="Real metrics from the local training run. Offline estimates only; no live A/B testing, and no number on this page is made up."
      />
      {q.loading && !q.data ? (
        <SkeletonBlock rows={7} label="Loading model metrics" />
      ) : q.error && !q.data ? (
        q.error.status === 503 ? (
          <EmptyState icon={Database} title="Models are not trained yet">
            The API says the model artifacts are not ready. Run <code>python scripts/train_pipeline.py</code> from the project folder, then reload.
          </EmptyState>
        ) : (
          <ErrorState title="Could not load model metrics" error={q.error} onRetry={q.reload} />
        )
      ) : (
        <div className="stack" style={{ '--gap': '28px' }}>
          <Stagger className="grid grid-4" inView={false}>
            <StatCard label="Selected model" value={label(q.data.metrics.selected_model)} icon={Layers} />
            <StatCard label="Test samples" value={q.data.metrics.test_samples} icon={Scale} hint={`${fmtInt(q.data.metrics.train_samples)} train · ${fmtInt(q.data.metrics.val_samples)} val`} />
            <StatCard label="Dataset" value={q.data.metrics.dataset_source} icon={Database} />
            <StatCard label="Features" value={q.data.metrics.features.length} icon={BarChart3} hint={`${q.data.metrics.actions.length} action types scored`} />
          </Stagger>
          <Tabs
            label="Analytics sections"
            value={tab}
            onChange={setTab}
            tabs={[
              { id: 'models', label: 'Models', icon: Layers },
              { id: 'diagnostics', label: 'Diagnostics', icon: BarChart3 },
              { id: 'policy', label: 'Offline policy', icon: Sigma },
              { id: 'fairness', label: 'Fairness audit', icon: ShieldCheck },
            ]}
          />
          {tab === 'models' && <Models m={q.data.metrics} />}
          {tab === 'diagnostics' && <Diagnostics m={q.data.metrics} />}
          {tab === 'policy' && <Policy m={q.data.metrics} />}
          {tab === 'fairness' && <Fairness fair={q.data.fair} />}
          {q.data.metrics.notes && <p className="small muted">{q.data.metrics.notes}</p>}
        </div>
      )}
    </div>
  )
}
