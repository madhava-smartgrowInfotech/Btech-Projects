import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Award, Loader2, RefreshCw, Send } from 'lucide-react'
import api from '../api'
import { Badge, Empty, ErrorBox, Loadable, PageHeader, SampleTag, useAction, useFetch } from '../components/ui'

const STATUSES = ['shortlisted', 'invited', 'interviewing', 'offered', 'hired', 'rejected']
const TONE = { shortlisted: 'slate', invited: 'sky', interviewing: 'indigo', offered: 'amber', hired: 'emerald', rejected: 'rose' }
const LANG = { python: 'Python', cpp: 'C++', java: 'Java' }

export default function DriveDetail() {
  const { id } = useParams()
  const d = useFetch(`/drives/${id}`)
  const [sel, setSel] = useState([])
  const [excluded, setExcluded] = useState(null)
  const [msg, setMsg] = useState('')
  const { busy, error, run } = useAction()
  const rebuild = () => run(async () => {
    const r = await api.post(`/drives/${id}/shortlist`)
    d.setData({ drive: r.data.drive, shortlist: r.data.shortlist })
    setExcluded({ list: r.data.excluded, total: r.data.excluded_total })
    setMsg(`Shortlist rebuilt: ${r.data.shortlist.length} eligible candidates.`)
  })
  const setStatus = (ids, status) => run(async () => {
    const r = await api.post(`/drives/${id}/status`, { candidate_ids: ids, status })
    setMsg(status === 'invited' ? `Invitations sent to ${r.data.updated} candidate(s).` : `${r.data.updated} candidate(s) moved to ${status}.`)
    setSel([])
    await d.reload(true)
  })
  const toggle = (cid) => setSel(sel.includes(cid) ? sel.filter((x) => x !== cid) : [...sel, cid])
  const drive = d.data?.drive
  return (
    <Loadable loading={d.loading} error={d.error} onRetry={d.reload}>
      {drive && (
        <>
          <Link to="/recruiter" className="text-sm text-indigo-600 flex items-center gap-1 mb-3"><ArrowLeft className="w-4 h-4" /> All drives</Link>
          <PageHeader title={drive.title} subtitle={`${drive.company} - ${drive.role}`}>
            <button className="btn-secondary" onClick={rebuild} disabled={busy}><RefreshCw className="w-4 h-4" /> Rebuild shortlist</button>
            <button className="btn-primary" onClick={() => setStatus(sel, 'invited')} disabled={busy || !sel.length}>
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Invite selected ({sel.length})
            </button>
          </PageHeader>
          <div className="flex flex-wrap gap-2 mb-4">
            <Badge tone="indigo">Eligibility: Level {drive.min_level}+</Badge>
            {drive.required_skills.map((s) => <Badge key={s}>{s}</Badge>)}
            {drive.min_readiness > 0 && <Badge>readiness {drive.min_readiness}+</Badge>}
            {drive.min_aptitude > 0 && <Badge>aptitude {drive.min_aptitude}%+</Badge>}
            <span className="mx-2 text-slate-300">|</span>
            {STATUSES.map((s) => <Badge key={s} tone={TONE[s]}>{s}: {drive.pipeline[s]}</Badge>)}
          </div>
          <ErrorBox error={error} />
          {msg && <div className="rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm px-4 py-2 mb-3">{msg}</div>}
          <div className="card overflow-x-auto">
            {d.data.shortlist.length ? (
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="th"><input type="checkbox" checked={sel.length === d.data.shortlist.length}
                      onChange={(e) => setSel(e.target.checked ? d.data.shortlist.map((r) => r.candidate_id) : [])} /></th>
                    <th className="th">Rank</th><th className="th">Candidate</th><th className="th">Score</th><th className="th">Evidence</th><th className="th">Skills evidence</th><th className="th">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {d.data.shortlist.map((r) => {
                    const e = r.evidence
                    return (
                      <tr key={r.candidate_id} className="align-top">
                        <td className="td"><input type="checkbox" checked={sel.includes(r.candidate_id)} onChange={() => toggle(r.candidate_id)} /></td>
                        <td className="td font-bold">{r.rank}</td>
                        <td className="td">
                          <div className="font-medium">{r.name} {e.job_ready && <Award className="w-4 h-4 text-emerald-600 inline" />}</div>
                          <div className="text-xs text-slate-400">{r.email}</div><SampleTag show={r.is_sample} />
                        </td>
                        <td className="td font-bold text-indigo-600">{r.score}</td>
                        <td className="td text-xs space-y-0.5 min-w-[180px]">
                          <div>Level {e.level} - readiness <b>{e.readiness}</b></div>
                          <div>Aptitude {e.aptitude_best}% - technical {e.technical_best}%</div>
                          <div>{e.solved} problems solved - rating {e.rating}</div>
                          <div>AI interview {e.ai_interview || '-'}/10 - ATS {Math.round(e.ats)}</div>
                          <div>{Object.entries(e.languages || {}).map(([l, n]) => `${LANG[l] || l}: ${n}`).join(', ')}</div>
                        </td>
                        <td className="td text-xs min-w-[180px]">
                          {(e.skill_evidence || []).map((s) => <div key={s.skill}><b>{s.skill}</b>: {s.evidence.join('; ')}</div>)}
                          {!e.skill_evidence?.length && <span className="text-slate-400">No required skills</span>}
                        </td>
                        <td className="td">
                          <select className="input !py-1 !text-xs" value={r.status} onChange={(ev) => setStatus([r.candidate_id], ev.target.value)} disabled={busy}>
                            {STATUSES.map((s) => <option key={s}>{s}</option>)}
                          </select>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            ) : <Empty>No candidate meets the eligibility rules yet. Rebuild the shortlist later or relax the criteria.</Empty>}
          </div>
          {excluded && excluded.total > 0 && (
            <details className="card p-4 mt-4">
              <summary className="text-sm font-semibold text-slate-600 cursor-pointer">{excluded.total} candidates not eligible - see why</summary>
              <ul className="text-sm mt-2 space-y-1">
                {excluded.list.map((x) => <li key={x.candidate_id}><b>{x.name}</b>: {x.reasons.join('; ')}</li>)}
              </ul>
            </details>
          )}
        </>
      )}
    </Loadable>
  )
}
