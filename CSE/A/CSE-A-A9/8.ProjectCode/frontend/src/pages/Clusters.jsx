import { Link } from 'react-router-dom'
import { Radar } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { fmtDays, fmtHour, fmtPct, fmtScore } from '../lib/format'
import { Badge, Card, EmptyState, PageHeader, Table } from '../components/ui'
import { Callout, Load, ScoreCell, StatusBadge } from '../components/app'

export default function Clusters() {
  const state = useAsync(() => api.clusters(), [])
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Botnet clusters"
        icon={Radar}
        title="Coordinated groups"
        lead="Louvain community detection over the learned account embeddings. Members of a real botnet look alike to the model because they share neighbours and behaviour."
      />
      <Load state={state} title="Could not load clusters">
        {(d) => (
          <>
            <Callout tone="info" title="Coordinated or loose?">
              A <b>coordinated</b> cluster has dense ties between its members. A <b>loose group</b> is suspicious accounts that merely look similar with almost no ties between them, so they are probably independent spammers.
            </Callout>
            <Card hover={false}>
              <Table
                caption="Botnet clusters"
                rowKey={(r) => r.id}
                pageSize={0}
                initialSort={{ key: 'size', dir: 'desc' }}
                cardTitle={(r) => <Link className="link-cell" to={`/app/clusters/${r.id}`}>{r.id}</Link>}
                columns={[
                  { key: 'id', label: 'Cluster', render: (r) => <Link className="link-cell" to={`/app/clusters/${r.id}`}>{r.id}</Link>, sortValue: (r) => r.id },
                  { key: 'kind', label: 'Type', render: (r) => <Badge tone={r.kind === 'coordinated' ? 'rose' : 'neutral'}>{r.kind === 'coordinated' ? 'Coordinated' : 'Loose group'}</Badge> },
                  { key: 'size', label: 'Accounts', numeric: true },
                  { key: 'mean_score', label: 'Avg fake probability', render: (r) => <ScoreCell score={r.mean_score} threshold={d.threshold} />, sortValue: (r) => r.mean_score },
                  { key: 'density', label: 'Tie density', numeric: true, render: (r) => fmtPct(r.density, 0) },
                  { key: 'peak_hour', label: 'Shared peak hour', numeric: true, render: (r) => `${fmtHour(r.peak_hour)} (${fmtPct(r.peak_hour_share, 0)})`, sortValue: (r) => r.peak_hour_share },
                  { key: 'created_span_days', label: 'Created within', numeric: true, render: (r) => fmtDays(Math.max(r.created_span_days, 1)) },
                  { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} />, sortable: false },
                ]}
                rows={d.items}
                empty={<EmptyState icon={Radar} title="No clusters found" message="No group of suspicious accounts was large enough to report." compact />}
              />
              <p className="small muted" style={{ marginTop: 12 }}>
                Candidates are accounts scored at {fmtScore(0.3)} or more; groups smaller than 5 are dropped.
              </p>
            </Card>
          </>
        )}
      </Load>
    </div>
  )
}
