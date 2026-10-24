import { Suspense, lazy } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Check, History, Network, ScanSearch, X } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { fmtDays, fmtHour, fmtInt, fmtNum, fmtScore, timeAgo } from '../lib/format'
import { Badge, Button, Card, EmptyState, ErrorState, KeyValueList, PageHeader, PageSkeleton, Skeleton, Timeline } from '../components/ui'
import { Callout, ContribBars, Gauge, Load, ScoreBadge, StatusBadge, scoreColor } from '../components/app'
import { DecisionPanel } from '../components/app/DecisionPanel'

const ForceGraph = lazy(() => import('../components/graph/ForceGraph'))

function Neighbourhood({ id, threshold }) {
  const nav = useNavigate()
  const state = useAsync(() => api.neighbourhood(id, 40), [id])
  return (
    <Load state={state} title="Could not load the neighbourhood" skeleton={<Skeleton height={380} radius={20} />}>
      {(g) => (
        <>
          <Suspense fallback={<Skeleton height={380} radius={20} />}>
            <ForceGraph
              nodes={g.nodes}
              links={g.links}
              height={380}
              threshold={threshold}
              label={`Neighbourhood graph: this account and ${g.shown} of its ${g.total_neighbours} neighbours`}
              onNodeClick={(n) => !n.ego && nav(`/app/accounts/${n.id}`)}
            />
          </Suspense>
          <div className="graph-legend">
            <span><i style={{ background: 'var(--rose)' }} />flagged</span>
            <span><i style={{ background: 'var(--peach)' }} />watch (30%+)</span>
            <span><i style={{ background: 'var(--mint)' }} />looks genuine</span>
            <span><i className="line" style={{ background: 'var(--rose)' }} />injected tie</span>
            <span>Ringed node = this account. Click a neighbour to open it.</span>
          </div>
          <p className="small muted" style={{ marginTop: 8 }}>
            Showing {g.shown} of {fmtInt(g.total_neighbours)} neighbours. {g.note}
          </p>
        </>
      )}
    </Load>
  )
}

