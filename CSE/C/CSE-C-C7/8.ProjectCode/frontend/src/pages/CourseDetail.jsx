import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { BookmarkPlus, CheckCircle2, ClipboardCheck, FileCheck2, LogIn, MessagesSquare, PlayCircle, Target } from 'lucide-react'
import { Alert, Badge, Breadcrumbs, Button, Card, ErrorState, KeyValueList, PageHeader, ProgressBar, SkeletonBlock, useToast } from '../components/ui'
import { get, track } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useApi } from '../lib/useApi'
import { fmtPct, splitList } from '../lib/format'

const ACTIONS = [
  { type: 'start', label: 'Start learning', icon: PlayCircle, variant: 'primary', done: 'Course started. Progress is tracked.' },
  { type: 'save', label: 'Save course', icon: BookmarkPlus, done: 'Saved to your list.' },
  { type: 'content', label: 'Content reviewed', icon: FileCheck2, done: 'Content review logged.' },
  { type: 'quiz', label: 'Log a quiz', icon: ClipboardCheck, done: 'Quiz activity logged.' },
  { type: 'forum', label: 'Log a discussion', icon: MessagesSquare, done: 'Discussion logged.' },
  { type: 'complete', label: 'Mark complete', icon: CheckCircle2, done: 'Marked complete. Your recommendations will adapt.' },
]

export default function CourseDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const toast = useToast()
  const q = useApi(() => get(`/api/courses/${encodeURIComponent(id)}`), [id, user?.id])
  const [busy, setBusy] = useState('')
  const [done, setDone] = useState({})
  const viewed = useRef('')

  // Opening a course counts as a "view" event for signed-in learners.
  useEffect(() => {
    if (!user || !q.data || viewed.current === `${user.id}:${id}`) return
    viewed.current = `${user.id}:${id}`
    track(id, 'view').catch(() => {})
  }, [user, q.data, id])

  useEffect(() => setDone({}), [id])

  const act = async (a) => {
    setBusy(a.type)
    try {
      await track(id, a.type)
      setDone((d) => ({ ...d, [a.type]: true }))
      toast.success(a.done)
    } catch (e) {
      toast.error(`Could not log "${a.label}": ${e.message}`)
    } finally {
      setBusy('')
    }
  }

  if (q.loading && !q.data) {
    return (
      <div className="container" style={{ paddingTop: 36 }}>
        <SkeletonBlock rows={6} label="Loading course" />
      </div>
    )
  }
  if (q.error && !q.data) {
    return (
      <div className="container" style={{ paddingTop: 36 }}>
        <ErrorState
          title={q.error.status === 404 ? 'Course not found' : 'Could not load this course'}
          error={q.error}
          hint={q.error.status === 404 ? 'That course id is not in the catalog.' : undefined}
          onRetry={q.error.status === 404 ? undefined : q.reload}
        />
        <p style={{ marginTop: 20, textAlign: 'center' }}>
          <Button to="/courses">Back to the catalog</Button>
        </p>
      </div>
    )
  }

  const c = q.data
  const matched = typeof c.match_score === 'number'
  return (
    <div className="container" style={{ paddingTop: 36, paddingBottom: 64 }}>
      <PageHeader
        crumbs={
          <Breadcrumbs
            items={[{ label: 'Courses', to: '/courses' }, { label: c.category, to: `/courses?category=${encodeURIComponent(c.category)}` }, { label: c.id }]}
          />
        }
        eyebrow={`${c.category} · ${c.skill_level}`}
        title={c.title}
        description={c.description}
      />
      <div className="detail-grid">
        <div className="stack" style={{ '--gap': '24px' }}>
          <Card title="Course facts">
            <KeyValueList
              items={[
                { label: 'Duration', value: `${c.duration_hours} hours` },
                { label: 'Difficulty', value: c.difficulty },
                { label: 'Format', value: c.resource_type },
                { label: 'Rating', value: `${c.rating} / 5` },
                { label: 'Topic', value: c.topic },
                { label: 'Prerequisites', value: c.prerequisites },
              ]}
            />
          </Card>
          <Card title="You will learn">
            <ul className="bullet-list">
              {splitList(c.outcomes).map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
            <div className="row" style={{ marginTop: 18, '--gap': '6px' }}>
              {splitList(c.tags).map((t) => (
                <Badge key={t}>{t}</Badge>
              ))}
            </div>
          </Card>
        </div>
        <div className="stack" style={{ '--gap': '24px' }}>
          {matched && (
            <Card title="Why it is recommended" tone="lime">
              <div className="stack" style={{ '--gap': '10px' }}>
                <div className="row-between">
                  <span className="stat-label">Match</span>
                  <span className="match-pct">{fmtPct(c.match_score)}</span>
                </div>
                <ProgressBar value={c.match_score} label="Match score" />
                <p>{c.explanation}</p>
                <p className="small">
                  Estimated success {fmtPct(c.success_prob)} · suggested action <strong>{c.suggested_action}</strong> (est. benefit {c.est_benefit})
                </p>
              </div>
            </Card>
          )}
          <Card title="Your progress">
            {user ? (
              <div className="action-grid">
                {ACTIONS.map((a) => (
                  <Button
                    key={a.type}
                    variant={a.variant || 'secondary'}
                    icon={done[a.type] ? CheckCircle2 : a.icon}
                    loading={busy === a.type}
                    disabled={Boolean(busy)}
                    onClick={() => act(a)}
                  >
                    {a.label}
                  </Button>
                ))}
              </div>
            ) : (
              <div className="stack">
                <Alert tone="info">Sign in to log progress and see how this course ranks for your profile.</Alert>
                <div className="row">
                  <Button variant="primary" to="/login" state={{ from: `/courses/${id}` }} icon={LogIn}>
                    Sign in
                  </Button>
                  <Button to="/register">Create account</Button>
                </div>
              </div>
            )}
            {user && (
              <p className="small muted" style={{ marginTop: 14 }}>
                Every action is logged and changes your next recommendations.{' '}
                <Link className="link-plain" to="/app/recommendations">
                  See them
                </Link>
              </p>
            )}
          </Card>
          {!user && (
            <Card flat>
              <div className="row">
                <Target size={22} aria-hidden="true" />
                <span className="small">Course details are public; personalization needs a profile.</span>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
