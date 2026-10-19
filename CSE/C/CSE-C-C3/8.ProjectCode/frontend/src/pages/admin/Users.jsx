import { useMemo, useState } from 'react'
import { RefreshCw, Users as UsersIcon } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, SearchField, Table } from '../../components/ui'
import { Api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { money, when } from '../../lib/format'

export default function Users() {
  const { data, error, loading, reload } = useAsync(() => Api.adminUsers(), [])
  const [q, setQ] = useState('')
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (data || []).filter((u) => !needle || `${u.name} ${u.email}`.toLowerCase().includes(needle))
  }, [data, q])

  const columns = [
    { key: 'name', label: 'User', render: (u) => (<><strong>{u.name}</strong><div className="faint">{u.email}</div></>) },
    { key: 'role', label: 'Role', render: (u) => <Badge tone={u.role === 'admin' ? 'info' : 'neutral'}>{u.role === 'admin' ? 'Admin' : 'Driver'}</Badge> },
    { key: 'trust_score', label: 'Trust', num: true, render: (u) => `${u.trust_score} / 5` },
    { key: 'benefit_streak', label: 'On-time streak', num: true, hideSm: true },
    { key: 'warning_count', label: 'Warnings', num: true, hideSm: true },
    { key: 'account_credit', label: 'Credit', num: true, render: (u) => money(u.account_credit) },
    {
      key: 'suspended_until',
      label: 'Booking',
      sortValue: (u) => u.suspended_until || '',
      render: (u) => (u.suspended_until && new Date(u.suspended_until) > new Date() ? <Badge tone="danger">Paused until {when(u.suspended_until)}</Badge> : <Badge tone="safe">Allowed</Badge>),
    },
  ]

  return (
    <div className="container">
      <PageHeader
        title="Users"
        description="Every account with its trust standing and credit balance."
        actions={
          <Button icon={RefreshCw} onClick={() => reload()} loading={loading && !!data}>
            Refresh
          </Button>
        }
      />
      {error ? (
        <ErrorState title="Could not load users" error={error} onRetry={() => reload()} />
      ) : (
        <Card>
          <div className="card-body filters">
            <SearchField value={q} onChange={setQ} label="Search users" placeholder="Search by name or email" />
          </div>
          <Table
            caption="Users"
            columns={columns}
            rows={rows}
            rowKey={(u) => u.id}
            loading={loading && !data}
            initialSort={{ key: 'name', dir: 'asc' }}
            pageSize={12}
            empty={<EmptyState icon={UsersIcon} title="No users match" actions={q ? <Button onClick={() => setQ('')}>Clear search</Button> : undefined}>{q ? 'Try a different name or email.' : 'No accounts exist yet.'}</EmptyState>}
          />
        </Card>
      )}
    </div>
  )
}
