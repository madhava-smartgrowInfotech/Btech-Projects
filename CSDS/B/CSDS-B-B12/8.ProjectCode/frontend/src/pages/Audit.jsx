import { useEffect, useState } from 'react'
import api from '../api.js'
import { PageHeader } from '../components/ui/Layout.jsx'
import { Badge, EmptyState, ErrorState, SkeletonBlock, Table } from '../components/ui/index.js'
import { failure, fmtDate } from '../lib/product.js'

const COLUMNS = [
  { key: 'at', label: 'Time', render: (r) => fmtDate(r.at), sortValue: (r) => r.at },
  { key: 'user', label: 'User', render: (r) => r.user || '—' },
  { key: 'action', label: 'Action', render: (r) => <Badge>{r.action}</Badge> },
  { key: 'target', label: 'Target', render: (r) => r.target || '—' },
]

export default function Audit() {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    setRows(null)
    api
      .get('/audit')
      .then((r) => setRows(r.data))
      .catch(async (e) => setError(await failure(e)))
  }
  useEffect(load, [])

  let body
  if (error) body = <ErrorState title="The audit log could not be loaded" error={error.message} onRetry={load} />
  else if (!rows) body = <SkeletonBlock rows={6} label="Loading audit log" />
  else if (rows.length === 0)
    body = <EmptyState title="No activity yet">Sign-ins, patient views, uploads, assistant questions and report downloads will appear here.</EmptyState>
  else body = <Table columns={COLUMNS} rows={rows} initialSort={{ key: 'at', dir: 'desc' }} pageSize={15} caption="Audit log entries" />

  return (
    <div className="page">
      <PageHeader
        eyebrow="Compliance"
        title="Audit log"
        description="Every sign-in, patient access, scan, assistant question and report download (latest 200)."
      />
      {body}
    </div>
  )
}
