import { useEffect, useState } from 'react'
import { ArrowRight, Wand2 } from 'lucide-react'
import { Alert, Button, Card, PageHeader, Skeleton, StatCard } from '../components/ui'
import { ActionError, Gate, RecordTable, useAction } from '../components/app/common'
import { api } from '../lib/api'
import { fmtInt } from '../lib/format'
import { usePipeline } from '../lib/pipeline'

export default function Features() {
  const { state, refresh } = usePipeline()
  const { run, loading, error } = useAction()
  const [data, setData] = useState(null)
  const [loadingExisting, setLoadingExisting] = useState(false)

  useEffect(() => {
    if (!state?.features_ready || data) return
    setLoadingExisting(true)
    api('/api/features')
      .then(setData)
      .catch(() => {})
      .finally(() => setLoadingExisting(false))
  }, [state?.features_ready, data])

  const build = async () => {
    const out = await run(() => api('/api/features/build', { method: 'POST' }), { success: 'Feature table built.' })
    if (out) {
      setData(out)
      refresh()
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="04 · Feature engineering"
        title="Features"
        description="Fills the days a product did not sell, then adds calendar, cyclical, lag, rolling and encoded product features."
        actions={
          state?.data_loaded && (
            <Button variant="primary" icon={Wand2} loading={loading} onClick={build}>
              {data ? 'Rebuild feature table' : 'Build feature table'}
            </Button>
          )
        }
      />
      <Gate ok={Boolean(state?.data_loaded)} loading={!state} title="Upload your data first" to="/app/upload" cta="Go to Data upload">
        <div className="page-stack">
          <ActionError error={error} />
          {loading && (
            <Alert tone="info">Filling missing dates and engineering features. On large uploads this can take a minute.</Alert>
          )}
          {loadingExisting && !data && <Skeleton height={200} />}
          {!data && !loading && !loadingExisting && (
            <Card flat>
              <p className="muted" style={{ maxWidth: '62ch' }}>
                No feature table yet. Building it adds time features (year to quarter, weekend and month flags), sin and cos encodings of month and day of
                week, lag 1, 7, 14 and 28, rolling means (7, 14, 28) and rolling standard deviations (7, 28). Rolling values are computed on shifted demand, so
                a day never sees its own sales.
              </p>
            </Card>
          )}
          {data && (
            <>
              <div className="metric-grid">
                <StatCard label="Rows" value={data.rows} />
                <StatCard label="Columns" value={data.columns} />
                <StatCard label="Model inputs" value={data.feature_columns.length} hint="Numeric, excluding date, id and target" />
              </div>
              <Card title="Model input features">
                <div className="chips">
                  {data.feature_columns.map((f) => (
                    <span key={f} className="chip">
                      {f}
                    </span>
                  ))}
                </div>
              </Card>
              <Card title="Feature table preview" actions={<span className="small mono">First 50 of {fmtInt(data.rows)} rows</span>}>
                <RecordTable
                  columns={data.head_columns}
                  rows={data.head}
                  caption="First 50 rows of the feature table"
                  pageSize={10}
                  format={{ article_id: (v) => String(v) }}
                />
              </Card>
              <div className="row">
                <Button variant="primary" to="/app/training" iconRight={ArrowRight}>
                  Continue to model training
                </Button>
              </div>
            </>
          )}
        </div>
      </Gate>
    </>
  )
}
