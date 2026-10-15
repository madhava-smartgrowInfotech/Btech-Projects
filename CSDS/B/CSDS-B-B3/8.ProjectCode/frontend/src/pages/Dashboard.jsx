import { Link } from 'react-router-dom'
import { Award, Flame, Handshake, Map as MapIcon, Medal, Store, Wallet, Zap, BookCheck, Trophy } from 'lucide-react'
import { AsyncView } from '../components/common'
import { Badge, Button, Card, CardHeader, EmptyState, PageHeader, ProgressBar, StatCard } from '../components/ui'
import { Stagger } from '../components/motion'
import { inr } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

const AUTO = { gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))' }

export default function Dashboard() {
  const state = useAsync(() => api.get('/student/dashboard'), [])
  return (
    <AsyncView state={state}>
      {(d) => {
        const c = d.counts
        const first = d.name.split(' ')[0]
        return (
          <>
            <PageHeader
              title={`Welcome back, ${first}`}
              description={`${d.profile.branch || 'Branch not set'} · ${d.profile.year || 'Year not set'} · Goal: ${d.profile.career_goal || 'Not set'}`}
              actions={
                <Button as={Link} to="/app/learning" variant="primary">
                  Continue learning
                </Button>
              }
            />
            <Stagger className="grid" style={AUTO}>
              <StatCard label="XP" value={d.points.xp} icon={Zap} delta={`Level: ${d.points.level}`} />
              <StatCard label="Streak" value={d.points.streak_days} format={(v) => `${Math.round(v)} ${Math.round(v) === 1 ? "day" : "days"}`} icon={Flame} tone="warn" />
              <StatCard label="Topics completed" value={c.completed} icon={BookCheck} />
              <StatCard label="Wallet" value={inr(d.profile.wallet_balance)} icon={Wallet} tone="info" />
              <StatCard label="Active mentors" value={d.active_mentors} icon={Handshake} />
            </Stagger>

            <div className="split mt">
              <div className="stack">
                <Card>
                  <CardHeader title="Learning snapshot" subtitle="Where you stand across the whole knowledge graph" />
                  <div className="card-body">
                    <ProgressBar
                      value={c.completed}
                      max={Math.max(c.total, 1)}
                      label="Topics completed"
                      valueLabel={`${c.completed} / ${c.total}`}
                    />
                    <div className="kpi-row mt">
                      <div className="kpi">
                        <strong>{c.completed}</strong>
                        <span>Completed</span>
                      </div>
                      <div className="kpi">
                        <strong>{c.strong}</strong>
                        <span>Strong</span>
                      </div>
                      <div className="kpi">
                        <strong>{c.weak}</strong>
                        <span>Weak</span>
                      </div>
                      <div className="kpi">
                        <strong>{c.locked}</strong>
                        <span>Locked</span>
                      </div>
                    </div>
                  </div>
                </Card>

                <Card>
                  <CardHeader
                    title="Latest roadmap"
                    subtitle="Your next five steps"
                    actions={
                      <Button as={Link} to="/app/learning" size="sm">
                        Open roadmap
                      </Button>
                    }
                  />
                  {d.roadmap.length ? (
                    <div>
                      {d.roadmap.map((s) => (
                        <div className="list-item" key={s.step} style={{ alignItems: 'center' }}>
                          <div className="row" style={{ flexWrap: 'nowrap', minWidth: 0 }}>
                            <span className="rank">{s.step}</span>
                            <div style={{ minWidth: 0 }}>
                              <strong>{s.name}</strong>
                              <div className="faint">{Math.round(s.completion_percent)}% complete</div>
                            </div>
                          </div>
                          <Badge tone={s.priority === 'High' ? 'danger' : s.priority === 'Medium' ? 'warn' : 'neutral'}>{s.priority} priority</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon={MapIcon}
                      title="No roadmap generated yet"
                      actions={
                        <Button as={Link} to="/app/learning" variant="primary">
                          Generate my roadmap
                        </Button>
                      }
                    >
                      Pick a career goal and SkillVerse will order the topics you need, respecting prerequisites.
                    </EmptyState>
                  )}
                </Card>
              </div>

              <div className="stack">
                <Card>
                  <CardHeader title="Badges" />
                  <div className="card-body">
                    {d.badges.length ? (
                      <div className="chips">
                        {d.badges.slice(0, 8).map((b) => (
                          <span className="chip ok" key={b.badge_name} title={b.description}>
                            <Medal size={13} aria-hidden="true" /> {b.badge_name}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">No badges yet. Complete an assessment, interview or coding problem to earn one.</p>
                    )}
                  </div>
                </Card>

                <Card>
                  <CardHeader title="Marketplace" actions={<Store size={18} aria-hidden="true" />} />
                  <div className="card-body kpi-row">
                    <div className="kpi">
                      <strong>{d.marketplace.uploads}</strong>
                      <span>Uploads</span>
                    </div>
                    <div className="kpi">
                      <strong>{d.marketplace.purchases}</strong>
                      <span>Purchases</span>
                    </div>
                    <div className="kpi">
                      <strong>{inr(d.marketplace.total_earnings)}</strong>
                      <span>Earnings</span>
                    </div>
                  </div>
                </Card>

                <Card>
                  <CardHeader title="Leaderboard" subtitle="Top 5 students by XP" actions={<Trophy size={18} aria-hidden="true" />} />
                  <div className="card-body">
                    {d.leaderboard.map((r, i) => (
                      <div className="row" key={`${i}-${r.name}`} style={{ justifyContent: 'space-between', padding: '8px 0', flexWrap: 'nowrap' }}>
                        <span className="row" style={{ flexWrap: 'nowrap', minWidth: 0 }}>
                          <span className="rank">{i + 1}</span>
                          <strong className="break">{r.name}</strong>
                        </span>
                        <span className="faint" style={{ whiteSpace: 'nowrap' }}>
                          {r.xp} XP · {r.level}
                        </span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          </>
        )
      }}
    </AsyncView>
  )
}
