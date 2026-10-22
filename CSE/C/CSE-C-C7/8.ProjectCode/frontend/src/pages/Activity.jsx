import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { History, ListChecks } from 'lucide-react'
import { Badge, Button, EmptyState, PageHeader, SkeletonBlock, Table, Tabs } from '../components/ui'
import { Async } from '../components/app/Async'
import { get } from '../lib/api'
import { useApi } from '../lib/useApi'
import { EVENT_LABEL, EVENT_TONE, fmtDate, fmtPct } from '../lib/format'

function load() {
  return Promise.all([get('/api/activity?limit=100'), get('/api/history'), get('/api/courses')]).then(([activity, history, courses]) => ({
    events: activity.events,
    history: history.history,
    titles: Object.fromEntries(courses.courses.map((c) => [c.id, c.title])),
  }))
}

export default function Activity() {
  const q = useApi(load, [])
  const [tab, setTab] = useState('events')

  const columns = useMemo(() => {
    const titles = q.data?.titles || {}
    const course = {
      key: 'course_id',
      label: 'Course',
      sortValue: (r) => titles[r.course_id] || r.course_id,
      render: (r) =>
        r.course_id ? (
          <Link className="link-plain" to={`/courses/${r.course_id}`}>
            {titles[r.course_id] || r.course_id}
          </Link>
        ) : (
          '—'
        ),
    }
    const when = { key: 'at', label: 'When', render: (r) => fmtDate(r.at), sortValue: (r) => r.at }
    return {
      events: [
        when,
        {
          key: 'event_type',
          label: 'Event',
          sortValue: (r) => r.event_type,
          render: (r) => <Badge tone={EVENT_TONE[r.event_type]}>{EVENT_LABEL[r.event_type] || r.event_type}</Badge>,
        },
        course,
      ],
      history: [
        when,
        course,
        { key: 'score', label: 'Match', numeric: true, render: (r) => fmtPct(r.score), sortValue: (r) => r.score },
        { key: 'explanation', label: 'Why', sortable: false },
      ],
    }
  }, [q.data])

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Activity"
        title="Your trail"
        description="Everything you did, and every recommendation the system showed you. Both feed the next ranking."
      />
      <Async q={q} title="Could not load your activity" skeleton={<SkeletonBlock rows={6} label="Loading activity" />}>
        {(d) => (
          <>
            <Tabs
              label="Activity views"
              value={tab}
              onChange={setTab}
              tabs={[
                { id: 'events', label: 'Interactions', icon: ListChecks, count: d.events.length },
                { id: 'history', label: 'Recommendation history', icon: History, count: d.history.length },
              ]}
            />
            {tab === 'events' ? (
              <Table
                caption="Your interactions"
                columns={columns.events}
                rows={d.events}
                rowKey={(r, i) => `${r.at}-${i}`}
                initialSort={null}
                pageSize={12}
                empty={
                  <EmptyState
                    icon={ListChecks}
                    title="No interactions yet"
                    action={
                      <Button variant="primary" to="/app/recommendations">
                        Browse recommendations
                      </Button>
                    }
                  >
                    Open, start, save or dismiss a course and it is logged here.
                  </EmptyState>
                }
              />
            ) : (
              <Table
                caption="Recommendation history"
                columns={columns.history}
                rows={d.history}
                rowKey={(r, i) => `${r.at}-${r.course_id}-${i}`}
                pageSize={12}
                empty={
                  <EmptyState
                    icon={History}
                    title="No history yet"
                    action={
                      <Button variant="primary" to="/app/recommendations">
                        Generate recommendations
                      </Button>
                    }
                  >
                    Each time recommendations are generated for you, the ranked courses are logged here (latest 40).
                  </EmptyState>
                }
              />
            )}
          </>
        )}
      </Async>
    </div>
  )
}
