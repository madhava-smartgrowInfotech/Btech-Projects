import { AlertTriangle, Boxes, Rows3 } from 'lucide-react'
import { Badge, Card, CardHeader, ErrorState, PageHeader, Skeleton, StatCard } from '../components/ui'
import { DonutChart, useChartColors } from '../components/charts'
import { api } from '../lib/api'
import { DISEASE_NAME, num, titleize } from '../lib/format'
import { useAsync } from '../lib/useAsync'

export default function Datasets() {
  const { data, error, loading, reload } = useAsync(api.datasets)
  const c = useChartColors()
  const total = data && data.reduce((n, d) => n + d.rows, 0)

  return (
    <div className="container">
      <PageHeader
        crumbs={[{ label: 'Insights' }, { label: 'Datasets' }]}
        title="Training datasets"
        description="The CSV files in data/ that the four models were trained on."
      />

      <div className="stack">
        <Card pad spotlight={false} role="note">
          <div className="row" style={{ gap: 12, alignItems: 'flex-start' }}>
            <AlertTriangle size={20} aria-hidden="true" style={{ color: 'var(--warn)', flexShrink: 0, marginTop: 2 }} />
            <p className="muted">
              These datasets are <strong>synthetically generated</strong> with medically informed value ranges (see the project README), not real patient records. Replace the CSVs
              in <code>data/</code> and re-run <code>train_models.py</code> to train on public clinical data.
            </p>
          </div>
        </Card>

        {error ? (
          <ErrorState title="Could not load the datasets" error={error} onRetry={reload} />
        ) : (
          <>
            <div className="grid grid-3">
              <StatCard label="Datasets" value={data?.length} icon={Boxes} loading={loading} />
              <StatCard label="Total rows" value={total} icon={Rows3} tone="info" loading={loading} />
              <StatCard label="Target column" value="1 = high risk" icon={AlertTriangle} tone="warn" />
            </div>

            <div className="grid grid-2">
              {loading
                ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} height={330} radius={18} />)
                : data.map((d) => (
                    <Card key={d.key}>
                      <CardHeader
                        title={DISEASE_NAME[d.key]}
                        subtitle={`${num(d.rows)} rows · ${d.features.length} features · target "${d.target}"`}
                      />
                      <div className="card-body">
                        <div style={{ height: 190 }} role="img" aria-label={`${DISEASE_NAME[d.key]} class balance: ${d.positive} high-risk, ${d.negative} low-risk`}>
                          <DonutChart
                            centerValue={num(d.rows)}
                            centerLabel="rows"
                            data={[
                              { name: 'High risk (1)', value: d.positive, color: c.danger },
                              { name: 'Low risk (0)', value: d.negative, color: c.accent },
                            ]}
                          />
                        </div>
                        <div className="legend" style={{ margin: '12px 0' }}>
                          <span>
                            <i style={{ background: c.danger }} />
                            High risk {num(d.positive)}
                          </span>
                          <span>
                            <i style={{ background: c.accent }} />
                            Low risk {num(d.negative)}
                          </span>
                        </div>
                        <div className="chips">
                          {d.features.map((f) => (
                            <Badge key={f}>{titleize(f)}</Badge>
                          ))}
                        </div>
                      </div>
                    </Card>
                  ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
