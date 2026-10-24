import { Suspense, lazy } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Network, Radar } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { fmtDays, fmtHour, fmtInt, fmtNum, fmtPct, fmtScore } from '../lib/format'
import { Badge, Card, KeyValueList, PageHeader, PageSkeleton, Skeleton, StatCard, Table } from '../components/ui'
import { Callout, Load, ScoreCell, StatusBadge } from '../components/app'
import { DecisionPanel } from '../components/app/DecisionPanel'

const ForceGraph = lazy(() => import('../components/graph/ForceGraph'))

export default function ClusterDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const state = useAsync(() => api.cluster(id), [id])

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <Load state={state} title="Could not load this cluster" skeleton={<PageSkeleton kpis={4} blocks={2} />}>
        {(c) => (
          <>
            <PageHeader
              crumbs={[{ label: 'Botnet clusters', to: '/app/clusters' }, { label: c.id }]}
              eyebrow="Botnet cluster"
              icon={Radar}
              title={c.id}
              lead={c.headline}
              actions={
                <>
                  <Badge tone={c.kind === 'coordinated' ? 'rose' : 'neutral'}>{c.kind === 'coordinated' ? 'Coordinated' : 'Loose group'}</Badge>
                  <StatusBadge status={c.status} />
                </>
              }
            />

            <div className="grid-kpi">
              <StatCard label="Accounts" value={c.size} format={fmtInt} icon={Network} tone="sky" foot={`${fmtPct(c.flagged_share, 0)} flagged individually`} />
              <StatCard label="Tie density" value={c.density} format={(v) => fmtPct(v, 0)} icon={Network} tone="rose" foot={`${fmtInt(c.internal_edges)} ties inside`} />
              <StatCard label="Shared peak hour" display={fmtHour(c.peak_hour)} icon={Radar} tone="peach" foot={`${fmtPct(c.peak_hour_share, 0)} within ±1 hour`} />
              <StatCard label="Reach into real accounts" value={c.reach.accounts} format={fmtInt} icon={Radar} tone="lavender" foot="distinct outside accounts tied to it" />
            </div>

            <div className="grid-2 wide-left">
              <Card title="Cluster graph" subtitle="Every member and the ties between them. Click an account to open it.">
                <Suspense fallback={<Skeleton height={420} radius={20} />}>
                  <ForceGraph
                    nodes={c.graph.nodes}
                    links={c.graph.links}
                    height={420}
                    threshold={c.threshold}
                    label={`Graph of the ${c.size} accounts in cluster ${c.id}`}
                    onNodeClick={(n) => nav(`/app/accounts/${n.id}`)}
                  />
                </Suspense>
                <div className="graph-legend">
                  <span><i style={{ background: 'var(--rose)' }} />flagged</span>
                  <span><i style={{ background: 'var(--peach)' }} />watch (30%+)</span>
                  <span><i style={{ background: 'var(--mint)' }} />looks genuine</span>
                  <span><i className="line" style={{ background: 'var(--rose)' }} />injected tie</span>
                </div>
              </Card>

              <div className="stack">
                <Card title="Moderator decision" subtitle={`Applies to all ${c.size} members.`}>
                  <DecisionPanel targetType="cluster" targetId={c.id} status={c.status} members={c.size} onDone={state.reload} />
                </Card>
                <Card title="Shared behaviour">
                  <KeyValueList
                    items={[
                      ['Average fake probability', fmtScore(c.mean_score)],
                      ['Created within', fmtDays(Math.max(c.created_span_days, 1))],
                      ['Median account age', fmtDays(c.median_account_age_days)],
                      ['Median posts per day', fmtNum(c.median_posts_per_day, 1)],
                      ['Median interactions / week', fmtNum(c.median_interactions_per_week, 0)],
                      ['Median followers', fmtInt(c.median_followers)],
                      ['Without profile picture', fmtPct(c.no_profile_pic_share, 0)],
                    ]}
                  />
                </Card>
              </div>
            </div>

            {c.reach.most_targeted.length > 0 && (
              <Callout tone="warn" title="Most-targeted real accounts">
                {c.reach.most_targeted.map((t, i) => (
                  <span key={t.id}>
                    {i > 0 && ', '}
                    <Link className="link-cell" to={`/app/accounts/${t.id}`}>@{t.handle}</Link> ({t.ties_from_cluster} ties)
                  </span>
                ))}
              </Callout>
            )}

            <Card title="Members" subtitle="Highest-scoring first.">
              <Table
                caption={`Members of ${c.id}`}
                rowKey={(r) => r.id}
                pageSize={15}
                searchKeys={['handle']}
                searchPlaceholder="Search members"
                cardTitle={(r) => <Link className="link-cell" to={`/app/accounts/${r.id}`}>@{r.handle}</Link>}
                columns={[
                  { key: 'handle', label: 'Account', render: (r) => <Link className="link-cell" to={`/app/accounts/${r.id}`}>@{r.handle}</Link>, sortValue: (r) => r.handle },
                  { key: 'score', label: 'Fake probability', render: (r) => <ScoreCell score={r.score} threshold={c.threshold} />, sortValue: (r) => r.score },
                  { key: 'inside_ties', label: 'Ties inside', numeric: true },
                  { key: 'degree', label: 'All ties', numeric: true },
                  { key: 'followers', label: 'Followers', numeric: true, render: (r) => fmtInt(r.followers) },
                  { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status === 'pending' ? (r.flagged ? 'pending' : 'clear') : r.status === 'confirm' ? 'confirmed' : 'dismissed'} />, sortable: false },
                ]}
                rows={c.members}
              />
            </Card>
          </>
        )}
      </Load>
    </div>
  )
}
