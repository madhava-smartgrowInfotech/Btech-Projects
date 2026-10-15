import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart3, Percent, Scale, TrendingUp, Trophy } from 'lucide-react'
import { api, plotUrl } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { fixed, num } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, PageHeader, Skeleton, StatCard, Table, Tabs } from '../components/ui'
import { ChartCard, GroupedBarChart, Legend, useChartColors } from '../components/charts'
import { LoadError } from '../components/bio'
import { Stagger } from '../components/motion'

export const MRI_METHODS = [
  { key: 'jepa', label: 'ViT + JEPA pre-training (BioSight)', short: 'JEPA' },
  { key: 'unet', label: 'U-Net, supervised', short: 'U-Net' },
  { key: 'mae', label: 'ViT + MAE reconstruction pre-training', short: 'MAE' },
  { key: 'scratch', label: 'ViT from scratch', short: 'Scratch' },
]

export function TrainHint({ command }) {
  return (
    <>
      Run <code>{command}</code> to train the models and write the metrics file, then reload this page.
    </>
  )
}

function Plot({ name, alt }) {
  const [state, setState] = useState('loading')
  return (
    <div>
      {state === 'loading' && <Skeleton height={220} radius={8} />}
      <img
        src={plotUrl(name)}
        alt={alt}
        className="plot-img"
        style={state === 'ok' ? undefined : { display: 'none' }}
        onLoad={() => setState('ok')}
        onError={() => setState('missing')}
      />
      {state === 'missing' && <p className="faint">The pre-training loss plot has not been generated yet.</p>}
    </div>
  )
}

