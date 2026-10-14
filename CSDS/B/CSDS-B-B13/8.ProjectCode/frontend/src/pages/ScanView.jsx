import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  AlertTriangle, Bot, Bug, CheckCircle2, ChevronDown, ChevronRight, Copy, Download, FileText, ListChecks, ShieldCheck, XCircle,
} from 'lucide-react'
import api, { errMsg } from '../api'
import { useAsync } from '../lib/useAsync'
import {
  Badge, Breadcrumbs, Button, Card, CardHeader, EmptyState, ErrorState, IconButton, PageHeader, ProgressBar, Skeleton, StatCard,
  Tabs, useToast,
} from '../components/ui'
import { ChartCard, DonutChart, HBarChart, useChartColors } from '../components/charts'
import { FadeIn } from '../components/motion'
import { SeverityBadge, StatusBadge } from '../components/scan'

const TABS = [
  { value: 'findings', label: 'Findings', icon: Bug },
  { value: 'ai', label: 'AI tests', icon: Bot },
  { value: 'validation', label: 'Validation', icon: ListChecks },
  { value: 'report', label: 'Report', icon: FileText },
]

const POLL_MS = 1500

export default function ScanView() {
  const { id } = useParams()
  const toast = useToast()
  const colors = useChartColors()
  const [scan, setScan] = useState(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [tab, setTab] = useState('findings')
  const lastStatus = useRef(null)

  // Poll the scan until it finishes. The timer chain stops on done/error and on unmount.
  useEffect(() => {
    let cancelled = false
    let timer = null
    const load = async () => {
      try {
        const r = await api.get(`/scans/${id}`)
        if (cancelled) return
        const s = r.data
        setScan(s)
        setError('')
        if (lastStatus.current && lastStatus.current !== 'done' && s.status === 'done') {
          toast({ title: `Scan #${s.id} finished`, message: `${s.target.name}: ${s.score}/100 (${s.grade})` })
        }
        lastStatus.current = s.status
        if (s.status !== 'done' && s.status !== 'error') timer = setTimeout(load, POLL_MS)
      } catch (e) {
        if (!cancelled) setError(errMsg(e))
      }
    }
    load()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
    // toast is stable from the provider; only the scan id and a manual retry restart polling
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, attempt])

  const crumbs = [{ label: 'Scans', to: '/app/scans' }, { label: `Scan #${id}` }]

  if (error && !scan) {
    return (
      <>
        <Breadcrumbs items={crumbs} />
        <ErrorState
          title="Could not load this scan"
          error={{ message: error }}
          onRetry={() => {
            setError('')
            setAttempt((a) => a + 1)
          }}
        />
      </>
    )
  }

  if (!scan) {
    return (
      <>
        <Breadcrumbs items={crumbs} />
        <Card spotlight={false} pad style={{ marginTop: 16 }}>
          <Skeleton width="40%" height={24} />
          <Skeleton width="70%" height={14} style={{ marginTop: 12 }} />
          <Skeleton width="100%" height={10} radius={999} style={{ marginTop: 24 }} />
        </Card>
      </>
    )
  }

  const counts = scan.severity_counts || {}
  const running = scan.status === 'pending' || scan.status === 'running'

  return (
    <FadeIn>
      <PageHeader
        crumbs={crumbs}
        title={scan.target.name}
        description={<span className="mono break">{scan.target.base_url}</span>}
        actions={<StatusBadge status={scan.status} progress={scan.progress} />}
      />

      {running && (
        <Card spotlight={false} pad>
          <ProgressBar label={scan.current_step || 'Starting…'} valueLabel={`${scan.progress}%`} value={scan.progress} max={100} />
          <p className="faint" style={{ marginTop: 12 }}>
            This page updates on its own. You can leave and come back later.
          </p>
        </Card>
      )}

      {scan.status === 'error' && (
        <ErrorState title="Scan failed" error={{ message: scan.error || 'The scan stopped before it finished.' }}>
          <p className="faint">Check the target is running and reachable, then start a new scan from Targets.</p>
          <div className="row">
            <Button as={Link} to="/app/targets" variant="ghost">
              Back to targets
            </Button>
          </div>
        </ErrorState>
      )}

      {scan.status === 'done' && (
        <>
          <div className="summary-grid">
            <ChartCard title="Security score" subtitle="Out of 100" height={200}>
              <DonutChart
                data={[
                  { name: 'Score', value: scan.score, color: colors.accent },
                  { name: 'Points lost', value: Math.max(0, 100 - scan.score), color: colors.grid },
                ]}
                centerValue={scan.score}
                centerLabel={`Grade ${scan.grade}`}
              />
            </ChartCard>
            <div className="stat-pair">
              <StatCard label="Total findings" value={scan.finding_count} icon={ShieldCheck} />
              <StatCard label="Critical and high" value={(counts.critical || 0) + (counts.high || 0)} icon={Bug} tone="danger" />
              <StatCard label="Medium" value={counts.medium || 0} icon={AlertTriangle} tone="warn" />
              <StatCard label="Low" value={counts.low || 0} icon={CheckCircle2} tone="info" />
            </div>
          </div>

          <div style={{ marginTop: 20 }}>
            <Tabs label="Scan sections" tabs={TABS} value={tab} onChange={setTab} />
          </div>
          <div className="tab-panel">
            {tab === 'findings' && <Findings scanId={id} />}
            {tab === 'ai' && <AITests scanId={id} />}
            {tab === 'validation' && <Validation scanId={id} />}
            {tab === 'report' && <Reports scanId={id} />}
          </div>
        </>
      )}
    </FadeIn>
  )
}

function Findings({ scanId }) {
  const findings = useAsync(() => api.get(`/scans/${scanId}/findings`).then((r) => r.data), [scanId])
  const [open, setOpen] = useState({})
  const colors = useChartColors()

  if (findings.error && !findings.data) {
    return <ErrorState title="Could not load findings" error={{ message: errMsg(findings.error) }} onRetry={findings.reload} />
  }
  if (!findings.data) {
    return (
      <div className="stack-list">
        {[0, 1, 2].map((i) => (
          <Card key={i} spotlight={false} pad>
            <Skeleton width="60%" height={18} />
          </Card>
        ))}
      </div>
    )
  }

  const real = findings.data.filter((f) => f.severity !== 'info')
  if (real.length === 0) {
    return (
      <EmptyState icon={ShieldCheck} title="No findings">
        No issues were detected in this scan.
      </EmptyState>
    )
  }

  // Findings per endpoint, computed from the findings list (the API has no separate breakdown).
  const byEndpoint = Object.values(
    real.reduce((acc, f) => {
      const key = f.endpoint || 'Unspecified'
      acc[key] = acc[key] || { endpoint: key, count: 0 }
      acc[key].count += 1
      return acc
    }, {}),
  ).sort((a, b) => b.count - a.count)

  return (
    <div className="stack-list">
      <ChartCard title="Findings per endpoint" subtitle="Grouped by the endpoint each finding was raised against" height={Math.max(160, byEndpoint.length * 44 + 40)}>
        <HBarChart data={byEndpoint} labelKey="endpoint" valueKey="count" color={colors.danger} />
      </ChartCard>

      {real.map((f) => {
        const isOpen = !!open[f.id]
        const panelId = `finding-${f.id}`
        return (
          <Card key={f.id} as="article" spotlight={false}>
            <button
              type="button"
              className="acc-toggle"
              aria-expanded={isOpen}
              aria-controls={panelId}
              onClick={() => setOpen((o) => ({ ...o, [f.id]: !o[f.id] }))}
            >
              {isOpen ? <ChevronDown size={16} aria-hidden="true" /> : <ChevronRight size={16} aria-hidden="true" />}
              <SeverityBadge severity={f.severity} />
              <span className="finding-title">{f.title}</span>
              <span className="faint hide-sm">
                {f.owasp_id} · {f.source === 'ai' ? 'AI' : 'OWASP'}
              </span>
            </button>
            {isOpen && <FindingDetail id={panelId} f={f} />}
          </Card>
        )
      })}
    </div>
  )
}

function FindingDetail({ id, f }) {
  return (
    <div id={id} className="finding-body">
      <p className="muted">
        <strong>{f.owasp_id}</strong> — {f.owasp_name}
        {f.endpoint && (
          <>
            {' '}
            · <code>{f.endpoint}</code>
          </>
        )}
      </p>
      <p>{f.description}</p>

      {f.curl && (
        <div>
          <h4>Reproduce (curl)</h4>
          <CodeBlock text={f.curl} label="Copy curl" />
        </div>
      )}

      <div>
        <h4>Evidence</h4>
        <CodeBlock text={JSON.stringify(f.evidence, null, 2)} label="Copy evidence" />
      </div>

      <div className="fix-box">
        <h4 style={{ color: 'var(--safe)' }}>Recommended fix</h4>
        <p>{f.recommendation}</p>
        {f.fix_snippet && <pre className="code-block" style={{ marginTop: 10 }}>{f.fix_snippet}</pre>}
      </div>
    </div>
  )
}

function CodeBlock({ text, label }) {
  const toast = useToast()
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      toast({ title: 'Copied to clipboard' })
    } catch {
      toast({ title: 'Copy failed', message: 'Select the text and copy it manually.', tone: 'error' })
    }
  }
  return (
    <div className="code-wrap">
      <pre className="code-block">{text}</pre>
      <IconButton icon={Copy} label={label} size="sm" className="code-copy" onClick={copy} />
    </div>
  )
}

