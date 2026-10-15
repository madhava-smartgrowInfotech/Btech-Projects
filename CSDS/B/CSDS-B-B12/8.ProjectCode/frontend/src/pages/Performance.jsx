import { useEffect, useState } from 'react'
import api from '../api.js'
import { PageHeader } from '../components/ui/Layout.jsx'
import { Card, EmptyState, ErrorState, SkeletonBlock, StatCard, Table } from '../components/ui/index.js'
import { BarBlocks, PALETTE } from '../components/ui/Charts.jsx'
import AuthImage from '../components/AuthImage.jsx'
import { failure } from '../lib/product.js'

const pctText = (v) => (v == null ? '—' : `${(v * 100).toFixed(1)}%`)

const CLASS_COLUMNS = [
  { key: 'class', label: 'Class' },
  { key: 'sensitivity', label: 'Sensitivity', numeric: true, render: (r) => pctText(r.sensitivity) },
  { key: 'precision', label: 'Precision', numeric: true, render: (r) => pctText(r.precision) },
  { key: 'f1', label: 'F1', numeric: true, render: (r) => pctText(r.f1) },
  { key: 'support', label: 'Test images', numeric: true },
]

function ClassifierCard({ title, m, figure }) {
  const rows = Object.entries(m.per_class).map(([c, v]) => ({ id: c, class: c, ...v }))
  const chart = rows.map((r) => ({ class: r.class, sensitivity: Number(((r.sensitivity || 0) * 100).toFixed(1)) }))
  return (
    <Card title={title}>
      <div className="stack" style={{ '--gap': '18px' }}>
        <p className="tiny muted">{m.test_images} held-out test images</p>
        <div className="stat-grid">
          <StatCard label="Accuracy" value={pctText(m.accuracy)} />
          <StatCard label="Macro-F1" value={pctText(m.macro_f1)} />
        </div>
        <Table columns={CLASS_COLUMNS} rows={rows} rowKey={(r) => r.id} initialSort={{ key: 'class', dir: 'asc' }} caption={`${title}: per-class results`} />
        <div>
          <h3 className="card-subtitle">Sensitivity per class (%)</h3>
          <BarBlocks data={chart} xKey="class" yKey="sensitivity" name="Sensitivity (%)" height={240} color={PALETTE.lime} />
        </div>
        <figure className="figure">
          <AuthImage className="fig-img" style={{ aspectRatio: 'auto' }} src={`/metrics/figure/${figure}`} alt={`${title} confusion matrix`} />
          <figcaption className="tiny muted">Confusion matrix on the held-out test images.</figcaption>
        </figure>
      </div>
    </Card>
  )
}

export default function Performance() {
  const [m, setM] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    setM(null)
    api
      .get('/metrics')
      .then((r) => setM(r.data))
      .catch(async (e) => setError(await failure(e)))
  }
  useEffect(load, [])

  let body
  if (error?.status === 404) {
    body = (
      <EmptyState title="No evaluation yet" action={null}>
        The evaluation has not been run on this copy of the project. Run <code>python ml/eval.py</code> from the project folder, then reload this page.
      </EmptyState>
    )
  } else if (error) {
    body = <ErrorState title="The evaluation could not be loaded" error={error.message} onRetry={load} />
  } else if (!m) {
    body = <SkeletonBlock rows={6} label="Loading evaluation" />
  } else {
    body = (
      <>
        <div className="stat-grid">
          <StatCard label="Dice (lung mask)" value={Number(m.segmentation.dice.toFixed(3))} decimals={3} hint={`${m.segmentation.test_images} test images`} />
          <StatCard label="IoU (lung mask)" value={Number(m.segmentation.iou.toFixed(3))} decimals={3} hint="overlap with expert masks" />
          <StatCard label="X-ray / CT routing" value={pctText(m.modality.routing_accuracy)} hint={`${m.modality.test_images} images`} />
          <StatCard label="Non-chest rejected" value={pctText(m.modality.other_reject_rate)} hint={`chest accepted ${pctText(m.modality.chest_accept_rate)}`} />
        </div>
        <div className="split">
          <ClassifierCard title="X-ray classifier (EfficientNet-B0)" m={m.xray} figure="confusion_xray.png" />
          <ClassifierCard title="CT classifier (EfficientNet-B0)" m={m.ct} figure="confusion_ct.png" />
        </div>
        {m.notes?.length > 0 && (
          <Card title="Notes">
            <ul className="stack" style={{ '--gap': '8px', paddingLeft: 18, margin: 0 }}>
              {m.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </Card>
        )}
      </>
    )
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Evaluation"
        title="Model performance"
        description={
          m
            ? `Measured on held-out test data by ml/eval.py, generated ${new Date(m.generated_at).toLocaleString()}.`
            : 'Measured on held-out test data by ml/eval.py.'
        }
      />
      {body}
    </div>
  )
}
