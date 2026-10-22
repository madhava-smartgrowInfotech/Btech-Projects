import { useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Download, FileCheck2, RefreshCw, Share2, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { actionLabel, ago, bytes, ROLE, when } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, KeyValueList, PageHeader, ProgressBar, Skeleton, Timeline } from '../components/ui'
import { SlideUp } from '../components/motion'
import ShareModal from '../features/ShareModal'
import { useFileActions } from '../features/useFileActions'

async function loadAll(id) {
  const meta = await api.file(id)
  const [perms, audit] = await Promise.all([
    api.permissions(id).catch(() => []),
    meta.effective_role === 'owner' ? api.fileAudit(id).catch(() => []) : Promise.resolve(null),
  ])
  return { meta, perms, audit }
}

export default function FileDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data, error, loading, reload } = useAsync(() => loadAll(id), [id])
  const actions = useFileActions((gone) => (gone ? navigate('/app/files') : reload({ quiet: true })))
  const [shareOpen, setShareOpen] = useState(false)
  const picker = useRef(null)

  const meta = data?.meta
  const role = meta?.effective_role
  const canWrite = role === 'owner' || role === 'editor'

  const crumbs = [{ label: 'Vault', to: '/app' }, { label: role && role !== 'owner' ? 'Shared with me' : 'My files', to: role && role !== 'owner' ? '/app/shared' : '/app/files' }, { label: meta?.original_filename || 'File' }]

  if (error) {
    return (
      <>
        <PageHeader crumbs={crumbs} title="File" />
        <ErrorState title={error.status === 403 ? 'You do not have access to this file' : error.status === 404 ? 'File not found' : 'Could not load this file'} error={error} onRetry={error.status === 403 || error.status === 404 ? undefined : reload}>
          <Link to="/app/files" className="btn">
            Back to my files
          </Link>
        </ErrorState>
      </>
    )
  }

  const pick = (e) => {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (f) actions.replace(meta.id, f)
  }

  return (
    <>
      <PageHeader
        crumbs={crumbs}
        title={meta?.original_filename || 'Loading file…'}
        description={meta ? `${bytes(meta.original_size)} · ${meta.mime_type}` : undefined}
        actions={
          meta && (
            <>
              <Button variant="primary" icon={Download} loading={actions.busyId === meta.id} onClick={() => actions.download(meta)}>
                Decrypt &amp; download
              </Button>
              {role === 'owner' && (
                <Button icon={Share2} onClick={() => setShareOpen(true)}>
                  Share
                </Button>
              )}
              {canWrite && (
                <>
                  <input ref={picker} type="file" hidden onChange={pick} aria-label="Choose replacement file" />
                  <Button icon={RefreshCw} loading={actions.busyId === 'replace'} onClick={() => picker.current?.click()}>
                    Replace content
                  </Button>
                </>
              )}
              {role === 'owner' && (
                <Button variant="danger" icon={Trash2} onClick={() => actions.askDelete(meta)}>
                  Delete
                </Button>
              )}
            </>
          )
        }
      />

      {actions.busyId === 'replace' && (
        <div className="upload-status" role="status" aria-live="polite">
          <ProgressBar indeterminate label={`${actions.stage || 'Working'}…`} />
        </div>
      )}

      <div className="detail-grid mt">
        <div className="stack">
          <SlideUp>
            <Card>
              <CardHeader title="Details" />
              <div className="card-body">
                {loading ? (
                  <div aria-busy="true">
                    {[0, 1, 2, 3, 4].map((i) => (
                      <Skeleton key={i} height={18} style={{ margin: '14px 0' }} />
                    ))}
                  </div>
                ) : (
                  <KeyValueList
                    items={[
                      ['Your role', <Badge tone={ROLE[role]?.tone}>{ROLE[role]?.label || role}</Badge>],
                      ['Owner', <span className="break">{meta.owner_name ? `${meta.owner_name} (${meta.owner_email})` : meta.owner_email}</span>],
                      ['Plaintext size', bytes(meta.original_size)],
                      ['Stored (ciphertext)', bytes(meta.encrypted_size)],
                      ['Created', when(meta.created_at)],
                      ['Last updated', when(meta.updated_at)],
                      ['SHA-256 of plaintext', <span className="hash">{meta.plaintext_sha256}</span>],
                      ['AES-GCM IV', <span className="hash">{meta.iv}</span>],
                    ]}
                  />
                )}
              </div>
            </Card>
          </SlideUp>
          <SlideUp delay={0.05}>
            <div className="callout">
              <FileCheck2 size={18} aria-hidden="true" />
              <span>
                <strong>Integrity is checked on every download.</strong> The ciphertext is authenticated by AES-GCM, then the decrypted bytes are compared with the stored SHA-256. If either check fails, the file is not saved.
              </span>
            </div>
          </SlideUp>
        </div>

        <div className="stack">
          <SlideUp delay={0.05}>
            <Card>
              <CardHeader title="Access list" subtitle={data ? `${data.perms.length} ${data.perms.length === 1 ? 'person' : 'people'}` : undefined} />
              <div className="card-body">
                {loading ? (
                  <Skeleton height={40} />
                ) : data.perms.length ? (
                  data.perms.map((p) => (
                    <div className="access-row" key={p.user_id}>
                      <div style={{ minWidth: 0 }}>
                        <strong className="break">{p.user_email}</strong>
                        <div className="faint">{p.user_name}</div>
                      </div>
                      <Badge tone={ROLE[p.role]?.tone}>{ROLE[p.role]?.label || p.role}</Badge>
                    </div>
                  ))
                ) : (
                  <EmptyState title="Access list unavailable" />
                )}
                {role === 'owner' && data && data.perms.length === 1 && (
                  <p className="faint" style={{ marginTop: 10 }}>
                    Only you can open this file.
                  </p>
                )}
              </div>
            </Card>
          </SlideUp>

          {role === 'owner' && (
            <SlideUp delay={0.1}>
              <Card>
                <CardHeader title="File history" subtitle="Owner-only view of audit events for this file" />
                <div className="card-body">
                  {loading ? (
                    <Skeleton height={80} />
                  ) : data.audit?.length ? (
                    <Timeline
                      items={data.audit.slice(0, 12).map((a) => ({
                        key: a.id,
                        title: actionLabel(a.action),
                        tone: a.success ? 'safe' : 'danger',
                        meta: `${ago(a.timestamp_utc)} · ${a.user_email || 'system'}`,
                        body: a.details,
                      }))}
                    />
                  ) : (
                    <EmptyState title="No events yet" />
                  )}
                </div>
              </Card>
            </SlideUp>
          )}
        </div>
      </div>

      {meta && role === 'owner' && <ShareModal file={meta} open={shareOpen} onClose={() => setShareOpen(false)} onChanged={() => reload({ quiet: true })} />}
      {actions.deleteDialog}
    </>
  )
}
