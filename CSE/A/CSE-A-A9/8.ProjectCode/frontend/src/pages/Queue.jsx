import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, ChevronLeft, ChevronRight, ListChecks, Radar, ShieldCheck, Undo2, Users, X } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useAsync } from '../lib/hooks'
import { fmtDateTime, fmtHour, fmtInt, fmtPct } from '../lib/format'
import { Badge, Button, Card, EmptyState, ErrorState, IconButton, PageHeader, Segmented, Skeleton, StatCard, Table, Tabs, useToast } from '../components/ui'
import { ScoreCell, StatusBadge } from '../components/app'
import { RetrainCard } from '../components/app/RetrainCard'

function QueueList({ kind, onChanged, summary }) {
  const { user } = useAuth()
  const toast = useToast()
  const [state, setState] = useState('pending')
  const [page, setPage] = useState(1)
  const [busy, setBusy] = useState(null)
  const list = useAsync(() => api.queue({ kind, state, page, page_size: 15 }), [kind, state, page, summary?.confirmed, summary?.dismissed])
  const d = list.data
  const can = user?.role === 'moderator'

  const decide = async (row, decision) => {
    setBusy(`${row.id}:${decision}`)
    try {
      const r = await api.decide(kind === 'accounts' ? 'account' : 'cluster', row.id, decision)
      toast({ kind: 'success', title: `${decision === 'confirm' ? 'Confirmed' : 'Dismissed'} ${row.id}`, message: `${r.affected_accounts} account${r.affected_accounts === 1 ? '' : 's'} logged for the next training run.` })
      await onChanged()
      list.reload()
    } catch (e) {
      toast({ kind: 'error', title: 'Decision not saved', message: e.message })
    } finally {
      setBusy(null)
    }
  }

  const actions = (r) =>
    can ? (
      <span className="row" style={{ '--gap': '6px', flexWrap: 'nowrap' }}>
        <IconButton icon={Check} label={`Confirm ${r.id} as fake`} disabled={!!busy} onClick={() => decide(r, 'confirm')} size={18} />
        <IconButton icon={X} label={`Dismiss ${r.id}`} disabled={!!busy} onClick={() => decide(r, 'dismiss')} size={18} />
      </span>
    ) : (
      <span className="muted small">view only</span>
    )

  const columns =
    kind === 'accounts'
      ? [
          { key: 'handle', label: 'Account', sortable: false, render: (r) => <Link className="link-cell" to={`/app/accounts/${r.id}`}>@{r.handle}</Link> },
          { key: 'score', label: 'Fake probability', sortable: false, render: (r) => <ScoreCell score={r.score} threshold={d.threshold} /> },
          { key: 'cluster_id', label: 'Botnet', sortable: false, render: (r) => (r.cluster_id ? <Link className="link-cell" to={`/app/clusters/${r.cluster_id}`}>{r.cluster_id}</Link> : <span className="muted">none</span>) },
          { key: 'flagged_neighbours', label: 'Flagged neighbours', numeric: true, sortable: false, render: (r) => `${r.flagged_neighbours} / ${r.degree}` },
          state === 'pending'
            ? { key: 'act', label: 'Decide', sortable: false, render: actions }
            : { key: 'decision', label: 'Decision', sortable: false, render: (r) => <StatusBadge status={r.decision === 'confirm' ? 'confirmed' : 'dismissed'} /> },
        ]
      : [
          { key: 'id', label: 'Cluster', sortable: false, render: (r) => <Link className="link-cell" to={`/app/clusters/${r.id}`}>{r.id}</Link> },
          { key: 'kind', label: 'Type', sortable: false, render: (r) => <Badge tone={r.kind === 'coordinated' ? 'rose' : 'neutral'}>{r.kind === 'coordinated' ? 'Coordinated' : 'Loose group'}</Badge> },
          { key: 'size', label: 'Accounts', numeric: true, sortable: false },
          { key: 'mean_score', label: 'Avg fake probability', sortable: false, render: (r) => <ScoreCell score={r.mean_score} threshold={d.threshold} /> },
          { key: 'density', label: 'Tie density', numeric: true, sortable: false, render: (r) => fmtPct(r.density, 0) },
          { key: 'peak_hour', label: 'Peak hour', numeric: true, sortable: false, render: (r) => fmtHour(r.peak_hour) },
          state === 'pending'
            ? { key: 'act', label: 'Decide', sortable: false, render: actions }
            : { key: 'decision', label: 'Decision', sortable: false, render: (r) => <StatusBadge status={r.decision === 'confirm' ? 'confirmed' : 'dismissed'} /> },
        ]

  return (
    <Card hover={false}>
      <div className="row between" style={{ marginBottom: 14 }}>
        <Segmented
          name={`state-${kind}`}
          label="Show"
          value={state}
          onChange={(v) => {
            setState(v)
            setPage(1)
          }}
          options={[
            { value: 'pending', label: 'Needs review' },
            { value: 'decided', label: 'Decided' },
          ]}
        />
      </div>
      {list.error && !d ? (
        <ErrorState title="Could not load the queue" error={list.error} onRetry={list.reload} compact />
      ) : !d ? (
        <div className="stack" role="status" aria-label="Loading queue">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} height={44} />
          ))}
        </div>
      ) : (
        <>
          <Table
            caption={`${kind} queue`}
            rowKey={(r) => r.id}
            pageSize={0}
            columns={columns}
            rows={d.items}
            cardTitle={(r) => (kind === 'accounts' ? `@${r.handle}` : r.id)}
            empty={
              <EmptyState
                icon={state === 'pending' ? ShieldCheck : ListChecks}
                tone={state === 'pending' ? 'mint' : 'lavender'}
                title={state === 'pending' ? 'Queue is clear' : 'Nothing decided yet'}
                message={state === 'pending' ? `Every flagged ${kind === 'accounts' ? 'account' : 'cluster'} has a decision.` : 'Decisions you make will be listed here.'}
                action={state === 'decided' ? <Button variant="secondary" onClick={() => setState('pending')}>Back to the queue</Button> : null}
                compact
              />
            }
          />
          {d.total > 0 && (
            <div className="pager">
              <span className="num">
                {(d.page - 1) * 15 + 1}–{Math.min(d.total, d.page * 15)} of {fmtInt(d.total)}
              </span>
              <div className="row" style={{ '--gap': '8px' }}>
                <Button variant="secondary" size="sm" icon={ChevronLeft} disabled={d.page <= 1} onClick={() => setPage(d.page - 1)} aria-label="Previous page">
                  Prev
                </Button>
                <span className="num">
                  Page {d.page} / {d.pages}
                </span>
                <Button variant="secondary" size="sm" iconRight={ChevronRight} disabled={d.page >= d.pages} onClick={() => setPage(d.page + 1)} aria-label="Next page">
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </Card>
  )
}

function DecisionLog({ onChanged }) {
  const { user } = useAuth()
  const toast = useToast()
  const log = useAsync(() => api.decisions(), [])
  const undo = async (r) => {
    try {
      await api.undo(r.id)
      toast({ kind: 'success', title: 'Decision undone', message: `${r.label} is back in the queue.` })
      await onChanged()
      log.reload()
    } catch (e) {
      toast({ kind: 'error', title: 'Could not undo', message: e.message })
    }
  }
  if (log.error && !log.data) return <ErrorState title="Could not load the log" error={log.error} onRetry={log.reload} compact />
  if (!log.data) return <Skeleton height={260} radius={20} />
  return (
    <Card hover={false}>
      <Table
        caption="Decision log"
        rowKey={(r) => r.id}
        pageSize={12}
        searchKeys={['label', 'by', 'note']}
        searchPlaceholder="Search the log"
        cardTitle={(r) => `${r.target_type} ${r.label}`}
        columns={[
          { key: 'at', label: 'When', render: (r) => fmtDateTime(r.at), sortValue: (r) => r.at },
          { key: 'label', label: 'Target', render: (r) => (r.target_type === 'account' ? <Link className="link-cell" to={`/app/accounts/${r.target_id}`}>@{r.label}</Link> : <Link className="link-cell" to={`/app/clusters/${r.target_id}`}>{r.label}</Link>) },
          { key: 'decision', label: 'Decision', render: (r) => <StatusBadge status={r.decision === 'confirm' ? 'confirmed' : 'dismissed'} />, sortValue: (r) => r.decision },
          { key: 'affected_accounts', label: 'Accounts', numeric: true },
          { key: 'by', label: 'By' },
          { key: 'note', label: 'Note', wrap: true, render: (r) => r.note || <span className="muted">–</span> },
          {
            key: 'used',
            label: 'Training',
            sortable: false,
            render: (r) =>
              r.used_in_run ? (
                <Badge tone="lavender">used in run #{r.used_in_run}</Badge>
              ) : user?.role === 'moderator' ? (
                <Button size="sm" variant="ghost" icon={Undo2} onClick={() => undo(r)}>
                  Undo
                </Button>
              ) : (
                <Badge tone="neutral">waiting</Badge>
              ),
          },
        ]}
        rows={log.data.items}
        empty={<EmptyState icon={ListChecks} title="No decisions yet" message="Confirm or dismiss an account or cluster to start the log." compact />}
      />
    </Card>
  )
}

export default function Queue() {
  const [tab, setTab] = useState('accounts')
  const sum = useAsync(() => api.queue({ kind: 'accounts', page_size: 1 }), [])
  const s = sum.data?.summary
  const refresh = async () => {
    await sum.reload()
  }

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader eyebrow="Moderator queue" icon={ShieldCheck} title="Review flagged accounts and botnets" lead="Work from the highest-scoring items down. Every decision is logged and becomes a training label." />
      {sum.error && !s ? (
        <ErrorState title="Could not load the queue" error={sum.error} onRetry={sum.reload} />
      ) : (
        <>
          <div className="grid-kpi">
            <StatCard label="Accounts to review" value={s?.pending_accounts ?? 0} format={fmtInt} icon={Users} tone="peach" />
            <StatCard label="Clusters to review" value={s?.pending_clusters ?? 0} format={fmtInt} icon={Radar} tone="rose" />
            <StatCard label="Confirmed fake" value={s?.confirmed ?? 0} format={fmtInt} icon={Check} tone="lavender" />
            <StatCard label="Dismissed" value={s?.dismissed ?? 0} format={fmtInt} icon={X} tone="mint" />
          </div>
          <div className="grid-2 wide-left">
            <div className="stack">
              <Tabs
                name="queue"
                label="Queue sections"
                value={tab}
                onChange={setTab}
                tabs={[
                  { id: 'accounts', label: 'Accounts', icon: Users },
                  { id: 'clusters', label: 'Botnet clusters', icon: Radar },
                  { id: 'log', label: 'Decision log', icon: ListChecks },
                ]}
              />
              {tab === 'log' ? <DecisionLog onChanged={refresh} /> : <QueueList key={tab} kind={tab} onChanged={refresh} summary={s} />}
            </div>
            <RetrainCard labels={s?.labels_for_next_run ?? 0} onDone={refresh} />
          </div>
        </>
      )}
    </div>
  )
}
