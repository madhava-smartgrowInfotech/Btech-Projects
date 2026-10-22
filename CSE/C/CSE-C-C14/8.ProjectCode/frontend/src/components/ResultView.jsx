import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, Cpu, Flame, GitMerge, ImageOff, RotateCcw, ShieldAlert, ShieldCheck } from 'lucide-react'
import { fmtNum, fmtPct } from '../lib/format'
import { isReal, labelText, labelTone } from '../lib/labels'
import { Badge, Button, Card, EmptyState, KeyValueList, PageHeader, Table, Tabs } from './ui'
import { CountUp, SlideUp, Stagger } from './motion'

const CAM_TABS = [
  { id: 'a1', label: 'EfficientNet' },
  { id: 'b', label: 'ResNet50' },
  { id: 'c', label: 'MobileNetV3' },
]

function ProbBar({ real, fake }) {
  return (
    <div>
      <div
        role="img"
        aria-label={`Real ${fmtPct(real)}, AI-generated ${fmtPct(fake)}`}
        style={{ display: 'flex', height: 16, borderRadius: 999, overflow: 'hidden', background: 'var(--surface-3)' }}
      >
        <div style={{ width: `${real * 100}%`, background: 'var(--mint)', transition: 'width .8s ease' }} />
        <div style={{ width: `${fake * 100}%`, background: 'var(--rose)', transition: 'width .8s ease' }} />
      </div>
      <div className="row between small" style={{ marginTop: 8 }}>
        <span>
          <i className="chart-tip-sw" style={{ background: 'var(--mint)' }} />
          Real <b className="num">{fmtPct(real)}</b>
        </span>
        <span>
          <i className="chart-tip-sw" style={{ background: 'var(--rose)' }} />
          AI-generated <b className="num">{fmtPct(fake)}</b>
        </span>
      </div>
    </div>
  )
}

