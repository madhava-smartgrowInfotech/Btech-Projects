import { useMemo, useState } from 'react'
import { Fingerprint, Hash, ListChecks, Search, Shuffle, Sigma, Trophy, X } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { fixed, num } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, Input, PageHeader, Skeleton, StatCard, Table, useToast } from '../components/ui'
import { LoadError, ReportCard } from '../components/bio'
import { FadeIn, Stagger } from '../components/motion'

const MIN_LOCI = 3

export default function StrMatch() {
  const toast = useToast()
  const meta = useAsync(() => api.get('/str/loci'), [])
  const [profile, setProfile] = useState({})
  const [note, setNote] = useState('')
  const [sampleBusy, setSampleBusy] = useState(false)
  const [formError, setFormError] = useState('')
  const [phase, setPhase] = useState({ loading: false, error: null, res: null })
  const [open, setOpen] = useState(0)

  const typed = useMemo(() => Object.values(profile).filter((v) => v && v.trim()).length, [profile])
  const { loading, error, res } = phase

  const loadSample = async () => {
    setSampleBusy(true)
    setFormError('')
    try {
      const data = await api.get('/str/sample-query')
      setProfile(data.profile)
      setNote(data.note)
      setPhase({ loading: false, error: null, res: null })
    } catch (e) {
      setFormError(e.message)
    } finally {
      setSampleBusy(false)
    }
  }

  const run = async () => {
    if (typed < MIN_LOCI) {
      setFormError(`Enter genotypes for at least ${MIN_LOCI} loci (you have ${typed}), or load the sample query.`)
      return
    }
    setFormError('')
    setPhase({ loading: true, error: null, res: null })
    try {
      const out = await api.post('/str/match', { profile })
      setOpen(0)
      setPhase({ loading: false, error: null, res: out })
      toast({ title: 'Search complete', message: `Top candidate ${out.matches[0].id}. Saved to your history.` })
    } catch (e) {
      setPhase({ loading: false, error: e, res: null })
    }
  }

  const clear = () => {
    setProfile({})
    setNote('')
    setFormError('')
    setPhase({ loading: false, error: null, res: null })
  }

  const selected = res?.matches[open]

  return (
    <div className="container">
      <PageHeader
        title="STR profile matching"
        description={
          meta.data
            ? `Rank a query genotype against ${num(meta.data.database_size)} synthetic reference profiles with theta-corrected likelihood ratios. Allele frequencies: ${meta.data.frequency_source}.`
            : 'Rank a query genotype over the 20 CODIS core loci against the reference database with likelihood ratios.'
        }
      />
      <div className="split split-str">
        <Card pad className="stack" style={{ gap: 16 }}>
          {meta.loading ? (
            <div className="loci-grid" aria-busy="true" aria-label="Loading loci">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton key={i} height={66} radius={8} />
              ))}
            </div>
          ) : meta.error ? (
            <LoadError title="Could not load the loci" error={meta.error} onRetry={meta.reload} />
          ) : (
            <>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <div>
                  <h2 style={{ fontSize: 16 }}>Query genotype</h2>
                  <p className="faint">
                    Two alleles per locus separated by a slash, e.g. <code>12/14</code>. One value is read as homozygous.
                  </p>
                </div>
                <Button size="sm" icon={Shuffle} loading={sampleBusy} onClick={loadSample}>
                  Sample query
                </Button>
              </div>
              {note && <p className="callout info">{note}</p>}
              <div className="loci-grid" role="group" aria-label="Genotype per locus">
                {meta.data.loci.map((l) => (
                  <Input
                    key={l}
                    label={l}
                    placeholder="e.g. 12/14"
                    value={profile[l] || ''}
                    onChange={(e) => setProfile((p) => ({ ...p, [l]: e.target.value }))}
                    autoComplete="off"
                    spellCheck={false}
                    inputMode="decimal"
                  />
                ))}
              </div>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <Badge tone={typed >= MIN_LOCI ? 'safe' : 'neutral'}>
                  {typed} of {meta.data.loci.length} loci entered
                </Badge>
                {typed < MIN_LOCI && <span className="faint">need at least {MIN_LOCI}</span>}
              </div>
              {formError && (
                <p className="callout danger" role="alert">
                  {formError}
                </p>
              )}
              <div className="row">
                <Button variant="primary" size="lg" icon={Search} loading={loading} onClick={run} style={{ flex: 1 }}>
                  {loading ? 'Searching and writing the report…' : 'Search database'}
                </Button>
                <Button icon={X} disabled={loading || (typed === 0 && !res)} onClick={clear}>
                  Clear
                </Button>
              </div>
            </>
          )}
        </Card>

        <div className="stack">
          {!res && !loading && !error && (
            <Card>
              <EmptyState icon={Fingerprint} title="No search yet">
                Enter at least {MIN_LOCI} loci or load the sample query, then search. You get ranked candidates with likelihood ratios, a per-locus comparison and a structured
                report.
              </EmptyState>
            </Card>
          )}

          {error && <LoadError title="The search failed" error={error} onRetry={run} hint={error.status === 400 ? 'Check the allele values (numbers such as 12 or 9.3) and try again.' : undefined} />}

          {loading && (
            <>
              <div className="grid grid-4" aria-busy="true" aria-label="Running search">
                {[0, 1, 2, 3].map((i) => (
                  <Skeleton key={i} height={112} radius={12} />
                ))}
              </div>
              <Skeleton height={300} radius={12} />
            </>
          )}

          {res && (
            <FadeIn className="stack">
              <Stagger className="grid grid-4">
                <StatCard label="Loci in query" value={res.query_loci} icon={Hash} />
                <StatCard label="Random match probability" value={res.random_match_probability.toExponential(2)} icon={Sigma} tone="info" delta={`theta = ${res.theta}`} />
                <StatCard label="Top log10 LR" value={fixed(res.matches[0].log10_lr, 2)} icon={Trophy} delta={res.matches[0].id} />
                <StatCard label="References with LR > 1" value={res.candidates_with_positive_support} icon={ListChecks} tone="warn" delta={`of ${num(res.database_size)}`} />
              </Stagger>

              <Card>
                <CardHeader title="Ranked candidates" subtitle="Select a row to compare it with the query locus by locus." />
                <Table
                  caption="Ranked candidate references"
                  rows={res.matches.map((m, i) => ({ ...m, rank: i + 1 }))}
                  rowKey={(r) => r.id}
                  pageSize={10}
                  onRowClick={(r) => setOpen(r.rank - 1)}
                  rowClassName={(r) => (r.rank - 1 === open ? 'highlight' : '')}
                  columns={[
                    { key: 'rank', label: '#', num: true },
                    { key: 'id', label: 'Reference', render: (r) => <strong>{r.id}</strong> },
                    { key: 'lr_display', label: 'LR', num: true, sortValue: (r) => r.log10_lr },
                    { key: 'log10_lr', label: 'log10 LR', num: true, render: (r) => fixed(r.log10_lr, 2) },
                    { key: 'loci_matched', label: 'Loci matched', num: true, sortValue: (r) => r.loci_matched, render: (r) => `${r.loci_matched}/${r.loci_compared}` },
                    { key: 'verbal', label: 'Verbal scale', hideSm: true },
                  ]}
                />
              </Card>

              {selected && (
                <Card>
                  <CardHeader title={`Per-locus comparison - ${selected.id}`} subtitle={`${selected.verbal} · ${selected.loci_matched} loci fully matched, ${selected.loci_mismatched} mismatched`} />
                  <div className="card-body">
                    <div className="locus-rows">
                      {selected.loci.map((l) => (
                        <div key={l.locus} className={`locus-row ${l.shared_alleles === 2 ? 'full' : l.shared_alleles === 1 ? 'part' : 'none'}`}>
                          <strong>{l.locus}</strong>
                          <span className="mono">
                            {l.query} vs {l.reference}
                          </span>
                          <span className="faint">LR {l.lr}</span>
                        </div>
                      ))}
                    </div>
                    <p className="faint" style={{ marginTop: 10 }}>
                      Green: both alleles shared. Amber: one allele shared. Red: none shared.
                    </p>
                  </div>
                </Card>
              )}

              <ReportCard report={res.report} />
            </FadeIn>
          )}
        </div>
      </div>
    </div>
  )
}
