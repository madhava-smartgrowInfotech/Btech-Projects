import { useEffect, useState } from 'react'
import { Medal, Save } from 'lucide-react'
import { AsyncView, PageSkeleton, useAction } from '../components/common'
import { Badge, Button, Card, CardHeader, Input, PageHeader, Select, StatCard, Textarea } from '../components/ui'
import { Zap, Flame, Award } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { day } from '../lib/format'

function StudentProfile({ d, reload }) {
  const [f, setF] = useState(d.profile)
  const [skills, setSkills] = useState(() => Object.fromEntries(d.skills.map((s) => [s.skill_id, Math.round(s.proficiency)])))
  const profileAction = useAction()
  const skillsAction = useAction()
  useEffect(() => setF(d.profile), [d.profile])
  const set = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }))

  const saveProfile = async (e) => {
    e.preventDefault()
    const r = await profileAction.run(
      () => api.put('/profile', { branch: f.branch, year: f.year, college: f.college, bio: f.bio, interests: f.interests, career_goal: f.career_goal }),
      'Profile updated',
    )
    if (r.ok) reload()
  }
  const saveSkills = async (e) => {
    e.preventDefault()
    const r = await skillsAction.run(() => api.put('/profile/skills', { skills }), 'Skills updated')
    if (r.ok) reload()
  }

  const careers = d.careers
  const categories = [...new Set(d.skills.map((s) => s.category))]

  return (
    <div className="stack">
      <div className="grid grid-3">
        <StatCard label="Level" value={d.points.level} icon={Award} />
        <StatCard label="XP" value={d.points.xp} icon={Zap} />
        <StatCard label="Streak" value={d.points.streak_days} format={(v) => `${Math.round(v)} ${Math.round(v) === 1 ? "day" : "days"}`} icon={Flame} tone="warn" />
      </div>

      <Card>
        <CardHeader title="Student profile" subtitle="Saving your profile earns a little XP, like in the original app." />
        <form className="card-body form-grid" onSubmit={saveProfile}>
          <Input label="Branch" value={f.branch} onChange={set('branch')} />
          <Input label="Year" value={f.year} onChange={set('year')} />
          <div className="span-2">
            <Input label="College" value={f.college} onChange={set('college')} />
          </div>
          <div className="span-2">
            <Textarea label="Bio" value={f.bio} onChange={set('bio')} />
          </div>
          <Input label="Interests" hint="Comma separated" value={f.interests} onChange={set('interests')} />
          <Select
            label="Career goal"
            value={f.career_goal || ''}
            onChange={set('career_goal')}
            options={[...(f.career_goal && !careers.includes(f.career_goal) ? [f.career_goal] : []), ...careers].map((c) => ({ value: c, label: c }))}
          />
          <div className="span-2">
            <Button type="submit" variant="primary" icon={Save} loading={profileAction.busy}>
              Save profile
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <CardHeader title="My skills" subtitle="Self-rated proficiency from 0 to 100. Career matching, the graph and mentors use these." />
        <form className="card-body" onSubmit={saveSkills}>
          {categories.map((cat) => (
            <fieldset key={cat} style={{ border: 0, padding: 0, margin: '0 0 18px' }}>
              <legend className="section-title" style={{ margin: '0 0 10px', padding: 0, fontSize: 15 }}>{cat}</legend>
              <div className="form-grid">
                {d.skills
                  .filter((s) => s.category === cat)
                  .map((s) => (
                    <div className="field" key={s.skill_id}>
                      <label htmlFor={`sk-${s.skill_id}`} className="field-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{s.name}</span>
                        <strong>{skills[s.skill_id] ?? 0}</strong>
                      </label>
                      <input
                        id={`sk-${s.skill_id}`}
                        type="range"
                        min="0"
                        max="100"
                        value={skills[s.skill_id] ?? 0}
                        onChange={(e) => setSkills((x) => ({ ...x, [s.skill_id]: Number(e.target.value) }))}
                        style={{ accentColor: 'var(--accent)', width: '100%' }}
                      />
                    </div>
                  ))}
              </div>
            </fieldset>
          ))}
          <Button type="submit" variant="primary" icon={Save} loading={skillsAction.busy}>
            Save skills
          </Button>
        </form>
      </Card>

      <Card>
        <CardHeader title="Achievements" subtitle={`Level ${d.points.level} · ${d.points.xp} XP · ${d.points.streak_days} day streak`} />
        <div className="card-body">
          {d.badges.length ? (
            <div className="chips">
              {d.badges.map((b) => (
                <span className="chip ok" key={b.badge_name} title={`${b.description} · ${day(b.earned_at)}`}>
                  <Medal size={13} aria-hidden="true" /> {b.badge_name}
                </span>
              ))}
            </div>
          ) : (
            <p className="muted">No badges yet. Finish an assessment, interview or coding problem to earn your first one.</p>
          )}
        </div>
      </Card>
    </div>
  )
}

function MentorProfile({ d, reload }) {
  const [f, setF] = useState(d.profile)
  const { busy, run } = useAction()
  useEffect(() => setF(d.profile), [d.profile])
  const set = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }))
  const save = async (e) => {
    e.preventDefault()
    const r = await run(
      () => api.put('/profile', { expertise: f.expertise, domain: f.domain, experience_years: Number(f.experience_years), bio: f.bio, availability: f.availability }),
      'Mentor profile updated',
    )
    if (r.ok) reload()
  }
  return (
    <div className="stack">
      <div className="grid grid-2">
        <Card pad>
          <div className="faint">Verification status</div>
          <div style={{ marginTop: 8 }}>
            <Badge tone={d.profile.is_verified ? 'safe' : 'warn'} dot>
              {d.profile.is_verified ? 'Verified' : 'Pending admin verification'}
            </Badge>
          </div>
        </Card>
        <Card pad>
          <div className="faint">Rating</div>
          <div className="big-num" style={{ marginTop: 6 }}>
            ⭐ {d.profile.rating} <span className="faint" style={{ fontSize: 14, fontWeight: 400 }}>({d.profile.rating_count} reviews)</span>
          </div>
        </Card>
      </div>
      <Card>
        <CardHeader title="Mentor profile" />
        <form className="card-body form-grid" onSubmit={save}>
          <div className="span-2">
            <Input label="Expertise" hint="Comma separated skills" value={f.expertise} onChange={set('expertise')} />
          </div>
          <Input label="Domain" value={f.domain} onChange={set('domain')} />
          <Input label="Years of experience" type="number" min="0" max="50" step="0.5" value={f.experience_years} onChange={set('experience_years')} />
          <div className="span-2">
            <Textarea label="Bio" value={f.bio} onChange={set('bio')} />
          </div>
          <div className="span-2">
            <Input label="Availability" value={f.availability} onChange={set('availability')} />
          </div>
          <div className="span-2">
            <Button type="submit" variant="primary" icon={Save} loading={busy}>
              Save profile
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

export default function Profile() {
  const state = useAsync(() => api.get('/profile'), [])
  return (
    <>
      <PageHeader title="My profile" description="Keep your details and skills current so recommendations stay accurate." />
      <AsyncView state={state} skeleton={<PageSkeleton stats={3} cards={2} />}>
        {(d) => (d.role === 'student' ? <StudentProfile d={d} reload={() => state.reload({ quiet: true })} /> : <MentorProfile d={d} reload={() => state.reload({ quiet: true })} />)}
      </AsyncView>
    </>
  )
}
