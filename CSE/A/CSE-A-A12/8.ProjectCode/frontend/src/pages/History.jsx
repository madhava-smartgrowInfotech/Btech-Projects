import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, Eye, ScanLine, SearchX, History as HistoryIcon } from 'lucide-react'
import { Button, ClassBadge, EmptyState, ErrorState, PageHeader, SearchField, Select, Skeleton, Table, useToast } from '../components/ui'
import { api } from '../lib/api'
import { fmtDateTime, fmtPct, plural } from '../lib/format'
import { useAsync, useDocumentTitle } from '../lib/hooks'

const FILTERS = [
  { value: 'all', label: 'All classes' },
  { value: 'Normal', label: 'Normal' },
  { value: 'Bacterial Pneumonia', label: 'Bacterial Pneumonia' },
  { value: 'Viral Pneumonia', label: 'Viral Pneumonia' },
]

const csvCell = (v) => `"${String(v).replace(/"/g, '""')}"`

export default function History() {
  useDocumentTitle('History')
  const nav = useNavigate()
  const toast = useToast()
  const { data, error, loading, reload } = useAsync(() => api.predictions(), [])
  const [q, setQ] = useState('')
  const [cls, setCls] = useState('all')

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (data || []).filter((r) => (cls === 'all' || r.prediction === cls) && (!needle || r.filename.toLowerCase().includes(needle)))
  }, [data, q, cls])

  const exportCsv = () => {
    const head = ['id', 'filename', 'prediction', 'confidence', 'p_normal', 'p_bacterial', 'p_viral', 'created_at']
    const lines = rows.map((r) =>
      [r.id, r.filename, r.prediction, r.confidence, r.probabilities.Normal, r.probabilities['Bacterial Pneumonia'], r.probabilities['Viral Pneumonia'], r.created_at]
        .map(csvCell)
        .join(','),
    )
    const url = URL.createObjectURL(new Blob([[head.join(','), ...lines].join('\n')], { type: 'text/csv' }))
    const a = Object.assign(document.createElement('a'), { href: url, download: 'pneumodetect-history.csv' })
    a.click()
    URL.revokeObjectURL(url)
    toast.success(`Exported ${plural(rows.length, 'scan')}.`)
  }

  const columns = [
    { key: 'id', label: '#', numeric: true },
    {
      key: 'thumb',
      label: 'Thumbnail',
      sortable: false,
      render: (r) => <img className="thumb" src={r.original_url} alt={`Thumbnail of ${r.filename}`} loading="lazy" />,
    },
    { key: 'filename', label: 'Filename' },
    { key: 'prediction', label: 'Prediction', render: (r) => <ClassBadge label={r.prediction} /> },
    { key: 'confidence', label: 'Confidence', numeric: true, render: (r) => fmtPct(r.confidence) },
    { key: 'created_at', label: 'Date', render: (r) => fmtDateTime(r.created_at) },
    {
      key: 'view',
      label: 'Open',
      sortable: false,
      render: (r) => (
        <Button size="sm" icon={Eye} to={`/app/result/${r.id}`} onClick={(e) => e.stopPropagation()} aria-label={`View scan ${r.id}`}>
          View
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        eyebrow="Records"
        title="Prediction history"
        description="Every analysis the system has run, newest first."
        actions={
          <>
            <Button icon={Download} onClick={exportCsv} disabled={!rows.length}>
              Export CSV
            </Button>
            <Button variant="primary" icon={ScanLine} to="/app/detect">
              New scan
            </Button>
          </>
        }
      />

      {loading && !data ? (
        <div className="stack" role="status" aria-label="Loading history">
          <Skeleton height={48} />
          <Skeleton height={320} />
        </div>
      ) : error ? (
        <ErrorState title="Could not load the history" error={error} onRetry={reload} />
      ) : data.length === 0 ? (
        <EmptyState
          icon={HistoryIcon}
          title="No predictions yet"
          action={
            <Button variant="primary" icon={ScanLine} to="/app/detect">
              Analyze an X-ray
            </Button>
          }
        >
          Analyze a chest X-ray to get started. Every result is saved here.
        </EmptyState>
      ) : (
        <>
          <div className="filter-bar">
            <SearchField value={q} onChange={setQ} label="Search by filename" placeholder="Search filename…" />
            <Select label="Class" value={cls} onChange={(e) => setCls(e.target.value)} options={FILTERS} />
            <span className="small mono" aria-live="polite" style={{ paddingBottom: 12 }}>
              {plural(rows.length, 'scan')}
            </span>
          </div>
          <Table
            caption="Prediction history"
            columns={columns}
            rows={rows}
            initialSort={{ key: 'id', dir: 'desc' }}
            pageSize={10}
            onRowClick={(r) => nav(`/app/result/${r.id}`)}
            empty={
              <EmptyState
                icon={SearchX}
                title="No scans match"
                action={
                  <Button
                    onClick={() => {
                      setQ('')
                      setCls('all')
                    }}
                  >
                    Clear filters
                  </Button>
                }
              >
                Try a different filename or class.
              </EmptyState>
            }
          />
        </>
      )}
    </>
  )
}
