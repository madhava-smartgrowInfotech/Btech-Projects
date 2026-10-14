import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertOctagon,
  CheckCircle2,
  ClipboardCopy,
  Files,
  Flag,
  Gauge,
  Link2,
  Play,
  ScanSearch,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestion,
  Square,
  Target,
  Users,
} from 'lucide-react'
import { api } from '../lib/api'
import { useStats } from '../lib/stats'
import { useAsync } from '../lib/useAsync'
import { DECIDED_BY, STATUS, VERDICT, ago, humanize, modelLabel, num, parseUrlList, pct } from '../lib/format'
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Checkbox,
  Container,
  EmptyState,
  ErrorState,
  FileDrop,
  IconButton,
  Input,
  KeyValueList,
  PageHeader,
  ProgressBar,
  Skeleton,
  StatCard,
  Table,
  Tabs,
  Textarea,
  Tooltip,
  useToast,
} from '../components/ui'
import { SlideUp, Stagger } from '../components/motion'
import '../styles/pages.css'

// Example inputs from the project README / smoke tests
const SAMPLES = [
  'http://paypal-login.verify-account.tk/signin',
  'http://192.168.1.5/wp-admin/bank/update.php',
  'https://github.com/anthropics',
]
const VERDICT_ICON = { phishing: ShieldAlert, suspicious: AlertOctagon, safe: ShieldCheck, unknown: ShieldQuestion }
const BATCH_LIMIT = 100

/* ----------------------------------------------------------------- gauge */
function RiskGauge({ value, tone }) {
  const r = 52
  const c = 2 * Math.PI * r
  const arc = c * 0.75
  const p = value ?? 0
  return (
    <div className="gauge" role="img" aria-label={value === null ? 'No probability' : `Phishing probability ${pct(value)}`}>
      <svg viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={r} className="gauge-track" strokeDasharray={`${arc} ${c}`} transform="rotate(135 64 64)" />
        <motion.circle
          cx="64"
          cy="64"
          r={r}
          className={`gauge-value tone-${tone}`}
          strokeDasharray={`${arc} ${c}`}
          transform="rotate(135 64 64)"
          initial={{ strokeDashoffset: arc }}
          animate={{ strokeDashoffset: arc * (1 - p) }}
          transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <div className="gauge-label">
        <strong>{value === null ? '-' : `${(p * 100).toFixed(1)}%`}</strong>
        <span>phishing probability</span>
      </div>
    </div>
  )
}

