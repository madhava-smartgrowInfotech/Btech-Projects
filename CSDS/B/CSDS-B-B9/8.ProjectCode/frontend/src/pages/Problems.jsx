import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, CircleDot } from 'lucide-react'
import { DiffBadge, Loadable, PageHeader, useFetch } from '../components/ui'

export default function Problems() {
  const { data, loading, error, reload } = useFetch('/problems')
  const [diff, setDiff] = useState('All')
  const [topic, setTopic] = useState('All')
  const [status, setStatus] = useState('All')
  const topics = useMemo(() => [...new Set((data || []).map((p) => p.topic))].sort(), [data])
  const rows = (data || []).filter((p) => (diff === 'All' || p.difficulty === diff) && (topic === 'All' || p.topic === topic)
    && (status === 'All' || p.status === status))
  const solved = (data || []).filter((p) => p.status === 'solved').length
  return (
    <>
      <PageHeader title="Coding practice" subtitle={data ? `${solved} of ${data.length} solved - every submission runs on hidden tests` : ''}>
        <select className="input !w-auto" value={diff} onChange={(e) => setDiff(e.target.value)}>
          {['All', 'Easy', 'Medium', 'Hard'].map((d) => <option key={d}>{d}</option>)}
        </select>
        <select className="input !w-auto" value={topic} onChange={(e) => setTopic(e.target.value)}>
          <option>All</option>
          {topics.map((t) => <option key={t}>{t}</option>)}
        </select>
        <select className="input !w-auto" value={status} onChange={(e) => setStatus(e.target.value)}>
          {[['All', 'Any status'], ['new', 'Not tried'], ['tried', 'Attempted'], ['solved', 'Solved']].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </PageHeader>
      <Loadable loading={loading} error={error} onRetry={reload}>
        <div className="card overflow-x-auto">
          <table className="w-full">
            <thead><tr><th className="th w-10"></th><th className="th">#</th><th className="th">Problem</th><th className="th">Topic</th><th className="th">Difficulty</th><th className="th">Hidden tests</th></tr></thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.slug} className="hover:bg-slate-50">
                  <td className="td">
                    {p.status === 'solved' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : p.status === 'tried' ? <CircleDot className="w-4 h-4 text-amber-500" /> : null}
                  </td>
                  <td className="td text-slate-400">{p.id}</td>
                  <td className="td"><Link className="text-indigo-600 font-medium hover:underline" to={`/problems/${p.slug}`}>{p.title}</Link></td>
                  <td className="td">{p.topic}</td>
                  <td className="td"><DiffBadge d={p.difficulty} /></td>
                  <td className="td">{p.hidden_tests}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Loadable>
    </>
  )
}
