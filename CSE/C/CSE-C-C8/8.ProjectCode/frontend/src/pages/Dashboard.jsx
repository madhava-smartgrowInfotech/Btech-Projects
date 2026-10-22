import { Link, useNavigate } from 'react-router-dom'
import { Activity, BarChart3, FileSearch, ScanSearch, Users } from 'lucide-react'
import { Badge, Button, Card, CardHeader, Container, EmptyState, ErrorState, PageHeader, StatCard, Table } from '../components/ui'
import { ChartCard, GroupedBarChart, Legend, useChartColors } from '../components/charts'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { when } from '../lib/format'
import { useAsync } from '../lib/useAsync'
import { useStats } from '../lib/stats'

export default function Dashboard() {
  const nav = useNavigate()
  const c = useChartColors()
  const { health, metrics, error: statsError } = useStats()
  const analyses = useAsync(() => api.analyses(), [])
  const reviewers = useAsync(() => api.reviewers(), [])

  const list = analyses.data || []
  const active = (reviewers.data || []).filter((r) => r.is_active).length
  const acc = metrics && metrics.status !== 'missing' ? metrics.accuracy : null
  const chartData = list
    .slice(0, 8)
    .reverse()
    .map((a) => ({ name: `#${a.id}`, concerns: a.concern_count, recs: a.recommendation_count }))

  const cols = [
    { key: 'filename', label: 'Paper', render: (a) => <span className="break">{a.filename}</span> },
    { key: 'created_at', label: 'Analyzed', hideSm: true, render: (a) => when(a.created_at) },
    { key: 'overall_assessment', label: 'Assessment', hideSm: true, sortable: false, render: (a) => (a.overall_assessment || '').slice(0, 70) },
    { key: 'top_reviewer', label: 'Top reviewer', render: (a) => a.top_reviewer || '-' },
  ]

  if (analyses.error && reviewers.error && statsError) {
    return (
      <Container>
        <PageHeader title="Dashboard" />
        <ErrorState title="The PeerScope backend is not reachable" error={statsError} onRetry={() => window.location.reload()} />
      </Container>
    )
  }

  return (
    <Container>
      <PageHeader
        title="Dashboard"
        description="Evaluate papers and match the right reviewers - locally, with an audit trail."
        actions={
          <Button as={Link} to="/app/analyze" variant="primary" icon={ScanSearch}>
            Analyze a paper
          </Button>
        }
      />

      <Stagger className="grid grid-4">
        <StatCard label="Reviewers in directory" value={health?.reviewer_count} icon={Users} loading={!health && !statsError} delta={reviewers.data ? `${active} active` : undefined} />
        <StatCard label="Analyses stored" value={analyses.loading ? undefined : list.length} icon={FileSearch} tone="info" loading={analyses.loading} />
        <StatCard
          label="Decision-model accuracy"
          value={acc === null ? (metrics ? 'Not trained' : undefined) : acc * 100}
          format={(v) => `${v.toFixed(1)}%`}
          icon={BarChart3}
          tone="warn"
          loading={!metrics && !statsError}
          delta={metrics?.synthetic_fallback ? 'synthetic training data' : undefined}
          deltaTone="down"
        />
        <StatCard
          label="Local AI review"
          value={health ? (health.llm_status === 'loaded' ? 'Loaded' : 'On demand') : undefined}
          icon={Activity}
          tone="info"
          loading={!health && !statsError}
          delta={health ? `embeddings: ${health.embedding_status === 'tfidf-fallback' ? 'TF-IDF fallback' : 'MiniLM'}` : undefined}
        />
      </Stagger>

      <div className="split mt">
        <Card>
          <CardHeader
            title="Recent analyses"
            subtitle="Open one to see the full review and reviewer ranking"
            actions={
              <Button as={Link} to="/app/history" size="sm" variant="ghost">
                View all
              </Button>
            }
          />
          {analyses.error ? (
            <ErrorState title="Could not load analyses" error={analyses.error} onRetry={analyses.reload} />
          ) : (
            <Table
              columns={cols}
              rows={list.slice(0, 6)}
              rowKey={(a) => a.id}
              loading={analyses.loading}
              pageSize={6}
              onRowClick={(a) => nav(`/app/analyses/${a.id}`)}
              caption="Recent analyses"
              empty={
                <EmptyState
                  icon={FileSearch}
                  title="No analyses yet"
                  actions={
                    <Button as={Link} to="/app/analyze" variant="primary">
                      Upload a paper
                    </Button>
                  }
                >
                  Upload a research-paper PDF to get a preliminary assessment and ranked reviewer recommendations.
                </EmptyState>
              }
            />
          )}
        </Card>

        <div className="stack">
          <Card>
            <CardHeader title="How it works" />
            <div className="card-body">
              <ol className="bullets" style={{ counterReset: 'n' }}>
                <li>
                  <strong>Upload</strong> a PDF (up to 20 MB). Text, sections and references are extracted locally.
                </li>
                <li>
                  <strong>Review</strong> - decision signal, structural checks and a local AI critique.
                </li>
                <li>
                  <strong>Match</strong> - expertise, topic, method and availability rank your reviewers, with conflict checks.
                </li>
              </ol>
            </div>
          </Card>
          {metrics?.synthetic_fallback && (
            <div className="note warn">
              <BarChart3 size={18} aria-hidden="true" />
              <span>
                The decision model was trained on a labelled <strong>synthetic fallback dataset</strong>. Treat its signal as a demonstration, not a benchmark.{' '}
                <Link to="/app/model">See metrics</Link>
              </span>
            </div>
          )}
        </div>
      </div>

      {chartData.length > 0 && (
        <div className="mt">
          <ChartCard
            title="Concerns vs. recommendations"
            subtitle="Most recent analyses"
            legend={
              <Legend
                items={[
                  { label: 'Concerns raised', color: c.warn },
                  { label: 'Recommendations', color: c.accent },
                ]}
              />
            }
            height={240}
          >
            <GroupedBarChart
              data={chartData}
              xKey="name"
              yDomain={[0, 'auto']}
              series={[
                { key: 'concerns', label: 'Concerns raised', color: c.warn },
                { key: 'recs', label: 'Recommendations', color: c.accent },
              ]}
            />
          </ChartCard>
        </div>
      )}
      {!health && statsError && (
        <div className="mt">
          <Badge tone="danger" dot>
            Backend offline - some figures are unavailable
          </Badge>
        </div>
      )}
    </Container>
  )
}
