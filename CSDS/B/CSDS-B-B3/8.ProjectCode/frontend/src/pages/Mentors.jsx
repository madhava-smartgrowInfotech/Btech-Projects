import { useEffect, useState } from 'react'
import { CalendarClock, Inbox, Search, Send, Star, UserSearch } from 'lucide-react'
import { AsyncView, CardSkeleton, StatusBadge, useAction } from '../components/common'
import { Button, Card, EmptyState, ErrorState, Input, Modal, PageHeader, ProgressBar, Select, Tabs, Textarea } from '../components/ui'
import { REQUEST_STATUS, SESSION_STATUS, day } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

function Find() {
  const profile = useAsync(() => api.get('/profile'), [])
  const requests = useAsync(() => api.get('/mentors/requests'), [])
  const pendingIds = new Set((requests.data || []).filter((r) => r.status === 'pending').map((r) => r.mentor_id))
  const [f, setF] = useState({ required_skill: 'Machine Learning', career_goal: '', domain: '' })
  const [matches, setMatches] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [target, setTarget] = useState(null)
  const [message, setMessage] = useState('')
  const [sent, setSent] = useState({})
  const { busy, run } = useAction()

  useEffect(() => {
    if (profile.data?.profile) setF((s) => ({ ...s, career_goal: profile.data.profile.career_goal || '' }))
  }, [profile.data])

  const search = async (e) => {
    e?.preventDefault()
    setLoading(true)
    setError(null)
    try {
      setMatches(await api.post('/mentors/recommend', f))
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  const openRequest = (m) => {
    setTarget(m)
    setMessage(`Hi ${m.name}, I'd love your guidance on ${f.required_skill || 'my learning path'}.`)
  }

  const send = async () => {
    const r = await run(() => api.post('/mentors/requests', { mentor_id: target.mentor_id, message }), (x) => ({ title: x.message }))
    if (r.ok) {
      setSent((s) => ({ ...s, [target.mentor_id]: true }))
      requests.reload({ quiet: true })
    }
    setTarget(null)
  }

  const set = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }))

  return (
    <div className="stack">
      <Card>
        <form className="card-body" onSubmit={search}>
          <div className="form-grid-3">
            <Input label="Skill you need help with" value={f.required_skill} onChange={set('required_skill')} />
            <Input label="Career goal" value={f.career_goal} onChange={set('career_goal')} />
            <Input label="Preferred domain" value={f.domain} onChange={set('domain')} />
          </div>
          <div className="btn-row mt">
            <Button type="submit" variant="primary" icon={Search} loading={loading}>
              Find matching mentors
            </Button>
          </div>
        </form>
      </Card>

      {error && <ErrorState title="Couldn't find mentors" error={error} onRetry={search} />}
      {loading && !matches && <CardSkeleton />}
      {!matches && !loading && !error && (
        <Card>
          <EmptyState icon={UserSearch} title="Get AI-recommended mentors">
            Describe the skill you need help with, then choose Find matching mentors. Matches are ranked by skill, domain, experience and rating.
          </EmptyState>
        </Card>
      )}
      {matches && matches.length === 0 && (
        <Card>
          <EmptyState icon={UserSearch} title="No verified mentors available">Mentors appear here once an admin has verified their profile.</EmptyState>
        </Card>
      )}
      {matches && matches.length > 0 && (
        <Card>
          {matches.map((m) => (
            <div className="list-item" key={m.mentor_id}>
              <div style={{ minWidth: 0, flex: 1 }}>
                <h3>
                  {m.name} <span className="faint" style={{ fontWeight: 400 }}>· {m.domain}</span>
                </h3>
                <div className="meta-line" style={{ marginBottom: 10 }}>
                  <span>Expertise: {m.expertise}</span>
                  <span>{m.experience_years} yrs experience</span>
                  <span>
                    <Star size={12} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-1px' }} /> {m.rating} ({m.rating_count})
                  </span>
                  <span>{m.availability}</span>
                </div>
                <div style={{ maxWidth: 420 }}>
                  <ProgressBar value={Math.min(m.match_score, 100)} max={100} label="Match score" valueLabel={`${m.match_score}%`} />
                </div>
              </div>
              <div className="item-side">
                <Button size="sm" variant="primary" icon={Send} disabled={sent[m.mentor_id] || pendingIds.has(m.mentor_id)} onClick={() => openRequest(m)}>
                  {sent[m.mentor_id] || pendingIds.has(m.mentor_id) ? 'Request pending' : 'Send request'}
                </Button>
              </div>
            </div>
          ))}
        </Card>
      )}

      <Modal
        open={!!target}
        onClose={() => setTarget(null)}
        title={`Request mentorship from ${target?.name ?? ''}`}
        footer={
          <>
            <Button onClick={() => setTarget(null)}>Cancel</Button>
            <Button variant="primary" icon={Send} loading={busy} disabled={!message.trim()} onClick={send}>
              Send request
            </Button>
          </>
        }
      >
        <Textarea label="Your message" value={message} onChange={(e) => setMessage(e.target.value)} data-autofocus />
      </Modal>
    </div>
  )
}