const RESULT = {
  vulnerable: { tone: 'danger', label: 'Vulnerable', icon: XCircle, color: 'var(--danger)' },
  safe: { tone: 'safe', label: 'Safe', icon: CheckCircle2, color: 'var(--safe)' },
}
const RESULT_DEFAULT = { tone: 'warn', label: 'Skipped', icon: AlertTriangle, color: 'var(--warn)' }

function AITests({ scanId }) {
  const toast = useToast()
  const tests = useAsync(() => api.get(`/scans/${scanId}/ai-tests`).then((r) => r.data), [scanId])
  const config = useAsync(() => api.get('/config').then((r) => r.data), [])
  const [busy, setBusy] = useState(false)
  const [runError, setRunError] = useState('')

  const run = async () => {
    setBusy(true)
    setRunError('')
    try {
      const r = await api.post(`/scans/${scanId}/ai-tests`)
      const gen = r.data.generator === 'gemini' ? 'Gemini' : 'built-in generator'
      toast({ title: `${r.data.count} AI tests ran`, message: `Generator: ${gen}` })
      await tests.reload()
    } catch (e) {
      setRunError(errMsg(e))
    } finally {
      setBusy(false)
    }
  }

  const generatorBadge = config.data ? (
    config.data.gemini_enabled ? (
      <Badge tone="info" dot>Gemini enabled</Badge>
    ) : (
      <Badge dot>Built-in generator (no Gemini key)</Badge>
    )
  ) : null

  return (
    <div className="stack-list">
      <Card spotlight={false} pad>
        <div className="ai-head">
          <p className="muted">
            Gemini reads the API spec and proposes business-logic abuse tests. The scanner then runs them against the live
            target. Without a key, a built-in generator produces the same kinds of tests.
          </p>
          <div className="row" style={{ gap: 10, flexWrap: 'wrap' }}>
            {generatorBadge}
            <Button variant="primary" icon={Bot} loading={busy} onClick={run}>
              {tests.data?.length ? 'Re-run' : 'Generate & run'}
            </Button>
          </div>
        </div>
        {runError && (
          <p className="form-error" role="alert" style={{ marginTop: 12 }}>
            {runError}
          </p>
        )}
      </Card>

      {tests.error && !tests.data ? (
        <ErrorState title="Could not load AI tests" error={{ message: errMsg(tests.error) }} onRetry={tests.reload} />
      ) : !tests.data ? (
        <Card spotlight={false} pad>
          <Skeleton width="50%" height={18} />
        </Card>
      ) : tests.data.length === 0 ? (
        <EmptyState icon={Bot} title="No AI tests yet">
          Use “Generate & run” to create business-logic abuse tests for this API and run them against the target.
        </EmptyState>
      ) : (
        tests.data.map((t) => {
          const r = RESULT[t.result] || RESULT_DEFAULT
          const Icon = r.icon
          return (
            <Card key={t.id} as="article" spotlight={false} pad>
              <div className="result-row">
                <Icon size={18} color={r.color} aria-hidden="true" />
                <h3>{t.name}</h3>
                <Badge tone={r.tone} dot>
                  {r.label}
                </Badge>
              </div>
              <p className="faint" style={{ marginTop: 8 }}>
                <code>{t.endpoint}</code> · {t.category}
              </p>
              {t.rationale && <p style={{ marginTop: 10 }}>{t.rationale}</p>}
              {t.detail && <p className="faint" style={{ marginTop: 6 }}>{t.detail}</p>}
            </Card>
          )
        })
      )}
    </div>
  )
}

