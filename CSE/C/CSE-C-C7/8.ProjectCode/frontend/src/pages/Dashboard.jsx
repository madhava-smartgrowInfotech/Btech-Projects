import { useState } from 'react'
import { ArrowRight, BookmarkPlus, Compass, Gauge, Hash, Route, Sparkles, Target } from 'lucide-react'
import { Alert, Button, Card, EmptyState, PageHeader, ProgressBar, SkeletonBlock, StatCard, Timeline, useToast } from '../components/ui'
import { CourseCard } from '../components/app/CourseCard'
import { Async, CardSkeletons } from '../components/app/Async'
import { Stagger } from '../components/motion'
import { get, track } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useApi } from '../lib/useApi'
import { EVENT_LABEL, bestAction, fmtDate, fmtPct } from '../lib/format'

function load() {
  return Promise.all([get('/api/recommendations?top_n=4'), get('/api/activity?limit=6')]).then(([recs, activity]) => ({ recs, activity }))
}

export default function Dashboard() {
  const { user } = useAuth()
  const toast = useToast()
  const q = useApi(load, [])
  const [saving, setSaving] = useState('')

  const save = async (id) => {
    setSaving(id)
    try {
      await track(id, 'save')
      toast.success('Saved to your list.')
    } catch (e) {
      toast.error(`Could not save: ${e.message}`)
    } finally {
      setSaving('')
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Dashboard"
        title={`Welcome back, ${user?.name?.split(' ')[0] || 'learner'}`}
        description="Your learning status, the single most useful next action, and the courses that fit you best right now."
        actions={
          <>
            <Button to="/app/path" icon={Route}>
              Learning path
            </Button>
            <Button variant="primary" to="/app/recommendations" icon={Sparkles}>
              All recommendations
            </Button>
          </>
        }
      />
      <Async
        q={q}
        title="Could not load your dashboard"
        skeleton={
          <div className="page-stack">
            <SkeletonBlock rows={3} label="Loading stats" />
            <CardSkeletons n={2} />
          </div>
        }
      >
        {({ recs, activity }) => {
          const best = bestAction(recs.uplift)
          const eng = recs.engagement
          return (
            <>
              <Stagger className="grid grid-4" inView={false}>
                <StatCard label="Learning status" value={eng.label} icon={Gauge} hint={`Engagement score ${fmtPct(eng.score)}`} />
                <StatCard label="Est. success" value={fmtPct(recs.success_probability)} icon={Target} hint="Model estimate for your current state" />
                <StatCard label="Interactions" value={eng.total} icon={Hash} hint="Events recorded so far" />
                <StatCard label="Quizzes done" value={eng.quizzes} icon={Hash} hint={`${eng.completes} course${eng.completes === 1 ? '' : 's'} completed`} />
              </Stagger>
              <div className="two-col">
                <Card title="Recommended next action" tone="lime">
                  {best ? (
                    <div className="stack" style={{ '--gap': '12px' }}>
                      <p className="display-md">{best.label}</p>
                      <p>
                        Estimated benefit <strong>{best.value}</strong>, based on observed learning patterns, not a proven causal effect.
                      </p>
                      <div>
                        <Button variant="secondary" to="/app/insights" iconRight={ArrowRight}>
                          See all action scores
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Alert tone="info">No action scores are available yet.</Alert>
                  )}
                </Card>
                <Card title="Recent activity">
                  {activity.events.length ? (
                    <Timeline
                      items={activity.events.map((e, i) => ({
                        key: i,
                        title: `${EVENT_LABEL[e.event_type] || e.event_type}${e.course_id ? ` · ${e.course_id}` : ''}`,
                        meta: fmtDate(e.at),
                        tone: e.event_type === 'complete' ? 'ok' : e.event_type === 'dismiss' ? 'bad' : undefined,
                      }))}
                    />
                  ) : (
                    <EmptyState
                      icon={Compass}
                      title="No activity yet"
                      action={
                        <Button variant="primary" to="/app/recommendations">
                          Open a recommendation
                        </Button>
                      }
                    >
                      Open, save or start a course and it shows up here.
                    </EmptyState>
                  )}
                </Card>
              </div>
              <section className="stack" aria-labelledby="top-recs">
                <div className="row-between">
                  <h2 id="top-recs" className="display-md">
                    Top picks for you
                  </h2>
                </div>
                <div className="course-grid">
                  {recs.recommendations.map((r) => (
                    <CourseCard key={r.course.id} course={r.course} rec={r}>
                      <Button size="sm" variant="primary" to={`/courses/${r.course.id}`} onClick={() => track(r.course.id, 'open').catch(() => {})}>
                        Open
                      </Button>
                      <Button size="sm" icon={BookmarkPlus} loading={saving === r.course.id} onClick={() => save(r.course.id)}>
                        Save
                      </Button>
                    </CourseCard>
                  ))}
                </div>
              </section>
            </>
          )
        }}
      </Async>
    </div>
  )
}
