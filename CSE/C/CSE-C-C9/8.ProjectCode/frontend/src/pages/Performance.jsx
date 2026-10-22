import { BarChart3, Database, Layers, Trophy } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { fmtMetric, modelLabel } from '../lib/format'
import { Badge, Card, PageHeader, StatCard, Table } from '../components/ui'
import { Stagger } from '../components/motion'
import { ChartLegend, GroupedBars } from '../components/charts'
import Async from '../components/Async'
import { ArtifactImage, Disclaimer } from '../components/Common'

export default function Performance() {
  const state = useAsync(api.performance)
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Performance"
        icon={BarChart3}
        title="Model performance"
        lead="Every number here comes from the actual training run on held-out data. The best model is selected by ROC-AUC."
      />
      <Async state={state} title="Could not load performance data">
        {({ comparison, validation, stats, summary }) => {
          const models = Object.entries(comparison.models || {}).map(([key, m]) => ({ key, ...m }))
          const best = comparison.best_model
          const folds = Object.entries(validation.cv_roc_auc || {}).map(([key, v]) => ({ key, folds: v }))
          const corr = Object.entries(stats.correlations_with_target || {}).map(([key, c]) => ({
            key, corr: c, coef: stats.logit_coefficients?.[key], p: stats.logit_pvalues?.[key],
          }))
          const chart = models.map((m) => ({ x: modelLabel(m.key), accuracy: m.accuracy, f1: m.f1, roc_auc: m.roc_auc }))
          return (
            <>
              <Stagger className="grid-kpi">
                <Stagger.Item><StatCard label="Best model" display={modelLabel(best)} icon={Trophy} tone="lavender" foot={`Selected by ${comparison.primary_metric?.replace('_', '-').toUpperCase() || 'ROC-AUC'}`} /></Stagger.Item>
                <Stagger.Item><StatCard label="Dataset rows" value={summary.rows} icon={Database} tone="mint" foot={summary.dataset} /></Stagger.Item>
                <Stagger.Item><StatCard label="Train / test split" display={validation.train_size ? `${validation.train_size.toLocaleString('en-US')} / ${validation.test_size.toLocaleString('en-US')}` : '–'} icon={Layers} tone="sky" foot="Stratified 80/20" /></Stagger.Item>
                <Stagger.Item><StatCard label="Models compared" value={models.length} icon={BarChart3} tone="peach" foot="Linear + tree ensembles" /></Stagger.Item>
              </Stagger>

              <Card hover={false} title="Model comparison" subtitle="Test set metrics and 5-fold cross-validated ROC-AUC.">
                <Table
                  caption="Model comparison"
                  rows={models}
                  rowKey={(r) => r.key}
                  pageSize={0}
                  highlight={(r) => r.key === best}
                  initialSort={{ key: 'roc_auc', dir: 'desc' }}
                  columns={[
                    { key: 'key', label: 'Model', render: (r) => <span className="row" style={{ '--gap': '8px' }}>{modelLabel(r.key)}{r.key === best && <Badge tone="lavender">Best</Badge>}</span> },
                    { key: 'accuracy', label: 'Accuracy', numeric: true, render: (r) => fmtMetric(r.accuracy, 4) },
                    { key: 'precision', label: 'Precision', numeric: true, render: (r) => fmtMetric(r.precision, 4) },
                    { key: 'recall', label: 'Recall', numeric: true, render: (r) => fmtMetric(r.recall, 4) },
                    { key: 'f1', label: 'F1', numeric: true, render: (r) => fmtMetric(r.f1, 4) },
                    { key: 'roc_auc', label: 'ROC-AUC', numeric: true, render: (r) => fmtMetric(r.roc_auc, 4) },
                    { key: 'cv_roc_auc_mean', label: 'CV AUC (mean ± std)', numeric: true, render: (r) => `${fmtMetric(r.cv_roc_auc_mean, 4)} ± ${fmtMetric(r.cv_roc_auc_std, 4)}` },
                  ]}
                  cardTitle={(r) => modelLabel(r.key)}
                />
              </Card>

              <Card hover={false} title="Metrics at a glance">
                <ChartLegend items={[{ label: 'Accuracy', color: 'var(--lavender)' }, { label: 'F1', color: 'var(--mint)' }, { label: 'ROC-AUC', color: 'var(--sky)' }]} />
                <GroupedBars
                  data={chart}
                  height={300}
                  series={[{ key: 'accuracy', name: 'Accuracy', color: '#C7B9FF' }, { key: 'f1', name: 'F1', color: '#A7E8C8' }, { key: 'roc_auc', name: 'ROC-AUC', color: '#A9D6FF' }]}
                  valueFormat={(v) => Number(v).toFixed(2)}
                  label="Accuracy, F1 and ROC-AUC for each model"
                />
              </Card>

              <div className="grid-2">
                <Card hover={false} title={`Confusion matrix (${modelLabel(best)})`}>
                  <ArtifactImage name="confusion_matrix.png" alt="Confusion matrix of the best model" />
                </Card>
                <Card hover={false} title="ROC curves">
                  <ArtifactImage name="roc_curve.png" alt="ROC curves for all models" />
                </Card>
              </div>

              <div className="grid-2">
                <Card hover={false} title="Validation strategy">
                  <div className="stack" style={{ '--gap': '12px' }}>
                    <p><strong>Protocol:</strong> {validation.protocol}</p>
                    <p><strong>Why:</strong> {validation.why}</p>
                    {validation.class_balance_test && (
                      <p className="small muted">Test class balance: {Object.entries(validation.class_balance_test).map(([k, v]) => `${k}: ${v.toLocaleString('en-US')}`).join(' · ')}</p>
                    )}
                  </div>
                </Card>
                <Card hover={false} title="Cross-validation fold AUCs">
                  <Table
                    caption="ROC-AUC per cross-validation fold"
                    rows={folds}
                    rowKey={(r) => r.key}
                    pageSize={0}
                    columns={[
                      { key: 'key', label: 'Model', render: (r) => modelLabel(r.key) },
                      { key: 'folds', label: 'Fold AUCs', sortable: false, wrap: true, render: (r) => r.folds.join(', ') },
                    ]}
                  />
                </Card>
              </div>

              <Card hover={false} title="Statistical analysis" subtitle="Complementary, associational evidence.">
                {corr.length ? (
                  <Table
                    caption="Correlation, logistic coefficient and p-value per variable"
                    rows={corr}
                    rowKey={(r) => r.key}
                    pageSize={0}
                    columns={[
                      { key: 'key', label: 'Variable' },
                      { key: 'corr', label: 'Correlation', numeric: true, render: (r) => fmtMetric(r.corr, 4) },
                      { key: 'coef', label: 'Logit coef', numeric: true, render: (r) => (r.coef == null ? '–' : fmtMetric(r.coef, 5)) },
                      { key: 'p', label: 'p-value', numeric: true, render: (r) => (r.p == null ? '–' : r.p < 0.0001 ? '< 0.0001' : fmtMetric(r.p, 4)) },
                    ]}
                  />
                ) : (
                  <p className="muted">{stats.note || 'Statistics are unavailable.'}</p>
                )}
                {stats.note && <p className="small muted" style={{ marginTop: 12 }}>{stats.note}</p>}
              </Card>
              <Disclaimer />
            </>
          )
        }}
      </Async>
    </div>
  )
}
