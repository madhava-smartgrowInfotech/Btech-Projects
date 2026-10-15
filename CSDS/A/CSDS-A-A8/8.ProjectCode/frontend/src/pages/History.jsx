import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { History as HistoryIcon, RefreshCw } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { KIND, fixed, num, when } from '../lib/format'
import { Badge, Button, Card, Drawer, EmptyState, KeyValueList, PageHeader, SearchField, Skeleton, Table, Tabs } from '../components/ui'
import { CardSkeleton, LoadError, ReportCard } from '../components/bio'

function facts(kind, s = {}) {
  if (kind === 'mri') {
    return [
      ['Model', s.model_label],
      ['Tumour detected', s.tumour_detected ? 'Yes' : 'No'],
      ['Area', s.area_mm2 !== undefined ? `${num(s.area_mm2, 1)} mm² (${num(s.area_pixels)} px)` : null],
      ['Share of brain', s.percent_of_brain !== undefined ? `${num(s.percent_of_brain, 2)}%` : null],
      ['Mean confidence', s.mean_confidence !== undefined ? fixed(s.mean_confidence) : null],
      ['Location', s.location],
      s.ground_truth ? ['Dice vs expert mask', fixed(s.ground_truth.dice)] : null,
    ].filter((x) => x && x[1] != null)
  }
  if (kind === 'dna') {
    return [
      ['Sequence', s.sequence ? `${s.sequence.id} · ${num(s.sequence.length)} bp · GC ${s.sequence.gc_percent}%` : null],
      ['Repeat type', s.repeat_type ? `${s.repeat_type.prediction} (confidence ${fixed(s.repeat_type.confidence, 2)})` : null],
      ['Organism class', s.organism_class ? `${s.organism_class.prediction} (confidence ${fixed(s.organism_class.confidence, 2)})` : null],
      ['Exact tandem repeats', s.repeat_scan ? num(s.repeat_scan.length) : null],
    ].filter((x) => x[1] != null)
  }
  const top = s.matches?.[0]
  return [
    ['Loci in query', s.query_loci != null ? num(s.query_loci) : null],
    ['Top candidate', top ? `${top.id} · log10 LR ${fixed(top.log10_lr, 2)}` : null],
    ['Verbal scale', top?.verbal],
    ['Random match probability', s.random_match_probability != null ? Number(s.random_match_probability).toExponential(2) : null],
    ['References with LR > 1', s.candidates_with_positive_support != null ? `${num(s.candidates_with_positive_support)} of ${num(s.database_size)}` : null],
  ].filter((x) => x[1] != null)
}

function Detail({ id }) {
  const q = useAsync(() => api.get(`/history/${id}`), [id])
  if (q.loading) return <CardSkeleton rows={6} />
  if (q.error) return <LoadError title="Could not load this analysis" error={q.error} onRetry={q.reload} />
  const a = q.data
  return (
    <div className="stack" style={{ gap: 16 }}>
      <div className="row">
        <Badge tone={KIND[a.kind]?.tone}>{KIND[a.kind]?.label || a.kind}</Badge>
        <span className="faint">{when(a.created_at)}</span>
      </div>
      <h3 style={{ fontSize: 17 }}>{a.title}</h3>
      <KeyValueList items={facts(a.kind, a.summary)} />
      {a.report ? <ReportCard report={a.report} /> : <p className="faint">No report was stored for this analysis.</p>}
    </div>
  )
}

export default function History() {
  const q = useAsync(() => api.get('/history'), [])
  const [kind, setKind] = useState('all')
  const [search, setSearch] = useState('')
  const [openId, setOpenId] = useState(null)

  const all = q.data || []
  const rows = useMemo(
    () => all.filter((r) => (kind === 'all' || r.kind === kind) && r.title.toLowerCase().includes(search.trim().toLowerCase())),
    [all, kind, search],
  )
  const count = (k) => all.filter((r) => r.kind === k).length

  return (
    <div className="container">
      <PageHeader
        title="History"
        description="Your last 50 analyses. Open one to see its stored results and structured report."
        actions={
          <Button icon={RefreshCw} onClick={() => q.reload()} loading={q.loading && !!q.data}>
            Refresh
          </Button>
        }
      />
      <Card>
        <div className="card-body row" style={{ justifyContent: 'space-between' }}>
          <Tabs
            label="Filter by type"
            value={kind}
            onChange={setKind}
            tabs={[
              { value: 'all', label: `All (${all.length})` },
              { value: 'mri', label: `MRI (${count('mri')})` },
              { value: 'dna', label: `DNA (${count('dna')})` },
              { value: 'str', label: `STR (${count('str')})` },
            ]}
          />
          <SearchField value={search} onChange={setSearch} label="Search analyses" placeholder="Search titles…" className="history-search" />
        </div>
        {q.error ? (
          <LoadError title="Could not load your history" error={q.error} onRetry={q.reload} />
        ) : (
          <Table
            caption="Saved analyses"
            rows={rows}
            loading={q.loading}
            rowKey={(r) => r.id}
            pageSize={10}
            initialSort={{ key: 'created_at', dir: 'desc' }}
            onRowClick={(r) => setOpenId(r.id)}
            empty={
              all.length === 0 ? (
                <EmptyState
                  icon={HistoryIcon}
                  title="No analyses yet"
                  actions={
                    <>
                      <Button as={Link} to="/app/mri" variant="primary">
                        Analyse an MRI slice
                      </Button>
                      <Button as={Link} to="/app/dna">
                        Classify a DNA sequence
                      </Button>
                      <Button as={Link} to="/app/str">
                        Match an STR profile
                      </Button>
                    </>
                  }
                >
                  Every MRI, DNA and STR analysis you run is saved here with its report.
                </EmptyState>
              ) : (
                <EmptyState
                  icon={HistoryIcon}
                  title="Nothing matches"
                  actions={
                    <Button
                      onClick={() => {
                        setKind('all')
                        setSearch('')
                      }}
                    >
                      Clear filters
                    </Button>
                  }
                >
                  No saved analysis matches this filter.
                </EmptyState>
              )
            }
            columns={[
              { key: 'created_at', label: 'When', sortValue: (r) => r.created_at, render: (r) => when(r.created_at) },
              { key: 'kind', label: 'Type', render: (r) => <Badge tone={KIND[r.kind]?.tone}>{KIND[r.kind]?.label || r.kind}</Badge> },
              { key: 'title', label: 'Title' },
            ]}
          />
        )}
      </Card>
      <Drawer open={openId !== null} onClose={() => setOpenId(null)} title="Analysis" side="right">
        {openId !== null && <Detail id={openId} />}
      </Drawer>
    </div>
  )
}
