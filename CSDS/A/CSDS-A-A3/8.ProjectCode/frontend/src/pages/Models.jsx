import { useEffect, useState } from 'react'
import { useMediaQuery } from '../lib/motion'
import { BrainCircuit, Clock, Crown, Database, Layers, RefreshCw, Sparkles, Terminal } from 'lucide-react'
import { api } from '../lib/api'
import { useStats } from '../lib/stats'
import { modelLabel, num, pct, when } from '../lib/format'
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Container,
  EmptyState,
  ErrorState,
  KeyValueList,
  Modal,
  PageHeader,
  ProgressBar,
  Skeleton,
  StatCard,
  Table,
  Tabs,
  useToast,
} from '../components/ui'
import { ChartCard, GroupedBarChart, HBarChart, Legend, RadarCompare, useChartColors } from '../components/charts'
import { Reveal, Stagger } from '../components/motion'
import '../styles/pages.css'

const METRICS = [
  { key: 'accuracy', label: 'Accuracy', short: 'Acc' },
  { key: 'precision', label: 'Precision', short: 'Prec' },
  { key: 'recall', label: 'Recall', short: 'Rec' },
  { key: 'f1', label: 'F1-score', short: 'F1' },
  { key: 'roc_auc', label: 'ROC-AUC', short: 'AUC' },
]

function ConfusionMatrix({ cm }) {
  const total = cm.tp + cm.tn + cm.fp + cm.fn || 1
  const cells = [
    { k: 'TN', v: cm.tn, label: 'Legit → legit', good: true },
    { k: 'FP', v: cm.fp, label: 'Legit → phishing', good: false },
    { k: 'FN', v: cm.fn, label: 'Phishing → legit', good: false },
    { k: 'TP', v: cm.tp, label: 'Phishing → phishing', good: true },
  ]
  return (
    <div>
      <div className="cm-axis faint">
        <span />
        <span>Predicted legit</span>
        <span>Predicted phishing</span>
      </div>
      <div className="cm">
        <span className="cm-row faint">Actual legit</span>
        {cells.slice(0, 2).map((c) => (
          <Cell key={c.k} c={c} total={total} />
        ))}
        <span className="cm-row faint">Actual phishing</span>
        {cells.slice(2).map((c) => (
          <Cell key={c.k} c={c} total={total} />
        ))}
      </div>
    </div>
  )
}

function Cell({ c, total }) {
  const share = c.v / total
  return (
    <div className={`cm-cell ${c.good ? 'good' : 'bad'}`} style={{ '--share': Math.min(1, share * 2.2) }} aria-label={`${c.k}: ${c.v} (${c.label})`}>
      <strong>{num(c.v)}</strong>
      <span>
        {c.k} · {(share * 100).toFixed(1)}%
      </span>
    </div>
  )
}

