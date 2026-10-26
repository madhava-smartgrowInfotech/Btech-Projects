import { useEffect, useState } from 'react'
import { ArrowRight, Shuffle } from 'lucide-react'
import { Alert, Button, Card, EmptyState, ErrorState, PageHeader, Select, Skeleton, StatCard } from '../components/ui'
import { PALETTE } from '../components/ui/palette'
import { ActionError, BoxBlocks, ChartCard, Gate, GroupedBlocks, RecordTable, useAction } from '../components/app/common'
import { useApi } from '../lib/useApi'
import { api } from '../lib/api'
import { fmtInt, fmtNum, fmtSigned } from '../lib/format'
import { usePipeline } from '../lib/pipeline'

const METRIC_NAMES = { RMSE: 'RMSE', MAE: 'MAE', 'MAPE (%)': 'MAPE', R2: 'R²' }

function accuracyHint(a) {
  if (a === null || a === undefined) return ''
  if (a < 0.6) return 'Near 50%: the domains look similar'
  if (a < 0.85) return 'Moderate shift between the domains'
  return 'Near 100%: the domains are very different'
}

function Result({ run }) {
  const top = run.top_shift_feature
  return (
    <div className="page-stack">
      <h2 className="display-sm">
        {run.source_label} → {run.target_label}
      </h2>

      <section className="page-stack" aria-label="Domain shift analysis">
        <div className="metric-grid">
          <StatCard
            label="Domain classifier accuracy"
            value={`${fmtNum(run.classifier_accuracy * 100, 1)}%`}
            hint={accuracyHint(run.classifier_accuracy)}
          />
          <StatCard label="Source rows" value={run.source_rows} hint={`Domain: ${run.source_label}`} />
          <StatCard label="Target rows" value={run.target_rows} hint={`${fmtInt(run.target_test_rows)} held out for testing`} />
          <StatCard label="Instance weights" value={`${fmtNum(run.weights.mean, 2)} avg`} hint={`min ${fmtNum(run.weights.min, 2)} · max ${fmtNum(run.weights.max, 2)} (clipped at 20)`} />
        </div>

        <Card title="Features that shifted most">
          <RecordTable
            columns={['feature', 'source_mean', 'target_mean', 'mean_diff', 'source_std', 'target_std']}
            rows={run.shift}
            pageSize={8}
            caption="Per-feature comparison of source and target means"
          />
        </Card>

        <div className="two-col">
          <ChartCard title={`Distribution: ${top}`} summary={`Histogram of ${top} in the source and target domains.`}>
            <GroupedBlocks
              data={run.histogram}
              xKey="label"
              series={[
                { key: 'source', name: 'Source', color: PALETTE.sky },
                { key: 'target', name: 'Target', color: PALETTE.coral },
              ]}
            />
          </ChartCard>
          <ChartCard
            title={`Box plot: ${top}`}
            height={190}
            summary={`Source median ${fmtNum(run.box.source.median)}, target median ${fmtNum(run.box.target.median)} for ${top}.`}
          >
            <BoxBlocks
              valueLabel={top}
              boxes={[
                { label: 'Source', color: PALETTE.sky, ...run.box.source },
                { label: 'Target', color: PALETTE.coral, ...run.box.target },
              ]}
            />
          </ChartCard>
        </div>
      </section>

      <section className="page-stack" aria-label="Before versus after adaptation">
        <h2 className="display-sm">Before vs after adaptation</h2>
        <div className="metric-grid">
          {run.report.map((r) => {
            const imp = r['Improvement (%)']
            const better = imp !== null && imp !== undefined && imp >= 0
            const fmt = (v) => (r.Metric === 'MAPE (%)' ? `${fmtNum(v, 1)}%` : fmtNum(v, 3))
            return (
              <StatCard
                key={r.Metric}
                label={METRIC_NAMES[r.Metric] || r.Metric}
                value={fmt(r['After Adaptation'])}
                delta={imp === null || imp === undefined ? 'n/a' : `${fmtSigned(imp)} ${better ? 'better' : 'worse'}`}
                deltaTone={imp === null || imp === undefined ? undefined : better ? PALETTE.lime : PALETTE.coral}
                hint={`Before: ${fmt(r['Before Adaptation'])}`}
              />
            )
          })}
        </div>
        <Card title="Report">
          <RecordTable
            columns={['Metric', 'Before Adaptation', 'After Adaptation', 'Improvement (%)']}
            rows={run.report}
            pageSize={10}
            caption="Before and after adaptation, evaluated on the held-out target domain"
            format={{ 'Improvement (%)': (v) => fmtSigned(v, 2) }}
          />
          <p className="small muted" style={{ marginTop: 12 }}>
            Improvement percentages reflect the actual experiment above, not a claimed or assumed result. A negative value means adaptation made that metric
            worse on this data.
          </p>
        </Card>
      </section>
    </div>
  )
}