export default function ResultView({ result, onAgain }) {
  const [cam, setCam] = useState('a1')
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])
  const real = isReal(result.predicted_label)
  const Icon = real ? ShieldCheck : ShieldAlert
  const consistent = result.robustness?.consistency || 'n/a'
  const [agree, total] = consistent.split('/').map(Number)
  const fullyConsistent = total > 0 && agree === total
  const camLabel = CAM_TABS.find((t) => t.id === cam).label

  const branchCols = [
    { key: 'name', label: 'Model', render: (b) => <strong>{b.name}</strong> },
    { key: 'label', label: 'Prediction', render: (b) => <Badge tone={labelTone(b.label)} dot>{labelText(b.label)}</Badge> },
    {
      key: 'conf',
      label: 'Confidence',
      numeric: true,
      sortValue: (b) => Math.max(b.prob_real, b.prob_fake),
      render: (b) => fmtPct(Math.max(b.prob_real, b.prob_fake)),
    },
    {
      key: 'weight',
      label: 'Final weight',
      numeric: true,
      sortValue: (b) => result.active_weights?.[b.key] ?? 0,
      render: (b) => (result.active_weights?.[b.key] != null ? fmtPct(result.active_weights[b.key], 1) : <Badge tone="peach">Excluded</Badge>),
    },
  ]
  // the API sorts JSON keys alphabetically; show the variants in the order they are applied
  const ORDER = ['original', 'jpeg', 'resize', 'blur']
  const robustRows = Object.entries(result.robustness?.outcomes || {})
    .map(([name, label]) => ({ name, label }))
    .sort((a, b) => ORDER.indexOf(a.name) - ORDER.indexOf(b.name))
  const variantName = (r) => (r.name === 'original' ? 'Original image' : `${r.name.charAt(0).toUpperCase()}${r.name.slice(1)} test`)
  const robustCols = [
    { key: 'name', label: 'Variant', render: (r) => variantName(r) },
    {
      key: 'label',
      label: 'Prediction',
      render: (r) =>
        String(r.label).startsWith('error') ? <Badge tone="peach">Unavailable</Badge> : <Badge tone={labelTone(r.label)} dot>{labelText(r.label)}</Badge>,
    },
  ]
  const camUrl = result.cams?.[cam]

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Analysis complete"
        icon={CheckCircle2}
        title="Here is what the ensemble found"
        lead="Four independent detectors voted, the votes were fused in logit space, and the result was re-tested under compression, resizing and blur."
        actions={<Button icon={RotateCcw} onClick={onAgain}>Analyze another image</Button>}
      />

      <SlideUp>
        <Card
          hover={false}
          tint={real ? 'mint' : undefined}
          style={real ? undefined : { background: 'var(--rose-soft)', borderColor: 'transparent' }}
          aria-label="Verdict"
        >
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))', gap: 24, alignItems: 'center' }}>
            <div style={{ borderRadius: 20, overflow: 'hidden', background: 'var(--surface)', border: '1px solid var(--border)', display: 'grid', placeItems: 'center' }}>
              <img src={result.original_image} alt={`Uploaded image ${result.filename}`} style={{ width: '100%', maxHeight: 360, objectFit: 'contain', display: 'block' }} />
            </div>
            <div className="stack" style={{ '--gap': '14px' }}>
              <div className="row">
                <Badge tone={labelTone(result.predicted_label)} icon={Icon}>Verdict</Badge>
                <span className="small muted" style={{ overflowWrap: 'anywhere' }}>{result.filename}</span>
              </div>
              <h2 style={{ fontSize: 'clamp(28px, 4vw, 40px)', fontWeight: 800 }}>{real ? 'Likely a real image' : 'Likely AI-generated'}</h2>
              <p style={{ fontSize: 18 }}>
                <strong className="num"><CountUp value={result.confidence_pct} format={(v) => `${fmtNum(v, 2)}%`} /></strong>{' '}
                <span className="muted">· {result.confidence_word}</span>
              </p>
              <ProbBar real={result.prob_real} fake={result.prob_fake} />
              <p className="small muted" style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <GitMerge size={15} aria-hidden="true" /> {result.agreement_count}/4 branches agree
                <span aria-hidden="true">·</span>
                <Cpu size={15} aria-hidden="true" /> analyzed on {result.device}
              </p>
            </div>
          </div>
        </Card>
      </SlideUp>

      {(result.excluded_branch || result.gate2_applied) && (
        <Stagger className="stack" style={{ '--gap': '10px' }}>
          {result.excluded_branch && (
            <Stagger.Item>
              <div className="card tint-peach" role="note" style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <AlertTriangle size={20} aria-hidden="true" style={{ color: 'var(--peach-ink)', flex: 'none', marginTop: 2 }} />
                <div><strong>Route adjustment.</strong> {result.gate1_reason}</div>
              </div>
            </Stagger.Item>
          )}
          {result.gate2_applied && (
            <Stagger.Item>
              <div className="card tint-sky" role="note" style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <GitMerge size={20} aria-hidden="true" style={{ color: 'var(--sky-ink)', flex: 'none', marginTop: 2 }} />
                <div><strong>Consensus adjustment.</strong> {result.gate2_reason}</div>
              </div>
            </Stagger.Item>
          )}
        </Stagger>
      )}

      <div className="grid-2 wide-left">
        <Card title="Branch votes" subtitle="Each model's own prediction and the weight it carried in the final fusion.">
          <Table columns={branchCols} rows={result.branches} rowKey={(b) => b.key} pageSize={0} caption="Branch votes" cardTitle={(b) => b.name} />
        </Card>
        <Card
          title="Robustness check"
          subtitle="The image is re-tested after JPEG compression, a 2x resample and a Gaussian blur."
          actions={
            <Badge tone={fullyConsistent ? 'mint' : 'peach'} icon={fullyConsistent ? CheckCircle2 : AlertTriangle}>
              Consistency {consistent}
            </Badge>
          }
        >
          {robustRows.length ? (
            <Table columns={robustCols} rows={robustRows} rowKey={(r) => r.name} pageSize={0} caption="Robustness variants" cardTitle={variantName} />
          ) : (
            <EmptyState compact icon={ImageOff} title="Robustness check unavailable" message="The variants could not be evaluated for this image." />
          )}
          <p className="small muted" style={{ marginTop: 14 }}>
            {fullyConsistent
              ? 'Every variant agrees with the original prediction.'
              : 'A consistency below full agreement suggests the image is borderline or sensitive to compression - treat the result with extra caution.'}
          </p>
        </Card>
      </div>

      <Card
        title="Visual explanation (Grad-CAM)"
        subtitle="Computed from each model's real gradients for the predicted class."
        hover={false}
      >
        <div style={{ marginBottom: 16, maxWidth: '100%' }}>
          <Tabs tabs={CAM_TABS} value={cam} onChange={setCam} label="Grad-CAM model" name="cam" />
        </div>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))', gap: 18 }}>
          <figure style={{ margin: 0 }}>
            <img src={result.original_image} alt="Original upload" style={{ width: '100%', borderRadius: 18, border: '1px solid var(--border)' }} />
            <figcaption className="small muted" style={{ marginTop: 8 }}>Original</figcaption>
          </figure>
          <figure style={{ margin: 0 }}>
            {camUrl ? (
              <img src={camUrl} alt={`Grad-CAM heatmap from ${camLabel}`} style={{ width: '100%', borderRadius: 18, border: '1px solid var(--border)' }} />
            ) : (
              <EmptyState compact icon={Flame} title="Heatmap unavailable" message="Grad-CAM could not be generated for this branch." tone="peach" />
            )}
            <figcaption className="small muted" style={{ marginTop: 8 }}>{camLabel} heatmap</figcaption>
          </figure>
        </div>
        <p className="small muted" style={{ marginTop: 14 }}>{result.heatmap_note}</p>
      </Card>

      <Card title="Fusion details" hover={false}>
        <KeyValueList
          items={[
            ['Predicted class', labelText(result.predicted_label)],
            ['Gate 1 (route B outlier)', result.gate1_reason],
            ['Gate 2 (B + C consensus)', result.gate2_reason],
            ['Final weights', Object.entries(result.active_weights || {}).map(([k, v]) => `${k.toUpperCase()} ${fmtPct(v, 1)}`).join(' · ')],
          ]}
        />
      </Card>
    </div>
  )
}
