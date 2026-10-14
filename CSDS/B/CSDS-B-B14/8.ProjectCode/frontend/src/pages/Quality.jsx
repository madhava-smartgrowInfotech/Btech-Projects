import { useState } from 'react'
import { CheckCircle2, FlaskConical, XCircle } from 'lucide-react'
import api, { errorText } from '../api'
import useApi from '../useApi'
import { Badge, Button, Card, EmptyState, ErrorState, Input, PageHeader, Skeleton, Table, useToast } from '../components/ui'
import { fmtNum, timeAgo } from '../lib/format'

const FIELDS = [
  ['ph', 'pH', ''],
  ['Hardness', 'Hardness', 'mg/L'],
  ['Solids', 'Total dissolved solids', 'mg/L'],
  ['Chloramines', 'Chloramines', 'mg/L'],
  ['Sulfate', 'Sulfate', 'mg/L'],
  ['Conductivity', 'Conductivity', 'µS/cm'],
  ['Organic_carbon', 'Organic carbon', 'mg/L'],
  ['Trihalomethanes', 'Trihalomethanes', 'µg/L'],
  ['Turbidity', 'Turbidity', 'NTU'],
]

const MEMBER_LABELS = { random_forest: 'Random Forest', xgboost: 'XGBoost', gradient_boosting: 'Gradient Boosting', decision_tree: 'Decision Tree' }
const LIMIT_STATUS = {
  ok: { tone: 'mint', text: 'within limit' },
  exceeds: { tone: 'rose', text: 'outside limit' },
}

// One bar per parameter: right of the centre pushes towards potable, left towards not potable.
function ShapBars({ reasons }) {
  const max = Math.max(...reasons.map((r) => Math.abs(r.shap)), 0.001)
  return (
    <div className="stack" style={{ '--gap': '10px' }} role="list" aria-label="How each parameter pushed the result">
      {reasons.map((r) => {
        const pos = r.shap >= 0
        const w = (Math.abs(r.shap) / max) * 50
        return (
          <div key={r.parameter} role="listitem" style={{ display: 'grid', gridTemplateColumns: 'minmax(96px, 150px) 1fr 64px', gap: 10, alignItems: 'center', fontSize: 13.5 }}>
            <span title={r.label} style={{ color: 'var(--text-2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {r.label}
            </span>
            <span style={{ position: 'relative', height: 14, borderRadius: 999, background: 'var(--surface-3)' }}>
              <span style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', width: 2, background: 'var(--border-strong)' }} />
              <span
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  borderRadius: 999,
                  background: pos ? 'var(--mint)' : 'var(--rose)',
                  ...(pos ? { left: '50%', width: `${w}%` } : { right: '50%', width: `${w}%` }),
                }}
              />
            </span>
            <span className="num" style={{ textAlign: 'right', fontWeight: 600, color: pos ? 'var(--mint-ink)' : 'var(--rose-ink)' }}>
              {pos ? '+' : ''}
              {r.shap.toFixed(3)}
            </span>
          </div>
        )
      })}
      <p className="tiny muted">Right of the centre line pushes towards potable; left pushes towards not potable.</p>
    </div>
  )
}

