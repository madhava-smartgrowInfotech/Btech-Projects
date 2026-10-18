// Project-level building blocks shared by the screens.
import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, BrainCircuit, CheckCircle2, Database, Info, Rocket, XCircle } from 'lucide-react'
import { api } from '../../lib/api'
import { celebrate, useAppState } from '../../lib/appstate'
import { useAsync, useDebounced } from '../../lib/hooks'
import { RISK_COLOR, RISK_TONE, shortBand } from '../../lib/risk'
import { fmtNum } from '../../lib/format'
import { Badge, Button, EmptyState, ErrorState, Modal, PageSkeleton, ProgressBar, SearchField, Select, Skeleton, Stepper, useToast } from '../ui'

const CALLOUT_ICON = { info: Info, success: CheckCircle2, warn: AlertTriangle, error: XCircle }

export function Callout({ tone = 'info', title, children, role }) {
  const Icon = CALLOUT_ICON[tone] || Info
  return (
    <div className={`callout ${tone}`} role={role || (tone === 'error' ? 'alert' : 'note')}>
      <Icon size={20} aria-hidden="true" />
      <div>
        {title && <strong>{title}</strong>}
        <div>{children}</div>
      </div>
    </div>
  )
}

export function RiskBadge({ band, short = false }) {
  if (!band) return null
  return (
    <Badge tone={RISK_TONE[band] || 'neutral'} dot>
      {short ? shortBand(band) : band}
    </Badge>
  )
}

/** Semi-circular probability gauge. */
export function Gauge({ value, band, label = 'Churn probability' }) {
  const v = Math.max(0, Math.min(100, value ?? 0))
  const arc = 'M 20 100 A 80 80 0 0 1 180 100'
  return (
    <div className="gauge" role="img" aria-label={`${label}: ${v.toFixed(1)} percent${band ? `, ${band}` : ''}`}>
      <svg viewBox="0 0 200 118" aria-hidden="true">
        <path d={arc} className="gauge-track" />
        <motion.path
          d={arc}
          className="gauge-arc"
          style={{ stroke: RISK_COLOR[band] || 'var(--lavender)' }}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: v / 100 }}
          transition={{ type: 'spring', stiffness: 60, damping: 16 }}
        />
        <text x="100" y="92" textAnchor="middle" className="gauge-num">
          {v.toFixed(1)}%
        </text>
        <text x="100" y="112" textAnchor="middle" className="gauge-label">
          {label}
        </text>
      </svg>
    </div>
  )
}

export function Slider({ id, label, value, min, max, step = 1, onChange, format = (v) => v, hint }) {
  const pct = max === min ? 0 : ((value - min) / (max - min)) * 100
  return (
    <div className="field">
      <label className="field-label slider-label" htmlFor={id}>
        <span>{label}</span>
        <output className="slider-val num" htmlFor={id}>
          {format(value)}
        </output>
      </label>
      <input
        id={id}
        type="range"
        className="slider"
        min={min}
        max={max}
        step={step}
        value={value}
        style={{ '--pct': `${pct}%` }}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      {hint && <span className="field-hint">{hint}</span>}
    </div>
  )
}

