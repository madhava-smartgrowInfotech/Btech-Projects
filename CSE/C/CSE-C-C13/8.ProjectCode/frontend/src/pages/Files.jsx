import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, FileText, FolderOpen, Share2, Trash2, Upload } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { ago, bytes, ROLE } from '../lib/format'
import { Badge, Card, CardHeader, EmptyState, ErrorState, FileDrop, IconButton, PageHeader, ProgressBar, SearchField, Select, Table } from '../components/ui'
import { SlideUp } from '../components/motion'
import ShareModal from '../features/ShareModal'
import { useFileActions } from '../features/useFileActions'

const stop = (fn) => (e) => {
  e.stopPropagation()
  fn()
}

export default function Files({ mode }) {
  const owned = mode === 'owned'
  const navigate = useNavigate()
  const { data, error, loading, reload } = useAsync(() => (owned ? api.files() : api.shared()), [mode])
  const { data: cfg } = useAsync(() => api.config(), [])
  const actions = useFileActions(() => reload({ quiet: true }))
  const [q, setQ] = useState('')
  const [role, setRole] = useState('all')
  const [shareFor, setShareFor] = useState(null)

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (data || []).filter(
      (f) =>
        (role === 'all' || f.effective_role === role) &&
        (!needle || f.original_filename.toLowerCase().includes(needle) || (f.owner_email || '').toLowerCase().includes(needle)),
    )
  }, [data, q, role])

  const maxMb = cfg?.max_upload_mb || 25
  const columns = [
    {
      key: 'original_filename',
      label: 'Name',
      render: (f) => (
        <span className="file-name">
          <span className="file-ico">
            <FileText size={18} aria-hidden="true" />
          </span>
          <span style={{ minWidth: 0 }}>
            <strong>{f.original_filename}</strong>
            <span className="faint">{f.mime_type}</span>
          </span>
        </span>
      ),
    },
    { key: 'original_size', label: 'Size', num: true, render: (f) => bytes(f.original_size) },
    { key: 'effective_role', label: 'Your role', render: (f) => <Badge tone={ROLE[f.effective_role]?.tone}>{ROLE[f.effective_role]?.label || f.effective_role}</Badge> },
    ...(owned ? [] : [{ key: 'owner_email', label: 'Owner', hideSm: true, render: (f) => <span className="break">{f.owner_email}</span> }]),
    { key: 'updated_at', label: 'Updated', hideSm: true, render: (f) => ago(f.updated_at || f.created_at) },
    {
      key: 'actions',
      label: '',
      sortable: false,
      render: (f) => (
        <span className="row-actions">
          <IconButton icon={Download} label={`Decrypt and download ${f.original_filename}`} disabled={actions.busyId === f.id} onClick={stop(() => actions.download(f))} />
          <IconButton icon={FolderOpen} label={`Open details for ${f.original_filename}`} onClick={stop(() => navigate(`/app/files/${f.id}`))} />
          {f.effective_role === 'owner' && (
            <>
              <IconButton icon={Share2} label={`Share ${f.original_filename}`} onClick={stop(() => setShareFor(f))} />
              <IconButton icon={Trash2} label={`Delete ${f.original_filename}`} onClick={stop(() => actions.askDelete(f))} />
            </>
          )}
        </span>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        crumbs={[{ label: 'Vault', to: '/app' }, { label: owned ? 'My files' : 'Shared with me' }]}
        title={owned ? 'My files' : 'Shared with me'}
        description={
          owned ? 'Everything you upload is encrypted in your browser first. The server only ever stores ciphertext.' : 'Files other people granted you access to. Your role decides what you can do.'
        }
      />

      {owned && (
        <SlideUp>
          <Card pad className="mt">
            <FileDrop
              preview={false}
              disabled={!!actions.busyId}
              maxBytes={maxMb * 1024 * 1024}
              label="Drop a file to encrypt and upload"
              hint={`Any file type, up to ${maxMb} MB. Encrypted with AES-256-GCM before it leaves this tab.`}
              onFile={actions.upload}
            />
            {actions.busyId === 'upload' && (
              <div className="upload-status" role="status" aria-live="polite">
                <ProgressBar indeterminate label={`${actions.stage || 'Working'}…`} />
              </div>
            )}
          </Card>
        </SlideUp>
      )}

      <SlideUp delay={0.05}>
        <Card className="mt">
          <CardHeader
            title={owned ? 'Your encrypted files' : 'Files shared with you'}
            subtitle={data ? `${rows.length} of ${data.length} shown` : undefined}
            actions={
              <div className="toolbar">
                <SearchField value={q} onChange={setQ} label="Search files" placeholder="Search files" />
                <Select
                  labelHidden
                  label="Filter by role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  options={[
                    { value: 'all', label: 'All roles' },
                    ...(owned ? [{ value: 'owner', label: 'Owner' }] : [{ value: 'editor', label: 'Editor' }, { value: 'viewer', label: 'Viewer' }]),
                  ]}
                />
              </div>
            }
          />
          {error ? (
            <ErrorState title="Could not load your files" error={error} onRetry={reload}>
              <p className="faint">Check that the backend is running, then try again.</p>
            </ErrorState>
          ) : (
            <Table
              caption={owned ? 'My files' : 'Files shared with me'}
              columns={columns}
              rows={rows}
              rowKey={(f) => f.id}
              loading={loading}
              pageSize={8}
              initialSort={{ key: 'updated_at', dir: 'desc' }}
              onRowClick={(f) => navigate(`/app/files/${f.id}`)}
              empty={
                data && data.length > 0 ? (
                  <EmptyState title="No files match" actions={<button className="btn" onClick={() => (setQ(''), setRole('all'))}>Clear filters</button>}>
                    Try a different name or role filter.
                  </EmptyState>
                ) : owned ? (
                  <EmptyState icon={Upload} title="Your vault is empty">
                    Drop a file in the box above to encrypt and store your first one.
                  </EmptyState>
                ) : (
                  <EmptyState icon={Share2} title="Nothing shared with you yet">
                    When someone shares a file with your email, it appears here with your role on it.
                  </EmptyState>
                )
              }
            />
          )}
        </Card>
      </SlideUp>

      {shareFor && <ShareModal file={shareFor} open onClose={() => setShareFor(null)} onChanged={() => reload({ quiet: true })} />}
      {actions.deleteDialog}
    </>
  )
}
