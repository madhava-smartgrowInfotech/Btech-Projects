import { useState } from 'react'
import { Check, Clock, Inbox, Save, X } from 'lucide-react'
import { AsyncView, CardSkeleton, StatusBadge, useAction } from '../components/common'
import { Badge, Button, Card, CardHeader, EmptyState, PageHeader, Table, Tabs, Textarea } from '../components/ui'
import { SESSION_STATUS, day } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

function Requests({ pending, reload }) {
  const { busy, run } = useAction()
  const respond = async (id, accept) => {
    const r = await run(() => api.post(`/mentor/requests/${id}/respond`, { accept }), (x) => ({ title: x.message }))
    if (r.ok) reload()
  }
  if (!pending.length)
    return (
      <Card>
        <EmptyState icon={Inbox} title="No pending mentorship requests">New requests from students will show up here.</EmptyState>
      </Card>
    )
  return (
    <Card>
      {pending.map((r) => (
        <div className="list-item" key={r.id}>
          <div style={{ minWidth: 0 }}>
            <h3>{r.student}</h3>
            <div className="meta-line">
              <span>{r.branch || 'Branch not set'}, {r.year || 'year not set'}</span>
              <span>Goal: {r.career_goal || 'not set'}</span>
              <span>Sent {day(r.created_at)}</span>
            </div>
            <p className="muted" style={{ marginTop: 8 }}>{r.message}</p>
          </div>
          <div className="item-side">
            <Button size="sm" variant="primary" icon={Check} disabled={busy} onClick={() => respond(r.id, true)}>
              Accept
            </Button>
            <Button size="sm" icon={X} disabled={busy} onClick={() => respond(r.id, false)}>
              Reject
            </Button>
          </div>
        </div>
      ))}
    </Card>
  )
}

function SessionCard({ s, reload }) {
  const [text, setText] = useState(s.mentor_feedback || '')
  const { busy, run } = useAction()
  const save = async () => {
    const r = await run(() => api.post(`/mentor/sessions/${s.id}/feedback`, { feedback: text }), (x) => ({ title: x.message }))
    if (r.ok) reload()
  }
  return (
    <Card>
      <CardHeader
        title={`${s.topic} with ${s.with}`}
        subtitle={`Scheduled: ${s.scheduled_time || 'To be scheduled'}`}
        actions={<StatusBadge map={SESSION_STATUS} value={s.status} />}
      />
      <div className="card-body">
        <div className="grid grid-2">
          <div>
            <div className="faint" style={{ marginBottom: 6 }}>Mentee skill snapshot</div>
            <Table
              caption={`${s.with} skills`}
              rows={s.skills}
              rowKey={(r) => r.skill}
              pageSize={5}
              cards={false}
              empty={<p className="faint">No skills recorded yet.</p>}
              columns={[
                { key: 'skill', label: 'Skill' },
                { key: 'proficiency', label: 'Proficiency', num: true, render: (r) => `${Math.round(r.proficiency)}%` },
              ]}
            />
          </div>
          <div>
            <div className="faint" style={{ marginBottom: 6 }}>Mentee topic progress</div>
            <Table
              caption={`${s.with} topic progress`}
              rows={s.progress}
              rowKey={(r) => r.topic}
              pageSize={5}
              cards={false}
              empty={<p className="faint">No topic progress yet.</p>}
              columns={[
                { key: 'topic', label: 'Topic' },
                { key: 'completion', label: 'Completion', num: true, render: (r) => `${Math.round(r.completion)}%` },
              ]}
            />
          </div>
        </div>
        <div className="mt">
          <Textarea label="Feedback for mentee" value={text} onChange={(e) => setText(e.target.value)} />
          <div className="btn-row mt">
            <Button icon={Save} loading={busy} onClick={save}>
              Save feedback
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default function MentorPanel() {
  const state = useAsync(() => api.get('/mentor/panel'), [])
  const [tab, setTab] = useState('requests')
  const reload = () => state.reload({ quiet: true })
  return (
    <>
      <PageHeader title="Mentor panel" description="Respond to mentorship requests and follow your mentees' progress." />
      <AsyncView state={state} skeleton={<CardSkeleton />}>
        {(d) => (
          <div className="stack">
            {!d.is_verified && (
              <div role="status" className="row" style={{ padding: '14px 18px', borderRadius: 'var(--radius)', background: 'var(--warn-soft)', border: '1px solid var(--border)', flexWrap: 'nowrap' }}>
                <Clock size={18} aria-hidden="true" style={{ color: 'var(--warn)', flexShrink: 0 }} />
                <span>
                  <strong>Pending admin verification.</strong> You can still configure your profile, but students won't see you in recommendations until you are verified.
                </span>
              </div>
            )}
            <div className="tab-gap" style={{ marginBottom: 0 }}>
              <Tabs
                label="Mentor sections"
                value={tab}
                onChange={setTab}
                tabs={[
                  { value: 'requests', label: `Requests${d.pending.length ? ` (${d.pending.length})` : ''}` },
                  { value: 'sessions', label: 'Sessions & mentee progress' },
                ]}
              />
            </div>
            {tab === 'requests' ? (
              <Requests pending={d.pending} reload={reload} />
            ) : d.sessions.length === 0 ? (
              <Card>
                <EmptyState icon={Inbox} title="No mentorship sessions yet">Accept a request and a session will appear here.</EmptyState>
              </Card>
            ) : (
              d.sessions.map((s) => <SessionCard key={s.id} s={s} reload={reload} />)
            )}
          </div>
        )}
      </AsyncView>
    </>
  )
}