function Validation({ scanId }) {
  const v = useAsync(() => api.get(`/scans/${scanId}/validation`).then((r) => r.data), [scanId])

  if (v.error && !v.data) {
    return <ErrorState title="Could not load validation" error={{ message: errMsg(v.error) }} onRetry={v.reload} />
  }
  if (!v.data) {
    return (
      <div className="target-grid">
        <Card spotlight={false} pad>
          <Skeleton width="60%" height={28} />
        </Card>
        <Card spotlight={false} pad>
          <Skeleton width="60%" height={28} />
        </Card>
      </div>
    )
  }
  if (!v.data.has_known_list) {
    return (
      <EmptyState icon={ListChecks} title="No known-vulnerability list">
        This target has no known-vulnerability list to validate against. Add one (the “Known vulnerabilities” field) when you
        import the target.
      </EmptyState>
    )
  }

  const d = v.data
  return (
    <div className="stack-list">
      <div className="stat-pair" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
        <StatCard label="Detection rate" value={`${d.detection_rate}%`} delta={`${d.detected_count}/${d.total_known} known vulns`} icon={ShieldCheck} tone="safe" />
        <StatCard label="Missed" value={d.missed_count} icon={AlertTriangle} tone="warn" />
        <StatCard label="False positives" value={d.false_positive_count} icon={XCircle} tone="info" />
      </div>
      <div className="stat-pair">
        <Card spotlight={false} pad>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>Detected</h3>
          <ListItems items={d.detected.map((x) => x.name)} tone="safe" empty="None" />
        </Card>
        <Card spotlight={false} pad>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>Missed</h3>
          <ListItems items={d.missed.map((x) => x.name)} tone="warn" empty="None" />
        </Card>
      </div>
      {d.false_positives.length > 0 && (
        <Card spotlight={false} pad>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>False positives</h3>
          <ListItems items={d.false_positives} tone="neutral" empty="None" />
        </Card>
      )}
    </div>
  )
}

