import { Brain, ClipboardList, Info } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { fmtMetric, modelLabel } from '../lib/format'
import { Badge, Button, Card, PageHeader, Table } from '../components/ui'
import { SlideUp } from '../components/motion'
import { BarCompare } from '../components/charts'
import Async from '../components/Async'
import { ArtifactImage, Disclaimer } from '../components/Common'

export default function Explain() {
  const state = useAsync(api.explain)
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Explainability"
        icon={Brain}
        title="Explainability (SHAP)"
        lead="Global importance is precomputed during training from real SHAP values. Local explanations are computed live for each assessment. SHAP explains learned associations - never causation."
        actions={<Button to="/app/assess" icon={ClipboardList}>Get my local explanation</Button>}
      />
      <Async state={state} title="Could not load explainability data">
        {(shap) => {
          const features = shap.features || []
          const rows = features.map((f, i) => ({ ...f, rank: i + 1 }))
          const top = features.slice(0, 12).map((f, i) => ({ name: f.label, value: f.mean_abs_shap, highlight: i < 3 }))
          return (
            <>
              {shap.note && (
                <Card tint="peach" hover={false}><p className="row" style={{ '--gap': '10px' }}><Info size={18} aria-hidden="true" />{shap.note}</p></Card>
              )}
              <div className="grid-2">
                <Card hover={false} title="Global importance" subtitle={`Mean |SHAP| for the ${modelLabel(shap.model)} model - top ${top.length} features.`} actions={<Badge tone="lavender">{modelLabel(shap.model)}</Badge>}>
                  {top.length ? (
                    <BarCompare data={top} horizontal height={420} yWidth={190} valueFormat={(v) => Number(v).toFixed(2)} name="Mean |SHAP|" label="Global SHAP importance by feature" />
                  ) : (
                    <p className="muted">No global SHAP data was found. Run <code>python scripts/train.py</code>.</p>
                  )}
                </Card>
                <Card hover={false} title="SHAP summary (beeswarm)" subtitle="Per-row effects across the training sample; colour shows the feature value.">
                  <ArtifactImage name="shap_beeswarm.png" alt="SHAP beeswarm summary plot" />
                </Card>
              </div>
              <Card hover={false} title="Original SHAP bar chart" subtitle="Rendered at training time.">
                <div style={{ maxWidth: 760 }}><ArtifactImage name="shap_bar.png" alt="SHAP global bar chart" /></div>
              </Card>
              <Card hover={false} title="Ranked features">
                <Table
                  caption="Features ranked by mean absolute SHAP value"
                  rows={rows}
                  rowKey={(r) => r.feature}
                  pageSize={10}
                  searchKeys={['label']}
                  searchPlaceholder="Search features"
                  initialSort={{ key: 'rank', dir: 'asc' }}
                  columns={[
                    { key: 'rank', label: '#', numeric: true },
                    { key: 'label', label: 'Feature', wrap: true },
                    { key: 'mean_abs_shap', label: 'Mean |SHAP|', numeric: true, render: (r) => fmtMetric(r.mean_abs_shap, 4) },
                    { key: 'reading', label: 'Reading', sortable: false, wrap: true, render: () => <span className="muted">Higher value → larger average effect on the model's output.</span> },
                  ]}
                  cardTitle={(r) => `${r.rank}. ${r.label}`}
                />
              </Card>
              <Card hover={false} title="How to read this">
                <ul className="stack" style={{ '--gap': '8px', paddingLeft: 20, margin: 0 }}>
                  <li><strong>Global bar:</strong> average impact magnitude across sampled training rows.</li>
                  <li><strong>Beeswarm:</strong> distribution of per-row effects; colour shows the feature value.</li>
                  <li><strong>Local (on results):</strong> per-person positive vs negative contributors with live SHAP values.</li>
                  <li>These are predictive associations. Do not treat them as proof that changing a factor causes an outcome.</li>
                </ul>
              </Card>
              <SlideUp><Disclaimer /></SlideUp>
            </>
          )
        }}
      </Async>
    </div>
  )
}
