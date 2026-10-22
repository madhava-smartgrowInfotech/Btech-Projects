import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Download, Eye, FileJson, FileSearch, ScanSearch } from 'lucide-react'
import { Button, Card, Container, EmptyState, ErrorState, IconButton, PageHeader, SearchField, Table, Tooltip, useToast } from '../components/ui'
import { download, exportPath, api } from '../lib/api'
import { when } from '../lib/format'
import { useAsync } from '../lib/useAsync'

export default function History() {
  const nav = useNavigate()
  const toast = useToast()
  const { data, error, loading, reload } = useAsync(() => api.analyses(), [])
  const [q, setQ] = useState('')

  const rows = useMemo(() => {
    const t = q.trim().toLowerCase()
    return (data || []).filter((a) => !t || `${a.filename} ${a.top_reviewer} ${a.overall_assessment}`.toLowerCase().includes(t))
  }, [data, q])

  const get = async (a, format) => {
    try {
      await download(exportPath(a.id, format), `peerscope_analysis_${a.id}.${format}`)
      toast({ title: `${format.toUpperCase()} exported`, message: `Analysis #${a.id} downloaded.` })
    } catch (e) {
      toast({ title: `Could not export ${format.toUpperCase()}`, message: e.message, tone: 'error' })
    }
  }

  const cols = [
    { key: 'id', label: 'ID', num: true, render: (a) => `#${a.id}` },
    { key: 'filename', label: 'Paper', render: (a) => <span className="break">{a.filename}</span> },
    { key: 'created_at', label: 'Analyzed', hideSm: true, render: (a) => when(a.created_at) },
    { key: 'concern_count', label: 'Concerns', num: true },
    { key: 'recommendation_count', label: 'Recs', num: true, hideSm: true },
    { key: 'top_reviewer', label: 'Top reviewer', hideSm: true, render: (a) => a.top_reviewer || '-' },
    {
      key: 'actions',
      label: '',
      sortable: false,
      render: (a) => (
        <span className="row" style={{ gap: 4, flexWrap: 'nowrap' }} onClick={(e) => e.stopPropagation()}>
          <Tooltip label="Open analysis">
            <IconButton icon={Eye} label={`Open analysis ${a.id}`} size="sm" onClick={() => nav(`/app/analyses/${a.id}`)} />
          </Tooltip>
          <Tooltip label="Export JSON">
            <IconButton icon={FileJson} label={`Export analysis ${a.id} as JSON`} size="sm" onClick={() => get(a, 'json')} />
          </Tooltip>
          <Tooltip label="Export PDF">
            <IconButton icon={Download} label={`Export analysis ${a.id} as PDF`} size="sm" onClick={() => get(a, 'pdf')} />
          </Tooltip>
        </span>
      ),
    },
  ]

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'History' }]}
        title="Analysis history"
        description="Every stored analysis. Reopen one to see the full review, or export it as JSON or PDF."
        actions={
          <Button as={Link} to="/app/analyze" variant="primary" icon={ScanSearch}>
            New analysis
          </Button>
        }
      />
      <Card>
        <div className="toolbar">
          <SearchField value={q} onChange={setQ} label="Search analyses" placeholder="Search by file, reviewer or assessment…" />
          <span className="faint">{data ? `${rows.length} of ${data.length}` : ''}</span>
        </div>
        {error ? (
          <ErrorState title="Could not load history" error={error} onRetry={reload} />
        ) : (
          <Table
            columns={cols}
            rows={rows}
            rowKey={(a) => a.id}
            loading={loading}
            initialSort={{ key: 'id', dir: 'desc' }}
            onRowClick={(a) => nav(`/app/analyses/${a.id}`)}
            caption="Stored analyses"
            empty={
              q ? (
                <EmptyState icon={FileSearch} title="No analyses match your search" actions={<Button onClick={() => setQ('')}>Clear search</Button>}>
                  Nothing in history contains “{q}”.
                </EmptyState>
              ) : (
                <EmptyState
                  icon={FileSearch}
                  title="No analyses yet"
                  actions={
                    <Button as={Link} to="/app/analyze" variant="primary">
                      Analyze your first paper
                    </Button>
                  }
                >
                  Analyses are saved automatically after each run and will appear here.
                </EmptyState>
              )
            }
          />
        )}
      </Card>
    </Container>
  )
}
