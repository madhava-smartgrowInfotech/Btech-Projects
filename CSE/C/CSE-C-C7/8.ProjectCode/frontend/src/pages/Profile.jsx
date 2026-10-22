import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Save } from 'lucide-react'
import { Alert, Button, Card, Input, PageHeader, Select, SkeletonBlock, useToast } from '../components/ui'
import { Async } from '../components/app/Async'
import { get, put } from '../lib/api'
import { useApi } from '../lib/useApi'

const EDUCATION = ['High School', 'Diploma', "Bachelor's Degree", "Master's Degree", 'Self-taught', 'Other']
const SKILL = ['Beginner', 'Intermediate', 'Advanced']
const STYLE = ['Self-paced', 'Structured schedule', 'Video-first', 'Reading-first', 'Project-based']
const AGE = ['18-24', '25-34', '35-44', '45+', 'Prefer not to say']
const GENDER = [
  { value: 'Prefer not to say', label: 'Prefer not to say' },
  { value: 'F', label: 'Female' },
  { value: 'M', label: 'Male' },
]

/** Keep a stored value selectable even if it is not in the standard list. */
const opts = (list, current) => (current && !list.includes(current) ? [current, ...list] : list)

function ProfileForm({ initial, first }) {
  const toast = useToast()
  const nav = useNavigate()
  const [form, setForm] = useState(initial)
  const [errors, setErrors] = useState({})
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => {
    setSaved(false)
    setForm((f) => ({ ...f, [k]: e.target.value }))
  }

  const submit = async (e) => {
    e.preventDefault()
    const hours = Number(form.weekly_hours)
    const errs = {}
    if (!Number.isFinite(hours) || hours < 1 || hours > 40) errs.weekly_hours = 'Enter between 1 and 40 hours.'
    setErrors(errs)
    setError('')
    if (Object.keys(errs).length) return
    setBusy(true)
    try {
      await put('/api/profile', { ...form, weekly_hours: hours })
      setSaved(true)
      toast.success('Profile saved. Recommendations will use it right away.')
      if (first) nav('/app', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <form className="stack" onSubmit={submit} noValidate style={{ '--gap': '22px' }}>
        {error && <Alert tone="error">Could not save your profile: {error}</Alert>}
        {saved && <Alert tone="success">Profile saved.</Alert>}
        <div className="form-grid">
          <Select label="Education / background" value={form.education} onChange={set('education')}>
            <option value="">Select…</option>
            {opts(EDUCATION, form.education).map((o) => (
              <option key={o}>{o}</option>
            ))}
          </Select>
          <Select label="Skill level" value={form.skill_level} onChange={set('skill_level')}>
            {opts(SKILL, form.skill_level).map((o) => (
              <option key={o}>{o}</option>
            ))}
          </Select>
          <Select label="Preferred learning style" value={form.learning_style} onChange={set('learning_style')}>
            {opts(STYLE, form.learning_style).map((o) => (
              <option key={o}>{o}</option>
            ))}
          </Select>
          <Input
            label="Weekly study hours"
            type="number"
            min="1"
            max="40"
            step="0.5"
            value={form.weekly_hours}
            onChange={set('weekly_hours')}
            error={errors.weekly_hours}
          />
        </div>
        <div className="form-grid">
          <Input label="Interests" value={form.interests} onChange={set('interests')} placeholder="python, data science, design" hint="Comma separated." />
          <Input
            label="Preferred topics"
            value={form.preferred_topics}
            onChange={set('preferred_topics')}
            placeholder="Machine Learning, Web Development"
            hint="Comma separated."
          />
          <Input label="Learning goals" value={form.goals} onChange={set('goals')} placeholder="get a data job, build portfolio" hint="Comma separated." />
          <Input
            label="Course preferences"
            value={form.course_preferences}
            onChange={set('course_preferences')}
            placeholder="hands-on labs, short videos"
            hint="Comma separated."
          />
        </div>
        <div className="form-grid">
          <Select label="Age band" value={form.age_band} onChange={set('age_band')} hint="Used only for the fairness audit.">
            {opts(AGE, form.age_band).map((o) => (
              <option key={o}>{o}</option>
            ))}
          </Select>
          <Select label="Gender (optional)" value={form.gender} onChange={set('gender')} hint="Used only for fairness transparency.">
            {opts(
              GENDER.map((g) => g.value),
              form.gender,
            ).map((v) => (
              <option key={v} value={v}>
                {GENDER.find((g) => g.value === v)?.label || v}
              </option>
            ))}
          </Select>
        </div>
        <div className="row">
          <Button type="submit" variant="primary" size="lg" icon={Save} loading={busy}>
            Save and get recommendations
          </Button>
        </div>
      </form>
    </Card>
  )
}

export default function Profile() {
  const q = useApi(() => get('/api/profile'), [])
  const loc = useLocation()
  const first = Boolean(loc.state?.first)
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow={first ? 'Step 2 of 2' : 'My profile'}
        title={first ? 'Tell us what you want to learn' : 'Your learner profile'}
        description="This drives your personalized recommendations. Be specific; comma-separated values work best."
      />
      <Async q={q} title="Could not load your profile" skeleton={<SkeletonBlock rows={7} label="Loading profile" />}>
        {(p) => <ProfileForm initial={p} first={first} />}
      </Async>
    </div>
  )
}
