import { Link, useNavigate } from 'react-router-dom'
import { Check, Network, Radar, ScanSearch, ShieldAlert, ShieldCheck, Target, Users, X } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { fmtCompact, fmtHour, fmtInt, fmtPct, fmtScore, timeAgo } from '../lib/format'
import { Badge, Button, Card, EmptyState, PageHeader, StatCard, Table, Timeline } from '../components/ui'
import { BarCompare } from '../components/charts'
import { Load, ScoreCell, StatusBadge } from '../components/app'
import { Stagger } from '../components/motion'
import { useChartTheme } from '../lib/palette'

export default function Overview() {
  const state = useAsync(() => api.overview(), [])
  const t = useChartTheme()
  const nav = useNavigate()

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <PageHeader
        eyebrow="Overview"
        icon={ShieldCheck}
        title="Trust & safety overview"
        lead="What the graph model sees across every account right now: who is flagged, which botnets it found, and what is waiting for a moderator."
        actions={
          <Button to="/app/queue" icon={ShieldAlert}>
            Open the queue
          </Button>
        }
      />
      <Load state={state}>
        {(d) => {
          const k = d.kpis
          const hist = d.score_histogram.map((b) => ({ name: b.bin.replace('%', ''), value: b.count, color: b.flagged ? t.rose : b.bin.startsWith('30') || b.bin.startsWith('40') ? t.peach : t.mint }))
          const f1 = d.model_f1.map((m) => ({ name: `${m.label} · ${fmtPct(m.f1, 1)}`, value: m.f1, highlight: m.model === d.model.best, color: m.model === 'baseline' ? t.peach : m.model === d.model.best ? t.lavender : t.sky }))
          return (
            <>
              <Stagger className="grid-kpi">
                <Stagger.Item>
                  <StatCard label="Accounts in graph" value={k.accounts} format={fmtInt} icon={Users} tone="sky" foot={`${fmtCompact(k.ties)} ties`} />
                </Stagger.Item>
                <Stagger.Item>
                  <StatCard label="Flagged as fake" value={k.flagged} format={fmtInt} icon={Target} tone="rose" foot={`${fmtPct(k.flagged / k.accounts)} of accounts`} />
                </Stagger.Item>
                <Stagger.Item>
                  <StatCard label="Botnet clusters" value={k.botnets} format={fmtInt} icon={Radar} tone="peach" foot={k.diffuse_groups ? `+${k.diffuse_groups} loose group` : undefined} />
                </Stagger.Item>
                <Stagger.Item>
                  <StatCard label="Waiting for review" value={k.pending_accounts} format={fmtInt} icon={ShieldAlert} tone="lavender" foot={`${k.pending_clusters} clusters · ${k.decided} decisions made`} />
                </Stagger.Item>
                <Stagger.Item>
                  <StatCard label={`F1 · ${d.model.label}`} value={d.model.f1.mean} format={(v) => fmtPct(v, 1)} icon={Network} tone="mint" delta={{ value: d.model.f1.mean - d.model.baseline_f1.mean, text: `${((d.model.f1.mean - d.model.baseline_f1.mean) * 100).toFixed(1)} pts`, label: 'vs no graph', good: 'up' }} />
                </Stagger.Item>
              </Stagger>

              <div className="grid-2">
                <Card title="How suspicious is everyone?" subtitle={`Accounts by fake-probability in percent. Flagged at ${fmtScore(d.model.threshold)} and above (rose).`}>
                  <BarCompare data={hist} height={260} valueFormat={fmtInt} name="Accounts" label="Histogram of fake-probability scores" />
                </Card>
                <Card title="Does the graph help?" subtitle="Test-set F1 on the same split. The no-graph model is the yardstick.">
                  <BarCompare data={f1} height={260} horizontal yWidth={230} valueFormat={(v) => fmtPct(v, 0)} name="F1" label="F1 by model" />
                </Card>
              </div>

              <Card
                title="Highest-scoring accounts"
                subtitle="The accounts the model is most sure about. Open one to see why."
                actions={
                  <Button to="/app/accounts" variant="secondary" size="sm">
                    All accounts
                  </Button>
                }
              >
                <Table
                  caption="Highest-scoring accounts"
                  rowKey={(r) => r.id}
                  pageSize={0}
                  cards
                  cardTitle={(r) => <Link className="link-cell" to={`/app/accounts/${r.id}`}>@{r.handle}</Link>}
                  columns={[
                    { key: 'handle', label: 'Account', render: (r) => <Link className="link-cell" to={`/app/accounts/${r.id}`}>@{r.handle}</Link>, sortValue: (r) => r.handle },
                    { key: 'score', label: 'Fake probability', render: (r) => <ScoreCell score={r.score} threshold={d.model.threshold} />, sortValue: (r) => r.score },
                    { key: 'cluster_id', label: 'Botnet', render: (r) => (r.cluster_id ? <Link className="link-cell" to={`/app/clusters/${r.cluster_id}`}>{r.cluster_id}</Link> : <span className="muted">none</span>) },
                    { key: 'followers', label: 'Followers', numeric: true, render: (r) => fmtInt(r.followers) },
                    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} />, sortable: false },
                  ]}
                  rows={d.top_accounts}
                  empty={<EmptyState icon={Users} title="No flagged accounts" message="Nothing is above the flag threshold." compact />}
                />
              </Card>

              <div className="grid-2">
                <Card title="Largest botnet clusters" subtitle="Groups the model believes are coordinated." actions={<Button to="/app/clusters" variant="secondary" size="sm">Explore</Button>}>
                  {d.top_clusters.length ? (
                    <ul className="driver-list">
                      {d.top_clusters.map((c) => (
                        <li key={c.id}>
                          <div className="driver-row">
                            <span>
                              <Link className="link-cell" to={`/app/clusters/${c.id}`}>{c.id}</Link>
                              <Badge tone={c.kind === 'coordinated' ? 'rose' : 'neutral'}>{c.kind === 'coordinated' ? 'coordinated' : 'loose group'}</Badge>
                            </span>
                            <span className="tiny num">{c.size} accounts · tie density {fmtPct(c.density, 0)} · peak {fmtHour(c.peak_hour)}</span>
                          </div>
                          <div className="bar-track">
                            <div className="bar-fill" style={{ width: `${c.mean_score * 100}%`, background: 'var(--rose)' }} />
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <EmptyState icon={Radar} title="No clusters yet" message="Train the model to find botnet clusters." compact />
                  )}
                </Card>
                <Card title="Latest moderator decisions" subtitle="Logged, and used the next time the model is retrained.">
                  {d.recent_decisions.length ? (
                    <Timeline
                      items={d.recent_decisions.map((r) => ({
                        id: r.id,
                        tone: r.decision === 'confirm' ? 'rose' : 'mint',
                        icon: r.decision === 'confirm' ? Check : X,
                        title: `${r.decision === 'confirm' ? 'Confirmed' : 'Dismissed'} ${r.target_type} ${r.target_id}`,
                        meta: `${r.by} · ${timeAgo(r.at)}`,
                      }))}
                    />
                  ) : (
                    <EmptyState
                      icon={ScanSearch}
                      title="No decisions yet"
                      message="Confirm or dismiss a flagged account and it will show up here."
                      action={<Button onClick={() => nav('/app/queue')}>Review the queue</Button>}
                      compact
                    />
                  )}
                </Card>
              </div>
            </>
          )
        }}
      </Load>
    </div>
  )
}
