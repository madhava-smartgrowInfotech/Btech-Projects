import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, Code2, Play, RotateCcw, XCircle } from 'lucide-react'
import { AsyncView, CardSkeleton, useAction } from '../components/common'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, PageHeader, Select, StatCard, Tabs, Skeleton } from '../components/ui'
import { ChartCard, GroupedBarChart } from '../components/charts'
import { FadeIn } from '../components/motion'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

const show = (v) => (typeof v === 'string' ? JSON.stringify(v) : JSON.stringify(v) ?? String(v))
const TONE = { Easy: 'safe', Medium: 'warn', Hard: 'danger' }

function Practice() {
  const [difficulty, setDifficulty] = useState('All')
  const list = useAsync(() => api.get(`/coding/problems?difficulty=${difficulty}`), [difficulty])
  const [pid, setPid] = useState('')
  const [codes, setCodes] = useState({})
  const [results, setResults] = useState({})
  const { busy, run } = useAction()
  const escaped = useRef(false)

  useEffect(() => {
    if (list.data) setPid((cur) => (list.data.some((p) => String(p.id) === cur) ? cur : String(list.data[0]?.id ?? '')))
  }, [list.data])

  const detail = useAsync(() => api.get(`/coding/problems/${pid}`), [pid], { enabled: !!pid })
  const p = detail.data
  const code = p ? codes[p.id] ?? p.starter_code : ''

  const submit = async () => {
    const r = await run(() => api.post(`/coding/problems/${p.id}/submit`, { code }))
    if (r.ok) {
      setResults((s) => ({ ...s, [p.id]: r.data }))
      list.reload({ quiet: true })
    }
  }
  const result = p ? results[p.id] : null

  // Tab inserts four spaces instead of moving focus out of the editor (Escape then Tab leaves it)
  const onKey = (e) => {
    if (e.key === 'Escape') {
      escaped.current = true
      return
    }
    if (e.key === 'Tab' && escaped.current) {
      escaped.current = false
      return
    }
    if (e.key === 'Tab' && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
      e.preventDefault()
      const t = e.target
      const next = t.value.slice(0, t.selectionStart) + '    ' + t.value.slice(t.selectionEnd)
      const pos = t.selectionStart + 4
      setCodes((s) => ({ ...s, [p.id]: next }))
      requestAnimationFrame(() => t.setSelectionRange(pos, pos))
    }
  }

  return (
    <div className="stack">
      <Card pad spotlight={false}>
        <div className="toolbar" style={{ marginBottom: 0 }}>
          <div style={{ minWidth: 160 }}>
            <Select
              label="Filter by difficulty"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              options={['All', 'Easy', 'Medium', 'Hard'].map((d) => ({ value: d, label: d }))}
            />
          </div>
          <div className="grow">
            {list.data && list.data.length > 0 ? (
              <Select
                label="Choose a problem"
                value={pid}
                onChange={(e) => setPid(e.target.value)}
                options={list.data.map((x) => ({ value: String(x.id), label: `${x.solved ? '✓ ' : ''}${x.title} (${x.difficulty})` }))}
              />
            ) : (
              <span className="faint">{list.loading ? 'Loading problems…' : ''}</span>
            )}
          </div>
        </div>
      </Card>

      {list.error && <ErrorState title="Couldn't load problems" error={list.error} onRetry={list.reload} />}
      {list.data && list.data.length === 0 && (
        <Card>
          <EmptyState icon={Code2} title="No problems match this filter" actions={<Button onClick={() => setDifficulty('All')}>Show all problems</Button>} />
        </Card>
      )}
      {detail.loading && <CardSkeleton rows={6} />}
      {detail.error && <ErrorState title="Couldn't load this problem" error={detail.error} onRetry={detail.reload} />}

      {p && !detail.loading && (
        <div className="split">
          <Card>
            <CardHeader
              title={p.title}
              subtitle={`Concept: ${p.concept_tag} · ${p.test_count} test cases`}
              actions={<Badge tone={TONE[p.difficulty]}>{p.difficulty}</Badge>}
            />
            <div className="card-body">
              <p style={{ whiteSpace: 'pre-wrap' }}>{p.description}</p>
              <div className="field mt">
                <label htmlFor="editor" className="field-label">
                  Your Python solution
                </label>
                <textarea
                  id="editor"
                  className="textarea mono editor"
                  spellCheck={false}
                  value={code}
                  onChange={(e) => setCodes((s) => ({ ...s, [p.id]: e.target.value }))}
                  onKeyDown={onKey}
                  aria-describedby="editor-hint"
                />
                <span id="editor-hint" className="field-hint">
                  Tab indents. Press Escape, then Tab, to leave the editor. Code runs in an isolated process with a 5 second limit.
                </span>
              </div>
              <div className="btn-row mt">
                <Button variant="primary" icon={Play} loading={busy} onClick={submit}>
                  Run &amp; submit
                </Button>
                <Button icon={RotateCcw} onClick={() => setCodes((s) => ({ ...s, [p.id]: p.starter_code }))}>
                  Reset to starter code
                </Button>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader title="Result" subtitle={result ? undefined : 'Submit your code to see test-case results'} />
            <div className="card-body" aria-live="polite">
              {busy && !result && <Skeleton height={80} />}
              {!result && !busy && <EmptyState icon={Play} title="Nothing run yet">Your per-test-case results will appear here.</EmptyState>}
              {result && (
                <FadeIn>
                  {result.error ? (
                    <div className="state error" role="alert" style={{ padding: '20px 8px' }}>
                      <span className="state-icon"><XCircle size={24} aria-hidden="true" /></span>
                      <h3>Execution error</h3>
                      <p>{result.error}</p>
                    </div>
                  ) : (
                    <>
                      <div className="row" style={{ justifyContent: 'space-between' }}>
                        <strong>
                          {result.tests_passed} / {result.tests_total} test cases passed
                        </strong>
                        <Badge tone={result.passed ? 'safe' : 'danger'} dot>
                          {result.passed ? 'All passed' : 'Not yet'}
                        </Badge>
                      </div>
                      {result.passed && <p className="muted" style={{ marginTop: 8 }}>All test cases passed. XP awarded.</p>}
                      <div className="mt">
                        {result.details.map((d, i) => (
                          <div className="test-row" key={i}>
                            {d.passed ? (
                              <CheckCircle2 size={18} aria-label="Passed" style={{ color: 'var(--safe)' }} />
                            ) : (
                              <XCircle size={18} aria-label="Failed" style={{ color: 'var(--danger)' }} />
                            )}
                            <div>
                              <strong>Test {i + 1}</strong>
                              <div className="faint">
                                input <code>{show(d.input)}</code>
                              </div>
                              <div className="faint">
                                expected <code>{show(d.expected)}</code> · got <code>{show(d.actual)}</code>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </FadeIn>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

function Stats() {
  const state = useAsync(() => api.get('/coding/stats'), [])
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(s) => (
        <div className="stack">
          <div className="grid grid-3">
            <StatCard label="Problems attempted" value={s.attempted} icon={Code2} />
            <StatCard label="Problems solved" value={s.solved} icon={CheckCircle2} />
            <StatCard label="Accuracy" value={s.accuracy} format={(v) => `${Math.round(v)}%`} />
          </div>
          <ChartCard title="Recent submissions" subtitle="Tests passed per submission (last 15)">
            {s.recent.length === 0 ? (
              <EmptyState icon={Code2} title="No submissions yet">Solve a problem in the Practice tab and your attempts will chart here.</EmptyState>
            ) : (
              <GroupedBarChart
                data={s.recent.map((r, i) => ({ ...r, label: r.date.slice(5, 16), n: i }))}
                xKey="label"
                yDomain={[0, 'auto']}
                series={[{ key: 'tests_passed', label: 'Tests passed' }]}
              />
            )}
          </ChartCard>
        </div>
      )}
    </AsyncView>
  )
}

export default function Coding() {
  const [tab, setTab] = useState('practice')
  return (
    <>
      <PageHeader title="Coding practice" description="Solve Python problems against test cases in a sandboxed runner." />
      <div className="tab-gap">
        <Tabs
          label="Coding sections"
          value={tab}
          onChange={setTab}
          tabs={[
            { value: 'practice', label: 'Practice' },
            { value: 'stats', label: 'My stats' },
          ]}
        />
      </div>
      {tab === 'practice' ? <Practice /> : <Stats />}
    </>
  )
}
