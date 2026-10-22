import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, PlayCircle, RefreshCw, SearchX, ThumbsDown } from 'lucide-react'
import { Button, EmptyState, PageHeader, SearchField, useToast } from '../components/ui'
import { CourseCard } from '../components/app/CourseCard'
import { Async, CardSkeletons } from '../components/app/Async'
import { get, post, track } from '../lib/api'
import { useApi } from '../lib/useApi'
import { fmtPct } from '../lib/format'

export default function Recommendations() {
  const toast = useToast()
  const nav = useNavigate()
  const q = useApi(() => get('/api/recommendations?top_n=12'), [])
  const [text, setText] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [busy, setBusy] = useState('')

  const list = useMemo(() => {
    const recs = q.data?.recommendations || []
    const needle = text.trim().toLowerCase()
    if (!needle) return recs
    return recs.filter((r) => `${r.course.title} ${r.course.description} ${r.course.tags} ${r.course.category}`.toLowerCase().includes(needle))
  }, [q.data, text])

  const refresh = async () => {
    setRefreshing(true)
    try {
      await post('/api/recommendations/refresh')
      q.reload()
      toast.success('Recommendations refreshed with the latest model files.')
    } catch (e) {
      toast.error(`Refresh failed: ${e.message}`)
    } finally {
      setRefreshing(false)
    }
  }

  const act = async (id, type, message, then) => {
    setBusy(`${id}:${type}`)
    try {
      await track(id, type)
      toast.success(message)
      then?.()
    } catch (e) {
      toast.error(`Could not record that: ${e.message}`)
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Recommendations"
        title="Ranked for you"
        description="Ranked for your profile and behavior. Every card shows why it was suggested; dismissing one teaches the ranking."
        actions={
          <Button icon={RefreshCw} loading={refreshing} onClick={refresh}>
            Refresh
          </Button>
        }
      />
      <div className="row">
        <SearchField value={text} onChange={setText} label="Search recommendations" placeholder="Search your recommendations…" />
        {q.data && (
          <span className="small mono muted" aria-live="polite">
            {list.length} shown · est. success {fmtPct(q.data.success_probability)} · {q.data.engagement.label}
          </span>
        )}
      </div>
      <Async q={q} skeleton={<CardSkeletons n={6} />} title="Could not load recommendations">
        {() =>
          list.length ? (
            <div className="course-grid">
              {list.map((r) => (
                <CourseCard key={r.course.id} course={r.course} rec={r}>
                  <Button size="sm" variant="primary" icon={Eye} onClick={() => act(r.course.id, 'open', 'Opening course…', () => nav(`/courses/${r.course.id}`))}>
                    View
                  </Button>
                  <Button
                    size="sm"
                    icon={PlayCircle}
                    loading={busy === `${r.course.id}:start`}
                    onClick={() => act(r.course.id, 'start', `Marked "${r.course.title}" as started.`)}
                  >
                    Start
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    icon={ThumbsDown}
                    loading={busy === `${r.course.id}:dismiss`}
                    onClick={() => act(r.course.id, 'dismiss', 'Dismissed. Future lists will adapt.', q.reload)}
                  >
                    Dismiss
                  </Button>
                </CourseCard>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={SearchX}
              title="No recommendations match"
              action={
                <Button variant="primary" onClick={() => setText('')}>
                  Clear search
                </Button>
              }
            >
              Nothing in your ranked list matches "{text}". Clear the search, or browse the full catalog.
            </EmptyState>
          )
        }
      </Async>
    </div>
  )
}
