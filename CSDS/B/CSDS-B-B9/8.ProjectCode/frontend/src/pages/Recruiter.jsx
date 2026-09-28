import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Loader2, Plus } from 'lucide-react'
import api from '../api'
import { Badge, Empty, ErrorBox, Loadable, PageHeader, fmtDate, useAction, useFetch } from '../components/ui'

export default function Recruiter() {
  const drives = useFetch('/drives')
  const [open, setOpen] = useState(false)
  return (
    <>
      <PageHeader title="Hiring drives" subtitle="Set eligibility rules and shortlist candidates by verified skill">
        <button className="btn-primary" onClick={() => setOpen(!open)}><Plus className="w-4 h-4" /> New drive</button>
      </PageHeader>
      {open && <CreateDrive />}
      <Loadable loading={drives.loading} error={drives.error} onRetry={drives.reload}>
        {drives.data?.length ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {drives.data.map((d) => (
              <Link key={d.id} to={`/recruiter/drives/${d.id}`} className="card p-5 hover:border-indigo-300 block">
                <div className="font-semibold text-slate-900">{d.title}</div>
                <div className="text-sm text-slate-500">{d.company} - {d.role}</div>
                <div className="flex flex-wrap gap-1 mt-3">
                  <Badge tone="indigo">Level {d.min_level}+</Badge>
                  {d.required_skills.map((s) => <Badge key={s}>{s}</Badge>)}
                  {d.min_readiness > 0 && <Badge>readiness {d.min_readiness}+</Badge>}
                </div>
                <div className="flex flex-wrap gap-2 mt-3 text-xs text-slate-500">
                  {Object.entries(d.pipeline).filter(([, n]) => n).map(([s, n]) => <span key={s}>{s}: <b>{n}</b></span>)}
                  {d.shortlisted_total === 0 && <span>No shortlist yet</span>}
                </div>
                <div className="text-xs text-slate-400 mt-2">Created {fmtDate(d.created_at)}</div>
              </Link>
            ))}
          </div>
        ) : <div className="card"><Empty>Create your first hiring drive</Empty></div>}
      </Loadable>
    </>
  )
}

function CreateDrive() {
  const nav = useNavigate()
  const [f, setF] = useState({ title: '', company: '', role: 'Python Developer', min_level: 3, skills: 'Python', min_readiness: 0, min_aptitude: 0 })
  const { busy, error, run } = useAction()
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const save = () => run(async () => {
    const r = await api.post('/drives', {
      title: f.title, company: f.company, role: f.role, min_level: Number(f.min_level),
      required_skills: f.skills.split(',').map((s) => s.trim()).filter(Boolean),
      min_readiness: Number(f.min_readiness), min_aptitude: Number(f.min_aptitude),
    })
    await api.post(`/drives/${r.data.id}/shortlist`)
    nav(`/recruiter/drives/${r.data.id}`)
  })
  return (
    <div className="card p-5 mb-6 grid md:grid-cols-4 gap-3">
      <div className="md:col-span-2"><label className="label">Drive title</label><input className="input" value={f.title} onChange={set('title')} placeholder="Backend hiring - Q4" /></div>
      <div><label className="label">Company</label><input className="input" value={f.company} onChange={set('company')} /></div>
      <div><label className="label">Role</label><input className="input" value={f.role} onChange={set('role')} /></div>
      <div><label className="label">Minimum level</label>
        <select className="input" value={f.min_level} onChange={set('min_level')}>{[1, 2, 3, 4, 5].map((l) => <option key={l} value={l}>Level {l}+</option>)}</select></div>
      <div><label className="label">Required skills (comma separated)</label><input className="input" value={f.skills} onChange={set('skills')} placeholder="Python, SQL" /></div>
      <div><label className="label">Min readiness (0-100)</label><input type="number" className="input" value={f.min_readiness} onChange={set('min_readiness')} /></div>
      <div><label className="label">Min aptitude %</label><input type="number" className="input" value={f.min_aptitude} onChange={set('min_aptitude')} /></div>
      <div className="md:col-span-4"><ErrorBox error={error} /></div>
      <div className="md:col-span-4">
        <button className="btn-primary" onClick={save} disabled={busy || !f.title.trim()}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Create drive & build shortlist</button>
      </div>
    </div>
  )
}
