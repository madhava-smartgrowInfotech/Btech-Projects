import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, Map as MapIcon, RefreshCw, Send, XCircle } from 'lucide-react'
import { AsyncView, CardSkeleton, StatusBadge, useAction } from '../components/common'
import {
  Badge, Button, Card, CardHeader, EmptyState, ErrorState, Input, PageHeader, ProgressBar, Select, Table, Tabs,
} from '../components/ui'
import { FadeIn } from '../components/motion'
import { STATUS } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

/* ------------------------------------------------------------ assessment */
function Assessment() {
  const list = useAsync(() => api.get('/learning/assessments'), [])
  const [id, setId] = useState('')
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const { busy, run } = useAction()

  useEffect(() => {
    if (list.data?.length && !id) setId(String(list.data[0].id))
  }, [list.data, id])

  const detail = useAsync(() => api.get(`/learning/assessments/${id}`), [id], { enabled: !!id })

  useEffect(() => {
    setAnswers({})
    setResult(null)
  }, [id])

  const questions = detail.data?.questions || []
  const unanswered = questions.filter((q) => !answers[q.id]).length

  const submit = async (e) => {
    e.preventDefault()
    const r = await run(
      () => api.post(`/learning/assessments/${id}/submit`, { answers }),
      (res) => ({ title: `You scored ${res.score}% in ${res.topic}`, message: `+${res.xp_gained} XP. Your knowledge state has been updated.` }),
    )
    if (r.ok) setResult(r.data)
  }

  return (
    <AsyncView state={list} skeleton={<CardSkeleton />}>
      {(items) =>
        items.length === 0 ? (
          <Card>
            <EmptyState title="No assessments available">The database has no assessments yet. Start the backend once to seed the demo data.</EmptyState>
          </Card>
        ) : (
          <Card>
            <CardHeader title="Take a skill assessment" subtitle="Answer every question. Your result updates your skill and topic proficiency." />
            <div className="card-body">
              <div style={{ maxWidth: 420 }}>
                <Select
                  label="Topic to assess"
                  value={id}
                  onChange={(e) => setId(e.target.value)}
                  options={items.map((a) => ({ value: String(a.id), label: `${a.topic} (${a.question_count} questions)` }))}
                />
              </div>
              {detail.loading && <div style={{ marginTop: 18 }}><CardSkeleton rows={4} /></div>}
              {detail.error && <ErrorState title="Couldn't load the questions" error={detail.error} onRetry={detail.reload} />}
              {result && (
                <FadeIn>
                  <div className="row mt" style={{ gap: 24, alignItems: 'center' }} role="status">
                    <div className="ring" style={{ '--v': result.score }}>
                      <span>{Math.round(result.score)}%</span>
                    </div>
                    <div>
                      <h3 style={{ fontSize: 20 }}>
                        {result.correct} of {result.total} correct
                      </h3>
                      <p className="muted" style={{ marginTop: 6 }}>
                        +{result.xp_gained} XP · your {result.topic} proficiency was updated.
                      </p>
                      {result.badge && (
                        <Badge tone="safe" dot className="mt">
                          Badge earned: {result.badge}
                        </Badge>
                      )}
                      <div className="btn-row mt">
                        <Button
                          icon={RefreshCw}
                          onClick={() => {
                            setResult(null)
                            setAnswers({})
                          }}
                        >
                          Retake
                        </Button>
                      </div>
                    </div>
                  </div>
                </FadeIn>
              )}
              {!detail.loading && !detail.error && questions.length > 0 && (
                <form onSubmit={submit} style={{ marginTop: 12 }}>
                  {questions.map((q, i) => {
                    const review = result?.results.find((r) => r.question_id === q.id)
                    return (
                      <fieldset className="question options" key={q.id} style={{ border: 0, padding: '18px 0', margin: 0 }}>
                        <legend style={{ padding: 0 }}>
                          <h3 style={{ font: '600 15.5px/1.5 var(--font-body)', marginBottom: 12 }}>
                            Q{i + 1}. {q.question}
                          </h3>
                        </legend>
                        {Object.entries(q.options).map(([k, text]) => {
                          const state = review ? (k === review.correct ? 'right' : k === review.chosen ? 'wrong' : '') : ''
                          return (
                            <label className={`option ${state}`} key={k}>
                              <input
                                type="radio"
                                name={`q-${q.id}`}
                                value={k}
                                checked={answers[q.id] === k}
                                disabled={!!result}
                                onChange={() => setAnswers((a) => ({ ...a, [q.id]: k }))}
                              />
                              <b>{k}</b>
                              <span>{text}</span>
                              {state === 'right' && <CheckCircle2 size={16} aria-label="Correct answer" style={{ marginLeft: 'auto', color: 'var(--safe)' }} />}
                              {state === 'wrong' && <XCircle size={16} aria-label="Your answer was wrong" style={{ marginLeft: 'auto', color: 'var(--danger)' }} />}
                            </label>
                          )
                        })}
                      </fieldset>
                    )
                  })}
                  {!result && (
                    <div className="btn-row">
                      <Button type="submit" variant="primary" icon={Send} loading={busy} disabled={unanswered > 0}>
                        Submit assessment
                      </Button>
                      {unanswered > 0 && <span className="faint">{unanswered} question{unanswered > 1 ? 's' : ''} left to answer</span>}
                    </div>
                  )}
                </form>
              )}
            </div>
          </Card>
        )
      }
    </AsyncView>
  )
}