export default function AccountDetail() {
  const { id } = useParams()
  const state = useAsync(() => api.account(id), [id])

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <Load state={state} title="Could not load this account" skeleton={<PageSkeleton kpis={0} blocks={2} />}>
        {(a) => {
          const ex = a.explanation
          const nb = a.neighbourhood
          const pushes = ex.top.filter((t) => t.contribution > 0).length
          return (
            <>
              <PageHeader
                crumbs={[{ label: 'Accounts', to: '/app/accounts' }, { label: `@${a.handle}` }]}
                eyebrow="Account"
                icon={ScanSearch}
                title={`@${a.handle}`}
                lead={`${a.display_name} · ${a.origin === 'real topology' ? 'part of the real network topology' : 'added to the graph as an injected account'}`}
                actions={<StatusBadge status={a.status} />}
              />

              <div className="grid-2 wide-left">
                <Card title="Fake probability" subtitle={`${a.model} · flagged at ${fmtScore(a.threshold)} and above`}>
                  <div className="grid-2" style={{ alignItems: 'center' }}>
                    <Gauge value={a.score} threshold={a.threshold} />
                    <div className="stack" style={{ '--gap': '14px' }}>
                      <ScoreBadge score={a.score} threshold={a.threshold} />
                      <p className="small muted">{a.flagged ? 'Above the flag threshold, so it sits in the moderator queue until someone decides.' : 'Below the flag threshold, so it is not in the queue.'}</p>
                      {a.cluster_id && (
                        <Button to={`/app/clusters/${a.cluster_id}`} variant="secondary" size="sm">
                          Member of {a.cluster_id} ({a.cluster_size})
                        </Button>
                      )}
                    </div>
                  </div>
                  <h3 style={{ margin: '22px 0 10px', fontSize: 15 }}>Same account, every model</h3>
                  <ul className="driver-list">
                    {a.model_scores.map((m) => (
                      <li key={m.model}>
                        <div className="driver-row">
                          <span>
                            {m.label} {!m.uses_graph && <Badge tone="peach">no graph</Badge>}
                          </span>
                          <span className="tiny num">{fmtScore(m.score)}</span>
                        </div>
                        <div className="bar-track">
                          <div className="bar-fill" style={{ width: `${Math.max(2, m.score * 100)}%`, background: scoreColor(m.score, a.threshold) }} />
                        </div>
                      </li>
                    ))}
                  </ul>
                </Card>

                <Card title="Moderator decision" subtitle="Logged and used in the next training run.">
                  <DecisionPanel targetType="account" targetId={a.id} status={a.status} onDone={state.reload} />
                </Card>
              </div>

              <div className="grid-2">
                <Card title="Why this score" subtitle="Which of the account's own traits pushed it towards fake (rose) or genuine (mint).">
                  <ContribBars items={ex.top} />
                  <div style={{ marginTop: 18 }}>
                  <Callout tone="info" title="What the neighbours add">
                    {Math.abs(ex.network) < 0.05
                      ? 'The accounts around it barely change the score.'
                      : ex.network > 0
                        ? `The accounts around it push the score towards fake (${ex.network > 0 ? '+' : ''}${ex.network.toFixed(2)} on the model margin).`
                        : `The accounts around it pull the score towards genuine (${ex.network.toFixed(2)} on the model margin).`}{' '}
                    {pushes} of the top {ex.top.length} traits push towards fake. Gradient × input attribution: an approximation, not a proof.
                  </Callout>
                  </div>
                </Card>

                <Card title="Profile and behaviour" subtitle="The raw values the model saw.">
                  <KeyValueList
                    items={[
                      ['Followers / following', `${fmtInt(a.profile.followers)} / ${fmtInt(a.profile.following)}`],
                      ['Posts', fmtInt(a.profile.posts)],
                      ['Account age', fmtDays(a.profile.account_age_days)],
                      ['Profile picture', a.profile.has_profile_pic ? 'Yes' : 'No'],
                      ['Bio length', `${a.profile.bio_length} characters`],
                      ['Posts per day', fmtNum(a.profile.posts_per_day, 1)],
                      ['Interactions per week', fmtNum(a.profile.interactions_per_week, 0)],
                      ['Most active hour', fmtHour(a.profile.peak_hour)],
                    ]}
                  />
                  <div style={{ marginTop: 18 }}>
                    <Callout tone="success" title={`Dataset label: ${a.dataset_label}`}>
                      The labelled dataset says this account is {a.dataset_label}. Used only for evaluation, never shown to the model at scoring time.
                    </Callout>
                  </div>
                </Card>
              </div>

              <Card
                title="Neighbourhood"
                subtitle={`${fmtInt(nb.degree)} ties · ${nb.flagged} flagged neighbours · average neighbour score ${fmtScore(nb.mean_score)}`}
                actions={<Network size={20} aria-hidden="true" />}
              >
                <Neighbourhood id={a.id} threshold={a.threshold} />
              </Card>

              <Card title="Decision history" subtitle="Every decision touching this account, newest first.">
                {a.history.length ? (
                  <Timeline
                    items={a.history.map((h) => ({
                      id: h.id,
                      tone: h.decision === 'confirm' ? 'rose' : 'mint',
                      icon: h.decision === 'confirm' ? Check : X,
                      title: `${h.decision === 'confirm' ? 'Confirmed fake' : 'Dismissed'}${h.target_type === 'cluster' ? ' (as part of a cluster)' : ''}`,
                      meta: `${h.by} · ${timeAgo(h.at)}${h.note ? ` · “${h.note}”` : ''}`,
                    }))}
                  />
                ) : (
                  <EmptyState icon={History} title="No decisions yet" message="Nobody has reviewed this account." compact />
                )}
              </Card>
            </>
          )
        }}
      </Load>
      {state.error && state.data && <ErrorState compact title="Could not refresh" error={state.error} onRetry={state.reload} />}
    </div>
  )
}
