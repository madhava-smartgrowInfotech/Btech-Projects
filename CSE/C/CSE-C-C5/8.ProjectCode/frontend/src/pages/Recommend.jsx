import { Play, RotateCcw, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import api, { describeError } from '../api'
import { MonoBars } from '../components/charts/Bars'
import ProfileFields from '../components/ProfileFields'
import { PageHeader } from '../components/ui/AppShell'
import { Button, Select } from '../components/ui/controls'
import { Badge, Card, ProbBadge, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import { TabPanel, Tabs } from '../components/ui/nav'
import Table from '../components/ui/Table'
import { SlideUp, Stagger } from '../components/motion'
import { lpa, pct, TIER_TONE } from '../format'
import { logEvent } from '../lib/activity'
import { useData } from '../lib/data'
import { numeric, RECOMMEND_DEFAULTS, validate } from '../lib/profile'

const KEYS = ['cgpa', 'aptitude', 'technical', 'communication', 'dsa', 'projects', 'internships', 'certifications', 'backlogs']

const columns = (base) => [
  { key: 'rank', label: '#', className: 'font-mono text-dim', render: (r) => r._rank },
  { key: 'company', label: 'Company', sortable: true, defaultDir: 'asc', render: (r) => <span className="font-medium text-fg">{r.company}</span> },
  { key: 'role', label: 'Role', sortable: true, defaultDir: 'asc' },
  { key: 'tier', label: 'Tier', sortable: true, defaultDir: 'asc', render: (r) => <Badge tone={TIER_TONE[r.tier]}>tier {r.tier}</Badge> },
  { key: 'package', label: 'Package', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => lpa(r.package) },
  { key: 'location', label: 'Location', sortable: true, defaultDir: 'asc' },
  { key: 'proximity', label: 'CGPA fit', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => pct(r.proximity, 0) },
  { key: 'prob', label: 'Probability', sortable: true, align: 'right', render: (r) => <ProbBadge value={r.prob} /> },
  { key: 'gain', label: 'vs base', align: 'right', sortValue: (r) => r.prob - base,
    render: (r) => <span className={`font-mono text-xs tabular-nums ${r.prob >= base ? 'text-ok' : 'text-alert'}`}>{r.prob >= base ? '+' : ''}{((r.prob - base) * 100).toFixed(1)} pt</span> },
]

function Cards({ r, base }) {
  return (
    <div className="panel p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-medium text-fg">{r._rank}. {r.company}</div>
          <div className="text-xs text-muted">{r.role} · {r.location} · {lpa(r.package)}</div>
        </div>
        <ProbBadge value={r.prob} />
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs text-muted">
        <Badge tone={TIER_TONE[r.tier]}>tier {r.tier}</Badge>
        <span className="font-mono">CGPA fit {pct(r.proximity, 0)}</span>
        <span className={`ml-auto font-mono ${r.prob >= base ? 'text-ok' : 'text-alert'}`}>{r.prob >= base ? '+' : ''}{((r.prob - base) * 100).toFixed(1)} pt</span>
      </div>
    </div>
  )
}

export default function Recommend() {
  const { meta, error: metaError, reload } = useData()
  const toast = useToast()
  const { state: nav } = useLocation()
  const [values, setValues] = useState(RECOMMEND_DEFAULTS)
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('SDE')
  const [location, setLocation] = useState('')
  const [errors, setErrors] = useState({})
  const [tab, setTab] = useState('hybrid')
  const [run, setRun] = useState({ status: 'idle', out: null, error: null })

  // arriving from the Eligibility screen: carry the profile over
  useEffect(() => {
    if (nav?.from) setValues((v) => Object.fromEntries(Object.keys(v).map((k) => [k, nav.from[k] ?? v[k]])))
  }, [nav])
  useEffect(() => {
    if (!meta) return
    setCompany(nav?.from?.company && meta.companies.includes(nav.from.company) ? nav.from.company : meta.companies[0])
    if (nav?.from?.role && meta.recommend_roles.includes(nav.from.role)) setRole(nav.from.role)
  }, [meta, nav])

  const set = (k, v) => {
    setValues((s) => ({ ...s, [k]: v }))
    setErrors((e) => (e[k] ? { ...e, [k]: undefined } : e))
  }

  async function submit(e) {
    e.preventDefault()
    const errs = validate(values, KEYS)
    setErrors(errs)
    if (Object.keys(errs).length) {
      toast({ tone: 'warn', title: 'Check the highlighted fields', body: 'Some values are out of range.' })
      document.getElementById(`f-${Object.keys(errs)[0]}`)?.focus()
      return
    }
    setRun({ status: 'loading', out: null, error: null })
    try {
      const { data } = await api.post('/recommend', {
        ...numeric(values, KEYS), branch: values.branch, target_company: company, target_role: role, location: location || null,
      })
      setRun({ status: 'done', out: data, error: null, company, role })
      setTab('hybrid')
      logEvent('ui', `recommend ${company}/${role}: base ${pct(data.base_prob)}, ${data.hybrid.length} alternatives`)
      toast({ tone: data.hybrid.length ? 'ok' : 'warn', title: data.hybrid.length ? 'Recommendations ready' : 'No feasible alternatives', body: data.hybrid.length ? `Top ${data.hybrid.length} company-role pairs ranked.` : 'No company passes the CGPA / aptitude filters.' })
    } catch (err) {
      setRun({ status: 'error', out: null, error: describeError(err) })
    }
  }

  const out = run.out
  const list = out ? { hybrid: out.hybrid, company: out.company_only, role: out.role_only }[tab] : []
  const rows = list.map((r, i) => ({ ...r, _rank: i + 1 }))
  const chart = out?.hybrid.map((r, i) => ({ name: `${i + 1}. ${r.company} · ${r.role}`, prob: r.prob, base: out.base_prob }))
  const opt = (a) => a.map((x) => [x, x])
  const tabs = out && [
    { id: 'hybrid', label: 'Hybrid', count: out.hybrid.length },
    { id: 'company', label: 'Company-only', count: out.company_only.length },
    { id: 'role', label: 'Role-only', count: out.role_only.length },
  ]

  return (
    <div>
      <PageHeader eyebrow="Rejected / low probability?" title="Company-role recommendations"
        subtitle="Ranks alternatives by calibrated acceptance probability, CGPA proximity and location preference (base paper §3.8-3.12)." />

      {metaError && !meta ? <ErrorState error={metaError} onRetry={reload} title="Could not load companies" /> : (
        <div className="space-y-5">
          <Card title="Student profile" eyebrow="input">
            {!meta ? (
              <div className="grid gap-3 sm:grid-cols-4">{Array.from({ length: 8 }, (_, i) => <Skeleton key={i} className="h-14" />)}</div>
            ) : (
              <form onSubmit={submit} noValidate className="space-y-5" aria-label="Recommendation profile">
                <fieldset className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <legend className="sr-only">Dream target</legend>
                  <Select label="Dream company" value={company} onChange={(e) => setCompany(e.target.value)} options={opt(meta.companies)} />
                  <Select label="Dream role" value={role} onChange={(e) => setRole(e.target.value)} options={opt(meta.recommend_roles)} />
                  <Select label="Branch" value={values.branch} onChange={(e) => set('branch', e.target.value)} options={opt(meta.branches)} />
                  <Select label="Preferred location" value={location} onChange={(e) => setLocation(e.target.value)} options={[['', 'No preference'], ...opt(meta.locations)]} />
                </fieldset>
                <fieldset className="grid gap-4 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9">
                  <legend className="sr-only">Scores and experience</legend>
                  <ProfileFields keys={KEYS} values={values} errors={errors} onChange={set} />
                </fieldset>
                <div className="flex flex-wrap gap-2">
                  <Button type="submit" icon={Play} size="lg" loading={run.status === 'loading'}>Recommend</Button>
                  <Button variant="secondary" icon={RotateCcw} size="lg" onClick={() => { setValues(RECOMMEND_DEFAULTS); setErrors({}); setRun({ status: 'idle', out: null, error: null }) }}>Reset</Button>
                </div>
              </form>
            )}
          </Card>

          <div aria-live="polite" className="space-y-5">
            {run.status === 'idle' && (
              <Card><EmptyState icon={Sparkles} title="No recommendations yet" body="Enter the profile and dream company, then press Recommend. Ranking takes a couple of seconds - every company is scored with the model."
                action={<Button variant="secondary" onClick={() => document.getElementById('f-cgpa')?.focus()}>Edit profile</Button>} /></Card>
            )}
            {run.status === 'loading' && (
              <div className="space-y-4" aria-busy="true">
                <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
                <Skeleton className="h-72" />
              </div>
            )}
            {run.status === 'error' && <ErrorState error={run.error} onRetry={() => submit({ preventDefault() {} })} title="Recommendation failed" />}
            {run.status === 'done' && out && (
              <SlideUp className="space-y-5">
                <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                  <StatCard label="Base probability" value={out.base_prob * 100} format={(v) => `${v.toFixed(1)}%`} sub={`${run.company} · ${run.role}`} tone={out.base_prob >= 0.5 ? 'ok' : 'hot'} />
                  <StatCard label="Avg. gain" value={out.avg_gain * 100} format={(v) => `${v >= 0 ? '+' : ''}${v.toFixed(1)} pt`} sub="over improved alternatives" tone="cyan" />
                  <StatCard label="Match rate" value={out.match_rate * 100} format={(v) => `${v.toFixed(0)}%`} sub="alternatives beating base" tone="info" />
                  <StatCard label="Top pick" value={out.hybrid[0] ? out.hybrid[0].company : '-'} sub={out.hybrid[0] ? `${out.hybrid[0].role} · ${pct(out.hybrid[0].prob)}` : 'no feasible alternative'} tone="ok" />
                </Stagger>

                {out.hybrid.length === 0 ? (
                  <Card><EmptyState icon={Sparkles} title="No feasible alternatives" body="Every company was filtered out by the CGPA-proximity, aptitude or backlog rules. Raise CGPA / aptitude, or clear backlogs, and try again."
                    action={<Button variant="secondary" onClick={() => document.getElementById('f-cgpa')?.focus()}>Edit profile</Button>} /></Card>
                ) : (
                  <>
                    <Card title="Hybrid top picks vs base" eyebrow="acceptance probability">
                      <MonoBars data={chart} xKey="name" series={[{ key: 'prob', label: 'Alternative', tone: 'ok' }, { key: 'base', label: 'Base target', tone: 'hot' }]}
                        valueFormat={(v) => pct(v, 0)} angle={-18} height={300} label="Bar chart: acceptance probability of each recommended alternative against the base target" />
                    </Card>
                    <Card title="Ranked alternatives" bodyClass="p-4">
                      <Tabs id="rec" tabs={tabs} value={tab} onChange={setTab} label="Recommendation strategy" />
                      <TabPanel tabsId="rec" value={tab} className="pt-3">
                        <Table columns={columns(out.base_prob)} rows={rows} rowKey={(r) => `${r.company}-${r.role}`} caption={`${tab} recommendations`}
                          cards={(r) => <Cards r={r} base={out.base_prob} />}
                          empty={<EmptyState title="Nothing in this view" body="Role-only keeps your dream company fixed; it is empty when that company fails the feasibility filters." />} />
                      </TabPanel>
                    </Card>
                    <div className="flex flex-wrap gap-2 font-mono text-[11px] text-dim">
                      <Badge>hybrid = best company-role pairs</Badge><Badge>company-only = best role per company</Badge><Badge>role-only = dream company, vary role</Badge>
                    </div>
                  </>
                )}
              </SlideUp>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
