import { useState } from 'react'
import { CheckCircle2, Loader2, Sparkles, Upload, XCircle } from 'lucide-react'
import api from '../api'
import { Badge, Bar, Empty, ErrorBox, Loadable, PageHeader, useAction, useFetch } from '../components/ui'

const BREAKDOWN = [
  ['sections_contact', 'Sections & contact', 25],
  ['skill_match', 'Skill match for role', 35],
  ['role_fit', 'Role fit (classifier)', 15],
  ['content_quality', 'Content quality', 25],
]

export default function ResumePage() {
  const roles = useFetch('/resume/roles')
  const latest = useFetch('/resume/latest')
  const [file, setFile] = useState(null)
  const [target, setTarget] = useState('')
  const [aiTips, setAiTips] = useState(true)
  const [report, setReport] = useState(null)
  const { busy, error, run } = useAction()
  const analyze = () => run(async () => {
    if (!file) throw new Error('Choose a PDF resume first')
    const fd = new FormData()
    fd.append('file', file)
    fd.append('target_role', target)
    fd.append('ai_tips', aiTips ? 'true' : 'false')
    const r = await api.post('/resume/analyze', fd)
    setReport(r.data)
  })
  const shown = report || latest.data
  return (
    <>
      <PageHeader title="Resume analyser" subtitle="ATS-style score, role match and missing skills - role classifier trained on 2,400+ real resumes" />
      <div className="card p-5 grid md:grid-cols-4 gap-3 items-end">
        <div className="md:col-span-2">
          <label className="label">Resume (PDF, max 5 MB)</label>
          <label className="flex items-center gap-2 input cursor-pointer">
            <Upload className="w-4 h-4 text-slate-400" />
            <span className="truncate text-slate-600">{file ? file.name : 'Choose a PDF...'}</span>
            <input type="file" accept="application/pdf,.pdf" className="hidden" onChange={(e) => setFile(e.target.files[0] || null)} />
          </label>
        </div>
        <div>
          <label className="label">Target role</label>
          <select className="input" value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="">Auto-detect from resume</option>
            {roles.data?.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
          </select>
        </div>
        <button className="btn-primary" onClick={analyze} disabled={busy}>
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} {busy ? 'Analysing...' : 'Analyse resume'}
        </button>
        <label className="text-sm text-slate-600 flex items-center gap-2 md:col-span-4">
          <input type="checkbox" checked={aiTips} onChange={(e) => setAiTips(e.target.checked)} /> Include AI improvement tips (Gemini)
        </label>
        <div className="md:col-span-4"><ErrorBox error={error} /></div>
      </div>
      <div className="mt-4">
        <Loadable loading={latest.loading} error={latest.error} onRetry={latest.reload}>
          {shown ? <Report r={shown} /> : <div className="card"><Empty>Upload your resume to see your ATS score</Empty></div>}
        </Loadable>
      </div>
    </>
  )
}

function Report({ r }) {
  const tone = r.ats_score >= 70 ? 'text-emerald-600' : r.ats_score >= 50 ? 'text-amber-600' : 'text-rose-600'
  return (
    <div className="space-y-4">
      {r.leveled_up && <Badge tone="emerald">Level up! You are now Level {r.level}</Badge>}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="text-sm text-slate-500">ATS score {r.filename && <span className="text-slate-400">- {r.filename}</span>}</div>
          <div className={`text-5xl font-extrabold ${tone}`}>{r.ats_score}<span className="text-xl text-slate-400">/100</span></div>
          <div className="space-y-2 mt-4">
            {BREAKDOWN.map(([k, l, max]) => <Bar key={k} label={l} value={r.breakdown[k]} max={max} right={`${r.breakdown[k]}/${max}`} />)}
          </div>
        </div>
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-2">Role match</div>
          <div className="text-sm text-slate-600">Target: <b>{r.target_label}</b> ({Math.round(r.target_match_prob * 100)}% match)</div>
          <div className="space-y-2 mt-3">
            {r.top_roles.map((x) => <Bar key={x.role} label={x.label} value={x.prob * 100} right={`${Math.round(x.prob * 100)}%`} tone="bg-sky-500" />)}
          </div>
          <div className="text-xs text-slate-400 mt-3">{r.word_count} words - {r.quantified_achievements} quantified results - {r.action_verbs} action verbs</div>
        </div>
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-2">Skills for {r.target_label}</div>
          <div className="flex flex-wrap gap-1">
            {r.matched_skills.map((s) => <Badge key={s} tone="emerald"><CheckCircle2 className="w-3 h-3" />{s}</Badge>)}
            {r.missing_skills.map((s) => <Badge key={s} tone="rose"><XCircle className="w-3 h-3" />{s}</Badge>)}
          </div>
          <div className="text-sm font-semibold text-slate-500 mt-4 mb-2">All skills found ({r.skills.length})</div>
          <div className="flex flex-wrap gap-1">{r.skills.map((s) => <Badge key={s}>{s}</Badge>)}</div>
        </div>
      </div>
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-2">What to fix</div>
          {r.issues.length ? <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">{r.issues.map((x, i) => <li key={i}>{x}</li>)}</ul> : <Empty>No issues found</Empty>}
        </div>
        <div className="card p-5">
          <div className="text-sm font-semibold text-slate-500 mb-2 flex items-center gap-1"><Sparkles className="w-4 h-4" /> AI coach</div>
          {r.ai ? (
            <>
              <p className="text-sm text-slate-700">{r.ai.summary}</p>
              <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1 mt-2">{r.ai.tips.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </>
          ) : r.ai_error ? <ErrorBox error={`AI tips unavailable: ${r.ai_error}`} /> : <Empty>AI tips were not requested or GEMINI_API_KEY is not set</Empty>}
        </div>
      </div>
    </div>
  )
}
