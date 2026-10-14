import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Boxes, Clock, Cpu, IndianRupee, Network, PackageCheck, RotateCcw, ShieldCheck, Sparkles, Timer, Warehouse, Zap } from 'lucide-react'
import NetworkMap from '../components/NetworkMap'
import { Stagger } from '../components/motion'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Input,
  KeyValueList,
  PageHeader,
  PageSkeleton,
  ProgressBar,
  Segmented,
  Select,
  StatCard,
  Stepper,
  Switch,
  Table,
  Timeline,
  useToast,
} from '../components/ui'
import { api } from '../lib/api'
import { celebrate } from '../lib/confetti'
import { fmtINR, fmtInt, fmtNum, fmtPct, monthLabel } from '../lib/format'
import { softSpring } from '../lib/motion'
import { cityIndex, getOptions, getRegions } from '../lib/shared'
import { useApi } from '../lib/useApi'

// keep the last plan when navigating away and back
let lastPlan = null
let lastForm = null

const NUM_FIELDS = [
  { key: 'n_hubs', label: 'Max hubs (p)', min: 1, max: 20, step: 1, hint: '1 – 20 hubs' },
  { key: 'capacity_factor', label: 'Capacity factor', min: 1, max: 5, step: 0.05, hint: 'capacity = factor × demand / p' },
  { key: 'transport_rate', label: 'Transport rate (₹/order/km)', min: 0, max: 10, step: 0.001 },
  { key: 'fixed_cost_per_hub', label: 'Fixed hub cost (₹/month)', min: 0, max: 1e9, step: 10000, hint: 'scaled by city tier' },
  { key: 'time_penalty', label: 'Time penalty (₹/order/hour)', min: 0, max: 1000, step: 0.5 },
  { key: 'sla_hours', label: 'Delivery SLA (hours)', min: 1, max: 500, step: 1 },
  { key: 'time_limit', label: 'Time limit (s)', min: 2, max: 300, step: 1, hint: 'per MIP call' },
]

const STEPS = [
  { label: 'Forecast demand', hint: 'Random Forest' },
  { label: 'Build the model', hint: 'capacitated MIP' },
  { label: 'Solve', hint: 'matheuristic / exact' },
  { label: 'Score', hint: 'KPIs on real demand' },
]

function validate(f) {
  const e = {}
  for (const d of NUM_FIELDS) {
    const v = Number(f[d.key])
    if (f[d.key] === '' || Number.isNaN(v)) e[d.key] = 'Enter a number'
    else if (v < d.min || v > d.max) e[d.key] = `Between ${d.min} and ${d.max}`
    else if (d.key === 'n_hubs' && !Number.isInteger(v)) e[d.key] = 'Whole number'
  }
  return e
}

function Elapsed() {
  const [s, setS] = useState(0)
  useEffect(() => {
    const t0 = Date.now()
    const id = setInterval(() => setS((Date.now() - t0) / 1000), 100)
    return () => clearInterval(id)
  }, [])
  return <span className="num">{s.toFixed(1)} s</span>
}

