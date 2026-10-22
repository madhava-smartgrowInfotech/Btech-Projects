import { ArrowRight, Check, Play, RotateCcw, Target, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api, { describeError } from '../api'
import ProfileFields from '../components/ProfileFields'
import { Button } from '../components/ui/controls'
import { Select } from '../components/ui/controls'
import { Badge, Card, KeyValueList, ProbBadge, ScoreBar } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import { PageHeader } from '../components/ui/AppShell'
import { SlideUp } from '../components/motion'
import { lpa, pct, probTone, TIER_TONE } from '../format'
import { logEvent } from '../lib/activity'
import { useData } from '../lib/data'
import { numeric, PREDICT_DEFAULTS, validate } from '../lib/profile'

const SCORE_KEYS = ['cgpa', 'tenth', 'twelfth', 'aptitude', 'technical', 'communication', 'dsa']
const COUNT_KEYS = ['projects', 'internships', 'certifications', 'backlogs']
const ALL_KEYS = [...SCORE_KEYS, ...COUNT_KEYS]

export default function Predict() {
  const { meta, error: metaError, reload } = useData()
  const toast = useToast()
  const [params] = useSearchParams()
  const [values, setValues] = useState(PREDICT_DEFAULTS)
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('SDE')
  const [errors, setErrors] = useState({})
  const [state, setState] = useState({ status: 'idle', result: null, error: null })

  // default to the first company (as the Flask form did) unless the URL names one
  useEffect(() => {
    if (!meta) return
    const wanted = params.get('company')
    setCompany(wanted && meta.companies.includes(wanted) ? wanted : meta.companies[0])
  }, [meta, params])

  const set = (k, v) => {
    setValues((s) => ({ ...s, [k]: v }))
    setErrors((e) => (e[k] ? { ...e, [k]: undefined } : e))
  }

  async function run(e) {
    e.preventDefault()
    const errs = validate(values, ALL_KEYS)
    setErrors(errs)
    if (Object.keys(errs).length) {
      toast({ tone: 'warn', title: 'Check the highlighted fields', body: 'Some values are out of range.' })
      document.getElementById(`f-${Object.keys(errs)[0]}`)?.focus()
      return
    }
    setState({ status: 'loading', result: null, error: null })
    try {
      const { data } = await api.post('/predict', {
        ...numeric(values, ALL_KEYS), branch: values.branch, degree: values.degree, target_company: company, target_role: role,
      })
      setState({ status: 'done', result: data, error: null, sent: { ...values, company, role } })
      logEvent('ui', `prediction ${data.company} / ${data.role} -> ${pct(data.placement_probability)}`)
      toast({ tone: data.eligible ? 'ok' : 'warn', title: data.eligible ? 'Placement ready' : 'Needs improvement', body: `${pct(data.placement_probability)} at ${data.company} (${data.role})` })
    } catch (err) {
      setState({ status: 'error', result: null, error: describeError(err) })
    }
  }

  function reset() {
    setValues(PREDICT_DEFAULTS)
    setErrors({})
    setState({ status: 'idle', result: null, error: null })
  }

  const opt = (list) => list.map((x) => [x, x])
  const companyDetail = useMemo(() => state.result?.company_detail, [state.result])

  return (
    <div>
      <PageHeader eyebrow="Student · hybrid XGBoost + kNN" title="Placement eligibility"
        subtitle="Probability of placement for one company and role, with the skill gaps that hold it back." />

      {metaError && !meta ? <ErrorState error={metaError} onRetry={reload} title="Could not load companies" /> : (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,460px)]">
          <Card title="Student profile" eyebrow="input">
            {!meta ? (
              <div className="grid gap-3 sm:grid-cols-3">{Array.from({ length: 9 }, (_, i) => <Skeleton key={i} className="h-14" />)}</div>
            ) : (
              <form onSubmit={run} noValidate className="space-y-5" aria-label="Student profile">
                <fieldset className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <legend className="sr-only">Target</legend>
                  <Select label="Company" value={company} onChange={(e) => setCompany(e.target.value)} options={opt(meta.companies)} />
                  <Select label="Role" value={role} onChange={(e) => setRole(e.target.value)} options={opt(meta.predict_roles)} />
                  <Select label="Branch" value={values.branch} onChange={(e) => set('branch', e.target.value)} options={opt(meta.branches)} />
                  <Select label="Degree" value={values.degree} onChange={(e) => set('degree', e.target.value)} options={opt(meta.degrees)} />
                </fieldset>
                <fieldset className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <legend className="mb-3 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">Scores</legend>
                  <ProfileFields keys={SCORE_KEYS} values={values} errors={errors} onChange={set} />
                </fieldset>
                <fieldset className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <legend className="mb-3 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">Experience</legend>
                  <ProfileFields keys={COUNT_KEYS} values={values} errors={errors} onChange={set} />
                </fieldset>
                <div className="flex flex-wrap gap-2">
                  <Button type="submit" icon={Play} loading={state.status === 'loading'} size="lg">Run prediction</Button>
                  <Button variant="secondary" icon={RotateCcw} size="lg" onClick={reset}>Reset</Button>
                </div>
              </form>
            )}
          </Card>

          <div className="min-w-0 xl:sticky xl:top-20 xl:self-start" aria-live="polite">
            {state.status === 'idle' && (
              <Card title="Result" eyebrow="output">
                <EmptyState icon={Target} title="No prediction yet" body="Fill in the profile, pick a company and role, then run the prediction."
                  action={<Button variant="secondary" onClick={() => document.getElementById('f-cgpa')?.focus()}>Edit profile</Button>} />
              </Card>
            )}
            {state.status === 'loading' && (
              <Card title="Result" eyebrow="running model…" bodyClass="space-y-3 p-4">
                <Skeleton className="h-10 w-40" /><Skeleton className="h-3 w-full" /><Skeleton className="h-24 w-full" /><Skeleton className="h-16 w-full" />
              </Card>
            )}
            {state.status === 'error' && <ErrorState error={state.error} onRetry={() => run({ preventDefault() {} })} title="Prediction failed" />}
            {state.status === 'done' && state.result && (
              <SlideUp>
                <Card title="Result" eyebrow={`${state.result.company} · ${state.result.role}`}>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <ProbBadge value={state.result.placement_probability} size="lg" />
                    <Badge tone={state.result.eligible ? 'ok' : 'warn'} dot>{state.result.label}</Badge>
                  </div>
                  <div className="mt-4"><ScoreBar value={state.result.placement_probability} label="Placement probability" /></div>

                  <h3 className="mb-1 mt-6 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">Profile vs company cutoffs</h3>
                  <ul className="divide-y divide-dashed divide-line">
                    {[['CGPA', Number(state.sent.cgpa), companyDetail.CGPA_Cutoff], ['Aptitude', Number(state.sent.aptitude), companyDetail.Apt_Cutoff], ['Technical', Number(state.sent.technical), companyDetail.Tech_Cutoff]].map(([n, mine, cut]) => (
                      <li key={n} className="flex items-center gap-3 py-2 text-sm">
                        {mine >= cut ? <Check size={15} className="text-ok" aria-hidden="true" /> : <X size={15} className="text-alert" aria-hidden="true" />}
                        <span className="flex-1 text-muted">{n}</span>
                        <span className="font-mono tabular-nums text-fg">{mine} <span className="text-dim">/ {cut}</span></span>
                        <span className="sr-only">{mine >= cut ? 'meets cutoff' : 'below cutoff'}</span>
                      </li>
                    ))}
                  </ul>

                  <h3 className="mb-1 mt-6 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">Company</h3>
                  <KeyValueList items={[
                    ['Tier', <Badge key="t" tone={TIER_TONE[companyDetail.Tier]}>tier {companyDetail.Tier}</Badge>],
                    ['Package', lpa(companyDetail.Package_LPA)], ['Location', companyDetail.Location],
                    ['Type', companyDetail.Company_Type], ['Hiring rate', pct(companyDetail.Hiring_Rate, 0)],
                  ]} />

                  <h3 className="mb-2 mt-6 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">Skill-gap tips</h3>
                  <ul className="prose-case text-sm text-muted">
                    {state.result.tips.map((t) => <li key={t}>{t}</li>)}
                  </ul>

                  <div className="mt-5 border-t border-line pt-4">
                    <Link to="/recommend" state={{ from: state.sent }} className="inline-flex items-center gap-1.5 font-mono text-xs text-ok hover:underline">
                      Not confident? Get better company-role alternatives <ArrowRight size={13} aria-hidden="true" />
                    </Link>
                  </div>
                </Card>
              </SlideUp>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
