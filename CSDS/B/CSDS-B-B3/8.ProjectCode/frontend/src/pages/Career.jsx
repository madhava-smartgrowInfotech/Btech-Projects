import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, Sparkles, X } from 'lucide-react'
import { CardSkeleton, useAction } from '../components/common'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, ProgressBar } from '../components/ui'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'

function Rec({ r, isGoal, onGoal, busy }) {
  return (
    <Card pad>
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'nowrap' }}>
        <div style={{ minWidth: 0 }}>
          <div className="row">
            <h2 style={{ fontSize: 20 }}>{r.title}</h2>
            {isGoal && <Badge tone="safe" dot>Your goal</Badge>}
          </div>
          <p className="muted" style={{ marginTop: 6 }}>{r.description}</p>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div className="big-num">{Math.round(r.match_score)}%</div>
          <div className="faint">Overall match</div>
          <div className="faint">{r.avg_salary_lpa}</div>
        </div>
      </div>
      <div className="mt">
        <ProgressBar value={r.skill_match_percent} max={100} label="Skill coverage" valueLabel={`${Math.round(r.skill_match_percent)}%`} />
      </div>
      <div className="grid grid-2 mt">
        <div>
          <strong>Matched skills</strong>
          <div className="chips" style={{ marginTop: 8 }}>
            {r.matched_skills.length ? r.matched_skills.map((s) => <span className="chip ok" key={s}><Check size={12} aria-hidden="true" />{s}</span>) : <span className="faint">None yet</span>}
          </div>
        </div>
        <div>
          <strong>Missing skills</strong>
          <div className="chips" style={{ marginTop: 8 }}>
            {r.missing_skills.length ? r.missing_skills.map((s) => <span className="chip bad" key={s}><X size={12} aria-hidden="true" />{s}</span>) : <span className="faint">None. You are fully equipped.</span>}
          </div>
        </div>
      </div>
      <details className="mt">
        <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Roadmap, projects and interview prep</summary>
        <div className="grid grid-3 mt">
          <div>
            <strong>Suggested certifications</strong>
            <ul className="bullets">{r.suggested_certifications.map((c) => <li key={c}>{c}</li>)}</ul>
          </div>
          <div>
            <strong>Suggested projects</strong>
            <ul className="bullets">{r.suggested_projects.map((c) => <li key={c}>{c}</li>)}</ul>
          </div>
          <div>
            <strong>Interview topics</strong>
            <ul className="bullets">{r.interview_topics.map((c) => <li key={c}>{c}</li>)}</ul>
          </div>
        </div>
      </details>
      <div className="btn-row mt">
        <Button size="sm" onClick={() => onGoal(r.title)} loading={busy} disabled={isGoal}>
          {isGoal ? 'Current career goal' : 'Set as my career goal'}
        </Button>
      </div>
    </Card>
  )
}

export default function Career() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { busy, run } = useAction()

  const fetchRecs = async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await api.get('/career/recommendations?top_n=8'))
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  const setGoal = async (title) => {
    const r = await run(() => api.post('/career/goal', { title }), () => ({ title: `Career goal updated to ${title}`, message: 'Visit Learning to regenerate your roadmap.' }))
    if (r.ok) setData((d) => ({ ...d, career_goal: title }))
  }

  return (
    <>
      <PageHeader
        title="AI career recommendation"
        description="Suggestions based on your current skills and profile. They are a guide to explore, not an absolute decision."
        actions={
          <Button variant="primary" icon={Sparkles} onClick={fetchRecs} loading={loading}>
            {data ? 'Refresh recommendations' : 'Get my career recommendations'}
          </Button>
        }
      />
      {loading && !data && (
        <div className="stack">
          <CardSkeleton rows={6} />
          <CardSkeleton rows={6} />
        </div>
      )}
      {error && <ErrorState title="Couldn't get recommendations" error={error} onRetry={fetchRecs} />}
      {!data && !loading && !error && (
        <Card>
          <EmptyState
            icon={Sparkles}
            title="Your recommendations will appear here"
            actions={<Button variant="primary" onClick={fetchRecs}>Get my career recommendations</Button>}
          >
            SkillVerse compares your skill proficiencies to each role using cosine similarity. Set your skills in your <Link to="/app/profile">profile</Link> or take assessments for better results.
          </EmptyState>
        </Card>
      )}
      {data && (
        <Stagger className="stack">
          {data.recommendations.map((r) => (
            <Rec key={r.title} r={r} isGoal={data.career_goal === r.title} onGoal={setGoal} busy={busy} />
          ))}
        </Stagger>
      )}
      {data && <p className="faint mt">AI-generated suggestions based on your current skills, assessments and interests. Not a guaranteed outcome.</p>}
    </>
  )
}
