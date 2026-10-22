import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BookOpen, FilterX } from 'lucide-react'
import { Button, EmptyState, PageHeader, SearchField, Select } from '../components/ui'
import { CourseCard } from '../components/app/CourseCard'
import { Async, CardSkeletons } from '../components/app/Async'
import { Stagger } from '../components/motion'
import { get } from '../lib/api'
import { useApi } from '../lib/useApi'
import { plural } from '../lib/format'

const LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'All levels']

export default function Catalog() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') || ''
  const level = params.get('level') || ''
  const urlQ = params.get('q') || ''
  const [text, setText] = useState(urlQ)
  const [debounced, setDebounced] = useState(urlQ)

  useEffect(() => {
    const t = setTimeout(() => setDebounced(text.trim()), 250)
    return () => clearTimeout(t)
  }, [text])

  const update = (key, value) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  // Keep ?q= in sync with the debounced search text.
  useEffect(() => {
    if (debounced !== urlQ) update('q', debounced)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced])

  // Unfiltered list feeds the category dropdown.
  const all = useApi(() => get('/api/courses'), [])
  const categories = useMemo(() => [...new Set((all.data?.courses || []).map((c) => c.category))].sort(), [all.data])

  const qs = new URLSearchParams()
  if (debounced) qs.set('q', debounced)
  if (category) qs.set('category', category)
  if (level) qs.set('level', level)
  const q = useApi(() => get(`/api/courses?${qs.toString()}`), [debounced, category, level])

  const filtered = Boolean(debounced || category || level)
  const clear = () => {
    setText('')
    setDebounced('')
    setParams({}, { replace: true })
  }

  return (
    <div className="container" style={{ paddingTop: 36, paddingBottom: 64 }}>
      <PageHeader
        eyebrow="Course catalog"
        title="All courses"
        description="Browse and filter the full catalog. Sign in to see how each course ranks for you."
      />
      <div className="filter-bar">
        <SearchField value={text} onChange={setText} label="Search courses" placeholder="Search title, topic, tags…" />
        <Select label="Category" value={category} onChange={(e) => update('category', e.target.value)}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </Select>
        <Select label="Level" value={level} onChange={(e) => update('level', e.target.value)}>
          <option value="">All levels</option>
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </Select>
        {filtered && (
          <Button icon={FilterX} onClick={clear}>
            Clear
          </Button>
        )}
      </div>
      <Async q={q} skeleton={<CardSkeletons n={6} />} title="Could not load the catalog">
        {(data) =>
          data.courses.length ? (
            <div className="stack">
              <p className="small mono muted" aria-live="polite">
                {plural(data.count, 'course')}
              </p>
              <Stagger className="course-grid" inView={false} key={`${debounced}|${category}|${level}`}>
                {data.courses.map((c) => (
                  <CourseCard key={c.id} course={c}>
                    <Button size="sm" variant="primary" to={`/courses/${c.id}`}>
                      View course
                    </Button>
                  </CourseCard>
                ))}
              </Stagger>
            </div>
          ) : (
            <EmptyState
              icon={BookOpen}
              title="No courses match"
              action={
                <Button variant="primary" icon={FilterX} onClick={clear}>
                  Clear filters
                </Button>
              }
            >
              Nothing in the catalog matches those filters. Try a broader search or clear them.
            </EmptyState>
          )
        }
      </Async>
    </div>
  )
}
