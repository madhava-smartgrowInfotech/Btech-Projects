import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, FileSearch, FolderOpen, Trash2, UploadCloud } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { when } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, Modal, PageHeader, SearchField, Skeleton, useToast } from '../components/ui'
import { Callout, Disclaimer, PageSkeleton, ReportStatusBadge, ResultsTable, SampleDataButton } from '../components/lab'

function ReportRow({ report, onDelete }) {
  const [open, setOpen] = useState(false)
  const detail = useAsync(() => api.report(report.id), [report.id], { enabled: open })
  const panel = `report-panel-${report.id}`
  return (
    <li className="report-item">
      <div className="report-head">
        <button type="button" className="report-toggle" aria-expanded={open} aria-controls={panel} onClick={() => setOpen((o) => !o)}>
          <ChevronRight size={18} className="chev" aria-hidden="true" />
          <span style={{ minWidth: 0 }}>
            <strong className="break">
              #{report.id} · {report.file_name}
            </strong>
            <span className="faint" style={{ display: 'block', fontSize: 13 }}>
              {when(report.upload_date)} · {(report.file_type || '').toUpperCase()} · {report.test_count} tests
            </span>
          </span>
        </button>
        <div className="report-badges">
          {report.abnormal_count > 0 && <Badge tone="warn">{report.abnormal_count} abnormal</Badge>}
          <ReportStatusBadge status={report.processing_status} />
        </div>
        <div className="report-actions">
          <Button as={Link} to={`/app/analysis/${report.id}`} size="sm" icon={FileSearch}>
            Analysis
          </Button>
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => onDelete(report)} aria-label={`Delete report ${report.file_name}`}>
            Delete
          </Button>
        </div>
      </div>
      {open && (
        <div id={panel} className="report-body">
          {report.error_message && (
            <div style={{ marginBottom: 12 }}>
              <Callout tone="danger" title="Processing failed:">
                {report.error_message}
              </Callout>
            </div>
          )}
          {detail.loading && <Skeleton height={120} radius={12} />}
          {detail.error && <ErrorState title="Could not load the results" error={detail.error} onRetry={detail.reload} />}
          {detail.data && (
            <ResultsTable
              results={detail.data.results}
              pageSize={8}
              caption={`Results for ${report.file_name}`}
              empty={<p className="muted">No test results were extracted for this report.</p>}
            />
          )}
        </div>
      )}
    </li>
  )
}

export default function Reports() {
  const toast = useToast()
  const { data, error, loading, reload } = useAsync(() => api.reports(), [])
  const [query, setQuery] = useState('')
  const [target, setTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const confirmDelete = async () => {
    setDeleting(true)
    try {
      await api.deleteReport(target.id)
      toast({ title: 'Report deleted', message: `${target.file_name} and its results were removed.` })
      setTarget(null)
      reload()
    } catch (err) {
      toast({ title: 'Could not delete the report', message: err.message, tone: 'error' })
    } finally {
      setDeleting(false)
    }
  }

  if (loading) return <PageSkeleton cards={0} />
  if (error) {
    return (
      <div className="container">
        <PageHeader title="My reports" />
        <ErrorState title="Could not load your reports" error={error} onRetry={reload} />
      </div>
    )
  }

  const reports = data || []
  const q = query.trim().toLowerCase()
  const shown = q ? reports.filter((r) => r.file_name.toLowerCase().includes(q) || String(r.id) === q || r.processing_status.toLowerCase().includes(q)) : reports

  return (
    <div className="container">
      <PageHeader
        title="My reports"
        description="Your full upload history. Open a report to see its results, or delete it."
        actions={
          <Button as={Link} to="/app/upload" variant="primary" icon={UploadCloud}>
            Upload report
          </Button>
        }
      />

      {reports.length === 0 ? (
        <Card>
          <EmptyState
            icon={FolderOpen}
            title="No reports uploaded yet"
            actions={
              <>
                <Button as={Link} to="/app/upload" variant="primary" icon={UploadCloud}>
                  Upload a report
                </Button>
                <SampleDataButton onDone={reload} />
              </>
            }
          >
            Reports you upload are kept here with their extracted results.
          </EmptyState>
        </Card>
      ) : (
        <Card>
          <CardHeader title={`${reports.length} report${reports.length === 1 ? '' : 's'}`} actions={<SearchField value={query} onChange={setQuery} label="Search reports" placeholder="Search by name or status…" />} />
          {shown.length === 0 ? (
            <EmptyState title="No reports match your search" actions={<Button onClick={() => setQuery('')}>Clear search</Button>}>
              Try a different file name or status.
            </EmptyState>
          ) : (
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {shown.map((r) => (
                <ReportRow key={r.id} report={r} onDelete={setTarget} />
              ))}
            </ul>
          )}
        </Card>
      )}

      <Modal
        open={!!target}
        onClose={() => !deleting && setTarget(null)}
        title="Delete this report?"
        footer={
          <>
            <Button onClick={() => setTarget(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="danger" icon={Trash2} loading={deleting} onClick={confirmDelete}>
              Delete report
            </Button>
          </>
        }
      >
        <p style={{ margin: 0 }}>
          <strong className="break">{target?.file_name}</strong> and all {target?.test_count} extracted results and insights will be permanently removed. This cannot be undone.
        </p>
      </Modal>

      <div className="mt">
        <Disclaimer />
      </div>
    </div>
  )
}