export default function Domain() {
  const { state } = usePipeline()
  const ready = Boolean(state?.features_ready)
  const { data: opts, error: optsError, loading: optsLoading, reload } = useApi('/api/domain/options', { enabled: ready })
  const { run, loading, error } = useAction()
  const [col, setCol] = useState('')
  const [source, setSource] = useState('')
  const [target, setTarget] = useState('')
  const [result, setResult] = useState(null)
  const [formError, setFormError] = useState('')

  const option = opts?.options.find((o) => o.column === col)

  useEffect(() => {
    if (!opts?.options.length || col) return
    const o = opts.options[0]
    setCol(o.column)
    setSource(String(o.values[0]?.value ?? ''))
    setTarget(String(o.values[Math.min(1, o.values.length - 1)]?.value ?? ''))
  }, [opts, col])

  useEffect(() => {
    if (!state?.domain_done || result) return
    api('/api/domain/last')
      .then((r) => r.run && setResult(r.run))
      .catch(() => {})
  }, [state?.domain_done, result])

  const changeCol = (c) => {
    const o = opts.options.find((x) => x.column === c)
    setCol(c)
    setSource(String(o.values[0]?.value ?? ''))
    setTarget(String(o.values[Math.min(1, o.values.length - 1)]?.value ?? ''))
    setFormError('')
  }

  const submit = async (e) => {
    e.preventDefault()
    if (source === target) {
      setFormError('Source and target values must be different.')
      return
    }
    setFormError('')
    const out = await run(() => api('/api/domain/run', { method: 'POST', body: { domain_col: col, source: Number(source), target: Number(target) } }), {
      success: 'Domain adaptation finished.',
    })
    if (out) setResult(out)
  }

  const valueOptions = (option?.values || []).map((v) => ({ value: String(v.value), label: v.label }))
  const tooFew = option && option.values.length < 2

  return (
    <>
      <PageHeader
        eyebrow="06 · Domain adaptation"
        title="Adapt to a new domain"
        description="Train on a source domain, test on a shifted target domain, measure the shift, then re-weight the source rows that look like the target."
      />
      <Gate ok={ready} loading={!state} title="Build the feature table first" to="/app/features" cta="Go to Feature engineering">
        <div className="page-stack">
          <Alert tone="info">
            Source rows get a weight of p / (1 − p), where p is a domain classifier’s probability that the row looks like the target. The model is then retrained
            on the weighted source data and tested on the target.
          </Alert>
          {optsError ? (
            <ErrorState title="Could not load the domain options" error={optsError} onRetry={reload} />
          ) : optsLoading || !opts ? (
            <Skeleton height={180} />
          ) : !opts.options.length ? (
            <EmptyState title="No domain column available">The feature table has none of sales_channel_id, product_group_name or department_name.</EmptyState>
          ) : (
            <form onSubmit={submit} noValidate>
              <Card title="Choose the domains">
                <div className="grid grid-3">
                  <Select label="Domain-defining column" value={col} onChange={(e) => changeCol(e.target.value)} options={opts.options.map((o) => ({ value: o.column, label: o.label }))} />
                  <Select label="Source domain value" value={source} onChange={(e) => setSource(e.target.value)} options={valueOptions} error={formError || undefined} />
                  <Select label="Target domain value" value={target} onChange={(e) => setTarget(e.target.value)} options={valueOptions} />
                </div>
                {tooFew && <Alert tone="error">This column has fewer than two distinct values, so it cannot be split into a source and a target.</Alert>}
                <div className="stack" style={{ marginTop: 20 }}>
                  <ActionError error={error} />
                  <div className="row">
                    <Button type="submit" variant="primary" size="lg" icon={Shuffle} loading={loading} disabled={tooFew}>
                      {loading ? 'Running analysis…' : 'Run shift analysis & adaptation'}
                    </Button>
                    {loading && <span className="small muted">Trains two XGBoost models and a classifier; allow a minute or two.</span>}
                  </div>
                </div>
              </Card>
            </form>
          )}

          {result && <Result run={result} />}
          {result && (
            <div className="row">
              <Button variant="primary" to="/app/evaluation" iconRight={ArrowRight}>
                See the full evaluation
              </Button>
            </div>
          )}
        </div>
      </Gate>
    </>
  )
}
