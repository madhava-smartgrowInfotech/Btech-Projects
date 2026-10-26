import { Alert, Card, ErrorState, PageHeader, Skeleton } from '../components/ui'
import { Gate, RecordTable } from '../components/app/common'
import { useApi } from '../lib/useApi'
import { usePipeline } from '../lib/pipeline'
import { fmtInt } from '../lib/format'

export default function Demand() {
  const { state } = usePipeline()
  const ready = Boolean(state?.data_loaded)
  const { data, error, loading, reload } = useApi('/api/demand/table?limit=200', { enabled: ready })

  return (
    <>
      <PageHeader
        eyebrow="03 · Demand analysis"
        title="Daily demand"
        description="The aggregated modelling table: how many units of each article sold on each date."
      />
      <Gate ok={ready} loading={!state} title="Upload your data first" to="/app/upload" cta="Go to Data upload">
        <div className="page-stack">
          {error ? (
            <ErrorState title="Could not load the demand table" error={error} onRetry={reload} />
          ) : loading || !data ? (
            <Skeleton height={360} />
          ) : (
            <Card title="Aggregated daily demand" actions={<span className="small mono">First {fmtInt(data.rows.length)} of {fmtInt(data.total)} rows</span>}>
              <RecordTable
                columns={data.columns}
                rows={data.rows}
                caption="Aggregated daily demand per article"
                pageSize={12}
                format={{ price: (v) => Number(v).toFixed(5), article_id: (v) => String(v) }}
              />
            </Card>
          )}
          <Alert tone="info">
            <strong>Note on data leakage.</strong> This table is built by counting transactions that occurred on that exact date for that exact product, so
            no future information is used in the aggregation itself. Leakage risk only enters later, in feature engineering, which is why lag and rolling
            features are computed with a strict shift before any rolling window.
          </Alert>
        </div>
      </Gate>
    </>
  )
}
