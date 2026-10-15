import { useState } from 'react'
import { Dna as DnaIcon, FlaskConical, Layers, Percent, Play, Repeat, Ruler, X } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { fixed, num } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, KeyValueList, PageHeader, Skeleton, StatCard, Table, Textarea, useToast } from '../components/ui'
import { LoadError, ProbBars, ReportCard } from '../components/bio'
import { FadeIn, Stagger } from '../components/motion'

export default function Dna() {
  const toast = useToast()
  const samples = useAsync(() => api.get('/dna/samples'), [])
  const [seq, setSeq] = useState('')
  const [picked, setPicked] = useState(null)
  const [phase, setPhase] = useState({ loading: false, error: null, res: null })

  const sampleList = samples.data || []
  const clean = seq.trim()

  const run = async () => {
    setPhase({ loading: true, error: null, res: null })
    try {
      const res = await api.post('/dna/classify', { sequence: clean })
      setPhase({ loading: false, error: null, res })
      toast({ title: 'Sequence classified', message: 'The analysis was saved to your history.' })
    } catch (error) {
      setPhase({ loading: false, error, res: null })
    }
  }

  const choose = (s) => {
    setSeq(s.sequence)
    setPicked(s.name)
    setPhase({ loading: false, error: null, res: null })
  }

  const { loading, error, res } = phase

  return (
    <div className="container">
      <PageHeader
        title="DNA analysis"
        description="Paste a DNA sequence (raw bases or FASTA). The k-mer JEPA encoder classifies its STR repeat type and organism class, and an exact scan lists the tandem repeats."
      />
      <div className="split split-dna">
        <Card pad className="stack" style={{ gap: 16 }}>
          <Textarea
            label="Sequence"
            mono
            rows={9}
            value={seq}
            onChange={(e) => {
              setSeq(e.target.value)
              setPicked(null)
            }}
            placeholder={'>read_1\nACGTTGCA…'}
            spellCheck={false}
            hint="A, C, G, T and N only. 20 to 20,000 bases; FASTA header optional."
          />
          <div>
            <span className="field-label" style={{ display: 'block', marginBottom: 8 }}>
              Sample sequences
            </span>
            {samples.loading ? (
              <div className="chips" aria-busy="true">
                {[120, 150, 140, 130].map((w, i) => (
                  <Skeleton key={i} width={w} height={30} radius={999} />
                ))}
              </div>
            ) : samples.error ? (
              <LoadError title="Could not load the samples" error={samples.error} onRetry={samples.reload} />
            ) : (
              <div className="chips">
                {sampleList.map((s) => (
                  <button key={s.name} type="button" className="chip" aria-pressed={picked === s.name} onClick={() => choose(s)}>
                    {s.name}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="row">
            <Button variant="primary" size="lg" icon={Play} loading={loading} disabled={!clean} onClick={run} style={{ flex: 1 }}>
              {loading ? 'Classifying and writing the report…' : 'Classify sequence'}
            </Button>
            <Button
              icon={X}
              disabled={!seq || loading}
              onClick={() => {
                setSeq('')
                setPicked(null)
                setPhase({ loading: false, error: null, res: null })
              }}
            >
              Clear
            </Button>
          </div>
        </Card>

        <div className="stack">
          {!res && !loading && !error && (
            <Card>
              <EmptyState icon={DnaIcon} title="No sequence analysed yet">
                Paste a sequence or click a sample, then classify it. You get the repeat type, the organism class, an exact tandem-repeat scan and a structured report.
              </EmptyState>
            </Card>
          )}

          {error && <LoadError title="The sequence could not be analysed" error={error} onRetry={clean ? run : undefined} hint={error.status === 400 ? 'Fix the sequence or check that the DNA models are installed on the server, then try again.' : undefined} />}

          {loading && (
            <>
              <div className="grid grid-4" aria-busy="true" aria-label="Running analysis">
                {[0, 1, 2, 3].map((i) => (
                  <Skeleton key={i} height={112} radius={12} />
                ))}
              </div>
              <Skeleton height={220} radius={12} />
            </>
          )}

          {res && (
            <FadeIn className="stack">
              <Stagger className="grid grid-4">
                <StatCard label="Length" value={res.sequence.length} format={(v) => `${num(v)} bp`} icon={Ruler} delta={res.sequence.id} />
                <StatCard label="GC content" value={res.sequence.gc_percent} format={(v) => `${num(v, 1)}%`} icon={Percent} />
                <StatCard label="Windows analysed" value={res.sequence.windows_analysed} icon={Layers} delta="99 bp, 96 4-mer tokens each" />
                <StatCard label="Exact repeats found" value={res.repeat_scan.length} icon={Repeat} tone="info" />
              </Stagger>

              <div className="grid grid-2">
                <Card>
                  <CardHeader
                    title="STR repeat type"
                    subtitle={`Strongest window #${res.repeat_type.strongest_window} · model held-out accuracy ${fixed(res.repeat_type.model_test_accuracy)}`}
                  />
                  <div className="card-body stack" style={{ gap: 14 }}>
                    <div className="row" style={{ justifyContent: 'space-between' }}>
                      <span className="big-label" style={{ color: 'var(--accent)' }}>
                        {res.repeat_type.prediction}
                      </span>
                      <Badge tone="info">confidence {fixed(res.repeat_type.confidence, 2)}</Badge>
                    </div>
                    <ProbBars probs={res.repeat_type.probabilities} best={res.repeat_type.prediction} />
                  </div>
                </Card>
                <Card>
                  <CardHeader
                    title="Organism class"
                    subtitle={`Model held-out accuracy ${fixed(res.organism_class.model_test_accuracy)} (chance ${fixed(res.organism_class.chance_accuracy)})`}
                  />
                  <div className="card-body stack" style={{ gap: 14 }}>
                    <div className="row" style={{ justifyContent: 'space-between' }}>
                      <span className="big-label">{res.organism_class.prediction}</span>
                      <Badge tone="warn">low reliability</Badge>
                    </div>
                    <ProbBars probs={res.organism_class.probabilities} best={res.organism_class.prediction} />
                    <p className="callout">{res.organism_class.note}</p>
                  </div>
                </Card>
              </div>

              <Card>
                <CardHeader title="Tandem repeats (exact scan)" subtitle="Motifs of 2-6 bases repeated at least 4 times in a row." />
                <Table
                  caption="Tandem repeats found by the exact scan"
                  rows={res.repeat_scan}
                  rowKey={(r) => `${r.start}-${r.motif}`}
                  pageSize={8}
                  empty={
                    <EmptyState icon={FlaskConical} title="No exact tandem repeats">
                      This sequence has no 2-6 base motif repeated four or more times in a row.
                    </EmptyState>
                  }
                  columns={[
                    { key: 'motif', label: 'Motif', render: (r) => <code>{r.motif}</code> },
                    { key: 'period', label: 'Period', num: true },
                    { key: 'start', label: 'Position', num: true, sortValue: (r) => r.start, render: (r) => `${r.start}-${r.end}` },
                    { key: 'copies', label: 'Copies', num: true },
                  ]}
                />
              </Card>

              <Card>
                <CardHeader title="Sequence details" />
                <div className="card-body">
                  <KeyValueList
                    items={[
                      ['Identifier', res.sequence.id],
                      ['Base counts', Object.entries(res.sequence.counts).map(([b, n]) => `${b} ${num(n)}`).join(' · ')],
                      ['Reverse complement (first 60)', <code key="rc" className="break">{res.sequence.reverse_complement_preview}</code>],
                    ]}
                  />
                  {res.analysis_id && (
                    <p className="faint" style={{ marginTop: 12 }}>
                      Saved to history #{res.analysis_id}.
                    </p>
                  )}
                </div>
              </Card>

              <ReportCard report={res.report} />
            </FadeIn>
          )}
        </div>
      </div>
    </div>
  )
}
