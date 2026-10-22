import { Link } from 'react-router-dom'
import { Clock, Star } from 'lucide-react'
import { Badge, Card, ProgressBar } from '../ui'
import { fmtPct } from '../../lib/format'

/** One course in a grid. Optional `rec` (a recommendation row) adds the match bar and reasons. */
export function CourseCard({ course, rec, children }) {
  return (
    <Card as="article" className="course-card" hot>
      <div className="badges">
        <Badge>{course.category}</Badge>
        <Badge tone="info">{course.skill_level}</Badge>
      </div>
      <h3>
        <Link to={`/courses/${course.id}`}>{course.title}</Link>
      </h3>
      <div className="course-meta">
        <span>
          <Clock size={14} aria-hidden="true" /> {course.duration_hours}h
        </span>
        <span>
          <Star size={14} aria-hidden="true" /> {course.rating}
        </span>
        <span>{course.difficulty}</span>
        <span>{course.resource_type}</span>
      </div>
      {rec ? (
        <>
          <div className="match-row">
            <div className="top">
              <span>Match</span>
              <span className="match-pct">{fmtPct(rec.score)}</span>
            </div>
            <ProgressBar value={rec.score} label={`${course.title} match`} />
            <span className="tiny mono muted">Est. success {fmtPct(rec.success_prob)}</span>
          </div>
          <p className="why">{rec.explanation}</p>
          {rec.suggested_action_label && (
            <p className="small muted">
              Suggested action: <strong style={{ color: 'var(--fg)' }}>{rec.suggested_action_label}</strong> (est. benefit {rec.est_benefit})
            </p>
          )}
        </>
      ) : (
        <p className="why muted">{course.description}</p>
      )}
      {children && <div className="foot">{children}</div>}
    </Card>
  )
}
