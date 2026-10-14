import { useNavigate } from 'react-router-dom'
import { Play, ScanSearch } from 'lucide-react'
import api, { errMsg } from '../api'
import { useAsync } from '../lib/useAsync'
import { when } from '../lib/format'
import { Button, Card, EmptyState, ErrorState, PageHeader, Table } from '../components/ui'
import { FadeIn } from '../components/motion'
import { GradeBadge, StatusBadge } from '../components/scan'

export default function Scans() {
  const navigate = useNavigate()
  // Refreshes quietly every 5 s so running scans update their status without a reload.
  const scans = useAsync(() => api.get('/scans').then((r) => r.data), [], { poll: 5000 })

  const columns = [
    { key: 'id', label: 'Scan', render: (s) => <span className="mono">#{s.id}</span> },
    { key: 'target_name', label: 'Target', render: (s) => <strong>{s.target_name}</strong> },
    { key: 'status', label: 'Status', sortable: false, render: (s) => <StatusBadge status={s.status} progress={s.progress} /> },
    {
      key: 'score',
      label: 'Score',
      num: true,
      sortValue: (s) => (s.status === 'done' ? s.score : -1),
      render: (s) =>
        s.status === 'done' ? (
          <span>
            {s.score}/100 <GradeBadge grade={s.grade} />
          </span>
        ) : (
          <span className="faint">-</span>
        ),
    },
    { key: 'created_at', label: 'Started', hideSm: true, sortValue: (s) => s.created_at || '', render: (s) => <span className="faint">{when(s.created_at)}</span> },
  ]

  return (
    <FadeIn>
      <PageHeader title="Scans" description="All security scans you have run." />

      {scans.error && !scans.data ? (
        <ErrorState title="Could not load scans" error={{ message: errMsg(scans.error) }} onRetry={scans.reload} />
      ) : (
        <Table
          caption="Scans"
          columns={columns}
          rows={scans.data}
          rowKey={(s) => s.id}
          initialSort={{ key: 'id', dir: 'desc' }}
          loading={!scans.data}
          onRowClick={(s) => navigate(`/app/scans/${s.id}`)}
          empty={
            <Card spotlight={false}>
              <EmptyState
                icon={ScanSearch}
                title="No scans yet"
                actions={
                  <Button variant="primary" icon={Play} onClick={() => navigate('/app/targets')}>
                    Go to targets
                  </Button>
                }
              >
                Start a scan from a target.
              </EmptyState>
            </Card>
          }
        />
      )}
    </FadeIn>
  )
}
