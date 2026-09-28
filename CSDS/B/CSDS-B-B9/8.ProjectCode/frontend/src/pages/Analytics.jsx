import { useState } from 'react'
import { Award, Gauge, Target, Users } from 'lucide-react'
import { Badge, Bar, Loadable, PageHeader, SampleTag, Stat, useFetch } from '../components/ui'

const COMP_LABEL = { aptitude: 'Aptitude', technical: 'Technical MCQs', coding: 'Coding', interview: 'AI interview', resume: 'Resume ATS' }
const accTone = (a) => (a < 40 ? 'bg-rose-500' : a < 60 ? 'bg-amber-500' : 'bg-emerald-500')

export default function Analytics() {
  const [sample, setSample] = useState(true)
  const { data, loading, error, reload } = useFetch(`/analytics/readiness?include_sample=${sample}`)
  return (
    <>
      <PageHeader title="Readiness analytics" subtitle="Cohort readiness, level funnel and weak topics">
        <label className="text-sm text-slate-600 flex items-center gap-2 card px-3 py-2">
          <input type="checkbox" checked={sample} onChange={(e) => setSample(e.target.checked)} /> Include sample cohort
        </label>
      </PageHeader>
      <Loadable loading={loading} error={error} onRetry={reload}>
        {data && <Body a={data} />}
      </Loadable>
    </>
  )
}

function Body({ a }) {
  const maxBucket = Math.max(1, ...a.buckets.map((b) => b.count))
  const maxLevel = Math.max(1, ...a.levels.map((b) => b.count))
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat icon={Users} label="Candidates" value={a.cohort_size} />
        <Stat icon={Gauge} label="Avg readiness" value={a.avg_readiness} tone="sky" />
        <Stat icon={Award} label="Job-ready" value={a.job_ready} tone="emerald" />
        <Stat icon={Target} label="Weakest topic" value={a.weak_topics[0]?.topic || '-'} hint={a.weak_topics[0] ? `${a.weak_topics[0].accuracy}% accuracy` : ''} tone="rose" />
      </div>
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-4">Readiness distribution</div>
          <div className="flex items-end gap-2 h-40">
            {a.buckets.map((b) => (
              <div key={b.range} className="flex-1 flex flex-col items-center justify-end h-full">
                <div className="text-xs font-semibold text-slate-700">{b.count}</div>
                <div className="w-full bg-indigo-500 rounded-t" style={{ height: `${(100 * b.count) / maxBucket}%`, minHeight: b.count ? 4 : 0 }} />
                <div className="text-[10px] text-slate-500 mt-1">{b.range}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-4">Level funnel</div>
          <div className="space-y-3">
            {a.levels.map((l) => <Bar key={l.level} label={`L${l.level} ${l.name}`} value={l.count} max={maxLevel} right={l.count} tone="bg-sky-500" />)}
          </div>
        </div>
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-4">Average by component</div>
          <div className="space-y-3">
            {Object.entries(a.component_avg).map(([k, v]) => <Bar key={k} label={`${COMP_LABEL[k]} (${Math.round(a.weights[k] * 100)}%)`} value={v} right={v} />)}
          </div>
        </div>
      </div>
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-4">Topic accuracy (weakest first)</div>
          <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
            {a.topics.map((t) => (
              <Bar key={t.kind + t.topic} label={<>{t.topic} <span className="text-slate-400">({t.kind}, {t.attempts} answers)</span></>} value={t.accuracy} right={`${t.accuracy}%`} tone={accTone(t.accuracy)} />
            ))}
          </div>
        </div>
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-4">Coding acceptance by topic</div>
          <div className="space-y-3 max-h-72 overflow-y-auto pr-2">
            {a.coding_topics.map((t) => <Bar key={t.topic} label={`${t.topic} (${t.submissions} submissions)`} value={t.acceptance} right={`${t.acceptance}%`} tone={accTone(t.acceptance)} />)}
          </div>
          <div className="flex flex-wrap gap-2 mt-4">
            {Object.entries(a.verdicts).map(([v, n]) => <Badge key={v}>{v}: {n}</Badge>)}
          </div>
        </div>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full">
          <thead><tr><th className="th">Candidate</th><th className="th">Level</th><th className="th">Readiness</th><th className="th">Aptitude</th><th className="th">Technical</th><th className="th">Solved</th><th className="th">Interview</th><th className="th">ATS</th><th className="th">Rating</th></tr></thead>
          <tbody>
            {a.candidates.map((c) => (
              <tr key={c.id}>
                <td className="td">{c.name} <SampleTag show={c.is_sample} /> {c.job_ready && <Award className="w-4 h-4 text-emerald-600 inline" />}</td>
                <td className="td">L{c.level}</td><td className="td font-semibold">{c.readiness}</td>
                <td className="td">{c.components.aptitude}</td><td className="td">{c.components.technical}</td><td className="td">{c.solved}</td>
                <td className="td">{c.components.interview ? (c.components.interview / 10).toFixed(1) : '-'}</td><td className="td">{Math.round(c.ats)}</td><td className="td">{c.rating}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
