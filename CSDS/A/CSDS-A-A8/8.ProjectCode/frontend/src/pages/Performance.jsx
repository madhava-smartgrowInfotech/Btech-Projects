import { Link } from 'react-router-dom'
import { ArrowRight, Brain, Dna, Fingerprint, Gauge, History as HistoryIcon, Target } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { KIND, fixed, num, pct, when } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, PageHeader, Skeleton, StatCard, Table } from '../components/ui'
import { ChartCard, GroupedBarChart, Legend, useChartColors } from '../components/charts'
import { LoadError } from '../components/bio'
import { Stagger } from '../components/motion'
import { MRI_METHODS, TrainHint } from './LabelEfficiency'

const DNA_METHODS = [
  { key: 'jepa', label: 'k-mer JEPA pre-training (BioSight)' },
  { key: 'mlm', label: 'Masked-token reconstruction pre-training' },
  { key: 'scratch', label: 'From scratch' },
]

function Missing({ icon, title, command }) {
  return (
    <Card>
      <CardHeader title={title} />
      <EmptyState icon={icon} title="Not available yet">
        This result file is not on the server. <TrainHint command={command} />
      </EmptyState>
    </Card>
  )
}

function MriSection({ mri }) {
  if (!mri) return <Missing icon={Brain} title="Brain-MRI segmentation" command="ml/train_mri.py --stage all" />
  const ft = mri.finetune || {}
  const rows = [10, 100].flatMap((p) => MRI_METHODS.filter((m) => ft[`${m.key}_${p}`]).map((m) => ({ ...ft[`${m.key}_${p}`], id: `${m.key}_${p}`, method: m, pct: p })))
  return (
    <Card>
      <CardHeader title="Brain-MRI segmentation" subtitle="Test slices from unseen patients, against supervised and reconstruction baselines." actions={<Button as={Link} to="/app/label-efficiency" size="sm" variant="ghost" iconRight={ArrowRight}>Chart</Button>} />
      <Table
        caption="MRI segmentation runs"
        rows={rows}
        rowKey={(r) => r.id}
        pageSize={8}
        initialSort={{ key: 'dice', dir: 'desc' }}
        rowClassName={(r) => (r.method.key === 'jepa' ? 'highlight' : '')}
        columns={[
          { key: 'method', label: 'Method', sortValue: (r) => r.method.label, render: (r) => r.method.label },
          { key: 'pct', label: 'Masks', num: true, render: (r) => `${r.pct}%` },
          { key: 'dice', label: 'Dice', num: true, render: (r) => fixed(r.dice) },
          { key: 'iou', label: 'IoU', num: true, render: (r) => fixed(r.iou) },
          { key: 'mean_dice_tumour_slices', label: 'Mean Dice (tumour slices)', num: true, hideSm: true, render: (r) => fixed(r.mean_dice_tumour_slices) },
        ]}
      />
      {mri.pretrain && (
        <div className="card-body grid grid-3" style={{ borderTop: '1px solid var(--border)' }}>
          {Object.entries(mri.pretrain).map(([k, v]) => (
            <div key={k}>
              <div className="faint">{k.toUpperCase()} pre-training</div>
              <strong>{v.epochs} epochs</strong>
              <div className="faint">
                final loss {fixed(v.history?.at(-1)?.loss, 4)} · {Math.round((v.seconds || 0) / 60)} min
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

function DnaSection({ dna }) {
  const colors = useChartColors()
  if (!dna) return <Missing icon={Dna} title="DNA encoder" command="ml/train_dna.py" />
  const rep = dna.repeat || {}
  const cm = rep.jepa_100?.confusion
  const labels = rep.jepa_100?.labels || []
  const palette = [colors.accent, colors.info, colors.violet]
  const series = DNA_METHODS.map((m, i) => ({ key: m.key, label: m.label, color: palette[i] }))
  const chartData = [10, 100].map((p) => ({ budget: `${p}% of labels`, ...Object.fromEntries(DNA_METHODS.map((m) => [m.key, rep[`${m.key}_${p}`]?.accuracy ?? null])) }))
  const rows = [10, 100]
    .flatMap((p) => DNA_METHODS.filter((m) => rep[`${m.key}_${p}`]).map((m) => ({ ...rep[`${m.key}_${p}`], id: `${m.key}_${p}`, name: m.label, budget: `${p}%` })))
    .concat(rep.jepa_probe_100 ? [{ ...rep.jepa_probe_100, id: 'probe', name: 'JEPA encoder frozen (linear probe)', budget: '100%' }] : [])
  const org = DNA_METHODS.filter((m) => dna.organism?.[`${m.key}_100`]).map((m) => ({ ...dna.organism[`${m.key}_100`], id: m.key, name: m.label }))
  return (
    <>
      <ChartCard
        title="DNA encoder - STR repeat-type accuracy"
        subtitle={`5 classes (none, di-, tri-, tetra-, penta-nucleotide repeats); ${num(dna.pretrain_sequences)} unlabelled sequences for pre-training.`}
        height={300}
        legend={<Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />}
      >
        <GroupedBarChart data={chartData} xKey="budget" series={series} valueFormat={(v) => (typeof v === 'number' ? v.toFixed(2) : v)} />
      </ChartCard>
      <Card>
        <CardHeader title="Repeat-type runs" />
        <Table
          caption="DNA repeat-type classification runs"
          rows={rows}
          rowKey={(r) => r.id}
          pageSize={8}
          columns={[
            { key: 'name', label: 'Method' },
            { key: 'budget', label: 'Labels', num: true },
            { key: 'accuracy', label: 'Accuracy', num: true, render: (r) => fixed(r.accuracy) },
            { key: 'macro_f1', label: 'Macro F1', num: true, render: (r) => fixed(r.macro_f1) },
            { key: 'labelled_sequences', label: 'Labelled sequences', num: true, hideSm: true, render: (r) => num(r.labelled_sequences) },
          ]}
        />
        {cm && (
          <div className="card-body cm-wrap" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="field-label" style={{ marginBottom: 8 }}>
              Confusion matrix - JEPA, 100% labels (rows = true class)
            </div>
            <table className="cm">
              <thead>
                <tr>
                  <th />
                  {labels.map((l) => (
                    <th key={l} scope="col">
                      {l}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cm.map((row, i) => (
                  <tr key={labels[i] ?? i}>
                    <th scope="row" className="row-h">
                      {labels[i]}
                    </th>
                    {row.map((v, j) => (
                      <td key={j} className={i === j ? 'diag' : undefined}>
                        {v}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      {org.length > 0 && (
        <Card>
          <CardHeader title="DNA encoder - organism class" subtitle="Every method scores close to chance on held-out data: the class labels in this dataset are not predictable from the sequence." />
          <Table
            caption="Organism class runs"
            rows={org}
            rowKey={(r) => r.id}
            columns={[
              { key: 'name', label: 'Method' },
              { key: 'accuracy', label: 'Accuracy', num: true, render: (r) => fixed(r.accuracy) },
              { key: 'macro_f1', label: 'Macro F1', num: true, render: (r) => fixed(r.macro_f1) },
              { key: 'chance_accuracy', label: 'Chance', num: true, render: (r) => fixed(r.chance_accuracy) },
            ]}
          />
        </Card>
      )}
    </>
  )
}

function StrSection({ ev }) {
  const s = ev?.str
  if (!s) return <Missing icon={Fingerprint} title="STR matching" command="ml/eval.py" />
  return (
    <Card>
      <CardHeader title="STR matching - simulated casework queries" subtitle="Queries with drop-out and typing errors against the reference database." />
      <div className="card-body">
        <Stagger className="grid grid-4">
          <StatCard label="Rank-1 identification" value={pct(s.rank1_accuracy)} icon={Target} delta={`${num(s.true_source_queries)} queries`} />
          <StatCard label="Median log10 LR (true source)" value={fixed(s.median_log10_lr_true_source, 2)} icon={Gauge} tone="info" />
          <StatCard label="Non-contributors with LR > 1" value={pct(s.non_contributor_lr_gt1_rate, 2)} icon={Fingerprint} tone="warn" delta={`${num(s.non_contributor_queries)} queries × database`} />
          <StatCard label="Max log10 LR, non-contributor" value={fixed(s.max_log10_lr_non_contributor, 2)} icon={Gauge} tone="danger" />
        </Stagger>
      </div>
    </Card>
  )
}

export default function Performance() {
  const metrics = useAsync(() => api.get('/metrics/all'), [])
  const hist = useAsync(() => api.get('/history'), [])
  const m = metrics.data

  return (
    <div className="container">
      <PageHeader title="Model performance" description="Held-out evaluation of every BioSight model against supervised and reconstruction-based baselines." />
      <div className="stack">
        {metrics.loading ? (
          <>
            <Skeleton height={300} radius={12} />
            <Skeleton height={300} radius={12} />
          </>
        ) : metrics.error ? (
          <LoadError title="Could not load the metrics" error={metrics.error} onRetry={metrics.reload} />
        ) : (
          <>
            <MriSection mri={m.mri} />
            <DnaSection dna={m.dna} />
            <StrSection ev={m.eval} />
          </>
        )}

        <Card>
          <CardHeader
            title="Your recent analyses"
            actions={
              <Button as={Link} to="/app/history" size="sm" variant="ghost" iconRight={ArrowRight}>
                All history
              </Button>
            }
          />
          {hist.error ? (
            <LoadError title="Could not load your history" error={hist.error} onRetry={hist.reload} />
          ) : (
            <Table
              caption="Recent analyses"
              rows={hist.data?.slice(0, 5)}
              loading={hist.loading}
              rowKey={(r) => r.id}
              pageSize={5}
              cards={false}
              empty={
                <EmptyState icon={HistoryIcon} title="No analyses yet" actions={<Button as={Link} to="/app/mri">Analyse an MRI slice</Button>}>
                  Every MRI, DNA and STR analysis you run is saved here.
                </EmptyState>
              }
              columns={[
                { key: 'created_at', label: 'When', render: (r) => when(r.created_at) },
                { key: 'kind', label: 'Type', render: (r) => <Badge tone={KIND[r.kind]?.tone}>{KIND[r.kind]?.label || r.kind}</Badge> },
                { key: 'title', label: 'Title' },
              ]}
            />
          )}
        </Card>
      </div>
    </div>
  )
}