/* ----------------------------------------------------------------- result */
function Result({ r, config, onCopy }) {
  const v = VERDICT[r.verdict] || VERDICT.unknown
  const Icon = VERDICT_ICON[r.verdict] || ShieldQuestion
  const by = DECIDED_BY[r.decided_by] || DECIDED_BY.none
  const groups = config?.feature_groups || { all: Object.keys(r.features) }
  const [group, setGroup] = useState(Object.keys(groups)[0])
  const rows = (groups[group] || []).filter((k) => k in r.features).map((k) => ({ k, v: r.features[k] }))
  const thresholds = config ? [config.suspicious_threshold, config.phishing_threshold] : [0.35, 0.6]

  return (
    <div className="stack">
      <Card className={`verdict tone-${v.tone}`} spotlight={false}>
        <div className="verdict-grid">
          <div style={{ minWidth: 0 }}>
            <div className="row" style={{ gap: 8 }}>
              <Badge tone={v.tone === 'neutral' ? 'neutral' : v.tone} dot>
                Verdict
              </Badge>
              <Badge tone={by.tone}>Decided by {by.label}</Badge>
              {r.model && <Badge>{modelLabel(r.model)} v{r.model_version}</Badge>}
            </div>
            <h2 className="verdict-word">
              <Icon size={34} aria-hidden="true" />
              {v.label}
            </h2>
            <div className="verdict-url mono break">
              {r.normalized_url}
              <IconButton icon={ClipboardCopy} label="Copy normalised URL" size="sm" onClick={() => onCopy(r.normalized_url)} />
            </div>
            <p className="verdict-reason">{r.reason}</p>
            {r.probability !== null && r.probability !== undefined && (
              <div className="risk-meter">
                <ProgressBar
                  variant="risk"
                  value={r.probability}
                  label="Risk scale"
                  valueLabel={r.ml_probability !== null && r.ml_probability !== undefined ? `raw model score ${pct(r.ml_probability)}` : undefined}
                />
                <div className="risk-ticks" aria-hidden="true">
                  {thresholds.map((t, i) => (
                    <span key={t} style={{ left: `${t * 100}%` }}>
                      {i === 0 ? 'suspicious' : 'phishing'} ≥ {Math.round(t * 100)}%
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="row" style={{ marginTop: 18 }}>
              <Button as={Link} to={`/app/report?url=${encodeURIComponent(r.normalized_url)}&verdict=phishing`} variant="danger" icon={Flag}>
                Report as phishing
              </Button>
              <Button as={Link} to={`/app/report?url=${encodeURIComponent(r.normalized_url)}&verdict=safe`} icon={CheckCircle2}>
                Report as safe
              </Button>
            </div>
          </div>
          <RiskGauge value={r.probability ?? null} tone={v.tone} />
        </div>
      </Card>

      <div className="grid grid-2">
        <Card>
          <CardHeader title={`Red flags (${r.red_flags.length})`} subtitle="Human-readable signals derived from the extracted features" />
          <div className="card-body">
            {r.red_flags.length ? (
              <Stagger as="ul" className="flags" gap={0.05}>
                {r.red_flags.map((f) => (
                  <li key={f}>
                    <ShieldAlert size={16} aria-hidden="true" />
                    <span>{f}</span>
                  </li>
                ))}
              </Stagger>
            ) : (
              <EmptyState icon={ShieldCheck} title="No red flags">
                None of the rule-based warning signs matched this URL.
              </EmptyState>
            )}
          </div>
        </Card>
        <Card>
          <CardHeader title="Community intelligence" subtitle="Crowdsourced reports for this URL or its host" />
          <div className="card-body">
            {r.community ? (
              <KeyValueList
                items={[
                  ['Status', <Badge key="s" tone={STATUS[r.community.status]?.tone} dot>{STATUS[r.community.status]?.label || humanize(r.community.status)}</Badge>],
                  ['Phishing votes', num(r.community.phishing_votes)],
                  ['Safe votes', num(r.community.safe_votes)],
                  ['Source', r.community.source],
                  ['Last updated', r.community.last_updated ? ago(r.community.last_updated) : '-'],
                ]}
              />
            ) : (
              <EmptyState
                icon={Users}
                title="No community reports"
                actions={
                  <Button as={Link} size="sm" to={`/app/report?url=${encodeURIComponent(r.normalized_url)}`} icon={Flag}>
                    Be the first to report
                  </Button>
                }
              >
                Nobody has reported this URL yet, so the verdict comes from the model.
              </EmptyState>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader
          title={`Extracted features (${Object.keys(r.features).length})`}
          subtitle="The exact vector the classifier scored"
          actions={
            <Tabs
              label="Feature group"
              value={group}
              onChange={setGroup}
              tabs={Object.keys(groups).map((g) => ({ value: g, label: `${g[0].toUpperCase()}${g.slice(1)} (${groups[g].length})` }))}
            />
          }
        />
        <div className="card-body">
          <div className="feature-grid">
            {rows.map(({ k, v: val }) => (
              <div key={k} className={`feature ${val ? 'on' : ''}`}>
                <code>{k}</code>
                <strong>{String(val)}</strong>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  )
}

/* ----------------------------------------------------------------- batch */
function BatchCheck({ onDone }) {
  const [text, setText] = useState('')
  const [dedupe, setDedupe] = useState(true)
  const [rows, setRows] = useState([])
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const stop = useRef(false)
  const toast = useToast()

  const urls = useMemo(() => {
    const list = parseUrlList(text)
    return (dedupe ? [...new Set(list)] : list).slice(0, BATCH_LIMIT)
  }, [text, dedupe])
  const total = parseUrlList(text).length

  const run = async () => {
    stop.current = false
    setRunning(true)
    setRows([])
    setProgress(0)
    const out = []
    for (let i = 0; i < urls.length; i++) {
      if (stop.current) break
      try {
        const r = await api.check(urls[i])
        out.push({ id: i, url: urls[i], verdict: r.verdict, probability: r.probability, decided_by: r.decided_by, norm: r.normalized_url })
      } catch (e) {
        out.push({ id: i, url: urls[i], verdict: 'error', error: e.message })
        if (e.network) {
          toast({ tone: 'error', title: 'Batch stopped', message: e.message })
          break
        }
      }
      setRows([...out])
      setProgress(i + 1)
    }
    setRunning(false)
    onDone?.()
    if (!stop.current && out.length) {
      const bad = out.filter((r) => r.verdict === 'phishing').length
      toast({ title: `Checked ${out.length} URLs`, message: `${bad} flagged as phishing.` })
    }
  }

  const counts = rows.reduce((a, r) => ({ ...a, [r.verdict]: (a[r.verdict] || 0) + 1 }), {})

  return (
    <div className="stack">
      <Card>
        <CardHeader title="Batch check" subtitle={`Upload a .txt or .csv (one URL per line, or a url column) or paste a list. Up to ${BATCH_LIMIT} URLs per run.`} />
        <div className="card-body">
          <div className="grid grid-2">
            <FileDrop
              accept=".txt,.csv"
              label="Drop a URL list here or click to browse"
              hint=".txt or .csv up to 512 KB"
              onFile={(f) => setText(f ? f.text : '')}
            />
            <Textarea
              label="Or paste URLs"
              mono
              rows={7}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={SAMPLES.join('\n')}
              hint={total ? `${total} URL${total === 1 ? '' : 's'} found${total > BATCH_LIMIT ? ` - the first ${BATCH_LIMIT} will be checked` : ''}` : 'One URL per line'}
            />
          </div>
          <div className="row" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <Checkbox label="Skip duplicate URLs" checked={dedupe} onChange={(e) => setDedupe(e.target.checked)} />
            <div className="row">
              {running && (
                <Button icon={Square} onClick={() => (stop.current = true)}>
                  Stop
                </Button>
              )}
              <Button variant="primary" icon={Play} loading={running} disabled={!urls.length} onClick={run}>
                Check {urls.length || ''} URL{urls.length === 1 ? '' : 's'}
              </Button>
            </div>
          </div>
          {(running || rows.length > 0) && (
            <div style={{ marginTop: 16 }}>
              <ProgressBar value={progress} max={urls.length || 1} label={running ? 'Checking…' : 'Done'} valueLabel={`${progress} / ${urls.length}`} />
            </div>
          )}
        </div>
      </Card>
      {rows.length > 0 && (
        <Card>
          <CardHeader
            title="Batch results"
            actions={
              <div className="row">
                {['phishing', 'suspicious', 'safe', 'error'].map((k) =>
                  counts[k] ? (
                    <Badge key={k} tone={k === 'error' ? 'danger' : VERDICT[k].tone}>
                      {counts[k]} {k}
                    </Badge>
                  ) : null,
                )}
              </div>
            }
          />
          <div style={{ marginTop: 12 }}>
            <Table
              caption="Batch check results"
              rows={rows}
              rowKey={(r) => r.id}
              pageSize={10}
              columns={[
                { key: 'url', label: 'URL', className: 'url-cell', render: (r) => (r.norm ? <Link to={`/app/check?url=${encodeURIComponent(r.norm)}`}>{r.url}</Link> : r.url) },
                {
                  key: 'verdict',
                  label: 'Verdict',
                  render: (r) =>
                    r.verdict === 'error' ? (
                      <Tooltip label={r.error}>
                        <Badge tone="danger">error</Badge>
                      </Tooltip>
                    ) : (
                      <Badge tone={VERDICT[r.verdict]?.tone} dot>
                        {VERDICT[r.verdict]?.label}
                      </Badge>
                    ),
                },
                { key: 'probability', label: 'Probability', num: true, render: (r) => pct(r.probability) },
                { key: 'decided_by', label: 'Decided by', render: (r) => DECIDED_BY[r.decided_by]?.label || '-' },
              ]}
            />
          </div>
        </Card>
      )}
    </div>
  )
}

/* ----------------------------------------------------------------- page */
export default function CheckUrl() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const paramUrl = params.get('url') || ''
  const [tab, setTab] = useState(params.get('mode') === 'batch' ? 'batch' : 'single')
  const [url, setUrl] = useState(paramUrl)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { ti, metrics, config, refresh, loading: statsLoading } = useStats()
  const toast = useToast()
  const inputRef = useRef(null)
  const recent = useAsync(() => api.checks(200), [])

  const run = useCallback(
    async (target) => {
      setLoading(true)
      setError(null)
      try {
        const r = await api.check(target)
        setResult(r)
      } catch (e) {
        setResult(null)
        setError(e)
      } finally {
        setLoading(false)
        refresh()
        recent.reload({ quiet: true })
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [refresh],
  )

  // ?url= deep links (from Report, Threat intel and Activity) check immediately, like the old UI
  // keyed on the history entry so each navigation checks exactly once (also under StrictMode)
  const location = useLocation()
  const handled = useRef(null)
  useEffect(() => {
    if (!paramUrl || handled.current === location.key) return
    handled.current = location.key
    setUrl(paramUrl)
    setTab('single')
    run(paramUrl)
  }, [location.key, paramUrl, run])

  const submit = (e) => {
    e.preventDefault()
    const target = url.trim()
    if (!target) {
      setError(new Error('Please enter a URL.'))
      inputRef.current?.focus()
      return
    }
    setParams({ url: target })
  }

  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      toast({ title: 'Copied', message: text })
    } catch {
      toast({ tone: 'error', title: 'Copy failed', message: 'Clipboard access was blocked by the browser.' })
    }
  }

  // KPI extras computed from the real check log
  const checks = recent.data || []
  const perDay = useMemo(() => {
    const days = {}
    checks.forEach((c) => {
      const d = (c.created_at || '').slice(0, 10)
      days[d] = (days[d] || 0) + 1
    })
    return Object.keys(days)
      .sort()
      .slice(-14)
      .map((d) => days[d])
  }, [checks])
  const today = new Date().toISOString().slice(0, 10)
  const todayCount = checks.filter((c) => (c.created_at || '').startsWith(today)).length
  const best = metrics?.models?.[metrics.best_model]
  const runnerUp = metrics
    ? Object.entries(metrics.models)
        .filter(([k]) => k !== metrics.best_model)
        .map(([, m]) => m.f1)
        .sort((a, b) => b - a)[0]
    : null

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'Check URL' }]}
        title="Is this link safe?"
        description="Each URL is checked first against community-confirmed threat intelligence, then scored by the best of three trained classifiers using lexical, structural and domain features."
        actions={
          <Tabs
            label="Check mode"
            value={tab}
            onChange={(t) => {
              setTab(t)
              if (t === 'batch' && paramUrl) navigate('/app/check?mode=batch', { replace: true })
            }}
            tabs={[
              { value: 'single', label: 'Single URL', icon: Link2 },
              { value: 'batch', label: 'Batch', icon: Files },
            ]}
          />
        }
      />

      {tab === 'batch' ? (
        <BatchCheck onDone={() => recent.reload({ quiet: true })} />
      ) : (
        <>
          <Card className="check-form-card">
            <form className="check-form" onSubmit={submit} noValidate>
              <Input
                ref={inputRef}
                label="URL to check"
                labelHidden
                size="lg"
                mono
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="e.g. http://paypal-secure-login.verify-account.tk/signin"
                autoComplete="off"
                spellCheck={false}
                inputMode="url"
                autoFocus={!paramUrl}
              />
              <Button type="submit" variant="primary" size="lg" icon={ScanSearch} loading={loading}>
                Check
              </Button>
            </form>
            <div className="samples">
              <span className="faint">Try:</span>
              {SAMPLES.map((s) => (
                <button key={s} type="button" className="chip mono" onClick={() => setParams({ url: s })}>
                  {s}
                </button>
              ))}
            </div>
          </Card>

          <div className="result-area">
            <AnimatePresence mode="wait">
              {loading ? (
                <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} aria-busy="true" aria-label="Checking URL">
                  <Card pad>
                    <div className="verdict-grid">
                      <div>
                        <Skeleton width={200} height={22} />
                        <Skeleton width="55%" height={44} style={{ margin: '16px 0' }} />
                        <Skeleton width="80%" height={16} />
                        <Skeleton width="70%" height={16} style={{ marginTop: 10 }} />
                        <Skeleton height={10} style={{ marginTop: 24 }} />
                      </div>
                      <Skeleton width={150} height={150} radius="50%" />
                    </div>
                  </Card>
                </motion.div>
              ) : error ? (
                <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <Card>
                    <ErrorState title="Could not check that URL" error={error} onRetry={url.trim() ? () => run(url.trim()) : undefined} />
                  </Card>
                </motion.div>
              ) : result ? (
                <SlideUp key={result.normalized_url + result.probability}>
                  <Result r={result} config={config} onCopy={copy} />
                </SlideUp>
              ) : (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <Card>
                    <EmptyState
                      icon={Target}
                      title="Paste a link to get a verdict"
                      actions={
                        <Button onClick={() => setParams({ url: SAMPLES[0] })} icon={Play}>
                          Run a sample check
                        </Button>
                      }
                    >
                      You will see the verdict, the phishing probability, the red flags behind it and any community reports.
                    </EmptyState>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </>
      )}

      <h2 className="section-title">At a glance</h2>
      <div className="grid grid-4">
        <StatCard
          label="URLs checked"
          icon={Gauge}
          value={ti?.checks}
          loading={statsLoading}
          delta={recent.data ? `${todayCount} today` : undefined}
          spark={perDay.length > 1 ? perDay : undefined}
          sparkLabel="Checks per day"
        />
        <StatCard label="Confirmed phishing URLs" icon={ShieldAlert} tone="danger" value={ti?.confirmed_phishing} loading={statsLoading} delta="community-confirmed" />
        <StatCard label="Community reports" icon={Users} tone="info" value={ti?.reports} loading={statsLoading} delta={ti ? `${ti.urls_tracked} URLs tracked` : undefined} />
        <StatCard
          label={`F1 of active model`}
          icon={Target}
          value={best ? best.f1 * 100 : metrics === null && !statsLoading ? '-' : undefined}
          format={(v) => `${v.toFixed(2)}%`}
          loading={statsLoading}
          delta={best && runnerUp !== undefined ? `${modelLabel(metrics.best_model)} · +${((best.f1 - runnerUp) * 100).toFixed(2)} pts vs next` : 'no model trained'}
          deltaTone={best ? 'up' : undefined}
        />
      </div>

      <h2 className="section-title">Recent checks</h2>
      <Card>
        {recent.error ? (
          <ErrorState title="Could not load recent checks" error={recent.error} onRetry={recent.reload} />
        ) : (
          <Table
            caption="Recent URL checks"
            loading={recent.loading}
            rows={checks.slice(0, 12)}
            rowKey={(c) => c.id}
            pageSize={12}
            onRowClick={(c) => setParams({ url: c.url })}
            empty={
              <EmptyState icon={ScanSearch} title="No checks yet" actions={<Button onClick={() => inputRef.current?.focus()}>Check your first URL</Button>}>
                Every URL you check is logged here so you can revisit it.
              </EmptyState>
            }
            columns={[
              { key: 'url', label: 'URL', className: 'url-cell', render: (c) => (c.url.length > 90 ? `${c.url.slice(0, 90)}…` : c.url) },
              { key: 'verdict', label: 'Verdict', render: (c) => <Badge tone={VERDICT[c.verdict]?.tone} dot>{VERDICT[c.verdict]?.label || c.verdict}</Badge> },
              { key: 'probability', label: 'Probability', num: true, render: (c) => pct(c.probability) },
              { key: 'decided_by', label: 'Decided by', hideSm: false, render: (c) => DECIDED_BY[c.decided_by]?.label || c.decided_by },
              { key: 'created_at', label: 'When', render: (c) => <span className="faint">{ago(c.created_at)}</span> },
            ]}
          />
        )}
        {checks.length > 12 && (
          <div className="table-foot">
            <span>Showing the 12 most recent</span>
            <Link to="/app/activity">Open the full activity log →</Link>
          </div>
        )}
      </Card>
    </Container>
  )
}