export default function LabelEfficiency() {
  const q = useAsync(() => api.get('/metrics/label-efficiency'), [])
  const [metric, setMetric] = useState('dice')
  const colors = useChartColors()

  const notTrained = q.error?.status === 404

  let body
  if (q.loading) {
    body = (
      <>
        <div className="grid grid-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} height={128} radius={12} />
          ))}
        </div>
        <Skeleton height={340} radius={12} style={{ marginTop: 18 }} />
      </>
    )
  } else if (notTrained) {
    body = (
      <Card>
        <EmptyState icon={BarChart3} title="No MRI results yet" actions={<Button as={Link} to="/app/performance">See what is available</Button>}>
          The label-efficiency comparison is read from the MRI training results, which are not on this server yet. <TrainHint command="ml/train_mri.py --stage all" />
        </EmptyState>
      </Card>
    )
  } else if (q.error) {
    body = <LoadError title="Could not load the results" error={q.error} onRetry={q.reload} />
  } else {
    const { data, finetune: ft = {}, pretrain = {} } = q.data
    const methods = MRI_METHODS.filter((m) => ft[`${m.key}_10`] || ft[`${m.key}_100`])
    const seriesColors = [colors.accent, colors.info, colors.violet, colors.warn]
    const series = methods.map((m) => ({ key: m.key, label: m.label, color: seriesColors[MRI_METHODS.indexOf(m) % 4] }))
    const chartData = [10, 100].map((p) => ({
      budget: `${p}% of masks`,
      ...Object.fromEntries(methods.map((m) => [m.key, ft[`${m.key}_${p}`]?.[metric] ?? null])),
    }))
    const j10 = ft.jepa_10?.dice
    const u100 = ft.unet_100?.dice
    const u10 = ft.unet_10?.dice
    const rows = [10, 100].flatMap((p) => methods.filter((m) => ft[`${m.key}_${p}`]).map((m) => ({ ...ft[`${m.key}_${p}`], id: `${m.key}_${p}`, method: m, pct: p })))
    const pretrainRows = Object.entries(pretrain)

    body = (
      <>
        <Stagger className="grid grid-4">
          <StatCard label="JEPA @ 10% masks" value={fixed(j10)} icon={Trophy} delta="test Dice" />
          <StatCard label="U-Net @ 100% masks" value={fixed(u100)} icon={Scale} tone="info" delta="fully supervised" />
          <StatCard label="JEPA 10% vs U-Net 100%" value={j10 && u100 ? `${Math.round((100 * j10) / u100)}%` : '-'} icon={Percent} delta="of the supervised Dice" />
          <StatCard
            label="Gain over U-Net @ 10%"
            value={j10 !== undefined && u10 !== undefined ? `${j10 - u10 >= 0 ? '+' : ''}${(j10 - u10).toFixed(3)}` : '-'}
            icon={TrendingUp}
            delta="Dice points"
            deltaTone={j10 - u10 >= 0 ? 'up' : 'down'}
          />
        </Stagger>

        <ChartCard
          title={`Test ${metric === 'dice' ? 'Dice' : 'IoU'} by label budget`}
          subtitle="Higher is better. Each group trains on the share of masks shown; pre-training never saw a mask."
          height={320}
          actions={
            <Tabs
              label="Metric"
              value={metric}
              onChange={setMetric}
              tabs={[
                { value: 'dice', label: 'Dice' },
                { value: 'iou', label: 'IoU' },
              ]}
            />
          }
          legend={<Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />}
        >
          <GroupedBarChart data={chartData} xKey="budget" series={series} valueFormat={(v) => (typeof v === 'number' ? v.toFixed(2) : v)} />
        </ChartCard>

        <Card>
          <CardHeader
            title="All runs"
            subtitle={`${num(data?.test_slices)} held-out test slices from unseen patients; ${num(data?.train_slices)} training slices. Dice / IoU pooled over all test pixels (threshold 0.5).`}
          />
          <Table
            caption="All fine-tuning runs"
            rows={rows}
            rowKey={(r) => r.id}
            pageSize={8}
            initialSort={{ key: 'dice', dir: 'desc' }}
            rowClassName={(r) => (r.method.key === 'jepa' ? 'highlight' : '')}
            columns={[
              { key: 'method', label: 'Method', sortValue: (r) => r.method.label, render: (r) => r.method.label },
              { key: 'pct', label: 'Masks', num: true, render: (r) => `${r.pct}%` },
              { key: 'labelled_slices', label: 'Labelled slices', num: true, hideSm: true, render: (r) => num(r.labelled_slices) },
              { key: 'dice', label: 'Dice', num: true, render: (r) => fixed(r.dice) },
              { key: 'iou', label: 'IoU', num: true, render: (r) => fixed(r.iou) },
              { key: 'mean_dice_tumour_slices', label: 'Mean Dice (tumour slices)', num: true, hideSm: true, render: (r) => fixed(r.mean_dice_tumour_slices) },
              { key: 'seconds', label: 'Train time', num: true, hideSm: true, render: (r) => (r.seconds ? `${Math.round(r.seconds / 60)} min` : '-') },
            ]}
          />
        </Card>

        <div className="grid grid-2">
          <Card>
            <CardHeader title="Self-supervised pre-training loss" subtitle="JEPA and MAE use the training slices only, without any masks." />
            <div className="card-body">
              <Plot name="mri_pretrain_loss.png" alt="Pre-training loss curves for JEPA and MAE" />
            </div>
          </Card>
          <Card>
            <CardHeader title="Pre-training runs" />
            <div className="card-body">
              {pretrainRows.length === 0 ? (
                <p className="faint">No pre-training summary was recorded.</p>
              ) : (
                <div className="stack" style={{ gap: 12 }}>
                  {pretrainRows.map(([k, v]) => (
                    <div key={k} className="row" style={{ justifyContent: 'space-between' }}>
                      <strong>{k.toUpperCase()}</strong>
                      <span className="muted">
                        {v.epochs} epochs · final loss {fixed(v.history?.at(-1)?.loss, 4)} · {Math.round((v.seconds || 0) / 60)} min
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      </>
    )
  }

  return (
    <div className="container">
      <PageHeader
        title="Label efficiency"
        description="Brain-MRI tumour segmentation: how well a JEPA-pre-trained ViT does with only 10% of the masks, against a supervised U-Net, an MAE-pre-trained ViT and a ViT trained from scratch."
        actions={q.data ? <Badge tone="safe" dot>Live from experiments/</Badge> : undefined}
      />
      <div className="stack">{body}</div>
    </div>
  )
}
