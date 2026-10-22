import { AlertTriangle, Cpu, Layers, Lock } from 'lucide-react'
import { api } from '../lib/api'
import { useDocTitle, useLoad } from '../lib/hooks'
import { fmtPct } from '../lib/format'
import { Badge, Card, ErrorState, KeyValueList, PageHeader, PageSkeleton, Timeline } from '../components/ui'
import { BarCompare } from '../components/charts'
import { Stagger } from '../components/motion'
import { useChartTheme } from '../lib/palette'

const TONES = ['lavender', 'sky', 'peach', 'mint']

const LIMITATIONS = [
  'AI-based assessment only - the product estimates statistical likelihood, it does not prove image origin or detect every generator.',
  'Accuracy drops on heavily compressed, tiny or out-of-distribution images; use the robustness consistency score as a caution signal.',
  'When the CIFAKE download is unavailable, training falls back to clearly-labelled synthetic demo data whose metrics do not transfer to real photography.',
  'CPU inference runs four models plus Grad-CAM and three robustness variants, so one image can take from a few seconds to about a minute.',
]

export default function Models() {
  useDocTitle('How it works · VeriVision AI')
  const { data, error, loading, reload } = useLoad((s) => api.config(s), [])
  const t = useChartTheme()
  const header = (
    <PageHeader
      eyebrow="Under the hood"
      icon={Layers}
      title="How the ensemble decides"
      lead="Four heterogeneous CNN routes, fused in logit space with transparent weights and two disagreement gates."
    />
  )
  if (loading) return <div className="stack">{header}<PageSkeleton kpis={4} blocks={1} /></div>
  if (error) return <div className="stack">{header}<ErrorState title="Could not load the model configuration" error={error} onRetry={reload} /></div>

  const total = Object.values(data.ensemble_weights).reduce((a, b) => a + b, 0) || 1
  const weight = (k) => data.ensemble_weights[k] / total
  const meta = Object.fromEntries((data.model_metadata?.models || []).map((m) => [m.branch, m]))
  const bars = data.branches.map((b, i) => ({ name: b.name, value: weight(b.key), color: t[['lavender', 'sky', 'peach', 'mint'][i]] }))
  const g = data.gates

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      {header}

      <Stagger className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 440px), 1fr))', gap: 18 }}>
        {data.branches.map((b, i) => {
          const m = meta[b.key]
          return (
            <Stagger.Item key={b.key}>
              <Card tint={TONES[i]} title={b.name} subtitle={b.role}>
                <KeyValueList
                  items={[
                    ['Backbone', b.backbone],
                    ['Input size', `${b.resolution}×${b.resolution}`],
                    ['Loss', b.loss],
                    ['Fusion weight', fmtPct(weight(b.key), 1)],
                    ['Trained on', m?.training_dataset || 'not recorded'],
                    ['Validation F1', m ? fmtPct(m.validation?.f1) : '–'],
                  ]}
                />
              </Card>
            </Stagger.Item>
          )
        })}
      </Stagger>

      <div className="grid-2">
        <Card title="Fusion weights" subtitle="Normalized from app/config.py; override with VERIVISION_W_* variables." hover={false}>
          <BarCompare data={bars} horizontal valueFormat={(v) => fmtPct(v, 0)} height={220} yWidth={130} name="Weight" label="Ensemble fusion weights" />
        </Card>
        <Card title="From pixels to verdict" hover={false}>
          <Timeline
            animate={false}
            items={[
              { title: 'Each route produces logits', meta: 'Route B also averages a horizontally flipped copy (test-time augmentation).', tone: 'lavender' },
              { title: 'Gate 1 - suppress a route-B outlier', meta: `If B is very confident (logit margin ≥ ${g.tau_b}) while every other route points the other way, B is excluded.`, tone: 'peach' },
              { title: 'Weighted logit fusion', meta: 'fused logit = Σ weight × logit, over the routes that are still active.', tone: 'mint' },
              { title: 'Gate 2 - B + C consensus', meta: `If B and C agree with each other, both are confident (margins ≥ ${g.tau_b} / ${g.tau_c}) and the fused result disagrees, the logits are nudged by ${g.correction} toward them.`, tone: 'sky' },
              { title: 'Softmax and confidence wording', meta: `High ≥ ${fmtPct(data.confidence_thresholds.high, 0)}, moderate ≥ ${fmtPct(data.confidence_thresholds.moderate, 0)}, otherwise low.`, tone: 'rose' },
            ]}
          />
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Privacy and security" hover={false}>
          <ul className="stack" style={{ '--gap': '10px', paddingLeft: 20, margin: 0 }}>
            <li>Inference runs locally; images are never sent to an external API.</li>
            <li>Uploads are validated ({data.allowed_extensions.join(', ').toUpperCase()}, up to {data.max_mb} MB, must decode as RGB) and never executed.</li>
            <li>Filenames are never used as filesystem paths; debug mode is off.</li>
          </ul>
          <p className="small muted" style={{ marginTop: 14, display: 'flex', gap: 8, alignItems: 'center' }}>
            <Lock size={14} aria-hidden="true" /> <Cpu size={14} aria-hidden="true" /> CPU or GPU is detected automatically.
          </p>
        </Card>
        <Card title="Limitations" tint="peach" hover={false} actions={<Badge tone="peach" icon={AlertTriangle}>Read before trusting a verdict</Badge>}>
          <ul className="stack" style={{ '--gap': '10px', paddingLeft: 20, margin: 0 }}>
            {LIMITATIONS.map((l) => <li key={l}>{l}</li>)}
          </ul>
        </Card>
      </div>
    </div>
  )
}
