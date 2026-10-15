import { useEffect, useState } from 'react'
import { Mic, Play, RotateCcw, Send, X } from 'lucide-react'
import { AsyncView, CardSkeleton, useAction } from '../components/common'
import { Badge, Button, Card, CardHeader, EmptyState, PageHeader, ProgressBar, Select, Textarea } from '../components/ui'
import { ChartCard, Legend, useChartColors } from '../components/charts'
import { MultiLine } from '../components/charts/MultiLine'
import { FadeIn } from '../components/motion'
import { day } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

const METRICS = [
  ['overall_score', 'Overall'],
  ['technical_score', 'Technical'],
  ['communication_score', 'Communication'],
  ['relevance_score', 'Relevance'],
  ['confidence_score', 'Confidence'],
]

function Report({ report, onAgain }) {
  return (
    <FadeIn>
      <div className="stack">
        <Card pad>
          <div className="row" style={{ gap: 24, flexWrap: 'wrap' }} role="status">
            <div className="ring" style={{ '--v': report.overall_score }}>
              <span>{Math.round(report.overall_score)}</span>
            </div>
            <div style={{ flex: 1, minWidth: 220 }}>
              <h2 style={{ fontSize: 22 }}>Interview complete</h2>
              <p className="muted" style={{ marginTop: 6 }}>{report.summary}</p>
              {report.badge && (
                <Badge tone="safe" dot className="mt">
                  Badge earned: {report.badge}
                </Badge>
              )}
            </div>
            <Button icon={RotateCcw} onClick={onAgain}>
              New interview
            </Button>
          </div>
          <div className="kpi-row mt">
            {METRICS.map(([k, label]) => (
              <div className="kpi" key={k}>
                <strong>{Math.round(report[k])}</strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
        </Card>

        <div className="grid grid-3">
          <Card pad>
            <h3 style={{ fontSize: 16 }}>Strengths</h3>
            <p className="muted" style={{ marginTop: 8 }}>{report.strengths}</p>
          </Card>
          <Card pad>
            <h3 style={{ fontSize: 16 }}>Weaknesses</h3>
            <p className="muted" style={{ marginTop: 8 }}>{report.weaknesses}</p>
          </Card>
          <Card pad>
            <h3 style={{ fontSize: 16 }}>Topics to revise</h3>
            <p className="muted" style={{ marginTop: 8 }}>{report.suggested_topics}</p>
          </Card>
        </div>

        <Card>
          <CardHeader title="Your answers and per-question scores" />
          {report.answers.map((a, i) => (
            <div className="list-item" key={i}>
              <div style={{ minWidth: 0, flex: 1 }}>
                <strong>{a.question}</strong>
                <p className="muted" style={{ marginTop: 6 }}>{a.answer.trim() || 'No answer provided'}</p>
                <div style={{ maxWidth: 320, marginTop: 10 }}>
                  <ProgressBar value={a.score} max={100} label="Score" valueLabel={`${Math.round(a.score)}/100`} />
                </div>
              </div>
            </div>
          ))}
        </Card>
      </div>
    </FadeIn>
  )
}

function Setup({ onStart }) {
  const meta = useAsync(() => api.get('/interview/meta'), [])
  const history = useAsync(() => api.get('/interview/history'), [])
  const [f, setF] = useState({ role: '', interview_type: 'Mixed', difficulty: 'Mixed', num_questions: 5 })
  const { busy, run } = useAction()
  const colors = useChartColors()
  const set = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }))

  const start = async (e) => {
    e.preventDefault()
    const role = f.role || meta.data.roles[0]
    const r = await run(() => api.post('/interview/start', { ...f, role, num_questions: Number(f.num_questions) }))
    if (r.ok) onStart({ ...f, role }, r.data.questions)
  }

  const rows = (history.data || []).map((h) => ({ ...h, label: h.Date.slice(5, 10) }))

  return (
    <div className="stack">
      <AsyncView state={meta} skeleton={<CardSkeleton />}>
        {(m) => (
          <Card>
            <CardHeader title="Configure your mock interview" subtitle="Questions come from the role-specific bank, falling back to general questions." />
            <form className="card-body" onSubmit={start}>
              <div className="form-grid-3">
                <Select label="Job role" value={f.role || m.roles[0]} onChange={set('role')} options={m.roles.map((r) => ({ value: r, label: r }))} />
                <Select label="Interview type" value={f.interview_type} onChange={set('interview_type')} options={m.types.map((r) => ({ value: r, label: r }))} />
                <Select label="Difficulty" value={f.difficulty} onChange={set('difficulty')} options={m.difficulties.map((r) => ({ value: r, label: r }))} />
              </div>
              <div className="field mt" style={{ maxWidth: 360 }}>
                <label htmlFor="nq" className="field-label">
                  Number of questions: <strong>{f.num_questions}</strong>
                </label>
                <input id="nq" type="range" min="3" max="8" value={f.num_questions} onChange={set('num_questions')} style={{ accentColor: 'var(--accent)' }} />
              </div>
              <div className="btn-row mt">
                <Button type="submit" variant="primary" icon={Play} loading={busy}>
                  Start interview
                </Button>
              </div>
            </form>
          </Card>
        )}
      </AsyncView>

      <ChartCard
        title="Your past interview performance"
        subtitle="Scores over time"
        height={280}
        legend={rows.length > 0 && <Legend items={[['Overall', 0], ['Technical', 1], ['Communication', 2], ['Relevance', 3]].map(([label, i]) => ({ label, color: colors.series[i] }))} />}
      >
        {history.loading && history.data === undefined ? (
          <CardSkeleton rows={4} />
        ) : history.error ? (
          <EmptyState title="Couldn't load your history">{history.error.message}</EmptyState>
        ) : rows.length === 0 ? (
          <EmptyState icon={Mic} title="No mock interviews taken yet">Start your first interview above. Your scores will chart here.</EmptyState>
        ) : (
          <MultiLine
            data={rows}
            xKey="Date"
            labelFormat={(l) => l.slice(5, 16)}
            series={[
              { key: 'Overall', label: 'Overall' },
              { key: 'Technical', label: 'Technical' },
              { key: 'Communication', label: 'Communication' },
              { key: 'Relevance', label: 'Relevance' },
            ]}
          />
        )}
      </ChartCard>
    </div>
  )
}

