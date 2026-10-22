import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, MessageSquarePlus, SearchX, Trash2 } from 'lucide-react'
import { Button, EmptyState, ErrorState, Modal, PageHeader, SearchField, SkeletonBlock, Table, useToast } from '../components/ui'
import { SafetyBadge } from '../components/app/Evidence'
import { historyApi } from '../lib/api'
import { fmtDate, pct, plural } from '../lib/format'

export function ConfirmDelete({ target, busy, onCancel, onConfirm }) {
  return (
    <Modal
      open={!!target}
      onClose={busy ? () => {} : onCancel}
      title="Delete this consultation?"
      describedBy="del-desc"
      footer={
        <>
          <Button onClick={onCancel} disabled={busy} data-autofocus>
            Keep it
          </Button>
          <Button variant="danger" icon={Trash2} loading={busy} onClick={onConfirm}>
            Delete
          </Button>
        </>
      }
    >
      <p id="del-desc">
        Consultation <strong>#{target?.id}</strong>
        {target?.top_condition ? ` (${target.top_condition})` : ''} and its saved evidence will be removed from this device. This cannot be undone.
      </p>
    </Modal>
  )
}

export default function History() {
  const toast = useToast()
  const nav = useNavigate()
  const [search, setSearch] = useState('')
  const [state, setState] = useState({ loading: true, error: null, items: [] })
  const [target, setTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback((q) => {
    setState((s) => ({ ...s, loading: true, error: null }))
    return historyApi
      .list(q)
      .then((items) => setState({ loading: false, error: null, items }))
      .catch((e) => {
        setState({ loading: false, error: e, items: [] })
      })
  }, [])

  useEffect(() => {
    document.title = 'History - CareLens AI'
  }, [])

  // Server-side search, debounced.
  useEffect(() => {
    const t = setTimeout(() => load(search.trim()), search ? 300 : 0)
    return () => clearTimeout(t)
  }, [search, load])

  const confirmDelete = async () => {
    setDeleting(true)
    try {
      await historyApi.remove(target.id)
      toast.success(`Consultation #${target.id} deleted.`)
      setTarget(null)
      load(search.trim())
    } catch (e) {
      toast.error(`Could not delete: ${e.message}`)
    } finally {
      setDeleting(false)
    }
  }

  const columns = [
    { key: 'id', label: '#', numeric: true, render: (r) => `#${r.id}` },
    { key: 'symptom_query', label: 'Symptoms', render: (r) => <div className="cell-clip">{r.symptom_query}</div> },
    { key: 'top_condition', label: 'Top condition', render: (r) => <strong>{r.top_condition || '—'}</strong> },
    { key: 'safety_flag', label: 'Safety', render: (r) => <SafetyBadge flag={r.safety_flag} /> },
    { key: 'retrieval_score', label: 'Relevance', numeric: true, render: (r) => pct(r.retrieval_score) },
    { key: 'created_at', label: 'Date', sortValue: (r) => r.created_at, render: (r) => fmtDate(r.created_at) },
    {
      key: 'actions',
      label: 'Actions',
      sortable: false,
      render: (r) => (
        <div className="row-actions" onClick={(e) => e.stopPropagation()}>
          <Button size="sm" icon={Eye} onClick={() => nav(`/history/${r.id}`)} aria-label={`View consultation ${r.id}`}>
            View
          </Button>
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => setTarget(r)} aria-label={`Delete consultation ${r.id}`}>
            Delete
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        eyebrow="History"
        title="Consultations"
        description="Every answer is saved privately on this device. Search by symptom or condition, open a record, or delete it."
        actions={
          <Button variant="primary" to="/assistant" icon={MessageSquarePlus}>
            New consultation
          </Button>
        }
      />
      <div className="history-tools">
        <SearchField value={search} onChange={setSearch} label="Search consultations" placeholder="Search symptoms or condition…" />
        {!state.loading && !state.error && <span className="small mono muted">{plural(state.items.length, 'consultation')}</span>}
      </div>
      {state.loading && !state.items.length ? (
        <SkeletonBlock rows={5} label="Loading consultations" />
      ) : state.error ? (
        <ErrorState title="Could not load your history" error={state.error} onRetry={() => load(search.trim())} />
      ) : (
        <Table
          columns={columns}
          rows={state.items}
          pageSize={8}
          initialSort={{ key: 'created_at', dir: 'desc' }}
          onRowClick={(r) => nav(`/history/${r.id}`)}
          caption="Consultation history"
          empty={
            search ? (
              <EmptyState icon={SearchX} title="No matches" action={<Button onClick={() => setSearch('')}>Clear search</Button>}>
                Nothing matches “{search}”. Try a different symptom or condition.
              </EmptyState>
            ) : (
              <EmptyState
                icon={MessageSquarePlus}
                title="No consultations yet"
                action={
                  <Button variant="primary" to="/assistant" icon={MessageSquarePlus}>
                    Describe your symptoms
                  </Button>
                }
              >
                Ask the assistant a question and the answer is saved here automatically.
              </EmptyState>
            )
          }
        />
      )}
      <ConfirmDelete target={target} busy={deleting} onCancel={() => setTarget(null)} onConfirm={confirmDelete} />
    </>
  )
}
