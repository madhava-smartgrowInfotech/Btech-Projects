import { Link } from 'react-router-dom'
import { ArrowRight, BarChart3, Boxes, ListChecks, Target } from 'lucide-react'
import { Badge, Button, Card, ErrorState, PageHeader, Skeleton, StatCard } from '../components/ui'
import { ChartCard, GroupedBarChart } from '../components/charts'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { ICON } from '../lib/diseases'
import { DISEASE_NAME, pct } from '../lib/format'
import { useAsync } from '../lib/useAsync'

export default function Overview() {
  const diseases = useAsync(api.diseases)
  const report = useAsync(api.report)
  const list = diseases.data
  const rep = report.data

  const best = list && list.reduce((a, b) => (b.accuracy > a.accuracy ? b : a))
  const inputs = list && list.reduce((n, d) => n + d.n_features, 0)
  const trained = rep && Object.values(rep).reduce((n, d) => n + Object.keys(d.all_results).length, 0)
  const loading = diseases.loading || report.loading

  return (
    <div className="container">
      <PageHeader
        crumbs={[{ label: 'Workspace' }, { label: 'Overview' }]}
        title="Overview"
        description="Four independent risk models. Pick a condition, enter clinical values, and get a prediction with its confidence."
        actions={
          <Button as={Link} to="/app/predict/diabetes" variant="primary" iconRight={ArrowRight}>
            Start a prediction
          </Button>
        }
      />

      {diseases.error || report.error ? (
        <ErrorState
          title="Could not load the overview"
          error={diseases.error || report.error}
          onRetry={() => {
            diseases.reload()
            report.reload()
          }}
        />
      ) : (
        <div className="stack">
          <div className="grid grid-4">
            <StatCard label="Conditions" value={list?.length} icon={Boxes} loading={loading} />
            <StatCard label="Clinical inputs" value={inputs} icon={ListChecks} tone="info" loading={loading} />
            <StatCard label="Models trained" value={trained} icon={BarChart3} tone="info" delta="4 algorithms each" loading={loading} />
            <StatCard
              label="Best accuracy"
              value={best?.accuracy}
              format={(v) => `${(v * 100).toFixed(1)}%`}
              icon={Target}
              delta={best && `${DISEASE_NAME[best.key]} · ${best.best_model}`}
              loading={loading}
            />
          </div>

          <ChartCard title="Test accuracy of the selected model" subtitle="Best model per condition, chosen by F1-score" height={260}>
            {list ? (
              <GroupedBarChart
                data={list.map((d) => ({ name: DISEASE_NAME[d.key], accuracy: d.accuracy }))}
                xKey="name"
                series={[{ key: 'accuracy', label: 'Accuracy' }]}
                yDomain={[0, 1]}
                valueFormat={(v) => `${Math.round(v * 100)}%`}
              />
            ) : (
              <Skeleton height="100%" />
            )}
          </ChartCard>

          <div>
            <h2 className="section-title">Choose a condition</h2>
            <div className="grid grid-4 mt">
              {list
                ? (
                  <>
                    {list.map((d) => {
                      const Icon = ICON[d.key]
                      return (
                        <Card as={Link} to={`/app/predict/${d.key}`} key={d.key} className="disease-card" pad aria-label={`${d.title} - open prediction form`}>
                          <span className="feature-icon">
                            <Icon size={22} aria-hidden="true" />
                          </span>
                          <div className="big">{pct(d.accuracy)}</div>
                          <h3>{DISEASE_NAME[d.key]}</h3>
                          <p className="muted" style={{ marginBottom: 14 }}>
                            {d.blurb}
                          </p>
                          <div className="chips">
                            <Badge tone="info">{d.best_model}</Badge>
                            <Badge>{d.n_features} inputs</Badge>
                          </div>
                        </Card>
                      )
                    })}
                  </>
                )
                : Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} height={210} radius={18} />)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