export default function Plan() {
  const toast = useToast()
  const boot = useApi(async () => {
    const [options, regions] = await Promise.all([getOptions(), getRegions()])
    return { options, regions: regions.regions }
  })
  const [f, setF] = useState(lastForm)
  const [errors, setErrors] = useState({})
  const [running, setRunning] = useState(false)
  const [res, setRes] = useState(lastPlan)
  const [reqError, setReqError] = useState(null)
  const resultsRef = useRef(null)

  const defaults = boot.data ? { ...boot.data.options.defaults, period: boot.data.options.next_period, method: 'matheuristic' } : null
  useEffect(() => {
    if (defaults && !f) setF(defaults)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boot.data])

  const set = (k, v) => {
    setF((x) => ({ ...x, [k]: v }))
    setErrors((e) => ({ ...e, [k]: undefined }))
  }

  const run = async (form = f) => {
    const errs = validate(form)
    setErrors(errs)
    if (Object.keys(errs).length) {
      toast({ kind: 'error', title: 'Check the parameters', message: 'Some values are out of range.' })
      return
    }
    const body = { ...form }
    NUM_FIELDS.forEach((d) => (body[d.key] = Number(form[d.key])))
    setRunning(true)
    setReqError(null)
    lastForm = form
    try {
      const r = { ...(await api.optimize(body)), form: body }
      setRes(r)
      lastPlan = r
      if (r.error) {
        toast({ kind: 'error', title: 'No feasible plan', message: r.error })
      } else {
        toast({ kind: 'success', title: `${r.kpi.n_hubs} hubs planned for ${monthLabel(r.period)}`, message: `${fmtINR(r.kpi.total_cost)} per month · ${fmtPct(r.kpi.fulfilment_rate)} fulfilment` })
        celebrate('plan')
        setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150)
      }
    } catch (e) {
      setReqError(e)
      toast({ kind: 'error', title: 'Optimisation failed', message: e.message })
    } finally {
      setRunning(false)
    }
  }

  const header = (
    <PageHeader
      eyebrow="Objectives 3 & 4 · Hub location"
      icon={Boxes}
      title="Plan hub locations"
      lead="Choose the planning month and network parameters. Demand comes from the Random Forest forecast - for a past month only data before it is used, so the plan is scored against what really happened."
    />
  )

  if (boot.loading || (!f && !boot.error))
    return (
      <>
        {header}
        <PageSkeleton kpis={3} blocks={1} />
      </>
    )
  if (boot.error)
    return (
      <>
        {header}
        <ErrorState title="Could not load planning options" error={boot.error} onRetry={boot.reload} />
      </>
    )

  const { options, regions } = boot.data
  const ok = res && !res.error
  const k = ok ? res.kpi : null
  const idx = cityIndex(regions)
  const assign = ok ? res.kpi.assignment.map((a) => idx[a.hub]) : null

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      {header}

      <Card title="Parameters" subtitle="Defaults come from hublocator/config.py" hover={false}>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            run()
          }}
          noValidate
        >
          <div className="form-grid">
            <Select
              label="Planning month"
              value={f.period}
              onChange={(e) => set('period', e.target.value)}
              options={options.plan_periods.map((p, i) => ({ value: p, label: `${monthLabel(p)}${i === 0 ? ' (next month)' : ''}` }))}
              hint={f.period === options.next_period ? 'Scored on the forecast' : 'Scored on realised demand'}
            />
            {NUM_FIELDS.map((d) => (
              <Input
                key={d.key}
                label={d.label}
                type="number"
                inputMode="decimal"
                min={d.min}
                max={d.max}
                step={d.step}
                value={f[d.key]}
                onChange={(e) => set(d.key, e.target.value)}
                error={errors[d.key]}
                hint={d.hint}
              />
            ))}
          </div>
          <div className="row" style={{ marginTop: 22, '--gap': '22px', alignItems: 'flex-end' }}>
            <Segmented
              name="method"
              label="Method"
              value={f.method}
              onChange={(v) => set('method', v)}
              options={[
                { value: 'matheuristic', label: 'Matheuristic (proposed)', icon: Sparkles },
                { value: 'exact', label: options.has_pulp ? 'Exact MIP (traditional)' : 'Exact MIP (needs pulp)', icon: Cpu },
              ]}
            />
            <Switch
              checked={!!f.sla_hard}
              onChange={(v) => set('sla_hard', v)}
              label={f.sla_hard ? 'Hard SLA' : 'Soft SLA'}
              description={f.sla_hard ? 'late assignments are forbidden' : 'late deliveries are penalised'}
            />
          </div>
          <div className="row" style={{ marginTop: 24 }}>
            <Button type="submit" size="lg" icon={Zap} loading={running}>
              {running ? 'Optimising…' : 'Optimise network'}
            </Button>
            <Button
              variant="ghost"
              icon={RotateCcw}
              disabled={running}
              onClick={() => {
                setF(defaults)
                setErrors({})
              }}
            >
              Reset to defaults
            </Button>
          </div>
        </form>
      </Card>

      <AnimatePresence mode="wait">
        {running && (
          <motion.div key="run" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={softSpring}>
            <Card hover={false} tint="lavender">
              <div className="row between" style={{ marginBottom: 14 }}>
                <strong>
                  Solving {f.method === 'exact' ? 'the exact MIP' : 'with the matheuristic'} for {monthLabel(f.period)}…
                </strong>
                <span className="muted small">
                  <Timer size={14} aria-hidden="true" style={{ verticalAlign: -2, marginRight: 4 }} />
                  <Elapsed />
                </span>
              </div>
              <Stepper steps={STEPS} current={2} label="Optimisation pipeline" />
              <div style={{ marginTop: 16 }}>
                <ProgressBar indeterminate label="Optimisation running" />
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <div ref={resultsRef} style={{ scrollMarginTop: 90 }} />
      {!running && reqError && <ErrorState title="The optimisation request failed" error={reqError} onRetry={() => run()} />}
      {!running && !reqError && res?.error && (
        <ErrorState
          title="No feasible plan for these parameters"
          error={res.error}
          hint="Raise the number of hubs or the capacity factor, or switch the SLA to soft, then optimise again."
          onRetry={() => run()}
        />
      )}
      {!running && !reqError && !res && (
        <EmptyState
          icon={Network}
          title="Plan your first network"
          message="Run the optimiser with the defaults to see which hubs open, how regions are allocated and what it costs."
          action={
            <Button icon={Zap} onClick={() => run(defaults)}>
              Run with defaults
            </Button>
          }
        />
      )}

      {ok && !running && (
        <motion.div className="stack" style={{ '--gap': '22px' }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} key={`${res.period}-${res.kpi.total_cost}`}>
          <div className="row between">
            <h2>
              Plan for {monthLabel(res.period, true)}{' '}
              <Badge tone={res.realized ? 'mint' : 'sky'} dot>
                {res.realized ? 'scored on realised demand' : 'scored on forecast'}
              </Badge>
            </h2>
          </div>
          <Stepper steps={STEPS} current={4} label="Optimisation pipeline" />
          <Stagger className="grid-kpi">
            <Stagger.Item>
              <StatCard label="Hubs opened" value={k.n_hubs} icon={Warehouse} tone="lavender" foot={k.hub_cities.join(', ')} />
            </Stagger.Item>
            <Stagger.Item>
              <StatCard label="Monthly operating cost" value={k.total_cost} format={(v) => fmtINR(v)} icon={IndianRupee} tone="peach" foot={`₹${fmtNum(k.cost_per_order, 2)} per order`} />
            </Stagger.Item>
            <Stagger.Item>
              <StatCard label="Avg delivery time" value={k.avg_delivery_hours} format={(v) => `${v.toFixed(1)} h`} icon={Clock} tone="sky" foot={`max ${k.max_delivery_hours} h · ${k.avg_distance_km} km avg`} />
            </Stagger.Item>
            <Stagger.Item>
              <StatCard label="Fulfilment rate" value={k.fulfilment_rate * 100} format={(v) => `${v.toFixed(1)}%`} icon={PackageCheck} tone="mint" foot={res.realized ? 'on realised demand' : 'on forecast'} />
            </Stagger.Item>
            <Stagger.Item>
              <StatCard label="Within SLA" value={k.reliability_sla * 100} format={(v) => `${v.toFixed(1)}%`} icon={ShieldCheck} tone="rose" foot={`orders delivered within ${fmtInt(res.form.sla_hours)} h`} />
            </Stagger.Item>
            <Stagger.Item>
              <StatCard
                label="Solve time"
                value={res.sol.seconds}
                format={(v) => `${v.toFixed(2)} s`}
                icon={Cpu}
                tone="lavender"
                foot={`${res.sol.status}${res.sol.subproblems_solved ? ` · ${res.sol.subproblems_solved} sub-MIPs · kernel ${res.sol.kernel_status}` : ''}`}
              />
            </Stagger.Item>
          </Stagger>

          <div className="grid-2 wide-left">
            <Card title="Network map" subtitle="Squares are hubs; circles are regions sized by demand and coloured by their hub">
              <NetworkMap regions={regions} hubs={res.sol.hubs} assign={assign} demand={res.demand_used} label={`Map of ${k.n_hubs} hubs serving ${regions.length} regions`} />
            </Card>
            <div className="stack">
              <Card title={`Hub utilisation${res.realized ? ' (realised demand)' : ''}`} subtitle="Load ÷ capacity">
                <div className="stack" style={{ '--gap': '15px' }}>
                  {Object.entries(k.utilisation).map(([h, u]) => (
                    <div key={h}>
                      <div className="row between" style={{ marginBottom: 6 }}>
                        <span style={{ fontWeight: 600 }}>{regions[Number(h)].city}</span>
                        <span className="row" style={{ '--gap': '8px' }}>
                          <span className="num small">{Math.round(u * 100)}%</span>
                          <Badge tone={u > 1 ? 'rose' : u > 0.9 ? 'peach' : 'mint'}>{u > 1 ? 'overloaded' : u > 0.9 ? 'tight' : 'ok'}</Badge>
                        </span>
                      </div>
                      <ProgressBar value={Math.min(u, 1)} tone={u > 1 ? 'rose' : u > 0.9 ? 'peach' : 'mint'} label={`${regions[Number(h)].city} utilisation`} />
                    </div>
                  ))}
                </div>
              </Card>
              <Card title="Cost split" subtitle="Per month">
                <KeyValueList
                  items={[
                    ['Fixed hub cost', fmtINR(k.fixed_cost, false)],
                    ['Transport', fmtINR(k.transport_cost, false)],
                    ['Delivery-time penalty', fmtINR(k.time_cost, false)],
                    ['Total', fmtINR(k.total_cost, false)],
                    ['Overloaded hubs', k.overloaded_hubs],
                  ]}
                />
              </Card>
            </div>
          </div>

          <div className="grid-2">
            <Card title="Search log" subtitle={res.sol.log?.length ? 'How the matheuristic improved the objective' : undefined}>
              {res.sol.log?.length ? (
                <Timeline
                  items={res.sol.log.map((l, i) => ({
                    id: i,
                    title: (
                      <>
                        {l.phase} <span className="num muted small">{fmtINR(l.objective)}</span>
                      </>
                    ),
                    meta: `t = ${l.t} s`,
                    tone: ['lavender', 'sky', 'mint', 'peach', 'rose'][i % 5],
                  }))}
                />
              ) : (
                <p className="muted">Exact MIP: {res.sol.status}</p>
              )}
            </Card>
            <Card title="Region allocation" subtitle={`${k.assignment.length} regions`} hover={false}>
              <Table
                caption="Region allocation"
                rows={k.assignment}
                rowKey={(r) => r.region_id}
                pageSize={8}
                searchKeys={['region', 'hub']}
                searchPlaceholder="Search region or hub"
                columns={[
                  { key: 'region', label: 'Region' },
                  { key: 'hub', label: 'Served by', render: (r) => (r.hub === r.region ? <Badge tone="lavender">hub</Badge> : r.hub) },
                  { key: 'demand', label: 'Demand', numeric: true, render: (r) => fmtInt(r.demand) },
                  { key: 'distance_km', label: 'Distance', numeric: true, render: (r) => `${r.distance_km} km` },
                  {
                    key: 'hours',
                    label: 'Delivery',
                    numeric: true,
                    render: (r) => (r.hours > res.form.sla_hours ? <Badge tone="rose">{r.hours} h</Badge> : `${r.hours} h`),
                  },
                ]}
              />
            </Card>
          </div>
        </motion.div>
      )}
    </div>
  )
}