function Requests() {
  const state = useAsync(() => api.get('/mentors/requests'), [])
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(rows) =>
        rows.length === 0 ? (
          <Card>
            <EmptyState icon={Inbox} title="No requests sent yet">Find a mentor and send your first request from the Find a mentor tab.</EmptyState>
          </Card>
        ) : (
          <Card>
            {rows.map((r) => (
              <div className="list-item" key={r.id}>
                <div>
                  <h3>{r.mentor}</h3>
                  <p className="muted">{r.message}</p>
                  <div className="meta-line" style={{ marginTop: 6 }}>
                    <span>Sent {day(r.created_at)}</span>
                  </div>
                </div>
                <StatusBadge map={REQUEST_STATUS} value={r.status} />
              </div>
            ))}
          </Card>
        )
      }
    </AsyncView>
  )
}

function Sessions() {
  const state = useAsync(() => api.get('/mentors/sessions'), [])
  const [ratings, setRatings] = useState({})
  const { busy, run } = useAction()
  const complete = async (s) => {
    const r = await run(() => api.post(`/mentors/sessions/${s.id}/complete`, { rating: ratings[s.id] || 5 }), (x) => ({ title: x.message }))
    if (r.ok) state.reload({ quiet: true })
  }
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(rows) =>
        rows.length === 0 ? (
          <Card>
            <EmptyState icon={CalendarClock} title="No sessions scheduled yet">Sessions appear here once a mentor accepts one of your requests.</EmptyState>
          </Card>
        ) : (
          <Card>
            {rows.map((s) => (
              <div className="list-item" key={s.id}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <h3>
                    {s.topic} <span className="faint" style={{ fontWeight: 400 }}>with {s.with}</span>
                  </h3>
                  <div className="meta-line">
                    <span>Scheduled: {s.scheduled_time || 'To be scheduled'}</span>
                  </div>
                  {s.mentor_feedback && (
                    <p className="muted" style={{ marginTop: 10 }}>
                      <strong>Mentor feedback:</strong> {s.mentor_feedback}
                    </p>
                  )}
                  {s.status === 'completed' && <p style={{ marginTop: 8 }}>Your rating: {'⭐'.repeat(Math.round(s.student_rating))}</p>}
                </div>
                <div className="item-side">
                  <StatusBadge map={SESSION_STATUS} value={s.status} />
                  {s.status === 'scheduled' && (
                    <>
                      <Select
                        label="Rate this session"
                        value={String(ratings[s.id] || 5)}
                        onChange={(e) => setRatings((r) => ({ ...r, [s.id]: Number(e.target.value) }))}
                        options={[5, 4, 3, 2, 1].map((n) => ({ value: String(n), label: `${n} star${n > 1 ? 's' : ''}` }))}
                      />
                      <Button size="sm" variant="primary" loading={busy} onClick={() => complete(s)}>
                        Mark completed &amp; rate
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </Card>
        )
      }
    </AsyncView>
  )
}

export default function Mentors() {
  const [tab, setTab] = useState('find')
  return (
    <>
      <PageHeader title="Peer mentorship" description="Get matched with verified mentors, track your requests and rate completed sessions." />
      <div className="tab-gap">
        <Tabs
          label="Mentorship sections"
          value={tab}
          onChange={setTab}
          tabs={[
            { value: 'find', label: 'Find a mentor' },
            { value: 'requests', label: 'My requests' },
            { value: 'sessions', label: 'My sessions' },
          ]}
        />
      </div>
      {tab === 'find' && <Find />}
      {tab === 'requests' && <Requests />}
      {tab === 'sessions' && <Sessions />}
    </>
  )
}