function ListItems({ items, tone, empty }) {
  if (items.length === 0) return <p className="faint">{empty}</p>
  return (
    <ul className="plain-list">
      {items.map((i) => (
        <li key={i}>
          <span className={`pip ${tone}`} aria-hidden="true" />
          <span>{i}</span>
        </li>
      ))}
    </ul>
  )
}

function Reports({ scanId }) {
  const toast = useToast()
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const openHtml = async () => {
    setBusy('html')
    setError('')
    try {
      const r = await api.get(`/scans/${scanId}/report.html`, { responseType: 'text' })
      const url = URL.createObjectURL(new Blob([r.data], { type: 'text/html' }))
      const win = window.open(url, '_blank')
      if (!win) toast({ title: 'Pop-up blocked', message: 'Allow pop-ups for this site to view the report.', tone: 'error' })
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy('')
    }
  }

  const downloadPdf = async () => {
    setBusy('pdf')
    setError('')
    try {
      const r = await api.get(`/scans/${scanId}/report.pdf`, { responseType: 'blob' })
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `apisentry-scan-${scanId}.pdf`
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
      toast({ title: 'PDF downloaded', message: `apisentry-scan-${scanId}.pdf` })
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy('')
    }
  }

  return (
    <Card spotlight={false} pad>
      <CardHeader title="Share a report" subtitle="Evidence, curl reproductions, OWASP mapping and fixes in one document." as="h3" />
      <div className="report-actions" style={{ marginTop: 16 }}>
        <Button variant="primary" icon={FileText} loading={busy === 'html'} onClick={openHtml}>
          Open HTML report
        </Button>
        <Button variant="ghost" icon={Download} loading={busy === 'pdf'} onClick={downloadPdf}>
          Download PDF
        </Button>
      </div>
      {error && (
        <p className="form-error" role="alert" style={{ marginTop: 14 }}>
          {error}
        </p>
      )}
    </Card>
  )
}
