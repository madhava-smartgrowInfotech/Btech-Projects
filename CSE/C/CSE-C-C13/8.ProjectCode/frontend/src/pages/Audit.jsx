import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { actionLabel, shortHash, when } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, PageHeader, SearchField, Select, Table } from '../components/ui'
import { SlideUp } from '../components/motion'
import VerifyChain from '../features/VerifyChain'

export default function Audit() {
  const { data, error, loading, reload } = useAsync(() => api.audit(300), [])
  const [q, setQ] = useState('')
  const [action, setAction] = useState('all')
  const [result, setResult] = useState('all')

  const actions = useMemo(() => [...new Set((data || []).map((e) => e.action))].sort(), [data])
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (data || []).filter(
      (e) =>
        (action === 'all' || e.action === action) &&
        (result === 'all' || (result === 'ok') === e.success) &&
        (!needle || `${e.details} ${e.user_email || ''} ${e.ip_address || ''}`.toLowerCase().includes(needle)),
    )
  }, [data, q, action, result])

  const columns = [
    { key: 'id', label: '#', num: true },
    { key: 'timestamp_utc', label: 'Time', render: (e) => when(e.timestamp_utc) },
    { key: 'action', label: 'Action', render: (e) => actionLabel(e.action) },
    { key: 'user_email', label: 'User', hideSm: true, render: (e) => <span className="break">{e.user_email || 'anonymous'}</span> },
    { key: 'file_id', label: 'File', hideSm: true, render: (e) => (e.file_id ? <Link to={`/app/files/${e.file_id}`} onClick={(ev) => ev.stopPropagation()}>#{e.file_id}</Link> : '-') },
    { key: 'success', label: 'Result', render: (e) => <Badge tone={e.success ? 'safe' : 'danger'} dot>{e.success ? 'Success' : 'Failed'}</Badge>, sortValue: (e) => (e.success ? 1 : 0) },
    { key: 'details', label: 'Details', hideSm: true, sortable: false, render: (e) => <span className="break">{e.details}</span> },
    { key: 'current_hash', label: 'Hash', hideSm: true, sortable: false, render: (e) => <span className="hash" title={`prev ${e.previous_hash}\nthis ${e.current_hash}`}>{shortHash(e.current_hash)}</span> },
  ]

  return (
    <>
      <PageHeader
        crumbs={[{ label: 'Vault', to: '/app' }, { label: 'Audit log' }]}
        title="Audit log"
        description="A hash-chained, tamper-evident record of security events. No file contents, passwords or keys are ever logged."
        actions={
          <Button icon={RefreshCw} onClick={() => reload()}>
            Refresh
          </Button>
        }
      />
      <SlideUp>
        <Card pad className="mt">
          <VerifyChain />
        </Card>
      </SlideUp>
      <SlideUp delay={0.05}>
        <Card className="mt">
          <CardHeader
            title="Events"
            subtitle={data ? `${rows.length} of ${data.length} latest events` : undefined}
            actions={
              <div className="toolbar">
                <SearchField value={q} onChange={setQ} label="Search events" placeholder="Search details, user, IP" />
                <Select labelHidden label="Filter by action" value={action} onChange={(e) => setAction(e.target.value)} options={[{ value: 'all', label: 'All actions' }, ...actions.map((a) => ({ value: a, label: actionLabel(a) }))]} />
                <Select
                  labelHidden
                  label="Filter by result"
                  value={result}
                  onChange={(e) => setResult(e.target.value)}
                  options={[
                    { value: 'all', label: 'Any result' },
                    { value: 'ok', label: 'Success' },
                    { value: 'fail', label: 'Failed' },
                  ]}
                />
              </div>
            }
          />
          {error ? (
            <ErrorState title="Could not load the audit log" error={error} onRetry={reload} />
          ) : (
            <Table
              caption="Audit events"
              columns={columns}
              rows={rows}
              rowKey={(e) => e.id}
              loading={loading}
              pageSize={12}
              initialSort={{ key: 'id', dir: 'desc' }}
              empty={
                <EmptyState title={data?.length ? 'No events match these filters' : 'No events recorded yet'}>
                  {data?.length ? 'Clear a filter or change the search.' : 'Events are recorded as soon as anyone uses the vault.'}
                </EmptyState>
              }
            />
          )}
        </Card>
      </SlideUp>
    </>
  )
}
