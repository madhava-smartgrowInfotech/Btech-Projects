import { useMemo, useRef, useState } from 'react'
import { Download, Pencil, Plus, Power, Trash2, Upload, Users } from 'lucide-react'
import {
  Badge,
  Button,
  Card,
  Container,
  EmptyState,
  ErrorState,
  IconButton,
  Input,
  Modal,
  PageHeader,
  ProgressBar,
  SearchField,
  Select,
  Table,
  Textarea,
  Tooltip,
  useToast,
} from '../components/ui'
import { api, download, REVIEWERS_CSV } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { useStats } from '../lib/stats'

const BLANK = {
  display_name: '',
  affiliation: '',
  expertise_description: '',
  research_topics: '',
  methods: '',
  keywords: '',
  publication_titles: '',
  current_load: 0,
  maximum_load: 5,
  is_active: true,
  conflict_terms: '',
}

const toPayload = (f) => ({
  display_name: f.display_name.trim(),
  affiliation: f.affiliation || '',
  expertise_description: f.expertise_description || '',
  research_topics: f.research_topics || '',
  methods: f.methods || '',
  keywords: f.keywords || '',
  publication_titles: f.publication_titles || '',
  current_load: Number(f.current_load) || 0,
  maximum_load: Number(f.maximum_load) || 1,
  is_active: !!f.is_active,
  conflict_terms: f.conflict_terms || '',
})

function validate(f) {
  const e = {}
  if (!f.display_name.trim()) e.display_name = 'Display name is required.'
  if (f.maximum_load === '' || Number(f.maximum_load) < 1 || Number(f.maximum_load) > 100) e.maximum_load = 'Enter a maximum load from 1 to 100.'
  if (f.current_load === '' || Number(f.current_load) < 0 || Number(f.current_load) > 100) e.current_load = 'Enter a current load from 0 to 100.'
  return e
}

function ReviewerForm({ initial, onSave, onClose }) {
  const [f, setF] = useState(initial)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [serverError, setServerError] = useState(null)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const editing = !!initial.id

  const submit = async (e) => {
    e.preventDefault()
    const errs = validate(f)
    setErrors(errs)
    if (Object.keys(errs).length) return
    setSaving(true)
    setServerError(null)
    try {
      await onSave(toPayload(f))
    } catch (err) {
      setServerError(err.message)
      setSaving(false)
    }
  }

  return (
    <Modal
      open
      onClose={onClose}
      dismissable={!saving}
      title={editing ? `Edit ${initial.display_name}` : 'Add reviewer'}
      footer={
        <>
          <Button onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button variant="primary" type="submit" form="reviewer-form" loading={saving}>
            {editing ? 'Save changes' : 'Add reviewer'}
          </Button>
        </>
      }
    >
      <form id="reviewer-form" onSubmit={submit} noValidate className="form-grid">
        <Input label="Display name" data-autofocus value={f.display_name} onChange={set('display_name')} error={errors.display_name} maxLength={200} required />
        <Input label="Affiliation" value={f.affiliation} onChange={set('affiliation')} maxLength={300} />
        <div className="full">
          <Textarea label="Expertise description" rows={3} value={f.expertise_description} onChange={set('expertise_description')} hint="Free text. Used for semantic similarity with the paper." />
        </div>
        <Input label="Research topics" value={f.research_topics} onChange={set('research_topics')} hint="Comma separated" />
        <Input label="Methods" value={f.methods} onChange={set('methods')} hint="Comma separated" />
        <div className="full">
          <Input label="Keywords" value={f.keywords} onChange={set('keywords')} hint="Comma separated" />
        </div>
        <div className="full">
          <Input label="Publication titles" value={f.publication_titles} onChange={set('publication_titles')} />
        </div>
        <Input label="Current load" type="number" min="0" max="100" value={f.current_load} onChange={set('current_load')} error={errors.current_load} />
        <Input label="Maximum load" type="number" min="1" max="100" value={f.maximum_load} onChange={set('maximum_load')} error={errors.maximum_load} />
        <Select
          label="Status"
          value={String(f.is_active)}
          onChange={(e) => setF({ ...f, is_active: e.target.value === 'true' })}
          options={[
            { value: 'true', label: 'Active' },
            { value: 'false', label: 'Inactive' },
          ]}
        />
        <Input label="Conflict terms" value={f.conflict_terms} onChange={set('conflict_terms')} hint="Comma separated. Papers mentioning these terms are penalised." />
        {serverError && (
          <p className="field-error full" role="alert">
            {serverError}
          </p>
        )}
      </form>
    </Modal>
  )
}