export default function Quality() {
  const toast = useToast()
  const samples = useApi('/quality/samples')
  const history = useApi('/quality/history')
  const [name, setName] = useState('Lab sample')
  const [values, setValues] = useState(() => Object.fromEntries(FIELDS.map(([k]) => [k, ''])))
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [formError, setFormError] = useState('')

  function loadSample(s) {
    setName(s.name)
    setValues(Object.fromEntries(FIELDS.map(([k]) => [k, s.values?.[k] == null ? '' : String(s.values[k])])))
    setResult(null)
    setFormError('')
  }

  async function submit(e) {
    e.preventDefault()
    const body = { sample_name: name.trim() || 'Lab sample' }
    for (const [k] of FIELDS) body[k] = values[k] === '' ? null : Number(values[k])
    if (FIELDS.every(([k]) => body[k] == null)) {
      setFormError('Enter at least one measured parameter, or load a recorded sample.')
      return
    }
    setFormError('')
    setError('')
    setBusy(true)
    try {
      const r = await api.post('/quality/predict', body)
      setResult(r.data)
      history.reload()
      toast({
        kind: r.data.potable ? 'success' : 'error',
        title: r.data.potable ? 'Sample is potable' : 'Sample is not potable',
        message: `${body.sample_name}: ${Math.round(r.data.confidence * 100)}% confidence${r.data.potable ? '' : '. An alert was raised.'}`,
      })
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Water quality"
        icon={FlaskConical}
        title="Water-quality check"
        lead="Check a lab sample against the potability model. Each result shows which parameters drove it and whether each one sits inside its guideline limit."
      />

      <div className="grid-2 wide-left">
        <Card as="form" hover={false} onSubmit={submit} noValidate title="Lab sample" subtitle="Leave a field empty if it was not measured. The model fills it from the training median.">
          <div className="stack" style={{ '--gap': '18px' }}>
            <div>
              <p className="field-label" style={{ marginBottom: 10 }}>
                Recorded samples
              </p>
              {samples.loading && !samples.data && <Skeleton height={40} radius={14} />}
              {samples.error && <ErrorState compact title="Recorded samples did not load" error={samples.error} onRetry={samples.reload} />}
              {samples.data && (
                <div className="row" style={{ '--gap': '8px' }}>
                  {samples.data.map((s) => (
                    <Button key={s.name} variant="secondary" size="sm" onClick={() => loadSample(s)}>
                      {s.name}
                    </Button>
                  ))}
                </div>
              )}
            </div>

            <Input id="sample-name" label="Sample name" value={name} onChange={(e) => setName(e.target.value)} />

            <div className="form-grid">
              {FIELDS.map(([k, label, unit]) => (
                <Input
                  key={k}
                  id={`q-${k}`}
                  label={unit ? `${label} (${unit})` : label}
                  type="number"
                  step="any"
                  inputMode="decimal"
                  placeholder="not measured"
                  value={values[k]}
                  onChange={(e) => setValues({ ...values, [k]: e.target.value })}
                />
              ))}
            </div>

            {formError && (
              <p className="field-error" role="alert">
                {formError}
              </p>
            )}
            {error && <ErrorState compact title="The check did not run" error={error} />}

            <Button type="submit" block size="lg" icon={FlaskConical} loading={busy}>
              Check potability
            </Button>
          </div>
        </Card>

        <div className="stack" style={{ '--gap': '24px' }}>
          {busy && (
            <Card hover={false} title="Running the check">
              <div className="stack" style={{ '--gap': '12px' }} role="status">
                <Skeleton height={28} width="60%" />
                <Skeleton height={14} />
                <Skeleton height={14} width="80%" />
              </div>
            </Card>
          )}

          {!busy && !result && (
            <EmptyState
              icon={FlaskConical}
              title="No result yet"
              message="Enter the measurements or load a recorded sample, then run the check."
            />
          )}

          {!busy && result && (
            <>
              <Card tint={result.potable ? 'mint' : 'peach'} hover={false}>
                <div className="row" style={{ '--gap': '16px', flexWrap: 'nowrap' }}>
                  {result.potable ? (
                    <CheckCircle2 size={40} color="var(--mint-ink)" aria-hidden="true" />
                  ) : (
                    <XCircle size={40} color="var(--rose-ink)" aria-hidden="true" />
                  )}
                  <div>
                    <h2 style={{ fontSize: 24 }}>{result.potable ? 'Potable' : 'Not potable'}</h2>
                    <p className="muted">
                      {Math.round(result.confidence * 100)}% confidence · probability potable {fmtNum(result.probability_potable * 100, 1)}%
                    </p>
                  </div>
                </div>
                <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', marginTop: 18 }}>
                  {Object.entries(result.members).map(([k, v]) => (
                    <div key={k} style={{ background: 'var(--surface)', borderRadius: 'var(--r-sm)', padding: '10px 12px' }}>
                      <div className="tiny muted">{MEMBER_LABELS[k] || k}</div>
                      <div style={{ fontWeight: 600 }}>{fmtNum(v * 100, 0)}% potable</div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card title="Why this result" subtitle={`Exact Shapley values over the whole ensemble. Baseline probability potable ${fmtNum(result.base_value * 100, 1)}%.`}>
                <ShapBars reasons={result.reasons} />
              </Card>

              <Card title="Guideline limits" subtitle="Each measured value against its guideline">
                <Table
                  caption="Measured values against guideline limits"
                  rows={result.limits}
                  rowKey={(l) => l.parameter}
                  pageSize={0}
                  columns={[
                    { key: 'label', label: 'Parameter', render: (l) => l.label },
                    { key: 'value', label: 'Value', numeric: true, sortable: false, render: (l) => (l.value == null ? '–' : `${fmtNum(l.value, 2)} ${l.unit}`) },
                    { key: 'limit', label: 'Guideline', sortable: false, render: (l) => `${l.limit} ${l.unit}` },
                    { key: 'source', label: 'Source', sortable: false, wrap: true, render: (l) => <span className="tiny muted">{l.source}</span> },
                    {
                      key: 'status',
                      label: 'Status',
                      sortable: false,
                      render: (l) => {
                        const s = LIMIT_STATUS[l.status]
                        return s ? <Badge tone={s.tone}>{s.text}</Badge> : <Badge tone="neutral">not measured</Badge>
                      },
                    },
                  ]}
                />
              </Card>
            </>
          )}

          <Card title="Recent checks" subtitle="Every check run on this server is saved here">
            {history.error && <ErrorState compact title="History did not load" error={history.error} onRetry={history.reload} />}
            {history.loading && !history.data && <Skeleton height={120} />}
            {history.data && (
              <Table
                caption="Recent water-quality checks"
                rows={history.data}
                rowKey={(h) => h.id}
                pageSize={6}
                searchKeys={['sample_name']}
                searchPlaceholder="Search samples"
                columns={[
                  { key: 'sample_name', label: 'Sample', render: (h) => h.sample_name },
                  {
                    key: 'potable',
                    label: 'Result',
                    sortable: false,
                    render: (h) => (
                      <Badge tone={h.potable ? 'mint' : 'rose'}>
                        {h.potable ? 'Potable' : 'Not potable'} {Math.round(h.confidence * 100)}%
                      </Badge>
                    ),
                  },
                  { key: 'exceeded', label: 'Limits exceeded', numeric: true },
                  { key: 'created_at', label: 'When', render: (h) => timeAgo(h.created_at) },
                ]}
              />
            )}
          </Card>
        </div>
      </div>
    </>
  )
}
