import { Link } from 'react-router-dom'
import {
  Award, Bell, Briefcase, CheckCircle2, Circle, Code2, FileText, GraduationCap, ListChecks, MessageSquare, Trophy,
} from 'lucide-react'
import { Badge, Bar, Empty, Loadable, PageHeader, Stat, Verdict, fmtDate, useFetch } from '../components/ui'

const COMP_LABEL = { aptitude: 'Aptitude', technical: 'Technical MCQs', coding: 'Coding', interview: 'AI interview', resume: 'Resume ATS' }
const NEXT_LINK = { 2: '/practice', 3: '/problems', 4: '/interview', 5: '/interview' }

export default function Dashboard() {
  const { data, loading, error, reload } = useFetch('/me/dashboard')
  return (
    <Loadable loading={loading} error={error} onRetry={reload}>
      {data && <Body d={data} />}
    </Loadable>
  )
}

function Body({ d }) {
  const st = d.stats
  const next = d.ladder.find((l) => l.current)
  return (
    <>
      <PageHeader title={`Welcome, ${d.user.name}`} subtitle="Your job-readiness at a glance">
        {st.job_ready ? (
          <Badge tone="emerald"><Award className="w-3.5 h-3.5" /> Job-ready</Badge>
        ) : (
          <Badge tone="indigo">Level {st.level} of 5</Badge>
        )}
      </PageHeader>

      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500">Readiness score</div>
          <div className="text-5xl font-extrabold text-indigo-600 mt-2">{st.readiness}<span className="text-xl text-slate-400">/100</span></div>
          <div className="space-y-3 mt-5">
            {Object.entries(st.components).map(([k, v]) => (
              <Bar key={k} label={COMP_LABEL[k]} value={v} right={Math.round(v)} />
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-4">Weighted: aptitude 25%, coding 25%, technical 20%, interview 15%, resume 15%.</p>
        </div>

        <div className="card p-5 lg:col-span-2">
          <div className="text-sm font-semibold text-slate-500 mb-3">Level progression</div>
          <div className="space-y-2">
            {d.ladder.map((l) => (
              <div key={l.level} className={`flex items-start gap-3 p-3 rounded-lg ${l.current ? 'bg-indigo-50 border border-indigo-200' : ''}`}>
                {l.done ? <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5" /> : <Circle className="w-5 h-5 text-slate-300 mt-0.5" />}
                <div className="flex-1">
                  <div className="font-medium text-slate-800">Level {l.level} - {l.name}</div>
                  <div className="text-sm text-slate-500">{l.requirement}</div>
                </div>
                {l.current && NEXT_LINK[l.level] && (
                  <Link to={NEXT_LINK[l.level]} className="btn-primary !py-1 text-xs">Work on it</Link>
                )}
              </div>
            ))}
          </div>
          {next && <p className="text-xs text-slate-500 mt-3">Next: {next.requirement}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 mt-4">
        <Stat icon={GraduationCap} label="Aptitude best" value={`${st.aptitude.best}%`} hint={`${st.aptitude.attempts} tests`} />
        <Stat icon={ListChecks} label="Technical best" value={`${st.technical.best}%`} hint={`${st.technical.attempts} tests`} tone="sky" />
        <Stat icon={Code2} label="Solved" value={st.solved_count} hint={`${st.submissions} submissions`} tone="emerald" />
        <Stat icon={Trophy} label="Rating" value={st.rating} tone="amber" />
        <Stat icon={MessageSquare} label="AI interview" value={st.ai_interview_best ? `${st.ai_interview_best}/10` : '-'} tone="rose" />
        <Stat icon={FileText} label="Resume ATS" value={st.ats ? Math.round(st.ats) : '-'} tone="slate" />
      </div>

      <div className="grid lg:grid-cols-3 gap-4 mt-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500 mb-3"><Bell className="w-4 h-4" /> Notifications</div>
          {d.notifications.length ? (
            <ul className="space-y-2">
              {d.notifications.map((n) => (
                <li key={n.id} className="text-sm border-l-2 border-indigo-300 pl-3">
                  <div className="text-slate-700">{n.text}</div>
                  <div className="text-xs text-slate-400">{fmtDate(n.at)}</div>
                </li>
              ))}
            </ul>
          ) : <Empty>No notifications yet</Empty>}
        </div>
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-3">Recent activity</div>
          {d.recent_tests.length + d.recent_submissions.length === 0 && <Empty>Take a test or solve a problem to get started</Empty>}
          <ul className="space-y-2 text-sm">
            {d.recent_tests.map((t) => (
              <li key={'t' + t.id} className="flex justify-between gap-2">
                <span className="text-slate-700 truncate">{t.kind === 'aptitude' ? 'Aptitude' : 'Technical'} - {t.topic}</span>
                <span className="font-semibold">{t.score}%</span>
              </li>
            ))}
            {d.recent_submissions.map((s) => (
              <li key={'s' + s.id} className="flex justify-between gap-2">
                <Link to={`/problems/${s.problem}`} className="text-indigo-600 truncate">{s.problem} ({s.language})</Link>
                <Verdict v={s.verdict} />
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500 mb-3"><Briefcase className="w-4 h-4" /> Hiring drives</div>
          {d.drives.length ? (
            <ul className="space-y-2 text-sm">
              {d.drives.map((x, i) => (
                <li key={i} className="flex justify-between gap-2">
                  <span className="text-slate-700">{x.company} - {x.drive}</span>
                  <Badge tone={x.status === 'invited' ? 'emerald' : 'slate'}>{x.status}</Badge>
                </li>
              ))}
            </ul>
          ) : <Empty>Recruiters will find you here once you are shortlisted</Empty>}
        </div>
      </div>
    </>
  )
}