export default function Interview() {
  const [session, setSession] = useState(null) // {cfg, questions, answers}
  const [report, setReport] = useState(null)
  const { busy, run } = useAction()

  // each phase (setup, questions, report) starts at the top of the page
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [report, !!session])

  const submit = async (e) => {
    e.preventDefault()
    const { cfg, questions, answers } = session
    const r = await run(
      () =>
        api.post('/interview/submit', {
          role: cfg.role,
          interview_type: cfg.interview_type,
          difficulty: cfg.difficulty,
          answers: questions.map((q) => ({ question_id: q.id, answer: answers[q.id] || '' })),
        }),
      'Interview complete. Your report is ready.',
    )
    if (r.ok) {
      setReport(r.data)
      setSession(null)
    }
  }

  if (report) {
    return (
      <>
        <PageHeader title="Interview report" description="AI-generated feedback from local keyword and semantic scoring." />
        <Report report={report} onAgain={() => setReport(null)} />
      </>
    )
  }

  if (session) {
    const answered = session.questions.filter((q) => (session.answers[q.id] || '').trim()).length
    return (
      <>
        <PageHeader
          title={`${session.cfg.role} · ${session.cfg.interview_type} interview`}
          description={`${session.questions.length} questions. Answer in your own words; longer, specific answers score better.`}
          actions={
            <Button icon={X} onClick={() => setSession(null)}>
              Cancel interview
            </Button>
          }
        />
        <Card>
          <form className="card-body" onSubmit={submit}>
            {session.questions.map((q, i) => (
              <div className="question" key={q.id}>
                <Textarea
                  label={`Q${i + 1}. ${q.question}`}
                  value={session.answers[q.id] || ''}
                  onChange={(e) => setSession((s) => ({ ...s, answers: { ...s.answers, [q.id]: e.target.value } }))}
                  placeholder="Type your answer…"
                />
              </div>
            ))}
            <div className="btn-row">
              <Button type="submit" variant="primary" icon={Send} loading={busy}>
                Submit interview &amp; get AI feedback
              </Button>
              <span className="faint">{answered} of {session.questions.length} answered. Unanswered questions score 0.</span>
            </div>
          </form>
        </Card>
      </>
    )
  }

  return (
    <>
      <PageHeader title="AI mock interview" description="Practise role-specific questions and get scored feedback on technical depth, communication and relevance." />
      <Setup onStart={(cfg, questions) => setSession({ cfg, questions, answers: {} })} />
    </>
  )
}
