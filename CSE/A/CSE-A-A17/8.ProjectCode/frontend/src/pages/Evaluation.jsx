import { Card, EmptyState, ErrorState, PageHeader, Skeleton } from '../components/ui'
import { PALETTE } from '../components/ui/palette'
import { ChartCard, ComparisonPanel, Gate, HBarBlocks, RecordTable } from '../components/app/common'
import { Button } from '../components/ui'
import { useApi } from '../lib/useApi'
import { usePipeline } from '../lib/pipeline'
import { fmtSigned } from '../lib/format'

export default function Evaluation() {
  const { state } = usePipeline()
  const ready = Boolean(state?.features_ready)
  const { data, error, loading, reload } = useApi('/api/evaluation', { enabled: ready })

  return (
    <>
      <PageHeader
        eyebrow="07 · Model evaluation"
        title="Evaluation"
        description="Every model side by side, the effect of domain adaptation, and which features drive the XGBoost forecast."
      />
      <Gate ok={ready} loading={!state} title="Build the feature table first" to="/app/features" cta="Go to Feature engineering">
        {error ? (
          <ErrorState title="Could not load the evaluation" error={error} onRetry={reload} />
        ) : loading || !data ? (
          <div className="page-stack">
            <Skeleton height={200} />
            <Skeleton height={300} />
          </div>
        ) : (
          <div className="page-stack">
            {data.has_results ? (
              <>
                <h2 className="display-sm">Baseline vs XGBoost</h2>
                <ComparisonPanel rows={data.comparison} />
              </>
            ) : (
              <EmptyState
                title="No models trained yet"
                action={
                  <Button variant="primary" to="/app/training">
                    Go to Model training
                  </Button>
                }
              >
                Train the baseline and XGBoost first, and their metrics will be compared here.
              </EmptyState>
            )}

            {data.domain && (
              <section className="page-stack" aria-label="Domain adaptation before versus after">
                <h2 className="display-sm">Domain adaptation: before vs after</h2>
                {data.domain.meta?.source_label && (
                  <p className="small mono muted">
                    {data.domain.meta.source_label} → {data.domain.meta.target_label}
                  </p>
                )}
                <Card>
                  <RecordTable
                    columns={['Metric', 'Before Adaptation', 'After Adaptation', 'Improvement (%)']}
                    rows={data.domain.report}
                    caption="Before and after domain adaptation"
                    format={{ 'Improvement (%)': (v) => fmtSigned(v, 2) }}
                  />
                </Card>
              </section>
            )}

            {data.importance.length > 0 && (
              <ChartCard
                title="Feature importance (XGBoost, top 20)"
                height={Math.max(220, data.importance.length * 32 + 40)}
                summary={`Most important feature: ${data.importance[0].feature}.`}
              >
                <HBarBlocks data={data.importance.map((i) => ({ ...i, importance: Number(i.importance.toFixed(4)) }))} labelKey="feature" valueKey="importance" name="Importance" color={PALETTE.lime} labelWidth={130} />
              </ChartCard>
            )}
          </div>
        )}
      </Gate>
    </>
  )
}
