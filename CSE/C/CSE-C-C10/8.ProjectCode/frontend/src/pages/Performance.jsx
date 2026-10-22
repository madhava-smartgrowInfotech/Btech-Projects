import { useApi } from '../api'
import { Bars, ConfusionMatrix, PrecisionRecall } from '../components/charts/Charts'
import { PageHeader } from '../components/ui/AppShell'
import Table from '../components/ui/Table'
import { Badge, Card } from '../components/ui/display'
import { ErrorState, PageSkeleton } from '../components/ui/feedback'
import { featureLabel, fixed, meanStd } from '../format'
import { useTheme } from '../lib/theme'

export default function Performance() {
  const metrics = useApi('/model-metrics')
  const fi = useApi('/feature-importance?top=15')
  const { tokens } = useTheme()

  const error = metrics.error || fi.error
  if (error) return <><PageHeader title="Model performance" eyebrow="validation" /><ErrorState error={error} title="Could not load the model metrics" onRetry={() => { metrics.reload(); fi.reload() }} /></>
  if (metrics.loading || fi.loading || !metrics.data || !fi.data) return <PageSkeleton />

  const m = metrics.data
  const best = m.best_model
  const rows = Object.entries(m.models).map(([name, v]) => ({ name, ...v }))
  const sel = (r) => (r.name === best ? tokens.ok : tokens.info)
  const bal = rows.map((r) => ({ name: r.name, value: r.balanced_accuracy.mean }))
  const f1 = rows.map((r) => ({ name: r.name, value: r.f1.mean }))
  const pr = rows.map((r) => ({ name: r.name, precision: r.precision.mean, recall: r.recall.mean }))
  const kRows = Object.entries(m.retrieval_k).map(([k, v]) => ({ name: k, ...v }))
  const repRows = [['structured_only', 'Structured only'], ['text_only', 'Text only'], ['combined', 'Combined']]
    .map(([k, label]) => ({ name: label, key: k, ...m.representations[k] }))
  const importance = fi.data.features.map((f) => ({ name: featureLabel(f.feature), value: f.value, coef: f.coefficient }))

  const metricCol = (key, label) => ({
    key, label, align: 'right', sortable: true, sortValue: (r) => r[key].mean,
    render: (r) => <span className={`font-mono tabular-nums ${r.name === best ? 'text-ok' : 'text-fg'}`}>{meanStd(r[key])}</span>,
  })
  const columns = [
    { key: 'name', label: 'Model', sortable: true, defaultDir: 'asc', render: (r) => (
      <span className="inline-flex items-center gap-2 text-fg">{r.name}{r.name === best && <Badge tone="ok" dot>best</Badge>}</span>) },
    metricCol('balanced_accuracy', 'Balanced acc.'), metricCol('accuracy', 'Accuracy'), metricCol('precision', 'Precision'),
    metricCol('recall', 'Recall'), metricCol('f1', 'F1'),
  ]
  const small = (extra) => [
    { key: 'name', label: extra, render: (r) => <span className="text-fg">{r.name}</span> },
    { key: 'mean', label: 'Balanced acc.', align: 'right', render: (r) => <span className="font-mono tabular-nums">{meanStd(r)}</span> },
  ]
  const bestRow = rows.find((r) => r.name === best)

  return (
    <>
      <PageHeader title="Model performance" eyebrow="validation"
        subtitle={<>5 repeated stratified 80/20 splits · balanced accuracy is the primary metric · best model: <b className="text-fg">{best}</b></>} />

      <Card title="Model comparison" eyebrow="mean ± std over 5 splits">
        <Table columns={columns} rows={rows} rowKey={(r) => r.name} caption="Metrics of the four classifiers" initialSort={{ key: 'balanced_accuracy', dir: 'desc' }}
          cards={(r) => (
            <div className={`rounded border px-3 py-2.5 text-sm ${r.name === best ? 'border-ok/50 bg-ok/5' : 'border-line bg-panel-2'}`}>
              <div className="mb-1 flex items-center justify-between"><b className="text-fg">{r.name}</b>{r.name === best && <Badge tone="ok" dot>best</Badge>}</div>
              <div className="grid grid-cols-2 gap-x-3 font-mono text-[11px] text-muted">
                <span>bal. acc. {meanStd(r.balanced_accuracy)}</span><span>acc. {meanStd(r.accuracy)}</span>
                <span>prec. {meanStd(r.precision)}</span><span>recall {meanStd(r.recall)}</span><span>F1 {meanStd(r.f1)}</span>
              </div>
            </div>
          )} />
      </Card>

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Balanced accuracy" eyebrow="chart">
          <Bars data={bal} xKey="name" height={240} valueFormat={(v) => fixed(v, 2)} domain={[0, 1]} legend={false} label="Balanced accuracy per model"
            series={[{ key: 'value', label: 'Balanced accuracy', color: tokens.info }]} colorBy={sel} />
        </Card>
        <Card title="F1-score" eyebrow="chart">
          <Bars data={f1} xKey="name" height={240} valueFormat={(v) => fixed(v, 2)} domain={[0, 1]} legend={false} label="F1-score per model"
            series={[{ key: 'value', label: 'F1', color: tokens.info }]} colorBy={sel} />
        </Card>
        <Card title="Precision vs recall" eyebrow="chart">
          <PrecisionRecall points={pr} best={best} label="Precision against recall for every model" />
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-dim">green = selected model · hover a point for its name</p>
        </Card>
        <Card title={`Confusion matrix · ${best}`} eyebrow="mean over 5 splits (test fold)">
          <ConfusionMatrix matrix={bestRow.confusion_matrix_mean} decimals={1} />
          <p className="mt-3 text-xs text-muted">Average counts per test fold: the diagonal is correct predictions, the off-diagonal cells are errors.</p>
        </Card>
        <Card title="Retrieval size comparison" eyebrow="similar-case weighted vote">
          <Bars data={kRows} xKey="name" height={200} valueFormat={(v) => fixed(v, 2)} domain={[0.5, 0.8]} legend={false} label="Balanced accuracy by retrieval size k"
            series={[{ key: 'mean', label: 'Balanced accuracy', color: tokens.cyan }]} colorBy={(r) => (r.name === 'k=50' ? tokens.ok : tokens.cyan)} />
          <div className="mt-3"><Table columns={small('k')} rows={kRows} rowKey={(r) => r.name} caption="Balanced accuracy by k" dense /></div>
        </Card>
        <Card title="Structured vs text vs combined" eyebrow="representation study">
          <Bars data={repRows} xKey="name" height={200} valueFormat={(v) => fixed(v, 2)} domain={[0.5, 0.8]} legend={false} label="Balanced accuracy by representation"
            series={[{ key: 'mean', label: 'Balanced accuracy', color: tokens.cyan }]} colorBy={(r) => (r.key === 'combined' ? tokens.ok : tokens.cyan)} />
          <div className="mt-3"><Table columns={small('Representation')} rows={repRows} rowKey={(r) => r.key} caption="Balanced accuracy by representation" dense /></div>
        </Card>
      </div>

      <Card title={`Feature importance · ${fi.data.model}`} eyebrow={fi.data.kind === 'abs_coefficient' ? 'top 15 |logistic coefficients|' : 'top 15 importances'} className="mt-5">
        <Bars data={importance} xKey="name" layout="horizontal" height={Math.max(300, importance.length * 26)} xWidth={150}
          valueFormat={(v) => fixed(v, 1)} legend={false} label="Top structured features"
          series={[{ key: 'value', label: fi.data.kind === 'abs_coefficient' ? '|coefficient|' : 'importance', color: tokens.info }]}
          colorBy={(r) => (r.coef === undefined ? tokens.info : r.coef >= 0 ? tokens.ok : tokens.alert)} />
        {fi.data.kind === 'abs_coefficient' && <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-dim">green = pushes toward SUCCESS · red = pushes toward FAILURE</p>}
      </Card>
    </>
  )
}
