import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, Map, PlayCircle } from 'lucide-react'
import { Alert, Badge, Button, Card, EmptyState, PageHeader, ProgressBar, SkeletonBlock, useToast } from '../components/ui'
import { Async } from '../components/app/Async'
import { Stagger } from '../components/motion'
import { get, track } from '../lib/api'
import { useApi } from '../lib/useApi'
import { fmtPct } from '../lib/format'

export default function LearningPath() {
  const q = useApi(() => get('/api/learning-path'), [])
  const toast = useToast()
  const nav = useNavigate()
  const [busy, setBusy] = useState(0)

  const start = async (s) => {
    setBusy(s.step)
    try {
      await track(s.course.id, 'start')
      toast.success(`Step ${s.step} started: ${s.course.title}`)
      nav(`/courses/${s.course.id}`)
    } catch (e) {
      toast.error(`Could not start this step: ${e.message}`)
      setBusy(0)
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Learning path"
        title="Your staged path"
        description="Beginner-friendly courses first, then up the levels, ordered by how well each one fits you."
      />
      <Async q={q} title="Could not load your learning path" skeleton={<SkeletonBlock rows={6} label="Loading path" />}>
        {(p) => (
          <>
            <Card tone="lime">
              <div className="row-between">
                <div className="stack" style={{ '--gap': '6px' }}>
                  <span className="stat-label">Status · {p.engagement.label}</span>
                  <p className="display-md">Next best action: {p.next_action}</p>
                </div>
                <div style={{ minWidth: 200, flex: '0 1 260px' }}>
                  <span className="tiny mono">Engagement {fmtPct(p.engagement.score)}</span>
                  <ProgressBar value={p.engagement.score} label="Engagement" />
                </div>
              </div>
            </Card>
            {p.steps.length ? (
              <Stagger className="path-list" inView={false}>
                {p.steps.map((s) => (
                  <div key={s.step} className="path-step">
                    <div className="path-num" aria-hidden="true">
                      {s.step}
                    </div>
                    <div className="path-body">
                      <div className="row" style={{ '--gap': '8px' }}>
                        <Badge tone="info">Step {s.step}</Badge>
                        <Badge>{s.course.skill_level}</Badge>
                        <Badge tone="upcoming">{s.action}</Badge>
                      </div>
                      <h3>{s.course.title}</h3>
                      <div className="course-meta">
                        <span>
                          <Clock size={14} aria-hidden="true" /> {s.course.duration_hours}h
                        </span>
                        <span>{fmtPct(s.score)} match</span>
                        <span>est. benefit {s.est_benefit}</span>
                      </div>
                      <p>{s.why}</p>
                      <div className="row">
                        <Button size="sm" variant="primary" icon={PlayCircle} loading={busy === s.step} onClick={() => start(s)}>
                          Start step {s.step}
                        </Button>
                        <Button size="sm" variant="ghost" to={`/courses/${s.course.id}`}>
                          Course details
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </Stagger>
            ) : (
              <EmptyState
                icon={Map}
                title="No path yet"
                action={
                  <Button variant="primary" to="/app/profile">
                    Complete your profile
                  </Button>
                }
              >
                A path needs a learner profile to rank courses against.
              </EmptyState>
            )}
            <Alert tone="info">
              Benefits are estimates from observed patterns, not proven causal effects.
            </Alert>
          </>
        )}
      </Async>
    </div>
  )
}
