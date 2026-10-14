import { BarChart3, Gauge, MapPinned, Scale, ShieldAlert, Waves } from 'lucide-react'
import useApi from '../useApi'
import { Card, ErrorState, PageHeader, PageSkeleton, StatCard, Table } from '../components/ui'
import { BarCompare } from '../components/charts'
import { fmtNum, fmtPct } from '../lib/format'
import { useChartTheme } from '../lib/palette'

// Two columns (measure, result) for the metric tables.
const metricColumns = [
  { key: 'metric', label: 'Measure', sortable: false },
  { key: 'value', label: 'Result', numeric: true, sortable: false },
]

const metricRows = (items) => items.map(([metric, value]) => ({ metric, value }))

function MetricTable({ caption, items }) {
  return <Table caption={caption} rows={metricRows(items)} rowKey={(r) => r.metric} columns={metricColumns} pageSize={0} />
}

export default function Evaluation() {
  const t = useChartTheme()
  const { data, loading, error, reload } = useApi('/metrics')

  const header = (
    <PageHeader
      eyebrow="Model evaluation"
      icon={BarChart3}
      title="Model evaluation"
      lead="How well each model does on held-out data. Every figure comes from the evaluation files written by the training and evaluation scripts."
    />
  )

  if (loading && !data) {
    return (
      <>
        {header}
        <PageSkeleton kpis={4} blocks={2} />
      </>
    )
  }
  if (error && !data) {
    return (
      <>
        {header}
        <ErrorState title="Evaluation results did not load" error={error} onRetry={reload} />
      </>
    )
  }

  const ev = data?.eval
  if (!ev) {
    return (
      <>
        {header}
        <ErrorState
          title="No evaluation results yet"
          error="experiments/eval/metrics.json was not found."
          hint="Run ml/eval.py once to create it, then reload this page."
          onRetry={reload}
        />
      </>
    )
  }

  const q = ev.quality
  const d = ev.demand
  const lk = ev.leaks
  const an = ev.anomaly
  const im = ev.imbalance
  const zoneMape = data.demand?.xgboost?.mape_7day_by_zone || {}

  const members = [
    ['Stacking ensemble (used in the app)', q.stacking_ensemble],
    ['Random Forest', q.members.random_forest],
    ['XGBoost', q.members.xgboost],
    ['Gradient Boosting', q.members.gradient_boosting],
    ['Decision Tree', q.members.decision_tree],
  ]

  return (
    <>
      {header}
      <div className="stack" style={{ '--gap': '24px' }}>
        <div className="grid-kpi">
          <StatCard label="Water-quality accuracy" display={fmtPct(q.stacking_ensemble.accuracy, 1)} icon={Waves} tone="lavender" foot={`${q.test_rows} held-out samples`} />
          <StatCard
            label="Demand error (7-day MAPE)"
            display={`${fmtNum(d.xgboost_mape, 2)}%`}
            icon={Gauge}
            tone="mint"
            foot={`seasonal naive: ${fmtNum(d.seasonal_naive_mape, 2)}%`}
          />
          <StatCard label="Leak detection F1" display={fmtNum(lk.detection.f1, 2)} icon={ShieldAlert} tone="peach" foot={`recall ${fmtNum(lk.detection.recall, 2)}`} />
          <StatCard label="Leak top-3 pipe accuracy" display={fmtPct(lk.localisation.top3_accuracy, 0)} icon={MapPinned} tone="sky" foot="correct pipe among the top three" />
        </div>

        <Card title="Water quality: model comparison" subtitle="Held-out test set. Higher accuracy, F1 and ROC-AUC are better.">
          <Table
            caption="Water-quality models compared"
            rows={members.map(([name, m]) => ({ name, accuracy: fmtPct(m.accuracy, 1), f1: fmtNum(m.f1, 3), auc: fmtNum(m.roc_auc, 3) }))}
            rowKey={(r) => r.name}
            pageSize={0}
            highlight={(r) => r.name.startsWith('Stacking')}
            columns={[
              { key: 'name', label: 'Model', sortable: false },
              { key: 'accuracy', label: 'Accuracy', numeric: true, sortable: false },
              { key: 'f1', label: 'F1', numeric: true, sortable: false },
              { key: 'auc', label: 'ROC-AUC', numeric: true, sortable: false },
            ]}
          />
        </Card>

        <div className="grid-2">
          <Card title="Demand: model against a simple baseline" subtitle="Mean absolute percentage error over 7-day forecasts. Lower is better.">
            <BarCompare
              label="7-day forecast error: XGBoost against seasonal naive"
              data={[
                { name: 'XGBoost', value: d.xgboost_mape, color: t.lavender },
                { name: 'Seasonal naive', value: d.seasonal_naive_mape, color: t.axis },
              ]}
              valueFormat={(v) => `${fmtNum(v, 1)}%`}
              horizontal
              yWidth={130}
              name="MAPE (%)"
              height={180}
            />
          </Card>
          <Card title="Demand: error by zone" subtitle="XGBoost, 7-day recursive forecast over the last 90 days">
            <BarCompare
              label="7-day forecast error per zone"
              data={Object.entries(zoneMape).map(([z, v]) => ({ name: z, value: v, color: t.sky }))}
              valueFormat={(v) => `${fmtNum(v, 1)}%`}
              name="MAPE (%)"
              height={180}
            />
          </Card>
        </div>

        <div className="grid-2">
          <Card title="Leak detection and localisation" subtitle={`${lk.scenarios} simulated scenarios, leaks of ${lk.leak_size_lps[0]} to ${lk.leak_size_lps[1]} L/s, ${lk.candidate_pipes} candidate pipes`}>
            <MetricTable
              caption="Leak detection and localisation results"
              items={[
                ['Detection precision', fmtNum(lk.detection.precision, 2)],
                ['Detection recall', fmtNum(lk.detection.recall, 2)],
                ['Detection F1', fmtNum(lk.detection.f1, 2)],
                ['Detection ROC-AUC', fmtNum(lk.detection.roc_auc, 4)],
                ['Localisation, top-1 pipe', fmtPct(lk.localisation.top1_accuracy, 1)],
                ['Localisation, top-3 pipes', fmtPct(lk.localisation.top3_accuracy, 1)],
                ['Correct zone', fmtPct(lk.localisation.zone_accuracy, 0)],
              ]}
            />
          </Card>

          <div className="stack" style={{ '--gap': '24px' }}>
            <Card title="Abnormal consumption" subtitle={`${fmtNum(an.meter_days, 0)} meter-days scored`}>
              <MetricTable
                caption="Abnormal consumption results"
                items={[
                  ['Day level, precision', fmtNum(an.day_level.precision, 2)],
                  ['Day level, recall', fmtNum(an.day_level.recall, 2)],
                  ['Meter level (last 7 days), precision', fmtNum(an.meter_level_last_7_days.precision, 2)],
                  ['Meter level (last 7 days), recall', fmtNum(an.meter_level_last_7_days.recall, 2)],
                ]}
              />
            </Card>

            <Card title="Distribution imbalance" subtitle={`Recommended plan: ${im.action}. Worst zone: ${im.worst_zone}.`}>
              <MetricTable
                caption="Distribution imbalance before and after the recommended plan"
                items={[
                  ['Equity score, before → after', `${fmtNum(im.equity_before, 1)} → ${fmtNum(im.equity_after, 1)}`],
                  ['Non-revenue water, before → after', `${fmtNum(im.nrw_before_pct, 2)}% → ${fmtNum(im.nrw_after_pct, 2)}%`],
                ]}
              />
            </Card>
          </div>
        </div>

        <Card hover={false}>
          <p className="small muted">
            Headline figures: experiments/eval/metrics.json. Per-zone demand error: experiments/demand_metrics.json. Each model also saves its own file in
            experiments/. These numbers come from simulated and sample data, as described in docs/02_HOW_IT_WORKS.md.
          </p>
        </Card>
      </div>
    </>
  )
}