export default function Models() {
  const { metrics, ti, loading, error, refresh, retraining, watchRetrain, onRetrainDone } = useStats()
  const colors = useChartColors()
  const toast = useToast()
  const [confirm, setConfirm] = useState(false)
  const [starting, setStarting] = useState(false)
  const [tab, setTab] = useState(null)
  const narrow = useMediaQuery('(max-width: 640px)')

  useEffect(
    () =>
      onRetrainDone((s) => {
        const m = s.metrics
        toast({
          title: 'Retraining finished',
          message: m?.best_model ? `${modelLabel(m.best_model)} selected · model v${m.model_version} · F1 ${pct(m.models[m.best_model].f1, 2)}` : 'Models reloaded.',
          duration: 8000,
        })
      }),
    [onRetrainDone, toast],
  )

  const startRetrain = async () => {
    setStarting(true)
    try {
      await api.startRetrain()
      watchRetrain()
      await refresh()
      setConfirm(false)
      toast({ tone: 'info', title: 'Retraining started', message: 'All three models are retraining in the background - this page updates when it finishes.' })
    } catch (e) {
      toast({ tone: 'error', title: 'Could not start retraining', message: e.message })
    } finally {
      setStarting(false)
    }
  }

  const names = metrics ? Object.keys(metrics.models) : []
  const active = tab && names.includes(tab) ? tab : metrics?.best_model
  const series = names.map((n, i) => ({ key: n, label: modelLabel(n), color: colors.model[n] || colors.series[i % colors.series.length] }))
  const chartData = METRICS.map((m) => ({ metric: narrow ? m.short : m.label, ...Object.fromEntries(names.map((n) => [n, metrics.models[n][m.key]])) }))
  const best = metrics?.models?.[metrics.best_model]
  const confirmed = ti ? ti.confirmed_phishing + ti.confirmed_safe : 0

  const retrainCard = (
    <Card className="retrain-card">
      <div className="card-body row" style={{ justifyContent: 'space-between', gap: 18, paddingTop: 20 }}>
        <div style={{ minWidth: 0, flex: '1 1 320px' }}>
          <h2 style={{ fontSize: 17 }}>Continuous refinement</h2>
          <p className="muted" style={{ marginTop: 6 }}>
            Retrain all three models on the base dataset plus {num(confirmed)} community-confirmed URLs ({ti ? num(ti.awaiting_training) : '-'} not yet used). Takes about a minute;
            the best model by F1 is hot-reloaded without a restart.
          </p>
          {retraining && (
            <div style={{ marginTop: 14 }}>
              <ProgressBar indeterminate label="Retraining in the background" valueLabel="checking every 3 s" />
            </div>
          )}
        </div>
        <Button variant="primary" icon={RefreshCw} loading={retraining} disabled={!!error} onClick={() => setConfirm(true)}>
          {retraining ? 'Retraining…' : 'Retrain now'}
        </Button>
      </div>
    </Card>
  )

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'Models' }]}
        title="Model comparison"
        description={
          metrics
            ? `Random Forest, XGBoost and Logistic Regression trained on the same ${metrics.n_features} features (${num(metrics.train_rows)} training / ${num(metrics.test_rows)} test URLs${metrics.crowd_rows ? `, including ${num(metrics.crowd_rows)} community-confirmed URLs weighted ×${metrics.crowd_weight}` : ''}).`
            : 'Random Forest, XGBoost and Logistic Regression trained and compared on the same features.'
        }
        actions={
          metrics && (
            <Button variant="primary" icon={RefreshCw} loading={retraining} onClick={() => setConfirm(true)}>
              {retraining ? 'Retraining…' : 'Retrain now'}
            </Button>
          )
        }
      />

      {loading && !metrics && !error ? (
        <div className="grid grid-4" aria-busy="true">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} height={128} radius={12} />
          ))}
          <Skeleton height={320} radius={12} style={{ gridColumn: '1 / -1' }} />
        </div>
      ) : error && !metrics ? (
        <Card>
          <ErrorState title="Could not load model metrics" error={error} onRetry={refresh} />
        </Card>
      ) : !metrics ? (
        <div className="stack">
          <Card>
            <EmptyState icon={Terminal} title="No model has been trained yet">
              Run <code>python run.py train</code> once, or start a training run here. Metrics appear as soon as it finishes.
            </EmptyState>
          </Card>
          {retrainCard}
        </div>
      ) : (
        <div className="stack">
          <Stagger className="grid grid-4">
            <StatCard label="Selected model" icon={Crown} value={modelLabel(metrics.best_model)} delta={`best F1 · version ${metrics.model_version}`} deltaTone="up" />
            <StatCard label="F1-score" icon={Sparkles} value={best.f1 * 100} format={(v) => `${v.toFixed(2)}%`} delta={`precision ${pct(best.precision)} · recall ${pct(best.recall)}`} />
            <StatCard label="ROC-AUC" icon={BrainCircuit} tone="info" value={best.roc_auc} format={(v) => v.toFixed(3)} delta={`false-positive rate ${pct(best.false_positive_rate, 2)}`} />
            <StatCard label="Trained" icon={Clock} tone="warn" value={new Date(metrics.trained_at).toLocaleDateString(undefined, { dateStyle: 'medium' })} delta={`${new Date(metrics.trained_at).toLocaleTimeString(undefined, { timeStyle: 'short' })} · ${metrics.n_features} features`} />
          </Stagger>

          <div className="grid grid-2">
            <Reveal>
              <ChartCard
                title="Held-out test metrics"
                subtitle="Same split, same features · axis starts at 50%"
                legend={<Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />}
              >
                <GroupedBarChart data={chartData} xKey="metric" series={series} yDomain={[0.5, 1]} valueFormat={(v) => `${(v * 100).toFixed(0)}%`} />
              </ChartCard>
            </Reveal>
            <Reveal delay={0.05}>
              <ChartCard title="Metric profile" subtitle="Larger area = stronger all-round model" legend={<Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />}>
                <RadarCompare data={chartData} series={series} angleKey="metric" />
              </ChartCard>
            </Reveal>
          </div>

          <Card>
            <CardHeader title="Comparison table" subtitle={`Best model by F1 highlighted · trained ${when(metrics.trained_at)}`} />
            <div style={{ marginTop: 12 }}>
              <Table
                caption="Model comparison"
                rows={names.map((n) => ({ name: n, ...metrics.models[n] }))}
                rowKey={(r) => r.name}
                initialSort={{ key: 'f1', dir: 'desc' }}
                rowClassName={(r) => (r.name === metrics.best_model ? 'highlight' : '')}
                columns={[
                  {
                    key: 'name',
                    label: 'Model',
                    render: (r) => (
                      <span className="row" style={{ gap: 8, flexWrap: 'nowrap' }}>
                        <strong>{modelLabel(r.name)}</strong>
                        {r.name === metrics.best_model && <Badge tone="safe">selected</Badge>}
                      </span>
                    ),
                  },
                  { key: 'accuracy', label: 'Accuracy', num: true, render: (r) => pct(r.accuracy, 2) },
                  { key: 'precision', label: 'Precision', num: true, render: (r) => pct(r.precision, 2) },
                  { key: 'recall', label: 'Recall', num: true, render: (r) => pct(r.recall, 2) },
                  { key: 'f1', label: 'F1', num: true, render: (r) => pct(r.f1, 2) },
                  { key: 'roc_auc', label: 'ROC-AUC', num: true, render: (r) => r.roc_auc.toFixed(4) },
                  { key: 'false_positive_rate', label: 'FPR', num: true, render: (r) => pct(r.false_positive_rate, 2) },
                  { key: 'train_seconds', label: 'Train time', num: true, render: (r) => `${r.train_seconds}s` },
                ]}
              />
            </div>
          </Card>

          <Card>
            <CardHeader
              title="Per-model detail"
              subtitle="Confusion matrix on the test set and the ten most important features"
              actions={<Tabs label="Model" value={active} onChange={setTab} tabs={names.map((n) => ({ value: n, label: modelLabel(n) }))} />}
            />
            <div className="card-body">
              <div className="model-detail">
                <div>
                  <h3 className="mini-title">
                    <Layers size={15} aria-hidden="true" /> Confusion matrix
                  </h3>
                  <ConfusionMatrix cm={metrics.models[active].confusion_matrix} />
                </div>
                <div className="chart-glow">
                  <h3 className="mini-title">
                    <Database size={15} aria-hidden="true" /> Top-10 feature importances
                  </h3>
                  <div style={{ height: 340 }}>
                    <HBarChart
                      data={metrics.models[active].top_features.slice(0, 10)}
                      labelKey="feature"
                      valueKey="importance"
                      valueFormat={(v) => (v < 0.01 ? v.toFixed(4) : v.toFixed(3))}
                    />
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {retrainCard}
        </div>
      )}

      <Modal
        open={confirm}
        onClose={() => setConfirm(false)}
        title="Retrain all models?"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirm(false)}>
              Cancel
            </Button>
            <Button variant="primary" icon={RefreshCw} loading={starting} onClick={startRetrain} data-autofocus>
              Start retraining
            </Button>
          </>
        }
      >
        <p>
          Random Forest, XGBoost and Logistic Regression are retrained on the base dataset plus {num(confirmed)} community-confirmed URLs. The best model by F1
          replaces the current one{metrics ? ` (v${metrics.model_version})` : ''} and checks keep working while it runs.
        </p>
      </Modal>
    </Container>
  )
}
