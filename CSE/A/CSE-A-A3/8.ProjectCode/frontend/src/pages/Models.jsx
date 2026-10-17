import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Trophy } from 'lucide-react'
import { Badge, Button, Card, CardHeader, ErrorState, PageHeader, Skeleton, Table, Tabs } from '../components/ui'
import { GroupedBarChart, Legend, useChartColors } from '../components/charts'
import { api } from '../lib/api'
import { ICON, KEYS } from '../lib/diseases'
import { DISEASE_NAME, METRICS, pct } from '../lib/format'
import { useAsync } from '../lib/useAsync'

export default function Models() {
  const { data, error, loading, reload } = useAsync(api.report)
  const [disease, setDisease] = useState('diabetes')
  const colors = useChartColors()

  const rows = useMemo(() => {
    if (!data) return []
    const d = data[disease]
    return Object.entries(d.all_results).map(([name, m]) => ({ name, ...m, best: name === d.best_model }))
  }, [data, disease])

  const series = METRICS.map((m, i) => ({ key: m.key, label: m.label, color: colors.series[i] }))

  const columns = [
    {
      key: 'name',
      label: 'Algorithm',
      render: (r) => (
        <span className="row" style={{ gap: 8 }}>
          <strong>{r.name}</strong>
          {r.best && (
            <Badge tone="safe" dot>
              Selected
            </Badge>
          )}
        </span>
      ),
    },
    ...METRICS.map((m) => ({ key: m.key, label: m.label, num: true, render: (r) => pct(r[m.key]) })),
  ]

  return (
    <div className="container">
      <PageHeader
        crumbs={[{ label: 'Insights' }, { label: 'Models' }]}
        title="Model comparison"
        description="Each condition is modelled with Logistic Regression, Decision Tree, Random Forest and SVM. The best by F1-score is the one used for live predictions."
      />
      <div style={{ marginBottom: 18, overflowX: 'auto' }}>
        <Tabs label="Condition" value={disease} onChange={setDisease} tabs={KEYS.map((k) => ({ value: k, label: DISEASE_NAME[k], icon: ICON[k] }))} />
      </div>

      {error ? (
        <ErrorState title="Could not load the training report" error={error} onRetry={reload} />
      ) : (
        <div className="stack">
          <Card>
            <CardHeader
              title={`${DISEASE_NAME[disease]} - metrics by algorithm`}
              subtitle="Held-out test set"
              actions={
                data && (
                  <Badge tone="safe">
                    <Trophy size={13} aria-hidden="true" /> {data[disease].best_model}
                  </Badge>
                )
              }
            />
            <div className="card-body">
              <Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />
              <div style={{ width: '100%', height: 300 }} role="img" aria-label={`Grouped bar chart of accuracy, precision, recall and F1 for each algorithm on ${DISEASE_NAME[disease]}`}>
                {loading ? (
                  <Skeleton height="100%" />
                ) : (
                  <GroupedBarChart data={rows} xKey="name" series={series} yDomain={[0, 1]} valueFormat={(v) => `${Math.round(v * 100)}%`} />
                )}
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader title="Scores" subtitle="Click a column header to sort" />
            <Table
              caption={`${DISEASE_NAME[disease]} model scores`}
              columns={columns}
              rows={rows}
              rowKey={(r) => r.name}
              loading={loading}
              initialSort={{ key: 'f1', dir: 'desc' }}
            />
          </Card>

          <div className="row">
            <Button as={Link} to={`/app/predict/${disease}`} variant="primary">
              Try the {DISEASE_NAME[disease].toLowerCase()} model
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
