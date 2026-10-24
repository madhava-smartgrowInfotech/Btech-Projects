import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Users } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync, useDebounced } from '../lib/hooks'
import { fmtDays, fmtInt } from '../lib/format'
import { Button, Card, EmptyState, ErrorState, PageHeader, Segmented, SearchField, Select, Skeleton, Table } from '../components/ui'
import { ScoreCell, StatusBadge } from '../components/app'

const STATUS = [
  { value: 'all', label: 'Any status' },
  { value: 'pending', label: 'Needs review' },
  { value: 'confirmed', label: 'Confirmed fake' },
  { value: 'dismissed', label: 'Dismissed' },
  { value: 'clear', label: 'Not flagged' },
]
const SORTS = [
  { value: 'score', label: 'Fake probability' },
  { value: 'neighbours', label: 'Flagged neighbours' },
  { value: 'followers', label: 'Followers' },
  { value: 'degree', label: 'Ties' },
  { value: 'age', label: 'Account age' },
]
const CLUSTERS = [
  { value: '', label: 'Any botnet' },
  { value: 'any', label: 'In a cluster' },
  { value: 'none', label: 'Not in a cluster' },
]

export default function Accounts() {
  const [sp, setSp] = useSearchParams()
  const [q, setQ] = useState(sp.get('q') || '')
  const dq = useDebounced(q, 300)
  const status = sp.get('status') || 'all'
  const cluster = sp.get('cluster') || ''
  const sort = sp.get('sort') || 'score'
  const order = sp.get('order') || 'desc'
  const page = Number(sp.get('page') || 1)

  const set = (patch) => {
    const next = new URLSearchParams(sp)
    Object.entries({ page: 1, ...patch }).forEach(([k, v]) => (v === '' || v == null || v === 'all' ? next.delete(k) : next.set(k, v)))
    setSp(next, { replace: true })
  }

  const state = useAsync(() => api.accounts({ q: dq, status: status === 'all' ? '' : status, cluster, sort, order, page, page_size: 25 }), [dq, status, cluster, sort, order, page])
  const d = state.data
  const clusterOptions = cluster && !CLUSTERS.some((c) => c.value === cluster) ? [...CLUSTERS, { value: cluster, label: cluster }] : CLUSTERS

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader eyebrow="Accounts" icon={Users} title="Ranked accounts" lead="Every account with its fake-probability from the graph model. Open one to see the reasons and its neighbourhood." />
      <Card hover={false}>
        <div className="filters">
          <div className="field grow">
            <SearchField
              value={q}
              onChange={(v) => {
                setQ(v)
                set({ q: v })
              }}
              placeholder="Search handle or name"
              label="Search accounts"
            />
          </div>
          <Select label="Status" value={status} options={STATUS} onChange={(e) => set({ status: e.target.value })} />
          <Select label="Botnet" value={cluster} options={clusterOptions} onChange={(e) => set({ cluster: e.target.value })} />
          <Select label="Sort by" value={sort} options={SORTS} onChange={(e) => set({ sort: e.target.value })} />
          <Segmented
            label="Order"
            name="order"
            value={order}
            onChange={(v) => set({ order: v })}
            options={[
              { value: 'desc', label: 'High → low' },
              { value: 'asc', label: 'Low → high' },
            ]}
          />
        </div>
      </Card>

      <Card hover={false}>
        {state.error && !d ? (
          <ErrorState title="Could not load accounts" error={state.error} onRetry={state.reload} compact />
        ) : !d ? (
          <div className="stack" role="status" aria-label="Loading accounts">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} height={44} />
            ))}
          </div>
        ) : (
          <>
            <Table
              caption="Accounts"
              rowKey={(r) => r.id}
              pageSize={0}
              cardTitle={(r) => <Link className="link-cell" to={`/app/accounts/${r.id}`}>@{r.handle}</Link>}
              columns={[
                {
                  key: 'handle',
                  label: 'Account',
                  sortable: false,
                  render: (r) => (
                    <span className="id-cell">
                      <Link to={`/app/accounts/${r.id}`}>@{r.handle}</Link>
                      <small>{r.display_name}</small>
                    </span>
                  ),
                },
                { key: 'score', label: 'Fake probability', sortable: false, render: (r) => <ScoreCell score={r.score} threshold={d.threshold} /> },
                { key: 'status', label: 'Status', sortable: false, render: (r) => <StatusBadge status={r.status} /> },
                { key: 'cluster_id', label: 'Botnet', sortable: false, render: (r) => (r.cluster_id ? <Link className="link-cell" to={`/app/clusters/${r.cluster_id}`}>{r.cluster_id}</Link> : <span className="muted">none</span>) },
                { key: 'flagged_neighbours', label: 'Flagged neighbours', numeric: true, sortable: false, render: (r) => `${r.flagged_neighbours} / ${r.degree}` },
                { key: 'followers', label: 'Followers', numeric: true, sortable: false, render: (r) => fmtInt(r.followers) },
                { key: 'account_age_days', label: 'Age', numeric: true, sortable: false, render: (r) => fmtDays(r.account_age_days) },
              ]}
              rows={d.items}
              empty={
                <EmptyState
                  icon={Users}
                  title="No accounts match"
                  message="Try a different search or clear the filters."
                  action={
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setQ('')
                        setSp({}, { replace: true })
                      }}
                    >
                      Clear filters
                    </Button>
                  }
                  compact
                />
              }
            />
            {d.total > 0 && (
              <div className="pager">
                <span className="num">
                  {(d.page - 1) * d.page_size + 1}–{Math.min(d.total, d.page * d.page_size)} of {fmtInt(d.total)}
                </span>
                <div className="row" style={{ '--gap': '8px' }}>
                  <Button variant="secondary" size="sm" icon={ChevronLeft} disabled={d.page <= 1} onClick={() => set({ page: d.page - 1 })} aria-label="Previous page">
                    Prev
                  </Button>
                  <span className="num">
                    Page {d.page} / {d.pages}
                  </span>
                  <Button variant="secondary" size="sm" iconRight={ChevronRight} disabled={d.page >= d.pages} onClick={() => set({ page: d.page + 1 })} aria-label="Next page">
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  )
}
