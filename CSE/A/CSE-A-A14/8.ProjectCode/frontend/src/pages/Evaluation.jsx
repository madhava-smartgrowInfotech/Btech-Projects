import { useState } from 'react'
import { LineChart } from 'lucide-react'
import { PageHeader, Badge, Card, ErrorState, PageSkeleton, StatCard, Tabs } from '../components/ui'
import { CurvesChart } from '../components/charts/extra'
import { Callout, Gate, HeatGrid } from '../components/app'
import { Stagger } from '../components/motion'
import { PASTEL } from '../lib/palette'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { fmtInt, fmtNum } from '../lib/format'

export default function Evaluation() {
  return (
    <div className="stack">
      <PageHeader eyebrow="Models" icon={LineChart} title="Model evaluation" lead="ROC and precision-recall curves for every model trained in this session, plus a confusion matrix for the one you pick." />
      <Gate need="trial">
        <EvalBody />
      </Gate>
    </div>
  )
}

const palette = [PASTEL[0], PASTEL[2], PASTEL[3], PASTEL[4], PASTEL[1]]

function EvalBody() {
  const { data, error, reload } = useAsync(() => api.evaluation(), [])
  const [sel, setSel] = useState()
  if (error && !data) return <ErrorState title="Evaluation could not load" error={error} onRetry={reload} />
  if (!data) return <PageSkeleton kpis={5} blocks={2} />

  const names = data.models.map((m) => m.name)
  const current = data.models.find((m) => m.name === sel) || data.models[0]
  const m = current.metrics
  const cm = current.confusion
  const total = cm.flat().reduce((a, b) => a + b, 0)

  return (
    <>
      <div className="grid-2">
        <Card title="ROC curves" subtitle="True positive rate (up) against false positive rate (across). Toward the top-left is better; the dashed line is a coin flip.">
          <CurvesChart
            label="ROC curves for all trained models"
            xLabel="False positive rate"
            series={[
              ...data.models.map((mod, i) => ({ key: mod.name, name: `${mod.name} (AUC ${fmtNum(mod.metrics.roc_auc, 3)})`, color: palette[i % palette.length], data: mod.roc })),
              { key: 'random', name: 'Random', color: 'var(--text-3)', dashed: true, data: [{ x: 0, y: 0 }, { x: 1, y: 1 }] },
            ]}
          />
        </Card>
        <Card title="Precision-recall curves" subtitle="Precision (up) against recall (across). Useful when churners are the minority class.">
          <CurvesChart
            label="Precision-recall curves for all trained models"
            xLabel="Recall"
            series={data.models.map((mod, i) => ({ key: mod.name, name: mod.name, color: palette[i % palette.length], data: mod.pr }))}
          />
        </Card>
      </div>

      <Card
        title="Per-model confusion matrix"
        subtitle="Rows are what happened, columns are what the model predicted."
        actions={current.active ? <Badge tone="mint">active model</Badge> : null}
      >
        <div className="stack">
          <Tabs tabs={names.map((n) => ({ id: n, label: n }))} value={current.name} onChange={setSel} label="Choose a model" name="eval-model" />
          <div className="grid-2 wide-left">
            <HeatGrid
              label={`Confusion matrix for ${current.name}`}
              xLabels={['Retained (0)', 'Churned (1)']}
              yLabels={['Retained (0)', 'Churned (1)']}
              matrix={cm}
              format={(v) => fmtInt(v)}
              cell={96}
              xTitle="Predicted"
              yTitle="Actual"
            />
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
              <StatCard label="Accuracy" value={m.accuracy} format={(v) => fmtNum(v, 4)} tone="lavender" />
              <StatCard label="Precision" value={m.precision} format={(v) => fmtNum(v, 4)} tone="mint" />
              <StatCard label="Recall" value={m.recall} format={(v) => fmtNum(v, 4)} tone="peach" />
              <StatCard label="F1-score" value={m.f1_score} format={(v) => fmtNum(v, 4)} tone="sky" />
              <StatCard label="ROC-AUC" value={m.roc_auc} format={(v) => fmtNum(v, 4)} tone="rose" />
            </div>
          </div>
          <p className="section-note">
            Of {fmtInt(total)} held-out customers, the model caught {fmtInt(cm[1][1])} of {fmtInt(cm[1][0] + cm[1][1])} actual churners and raised {fmtInt(cm[0][1])} false alarms.
          </p>
        </div>
      </Card>

      <Callout tone="info" title="Why not just accuracy?">
        On an imbalanced churn dataset, precision, recall, F1-score and ROC-AUC together give a more reliable picture of how well a model identifies customers who will actually churn.
      </Callout>
    </>
  )
}