/** Toggle pills (multi-select). options: [{value, label}] */
export function ChipGroup({ options, value, onChange, label }) {
  const toggle = (v) => onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v])
  return (
    <div role="group" aria-label={label} className="chips">
      {options.map((o) => {
        const opt = typeof o === 'string' ? { value: o, label: o } : o
        const on = value.includes(opt.value)
        return (
          <button key={opt.value} type="button" className={`chip-btn ${on ? 'on' : ''}`} aria-pressed={on} onClick={() => toggle(opt.value)}>
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}

/** Colour-scaled grid for the correlation matrix and the confusion matrix. */
export function HeatGrid({ xLabels, yLabels, matrix, format = (v) => v, tone = 'sequential', cell = 56, label, xTitle, yTitle }) {
  const flat = matrix.flat().filter((v) => v != null)
  const max = tone === 'diverging' ? 1 : Math.max(...flat, 1)
  return (
    <div className="heat-wrap" role="img" aria-label={label}>
      {yTitle && <span className="heat-ytitle">{yTitle}</span>}
      <div className="heat-scroll">
        <div className="heat" style={{ gridTemplateColumns: `max-content repeat(${xLabels.length}, minmax(${cell}px, 1fr))` }}>
          <span />
          {xLabels.map((x) => (
            <span key={x} className="heat-x" title={x}>
              {x}
            </span>
          ))}
          {matrix.map((row, i) => (
            <div key={yLabels[i]} style={{ display: 'contents' }}>
              <span className="heat-y" title={yLabels[i]}>
                {yLabels[i]}
              </span>
              {row.map((v, j) => {
                const strength = v == null ? 0 : Math.min(100, (Math.abs(v) / max) * 100)
                const base = tone === 'diverging' ? (v >= 0 ? 'var(--lavender)' : 'var(--peach)') : 'var(--sky)'
                return (
                  <span key={j} className="heat-cell num" style={{ background: `color-mix(in srgb, ${base} ${Math.round(strength * 0.9)}%, var(--surface-2))`, height: cell }}>
                    {v == null ? '–' : format(v)}
                  </span>
                )
              })}
            </div>
          ))}
        </div>
      </div>
      {xTitle && <span className="heat-xtitle">{xTitle}</span>}
    </div>
  )
}

/** Search + select a customer (highest risk first). */
export function CustomerPicker({ value, onChange, label = 'Customer' }) {
  const [q, setQ] = useState('')
  const dq = useDebounced(q, 300)
  const { data, loading, error, reload } = useAsync(() => api.customers(dq, 100), [dq])
  useEffect(() => {
    if (!value && data?.rows?.length) onChange(data.rows[0].id)
  }, [data, value, onChange])
  const options = useMemo(() => {
    const rows = (data?.rows || []).map((r) => ({
      value: r.id,
      label: `${data.has_id ? r.id : `Row ${r.id}`} · ${r.probability.toFixed(1)}% · ${shortBand(r.risk)}`,
    }))
    if (value && !rows.some((r) => r.value === value)) rows.unshift({ value, label: data?.has_id === false ? `Row ${value}` : value })
    return rows
  }, [data, value])
  if (error && !data) return <ErrorState compact title="Could not load customers" error={error} onRetry={reload} />
  return (
    <div className="picker">
      <SearchField value={q} onChange={setQ} label="Search customers" placeholder={data?.has_id === false ? 'Search row number' : 'Search customer ID'} />
      {loading && !data ? (
        <Skeleton height={50} radius={16} />
      ) : (
        <Select
          label={label}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          options={options.length ? options : [{ value: '', label: 'No customers match' }]}
          hint={data ? `${data.matched.toLocaleString('en-IN')} match${data.matched === 1 ? '' : 'es'} · highest risk first · showing up to 100` : undefined}
        />
      )}
    </div>
  )
}

/** Wraps a screen that needs a prepared dataset, a trial run, or an active model. */
export function Gate({ need = 'model', children }) {
  const { state, error, hasData, hasModel, hasTrial, refresh } = useAppState()
  if (error && !state) return <ErrorState title="Cannot reach the API" error={error} onRetry={refresh} />
  if (!state) return <PageSkeleton />
  if ((need === 'data' || need === 'model') && !hasData) {
    return (
      <EmptyState
        icon={Database}
        title="Load a dataset first"
        message="This screen works on a prepared customer dataset. Load the built-in sample (1,000 synthetic telecom customers) or upload your own CSV."
        action={
          <>
            {hasModel ? <LoadSampleButton /> : <QuickStartButton />}
            <Button variant="secondary" to="/app/data">
              Go to Data upload
            </Button>
          </>
        }
      />
    )
  }
  if (need === 'trial' && !hasTrial) {
    return (
      <EmptyState
        icon={BrainCircuit}
        tone="peach"
        title="No models trained in this session"
        message="Training happens on the Model training screen. Comparison curves and confusion matrices appear here afterwards."
        action={
          <Button to="/app/train" icon={BrainCircuit}>
            Train models
          </Button>
        }
      />
    )
  }
  if (need === 'model' && !hasModel) {
    return (
      <EmptyState
        icon={BrainCircuit}
        tone="peach"
        title="Train and save a model first"
        message="Risk scoring, explanations, what-if and recommendations all use the active model. Train the three required models, then save the best one."
        action={
          <>
            <QuickStartButton />
            <Button variant="secondary" to="/app/train">
              Open Model training
            </Button>
          </>
        }
      />
    )
  }
  return children
}

/** Loads and prepares the sample dataset without touching the active model (useful after a restart). */
export function LoadSampleButton({ variant = 'primary', children = 'Load the sample dataset' }) {
  const { refresh } = useAppState()
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const run = async () => {
    setBusy(true)
    try {
      await api.loadSample()
      await api.prepare()
      await refresh()
      toast({ kind: 'success', title: 'Sample dataset ready', message: '1,000 customers loaded and prepared.' })
    } catch (e) {
      toast({ kind: 'error', title: 'Could not load the sample', message: e.message })
    } finally {
      setBusy(false)
    }
  }
  return (
    <Button variant={variant} icon={Database} onClick={run} loading={busy}>
      {children}
    </Button>
  )
}

const QUICK_STEPS = [
  { label: 'Load sample', hint: '1,000 customers' },
  { label: 'Prepare data', hint: 'Clean duplicates' },
  { label: 'Train models', hint: 'LR · Tree · Forest' },
  { label: 'Save best', hint: 'Set active model' },
]

/** One click: sample data -> prepare -> train the three required models -> save the recommended one. */
export function QuickStartButton({ variant = 'primary', size, children = 'Quick start with sample data' }) {
  const { refresh } = useAppState()
  const toast = useToast()
  const navigate = useNavigate()
  const [step, setStep] = useState(-1)
  const running = step >= 0

  const run = async () => {
    try {
      setStep(0)
      await api.loadSample()
      setStep(1)
      await api.prepare()
      setStep(2)
      const tr = await api.train({
        test_size: 0.2,
        imbalance_strategy: 'class_weight',
        models: ['Logistic Regression', 'Decision Tree', 'Random Forest'],
        selection_metric: 'f1_score',
      })
      setStep(3)
      await api.saveModel(tr.recommended)
      setStep(4)
      await refresh()
      celebrate()
      toast({ kind: 'success', title: 'Workspace is ready', message: `${tr.recommended} is now the active model.` })
      navigate('/app')
    } catch (e) {
      toast({ kind: 'error', title: 'Quick start stopped', message: e.message })
    } finally {
      setStep(-1)
      refresh()
    }
  }

  return (
    <>
      <Button variant={variant} size={size} icon={Rocket} onClick={run} loading={running}>
        {children}
      </Button>
      <Modal open={running} onClose={() => {}} title="Setting up your workspace" description="This takes a few seconds. Everything runs locally on this machine.">
        <Stepper steps={QUICK_STEPS} current={Math.min(step, QUICK_STEPS.length)} label="Quick start progress" />
        <div style={{ marginTop: 18 }}>
          <ProgressBar indeterminate label="Working" />
        </div>
      </Modal>
    </>
  )
}

/** Ranked factors with relative bars. tone: rose | mint */
export function FactorList({ items, tone, icon: Icon, empty }) {
  const max = Math.max(...items.map((i) => Math.abs(i.value)), 1e-9)
  if (!items.length) return <p className="muted">{empty}</p>
  return (
    <ul className="driver-list">
      {items.map((i) => (
        <li key={i.feature}>
          <div className="driver-row">
            <span>
              <Icon size={16} aria-hidden="true" style={{ color: `var(--${tone}-ink)`, flex: 'none' }} />
              {i.label}
            </span>
            <span className="tiny num">{i.value > 0 ? '+' : ''}{fmtNum(i.value, 3)}</span>
          </div>
          <div className="bar-track" aria-hidden="true">
            <div className="bar-fill" style={{ width: `${Math.max(6, (Math.abs(i.value) / max) * 100)}%`, background: `var(--${tone})` }} />
          </div>
        </li>
      ))}
    </ul>
  )
}
