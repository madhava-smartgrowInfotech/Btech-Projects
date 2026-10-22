import { Download, Filter, Users } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import api, { describeError } from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Button, Input, Select } from '../components/ui/controls'
import { Badge, Card, StatusDot } from '../components/ui/display'
import { EmptyState, ErrorState, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { logEvent } from '../lib/activity'
import { useData } from '../lib/data'

const COLS = [
  { key: 'CGPA', label: 'CGPA', sortable: true, className: 'font-mono tabular-nums text-fg', render: (r) => r.CGPA.toFixed(2) },
  { key: 'Branch', label: 'Branch', sortable: true, defaultDir: 'asc' },
  { key: 'Aptitude_Score', label: 'Aptitude', sortable: true, align: 'right', className: 'font-mono tabular-nums' },
  { key: 'Technical_Score', label: 'Technical', sortable: true, align: 'right', className: 'font-mono tabular-nums' },
  { key: 'Internships', label: 'Intern.', sortable: true, align: 'right', className: 'font-mono tabular-nums' },
  { key: 'Target_Company', label: 'Target', sortable: true, defaultDir: 'asc', render: (r) => <span className="text-fg">{r.Target_Company}</span> },
  { key: 'Target_Role', label: 'Role', sortable: true, defaultDir: 'asc' },
  { key: 'Placed', label: 'Placed (hist.)', sortable: true, align: 'right', render: (r) => <Badge tone={r.Placed ? 'ok' : 'alert'} dot>{r.Placed ? 'placed' : 'not placed'}</Badge> },
]

function StudentCard({ r }) {
  return (
    <div className="panel p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-lg font-semibold text-fg">{r.CGPA.toFixed(2)}</span>
        <Badge tone={r.Placed ? 'ok' : 'alert'} dot>{r.Placed ? 'placed' : 'not placed'}</Badge>
      </div>
      <div className="mt-1 text-sm text-fg">{r.Branch} · {r.Target_Company}</div>
      <div className="text-xs text-muted">{r.Target_Role}</div>
      <div className="mt-2 flex gap-4 font-mono text-xs text-muted">
        <span>apt {r.Aptitude_Score}</span><span>tech {r.Technical_Score}</span><span>intern {r.Internships}</span>
      </div>
    </div>
  )
}

function toCsv(rows) {
  const keys = Object.keys(rows[0])
  const esc = (v) => `"${String(v).replace(/"/g, '""')}"`
  return [keys.join(','), ...rows.map((r) => keys.map((k) => esc(r[k])).join(','))].join('\n')
}

export default function Recruiter() {
  const { meta } = useData()
  const toast = useToast()
  const [form, setForm] = useState({ min_cgpa: '7.5', min_apt: '65', branch: 'ALL' })
  const [errors, setErrors] = useState({})
  const [res, setRes] = useState({ status: 'loading', data: null, error: null })

  const search = useCallback(async (f, announce = false) => {
    setRes((s) => ({ ...s, status: 'loading', error: null }))
    try {
      const { data } = await api.post('/recruiter/shortlist', { min_cgpa: Number(f.min_cgpa), min_apt: Number(f.min_apt), branch: f.branch })
      setRes({ status: 'done', data, error: null })
      logEvent('ui', `shortlist cgpa>=${f.min_cgpa} apt>=${f.min_apt} ${f.branch}: ${data.total_matches} matches`)
      if (announce) toast({ tone: data.total_matches ? 'ok' : 'warn', title: `${data.total_matches} candidate${data.total_matches === 1 ? '' : 's'} match`, body: data.total_matches > 50 ? 'Showing the top 50 by CGPA.' : undefined })
    } catch (err) {
      setRes({ status: 'error', data: null, error: describeError(err) })
    }
  }, [toast])

  useEffect(() => { search(form) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function submit(e) {
    e.preventDefault()
    const errs = {}
    const c = Number(form.min_cgpa), a = Number(form.min_apt)
    if (form.min_cgpa === '' || Number.isNaN(c) || c < 0 || c > 10) errs.min_cgpa = 'Must be 0 - 10'
    if (form.min_apt === '' || Number.isNaN(a) || a < 0 || a > 100) errs.min_apt = 'Must be 0 - 100'
    setErrors(errs)
    if (Object.keys(errs).length) return
    search(form, true)
  }

  function exportCsv() {
    const blob = new Blob([toCsv(res.data.students)], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'shortlist.csv'
    a.click()
    URL.revokeObjectURL(url)
    toast({ title: 'Shortlist exported', body: `${res.data.students.length} rows saved to shortlist.csv` })
  }

  const rows = res.data?.students
  const set = (k) => (e) => setForm((s) => ({ ...s, [k]: e.target.value }))

  return (
    <div>
      <PageHeader eyebrow="Recruiter" title="Candidate shortlisting"
        subtitle="Filter the campus dataset by CGPA, aptitude and branch. Results are the top 50 by CGPA, then technical score." />
      <div className="space-y-5">
        <Card title="Filters" eyebrow="shortlist">
          <form onSubmit={submit} noValidate className="grid items-start gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_auto]" aria-label="Shortlist filters">
            <Input label="Min CGPA" type="number" step="0.1" min="0" max="10" value={form.min_cgpa} onChange={set('min_cgpa')} error={errors.min_cgpa} />
            <Input label="Min aptitude" type="number" step="1" min="0" max="100" value={form.min_apt} onChange={set('min_apt')} error={errors.min_apt} />
            <Select label="Branch" value={form.branch} onChange={set('branch')} options={[['ALL', 'All branches'], ...(meta?.branches || []).map((b) => [b, b])]} />
            <div className="flex items-end sm:col-span-2 lg:col-span-1 lg:pt-[22px]"><Button type="submit" icon={Filter} size="lg" loading={res.status === 'loading'} className="w-full">Filter</Button></div>
          </form>
        </Card>

        <Card title="Candidates" eyebrow={rows ? `${res.data.total_matches} match` : 'loading'} bodyClass="p-4" action={rows?.length ? <Button variant="secondary" size="sm" icon={Download} onClick={exportCsv}>Export CSV</Button> : null}>
          <div aria-live="polite">
            {res.status === 'error' ? <ErrorState error={res.error} onRetry={() => search(form)} title="Shortlist failed" /> : (
              <Table columns={COLS} rows={rows} loading={res.status === 'loading'} pageSize={10} rowKey={(r) => `${r.CGPA}-${r.Aptitude_Score}-${r.Technical_Score}-${r.Target_Company}-${r.Placement_Year}-${r.Communication_Score}-${r.DSA_Score}`}
                caption="Shortlisted candidates" cards={(r) => <StudentCard r={r} />}
                footer={rows ? <span className="inline-flex items-center gap-2"><StatusDot tone="ok" blink={false} />showing {rows.length} of {res.data.total_matches}</span> : undefined}
                empty={<EmptyState icon={Users} title="No candidates match" body="No student meets both thresholds for this branch. Lower the minimum CGPA or aptitude, or choose All branches."
                  action={<Button variant="secondary" onClick={() => { const f = { min_cgpa: '7.0', min_apt: '60', branch: 'ALL' }; setForm(f); setErrors({}); search(f, true) }}>Reset filters</Button>} />} />
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
