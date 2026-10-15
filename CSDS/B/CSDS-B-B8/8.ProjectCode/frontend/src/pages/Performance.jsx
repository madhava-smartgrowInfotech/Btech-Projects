import { Activity, Gauge, RefreshCw, ShieldCheck, Target, Timer } from 'lucide-react'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, PageHeader, Skeleton, StatCard, Table } from '../components/ui'
import { ChartCard, GroupedBarChart, Legend } from '../components/charts'
import { useChartColors } from '../components/charts/colors'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { activityColor, humanize, pct, seconds } from '../lib/format'

const COND = {
  normal: 'Normal light',
  dim_no_enhancement: 'Dim, no enhancement',
  dim_enhanced: 'Dim + CareWatch enhancement',
  occluded_legs: 'Legs occluded',
}
const SHORT = { normal: 'Normal', dim_no_enhancement: 'Dim', dim_enhanced: 'Dim + enhanced', occluded_legs: 'Legs hidden' }

function Confusion({ classes, matrix }) {
  const rowMax = matrix.map((r) => Math.max(1, r.reduce((a, b) => a + b, 0)))
  return (
    <div className="cm-wrap">
      <table className="cm">
        <caption className="sr-only">Confusion matrix: rows are the true activity, columns the predicted activity</caption>
        <thead>
          <tr>
            <th scope="col">true ↓ / predicted →</th>
            {classes.map((c) => (
              <th key={c} scope="col">{humanize(c)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={classes[i]}>
              <th scope="row">{humanize(classes[i])}</th>
              {row.map((v, j) => {
                const share = v / rowMax[i]
                return (
                  <td key={j} className={share > 0.55 ? 'hot' : ''} style={{ '--v': share.toFixed(2) }}>
                    {v}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Performance() {
  const metrics = useAsync(() => api.get('/metrics'), [])
  const c = useChartColors()
  const m = metrics.data
  const tr = m?.training
  const ev = m?.evaluation
  const act = ev?.activity
  const fall = ev?.fall
  const lat = ev?.latency

  const condKeys = act ? Object.keys(act.conditions) : []
  const condColors = [c.accent, c.warn, c.info, c.violet]
  const series = condKeys.map((k, i) => ({ key: k, label: COND[k] || humanize(k), color: condColors[i % 4] }))
  const barData = act?.classes.map((cl) => ({
    activity: humanize(cl),
    ...Object.fromEntries(condKeys.map((k) => [k, act.conditions[k].per_class[cl]?.accuracy])),
  }))

  const actCols = act
    ? [
        {
          key: 'activity',
          label: 'Activity',
          sortValue: (cl) => cl,
          render: (cl) => (
            <span className="cap">
              <span className="legend"><i style={{ background: activityColor(cl) }} /></span>
              {humanize(cl)}
            </span>
          ),
        },
        ...condKeys.flatMap((k) => [
          { key: `${k}-a`, label: `${SHORT[k] || k} acc.`, num: true, sortValue: (cl) => act.conditions[k].per_class[cl]?.accuracy, render: (cl) => pct(act.conditions[k].per_class[cl]?.accuracy) },
          { key: `${k}-f`, label: `${SHORT[k] || k} F1`, num: true, hideSm: true, sortValue: (cl) => act.conditions[k].per_class[cl]?.f1, render: (cl) => pct(act.conditions[k].per_class[cl]?.f1) },
        ]),
      ]
    : []

  const scenarios = fall ? Object.entries(fall.by_scenario) : []
  const scenCols = [
    { key: 'name', label: 'Scenario', sortValue: ([k]) => k, render: ([k, v]) => <span className="cap">{humanize(k)} {v.is_fall && <Badge tone="danger">fall</Badge>}</span> },
    { key: 'n', label: 'Sequences', num: true, sortValue: ([, v]) => v.n, render: ([, v]) => v.n },
    { key: 'alerts', label: 'Alerts raised', num: true, sortValue: ([, v]) => v.alerts, render: ([, v]) => v.alerts },
  ]

  return (
    <div>
      <PageHeader
        title="Model performance"
        description="Activity recognition accuracy, fall detection and alert latency, measured on held-out data."
        actions={
          <Button icon={RefreshCw} onClick={() => metrics.reload()} loading={metrics.loading && !!m}>
            Refresh
          </Button>
        }
      />

      {metrics.error && !m ? (
        <ErrorState title="Couldn't load the metrics" error={metrics.error} onRetry={metrics.reload} />
      ) : !m ? (
        <div className="stack" aria-busy="true" aria-label="Loading metrics">
          <div className="grid grid-4">
            {[0, 1, 2, 3].map((i) => <Skeleton key={i} height={116} />)}
          </div>
          <Skeleton height={320} />
        </div>
      ) : (
        <div className="stack">
          {!tr && !ev && (
            <Card>
              <EmptyState icon={Gauge} title="No model results yet">
                Train and evaluate the models first: <code>python ml/train.py</code> then <code>python ml/eval.py</code>.
              </EmptyState>
            </Card>
          )}

          {act && (
            <>
              <Stagger className="grid grid-4" gap={0.06}>
                {condKeys.map((k, i) => (
                  <StatCard
                    key={k}
                    label={COND[k] || humanize(k)}
                    icon={[Activity, Target, ShieldCheck, Gauge][i % 4]}
                    value={pct(act.conditions[k].accuracy)}
                    delta={`macro F1 ${pct(act.conditions[k].macro_f1)} · ${act.conditions[k].windows} windows`}
                  />
                ))}
              </Stagger>
              <ChartCard
                title="Accuracy per activity"
                subtitle="Recall for each activity under four conditions"
                height={320}
                legend={<Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />}
              >
                <GroupedBarChart data={barData} xKey="activity" series={series} valueFormat={(v) => `${Math.round(v * 100)}%`} yDomain={[0, 1]} />
              </ChartCard>
              <Card>
                <CardHeader title="Per-activity accuracy and F1" subtitle={act.note} />
                <Table columns={actCols} rows={act.classes} rowKey={(cl) => cl} pageSize={10} cards={false} caption="Per-activity accuracy and F1" />
              </Card>
            </>
          )}

          {fall && (
            <div className="grid grid-2">
              <Card>
                <CardHeader title="Fall detection" subtitle="Simulated 10 fps sequences built from real poses" />
                <div className="card-body stack">
                  <div className="grid grid-2">
                    <StatCard label="Sensitivity" icon={Target} value={pct(fall.sensitivity)} delta={`${fall.tp} of ${fall.positives} falls caught`} />
                    <StatCard label="Specificity" icon={ShieldCheck} value={pct(fall.specificity)} delta={`${fall.tn} of ${fall.negatives} non-falls ignored`} />
                  </div>
                  <Table columns={scenCols} rows={scenarios} rowKey={([k]) => k} pageSize={10} cards={false} caption="Fall detection by scenario" />
                </div>
              </Card>
              <Card>
                <CardHeader title="Alert latency" subtitle="From impact to the alert leaving the building" />
                <div className="card-body stack">
                  <div className="grid grid-2">
                    <StatCard
                      label="Impact to confirmed fall"
                      icon={Timer}
                      value={seconds(fall.detection_latency_s?.mean)}
                      delta={`median ${seconds(fall.detection_latency_s?.median)} · 95th pct ${seconds(fall.detection_latency_s?.p95)}`}
                    />
                    <StatCard label="Pose model per frame" icon={Gauge} value={lat ? `${lat.pose_ms_per_frame} ms` : '-'} delta={lat ? `${lat.pipeline_fps} fps on CPU` : undefined} />
                    <StatCard label="Alert delivery" icon={Activity} value={lat?.dispatch_ms != null ? `${lat.dispatch_ms} ms` : '-'} delta={lat?.dispatch_note} />
                    <StatCard label="Impact to alert sent" icon={Timer} value={seconds(lat?.end_to_end_s)} delta={lat ? `includes the ${lat.countdown_s}s "I'm OK" countdown` : undefined} />
                  </div>
                  {m.live?.fall_alerts > 0 ? (
                    <p className="muted">
                      Live so far: {m.live.fall_alerts} fall alerts, {m.live.sent} sent, {m.live.cancelled_im_ok} cancelled with "I'm OK"
                      {m.live.mean_detection_latency_ms != null && `, mean confirmation ${(m.live.mean_detection_latency_ms / 1000).toFixed(2)} s`}.
                    </p>
                  ) : (
                    <p className="faint">No live fall alerts yet. Live statistics appear here after the first confirmed fall.</p>
                  )}
                </div>
              </Card>
            </div>
          )}

          {tr && (
            <Card>
              <CardHeader
                title="Training"
                subtitle={`${tr.model} · ${tr.train_windows} training windows (${tr.own_clip_train_windows} from recorded clips), trained in ${tr.train_seconds}s on CPU.`}
              />
              <div className="card-body">
                <Confusion classes={tr.classes} matrix={tr.confusion_matrix} />
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