export default function Reviewers() {
  const toast = useToast()
  const { refresh } = useStats()
  const { data, error, loading, reload } = useAsync(() => api.reviewers(), [])
  const [q, setQ] = useState('')
  const [form, setForm] = useState(null)
  const [del, setDel] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [importing, setImporting] = useState(false)
  const fileRef = useRef(null)

  const rows = useMemo(() => {
    const t = q.trim().toLowerCase()
    return (data || []).filter((r) => !t || `${r.display_name} ${r.affiliation} ${r.research_topics} ${r.methods} ${r.keywords}`.toLowerCase().includes(t))
  }, [data, q])

  const changed = async () => {
    await reload({ quiet: true })
    refresh()
  }

  const save = async (payload) => {
    if (form.id) {
      await api.updateReviewer(form.id, payload)
      toast({ title: 'Reviewer updated', message: `${payload.display_name} was saved.` })
    } else {
      await api.createReviewer(payload)
      toast({ title: 'Reviewer added', message: `${payload.display_name} is now in the directory.` })
    }
    setForm(null)
    await changed()
  }

  const toggle = async (r) => {
    try {
      const { id, ...rest } = r
      await api.updateReviewer(id, { ...rest, is_active: !r.is_active })
      toast({ title: r.is_active ? 'Reviewer deactivated' : 'Reviewer activated', message: `${r.display_name} is now ${r.is_active ? 'inactive' : 'active'}.` })
      await changed()
    } catch (e) {
      toast({ title: 'Could not update reviewer', message: e.message, tone: 'error' })
    }
  }

  const confirmDelete = async () => {
    setDeleting(true)
    try {
      await api.deleteReviewer(del.id)
      toast({ title: 'Reviewer deleted', message: `${del.display_name} was removed.` })
      setDel(null)
      await changed()
    } catch (e) {
      toast({ title: 'Could not delete reviewer', message: e.message, tone: 'error' })
    } finally {
      setDeleting(false)
    }
  }

  const importCsv = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setImporting(true)
    try {
      const r = await api.importReviewers(file)
      toast({ title: 'CSV imported', message: `${r.imported} reviewer${r.imported === 1 ? '' : 's'} added from ${file.name}.` })
      await changed()
    } catch (err) {
      toast({ title: 'Import failed', message: err.message, tone: 'error' })
    } finally {
      setImporting(false)
    }
  }

  const exportCsv = async () => {
    try {
      await download(REVIEWERS_CSV, 'peerscope_reviewers.csv')
      toast({ title: 'CSV exported', message: 'The reviewer directory was downloaded.' })
    } catch (e) {
      toast({ title: 'Could not export CSV', message: e.message, tone: 'error' })
    }
  }

  const cols = [
    {
      key: 'display_name',
      label: 'Reviewer',
      render: (r) => (
        <div>
          <strong>{r.display_name}</strong>
          <div className="faint">{r.affiliation || '-'}</div>
        </div>
      ),
    },
    { key: 'research_topics', label: 'Topics', hideSm: true, sortable: false, render: (r) => <span className="muted">{r.research_topics || '-'}</span> },
    {
      key: 'current_load',
      label: 'Load',
      sortValue: (r) => r.current_load / (r.maximum_load || 1),
      render: (r) => (
        <div style={{ minWidth: 96 }}>
          <ProgressBar value={r.current_load} max={r.maximum_load || 1} label={`${r.current_load} of ${r.maximum_load}`} />
        </div>
      ),
    },
    {
      key: 'is_active',
      label: 'Status',
      sortValue: (r) => (r.is_active ? 1 : 0),
      render: (r) => (
        <Badge tone={r.is_active ? 'safe' : 'warn'} dot>
          {r.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: '',
      sortable: false,
      render: (r) => (
        <span className="row" style={{ gap: 4, flexWrap: 'nowrap' }} onClick={(e) => e.stopPropagation()}>
          <Tooltip label="Edit">
            <IconButton icon={Pencil} label={`Edit ${r.display_name}`} size="sm" onClick={() => setForm(r)} />
          </Tooltip>
          <Tooltip label={r.is_active ? 'Deactivate' : 'Activate'}>
            <IconButton icon={Power} label={`${r.is_active ? 'Deactivate' : 'Activate'} ${r.display_name}`} size="sm" onClick={() => toggle(r)} />
          </Tooltip>
          <Tooltip label="Delete">
            <IconButton icon={Trash2} label={`Delete ${r.display_name}`} size="sm" onClick={() => setDel(r)} />
          </Tooltip>
        </span>
      ),
    },
  ]

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'Reviewers' }]}
        title="Reviewer directory"
        description="The pool PeerScope ranks against. Inactive reviewers are skipped when ‘active only’ is on."
        actions={
          <>
            <input ref={fileRef} type="file" accept=".csv,text/csv" className="sr-only" tabIndex={-1} aria-label="Import reviewers from CSV" onChange={importCsv} />
            <Button icon={Upload} loading={importing} onClick={() => fileRef.current?.click()}>
              Import CSV
            </Button>
            <Button icon={Download} onClick={exportCsv} disabled={!data?.length}>
              Export CSV
            </Button>
            <Button variant="primary" icon={Plus} onClick={() => setForm({ ...BLANK })}>
              Add reviewer
            </Button>
          </>
        }
      />
      <Card>
        <div className="toolbar">
          <SearchField value={q} onChange={setQ} label="Search reviewers" placeholder="Search by name, topic, method…" />
          <span className="faint">{data ? `${rows.length} of ${data.length}` : ''}</span>
        </div>
        {error ? (
          <ErrorState title="Could not load reviewers" error={error} onRetry={reload} />
        ) : (
          <Table
            columns={cols}
            rows={rows}
            rowKey={(r) => r.id}
            loading={loading}
            initialSort={{ key: 'display_name', dir: 'asc' }}
            caption="Reviewer directory"
            empty={
              q ? (
                <EmptyState icon={Users} title="No reviewers match your search" actions={<Button onClick={() => setQ('')}>Clear search</Button>} />
              ) : (
                <EmptyState
                  icon={Users}
                  title="The reviewer directory is empty"
                  actions={
                    <>
                      <Button variant="primary" icon={Plus} onClick={() => setForm({ ...BLANK })}>
                        Add reviewer
                      </Button>
                      <Button icon={Upload} onClick={() => fileRef.current?.click()}>
                        Import CSV
                      </Button>
                    </>
                  }
                >
                  Analyses need at least one reviewer to rank. Add one by hand or import a CSV exported from PeerScope.
                </EmptyState>
              )
            }
          />
        )}
      </Card>

      {form && <ReviewerForm key={form.id ?? 'new'} initial={form} onSave={save} onClose={() => setForm(null)} />}

      <Modal
        open={!!del}
        onClose={() => setDel(null)}
        dismissable={!deleting}
        title="Delete reviewer?"
        footer={
          <>
            <Button onClick={() => setDel(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="danger" icon={Trash2} loading={deleting} onClick={confirmDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p>
          <strong>{del?.display_name}</strong> will be removed from the directory. Stored analyses keep their results, but this reviewer will no longer be ranked. This cannot be undone.
        </p>
      </Modal>
    </Container>
  )
}