/* ------------------------------------------------------------ roadmap */
function Step({ s }) {
  const [open, setOpen] = useState(false)
  const tone = s.priority === 'High' ? 'danger' : s.priority === 'Medium' ? 'warn' : 'neutral'
  return (
    <div className="list-item" style={{ display: 'block', padding: 0 }}>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        style={{ all: 'unset', boxSizing: 'border-box', width: '100%', cursor: 'pointer', padding: '16px 22px', display: 'flex', gap: 14, alignItems: 'center' }}
      >
        <span className="rank">{s.step}</span>
        <span style={{ flex: 1, minWidth: 0 }}>
          <strong>{s.name}</strong>
          <span className="faint" style={{ display: 'block' }}>
            {s.difficulty} · {Math.round(s.estimated_hours)} h · {Math.round(s.completion_percent)}% complete
          </span>
        </span>
        <Badge tone={tone}>{s.priority}</Badge>
        <ChevronDown size={18} aria-hidden="true" style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 200ms' }} />
      </button>
      {open && (
        <div style={{ padding: '0 22px 18px 62px' }}>
          <ProgressBar value={s.completion_percent} max={100} label="Current proficiency" valueLabel={`${Math.round(s.completion_percent)}%`} />
          <dl className="kv mt">
            <dt>Prerequisites</dt>
            <dd>{s.prerequisites.length ? s.prerequisites.join(', ') : 'None'}</dd>
            <dt>Why recommended</dt>
            <dd>{s.explanation}</dd>
          </dl>
          <div className="faint" style={{ marginTop: 10 }}>Recommended resources</div>
          <ul className="bullets">
            {s.recommended_resources.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function Roadmap() {
  const saved = useAsync(() => api.get('/learning/roadmap'), [])
  const [goal, setGoal] = useState('')
  const [result, setResult] = useState(null)
  const { busy, run } = useAction()

  useEffect(() => {
    if (saved.data && !goal) setGoal(saved.data.career_goal || 'Machine Learning Engineer')
  }, [saved.data, goal])

  const generate = async (e) => {
    e.preventDefault()
    const r = await run(() => api.post('/learning/roadmap', { career_goal: goal }), 'Roadmap generated')
    if (r.ok) setResult(r.data)
  }

  return (
    <AsyncView state={saved} skeleton={<CardSkeleton />}>
      {(s) => {
        const steps = result ? result.roadmap : s.roadmap
        const weak = result?.weak_prerequisites || []
        return (
          <div className="stack">
            <Card>
              <CardHeader
                title="AI-generated personalized roadmap"
                subtitle="Graph-based knowledge-state tracking from the base paper, extended with career-goal-aware prioritization."
              />
              <form className="card-body toolbar" onSubmit={generate} style={{ marginBottom: 0 }}>
                <div className="grow">
                  <Input
                    label="Career goal for roadmap generation"
                    list="career-goals"
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    hint="Pick a role from the list or type your own"
                  />
                  <datalist id="career-goals">
                    {s.careers.map((c) => (
                      <option key={c} value={c} />
                    ))}
                  </datalist>
                </div>
                <Button type="submit" variant="primary" icon={RefreshCw} loading={busy} disabled={!goal.trim()}>
                  Generate / refresh roadmap
                </Button>
              </form>
            </Card>

            {weak.length > 0 && (
              <div className="state error" role="status" style={{ alignItems: 'flex-start', textAlign: 'left', padding: '16px 20px', background: 'var(--warn-soft)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div className="row" style={{ flexWrap: 'nowrap', alignItems: 'flex-start' }}>
                  <AlertTriangle size={18} aria-hidden="true" style={{ color: 'var(--warn)', flexShrink: 0, marginTop: 2 }} />
                  <div>
                    <strong>Weak prerequisite topics detected</strong>
                    <div className="muted">{weak.slice(0, 5).map((w) => `${w.name} (${Math.round(w.proficiency)}%)`).join(', ')}</div>
                  </div>
                </div>
              </div>
            )}

            {steps && steps.length ? (
              <Card>
                <CardHeader
                  title={`Roadmap to ${result?.career_goal || s.career_goal || 'your goal'}`}
                  subtitle={`${steps.length} steps · select a step to see details`}
                />
                {steps.map((st) => (
                  <Step key={st.step} s={st} />
                ))}
              </Card>
            ) : (
              <Card>
                <EmptyState icon={MapIcon} title="No roadmap yet">
                  Set a career goal above and generate a roadmap to see your personalized learning path here.
                </EmptyState>
              </Card>
            )}
          </div>
        )
      }}
    </AsyncView>
  )
}

/* ------------------------------------------------------------ progress */
function MarkProgress() {
  const topics = useAsync(() => api.get('/learning/topics'), [])
  const [topicId, setTopicId] = useState('')
  const [pct, setPct] = useState(50)
  const { busy, run } = useAction()

  useEffect(() => {
    if (topics.data?.length && !topicId) setTopicId(String(topics.data[0].id))
  }, [topics.data, topicId])

  const current = topics.data?.find((t) => String(t.id) === topicId)
  useEffect(() => {
    if (current) setPct(Math.round(current.proficiency))
  }, [topicId]) // eslint-disable-line react-hooks/exhaustive-deps

  const update = async (e) => {
    e.preventDefault()
    const r = await run(
      () => api.post('/learning/progress', { topic_id: Number(topicId), completion_percent: pct }),
      (res) => ({ title: `Updated ${res.topic} to ${Math.round(res.completion_percent)}%`, message: res.badge ? `Badge earned: ${res.badge}` : undefined }),
    )
    if (r.ok) topics.reload({ quiet: true })
  }

  return (
    <AsyncView state={topics} skeleton={<CardSkeleton />}>
      {(list) => (
        <div className="split">
          <Card>
            <CardHeader title="Mark topic progress" subtitle="Reaching 85% marks a topic completed and earns XP and a badge." />
            <form className="card-body stack" onSubmit={update} style={{ gap: 18 }}>
              <Select
                label="Topic"
                value={topicId}
                onChange={(e) => setTopicId(e.target.value)}
                options={list.map((t) => ({ value: String(t.id), label: t.name }))}
              />
              <div className="field">
                <label htmlFor="pct" className="field-label">
                  Completion: <strong>{pct}%</strong>
                </label>
                <input id="pct" type="range" min="0" max="100" value={pct} onChange={(e) => setPct(Number(e.target.value))} style={{ accentColor: 'var(--accent)', width: '100%' }} />
              </div>
              <div>
                <Button type="submit" variant="primary" loading={busy}>
                  Update progress
                </Button>
              </div>
            </form>
          </Card>
          <Card>
            <CardHeader title="All topics" subtitle="Current knowledge state" />
            <Table
              caption="Topic knowledge state"
              rows={list}
              rowKey={(r) => r.id}
              pageSize={8}
              columns={[
                { key: 'name', label: 'Topic' },
                { key: 'status', label: 'Status', render: (r) => <StatusBadge map={STATUS} value={r.status} />, sortValue: (r) => r.status },
                { key: 'proficiency', label: 'Proficiency', num: true, render: (r) => `${Math.round(r.proficiency)}%` },
              ]}
            />
          </Card>
        </div>
      )}
    </AsyncView>
  )
}

export default function Learning() {
  const [tab, setTab] = useState('assess')
  return (
    <>
      <PageHeader title="Learning center" description="Assess your skills, follow a personalized roadmap and track topic progress." />
      <div className="tab-gap">
        <Tabs
          label="Learning sections"
          value={tab}
          onChange={setTab}
          tabs={[
            { value: 'assess', label: 'Skill assessment' },
            { value: 'roadmap', label: 'AI roadmap' },
            { value: 'progress', label: 'Mark progress' },
          ]}
        />
      </div>
      {tab === 'assess' && <Assessment />}
      {tab === 'roadmap' && <Roadmap />}
      {tab === 'progress' && <MarkProgress />}
    </>
  )
}
