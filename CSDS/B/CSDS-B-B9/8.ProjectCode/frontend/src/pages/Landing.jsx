import { Link } from 'react-router-dom'
import {
  BarChart3, Briefcase, Code2, FileText, GraduationCap, Layers, ListChecks, MessageSquare, Trophy,
} from 'lucide-react'

const FEATURES = [
  [GraduationCap, 'Aptitude practice', 'Timed tests by topic and difficulty with instant scoring and explanations.'],
  [Code2, 'Coding judge', 'Monaco editor, Python / C++ / Java, hidden tests, time limits and real verdicts.'],
  [ListChecks, 'Technical MCQs', 'Programming, DBMS, operating systems and computer networks.'],
  [Trophy, 'Contests & leaderboards', 'Scheduled contests with live standings and Elo-style ratings.'],
  [Layers, 'Level progression', 'Five levels that unlock by score, ending in an expert interview and a Job-ready badge.'],
  [MessageSquare, 'AI mock interviews', 'Role-specific questions, rubric scoring and actionable feedback - by voice or text.'],
  [FileText, 'Resume analysis', 'ATS score, role match and missing skills from a classifier trained on 2,400+ resumes.'],
  [Briefcase, 'Recruiter drives', 'Eligibility rules, ranked shortlists with skill evidence and a status pipeline.'],
  [BarChart3, 'Readiness analytics', 'Cohort readiness, level funnel and weak topics for career-services teams.'],
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      <header className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-slate-900 text-lg">
          <span className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center">T</span> TalentTrack
        </div>
        <Link to="/login" className="btn-primary">Sign in</Link>
      </header>

      <section className="max-w-6xl mx-auto px-4 pt-12 pb-16 grid md:grid-cols-2 gap-10 items-center">
        <div>
          <p className="text-indigo-600 font-semibold text-sm uppercase tracking-wider">Build and prove job readiness</p>
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 mt-3 leading-tight">
            Practice, get measured, get shortlisted - on real skill.
          </h1>
          <p className="text-slate-600 mt-5 text-lg">
            TalentTrack brings aptitude, coding and technical practice, contests, AI mock interviews and resume analysis
            into one readiness score - and connects ready candidates to recruiters who shortlist by evidence.
          </p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link to="/login?mode=register" className="btn-primary !px-6 !py-3 text-base">Start practising</Link>
            <Link to="/login" className="btn-secondary !px-6 !py-3 text-base">I'm a recruiter</Link>
          </div>
        </div>
        <div className="card p-6 bg-gradient-to-br from-indigo-50 to-white">
          <div className="text-sm font-semibold text-slate-500 mb-4">The readiness ladder</div>
          {['Foundation', 'Aptitude', 'Coder', 'Interview-ready', 'Job-ready'].map((l, i) => (
            <div key={l} className="flex items-center gap-3 py-2">
              <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm ${i === 4 ? 'bg-emerald-600 text-white' : 'bg-indigo-600 text-white'}`}>{i + 1}</div>
              <div className="flex-1">
                <div className="font-medium text-slate-800">{l}</div>
                <div className="h-1.5 bg-slate-200 rounded-full mt-1">
                  <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${20 * (i + 1)}%` }} />
                </div>
              </div>
            </div>
          ))}
          <p className="text-xs text-slate-500 mt-3">Levels unlock by score; the last step is an expert-led mock interview.</p>
        </div>
      </section>

      <section className="bg-slate-50 border-t border-slate-200">
        <div className="max-w-6xl mx-auto px-4 py-14">
          <h2 className="text-2xl font-bold text-slate-900 text-center">Everything in one place</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
            {FEATURES.map(([Icon, t, d]) => (
              <div key={t} className="card p-5">
                <Icon className="w-6 h-6 text-indigo-600" />
                <div className="font-semibold text-slate-900 mt-3">{t}</div>
                <p className="text-sm text-slate-600 mt-1">{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-4 py-14 grid md:grid-cols-3 gap-6 text-center">
        {[
          ['Candidates', 'Practise with guidance and earn a verified Job-ready badge.'],
          ['Recruiters', 'Create drives, set eligibility and shortlist with skill evidence.'],
          ['Career services', 'Track cohort readiness and the topics that need attention.'],
        ].map(([t, d]) => (
          <div key={t}>
            <div className="font-bold text-slate-900">{t}</div>
            <p className="text-sm text-slate-600 mt-1">{d}</p>
          </div>
        ))}
      </section>
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-400">TalentTrack</footer>
    </div>
  )
}
