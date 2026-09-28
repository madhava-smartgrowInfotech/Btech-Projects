import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ChevronDown, ChevronRight, Bot, FileText, Download, ListChecks,
  Bug, CheckCircle2, XCircle, AlertTriangle,
} from 'lucide-react'
import api, { errMsg } from '../api'
import { ErrorBox, Spinner, ScoreRing, GradeBadge, SeverityTag } from '../components/ui'

const TABS = [
  { key: 'findings', label: 'Findings', icon: Bug },
  { key: 'ai', label: 'AI tests', icon: Bot },
  { key: 'validation', label: 'Validation', icon: ListChecks },
  { key: 'report', label: 'Report', icon: FileText },
]

export default function ScanView() {
  const { id } = useParams()
  const [scan, setScan] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('findings')
  const timer = useRef(null)

  const poll = useCallback(() => {
    api.get(`/scans/${id}`)
      .then((r) => {
        setScan(r.data)
        if (['done', 'error'].includes(r.data.status) && timer.current) {
          clearInterval(timer.current); timer.current = null
        }
      })
      .catch((e) => setError(errMsg(e)))
  }, [id])

  useEffect(() => {
    poll()
    timer.current = setInterval(poll, 1500)
    return () => timer.current && clearInterval(timer.current)
  }, [poll])

  if (error) return <ErrorBox message={error} />
  if (!scan) return <Spinner />

  return (
    <div>
      <Link to="/app/scans" className="text-sm text-brand-600">← All scans</Link>
      <div className="card p-6 mt-2">
        <div className="flex flex-wrap items-center gap-6">
          <div>
            <h1 className="text-2xl font-extrabold">{scan.target.name}</h1>
            <div className="text-slate-500 text-sm break-all">{scan.target.base_url}</div>
            <div className="text-slate-400 text-xs mt-1">Scan #{scan.id}</div>
          </div>
          {scan.status === 'done' && (
            <div className="flex items-center gap-5 ml-auto">
              <ScoreRing score={scan.score} grade={scan.grade} />
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <GradeBadge grade={scan.grade} />
                  <span className="text-slate-500 text-sm">Grade</span>
                </div>
                <SeverityCounts counts={scan.severity_counts} />
              </div>
            </div>
          )}
        </div>

        {['pending', 'running'].includes(scan.status) && (
          <Progress scan={scan} />
        )}
        {scan.status === 'error' && (
          <ErrorBox message={`Scan failed: ${scan.error}`} />
        )}
      </div>

      {scan.status === 'done' && (
        <>
          <div className="flex gap-1 mt-6 border-b border-slate-200">
            {TABS.map((t) => (
              <button key={t.key} onClick={() => setTab(t.key)}
                className={`flex items-center gap-2 px-4 py-2 font-semibold text-sm border-b-2 -mb-px ${
                  tab === t.key ? 'border-brand-500 text-brand-700'
                    : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
                <t.icon size={16} /> {t.label}
              </button>
            ))}
          </div>
          <div className="mt-5">
            {tab === 'findings' && <Findings scanId={id} />}
            {tab === 'ai' && <AITests scanId={id} />}
            {tab === 'validation' && <Validation scanId={id} />}
            {tab === 'report' && <Reports scanId={id} />}
          </div>
        </>
      )}
    </div>
  )
}

function Progress({ scan }) {
  return (
    <div className="mt-6">
      <div className="flex justify-between text-sm text-slate-600 mb-1">
        <span>{scan.current_step || 'Starting…'}</span>
        <span>{scan.progress}%</span>
      </div>
      <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full bg-brand-500 transition-all duration-500"
          style={{ width: `${scan.progress}%` }} />
      </div>
      <div className="flex items-center gap-2 text-slate-500 text-sm mt-3">
        <Spinner label="Scanning target…" />
      </div>
    </div>
  )
}

function SeverityCounts({ counts }) {
  const order = ['critical', 'high', 'medium', 'low', 'info']
  const items = order.filter((k) => counts[k])
  if (items.length === 0) return <span className="text-green-700 font-semibold">No findings</span>
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((k) => (
        <span key={k}><SeverityTag severity={k} /> <b className="text-sm">{counts[k]}</b></span>
      ))}
    </div>
  )
}

function Findings({ scanId }) {
  const [rows, setRows] = useState(null)
  const [open, setOpen] = useState({})
  const [error, setError] = useState('')

  useEffect(() => {
    api.get(`/scans/${scanId}/findings`)
      .then((r) => setRows(r.data)).catch((e) => setError(errMsg(e)))
  }, [scanId])

  if (error) return <ErrorBox message={error} />
  if (!rows) return <Spinner />
  const real = rows.filter((f) => f.severity !== 'info')
  if (real.length === 0) return <div className="text-slate-500">No findings.</div>

  return (
    <div className="space-y-2">
      {real.map((f) => {
        const isOpen = open[f.id]
        return (
          <div key={f.id} className="card overflow-hidden">
            <button onClick={() => setOpen((o) => ({ ...o, [f.id]: !o[f.id] }))}
              className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50">
              {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              <SeverityTag severity={f.severity} />
              <span className="font-semibold flex-1">{f.title}</span>
              <span className="text-xs text-slate-500 hidden sm:block">
                {f.owasp_id} · {f.source === 'ai' ? 'AI' : 'OWASP'}
              </span>
            </button>
            {isOpen && <FindingDetail f={f} />}
          </div>
        )
      })}
    </div>
  )
}

function FindingDetail({ f }) {
  return (
    <div className="px-4 pb-4 pt-1 border-t border-slate-100 space-y-3 text-sm">
      <div className="text-slate-500">
        <b>{f.owasp_id}</b> — {f.owasp_name}
        {f.endpoint && <> · <code className="bg-slate-100 px-1 rounded">{f.endpoint}</code></>}
      </div>
      <p>{f.description}</p>

      {f.curl && (
        <div>
          <div className="text-slate-500 font-medium mb-1">Reproduce (curl)</div>
          <pre className="bg-ink text-slate-100 p-3 rounded-lg overflow-auto text-xs">{f.curl}</pre>
        </div>
      )}

      <div>
        <div className="text-slate-500 font-medium mb-1">Evidence</div>
        <pre className="bg-slate-50 border border-slate-200 p-3 rounded-lg overflow-auto text-xs
          max-h-52">{JSON.stringify(f.evidence, null, 2)}</pre>
      </div>

      <div className="rounded-lg bg-green-50 border border-green-200 p-3">
        <div className="text-green-800 font-semibold mb-1">Recommended fix</div>
        <p className="text-green-900">{f.recommendation}</p>
        {f.fix_snippet && (
          <pre className="bg-ink text-slate-100 p-3 rounded-lg overflow-auto text-xs mt-2">{f.fix_snippet}</pre>
        )}
      </div>
    </div>
  )
}

function AITests({ scanId }) {
  const [rows, setRows] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [gen, setGen] = useState('')

  const load = useCallback(() => {
    api.get(`/scans/${scanId}/ai-tests`).then((r) => {
      setRows(r.data)
      if (r.data[0]) setGen(r.data[0].generator)
    }).catch((e) => setError(errMsg(e)))
  }, [scanId])
  useEffect(load, [load])

  const run = async () => {
    setBusy(true); setError('')
    try { const r = await api.post(`/scans/${scanId}/ai-tests`); setGen(r.data.generator); load() }
    catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <p className="text-sm text-slate-600 flex-1">
          Gemini reads the API spec and proposes business-logic abuse tests, which the
          scanner then runs against the live target. {gen && <span className="text-slate-400">
            (generator: {gen})</span>}
        </p>
        <button className="btn-primary" onClick={run} disabled={busy}>
          <Bot size={16} /> {busy ? 'Generating…' : rows?.length ? 'Re-run' : 'Generate & run'}
        </button>
      </div>
      <ErrorBox message={error} />
      {rows === null ? <Spinner /> : rows.length === 0 ? (
        <div className="text-slate-500">No AI tests yet — click “Generate & run”.</div>
      ) : (
        <div className="space-y-2">
          {rows.map((t) => (
            <div key={t.id} className="card p-4">
              <div className="flex items-center gap-2">
                {t.result === 'vulnerable'
                  ? <XCircle size={18} className="text-red-600" />
                  : t.result === 'safe'
                    ? <CheckCircle2 size={18} className="text-green-600" />
                    : <AlertTriangle size={18} className="text-amber-500" />}
                <span className="font-semibold flex-1">{t.name}</span>
                <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded-full ${
                  t.result === 'vulnerable' ? 'bg-red-100 text-red-700'
                    : t.result === 'safe' ? 'bg-green-100 text-green-700'
                      : 'bg-amber-100 text-amber-700'}`}>{t.result}</span>
              </div>
              <div className="text-sm text-slate-500 mt-1">
                <code className="bg-slate-100 px-1 rounded">{t.endpoint}</code> · {t.category}
              </div>
              {t.rationale && <p className="text-sm mt-2">{t.rationale}</p>}
              {t.detail && <p className="text-xs text-slate-500 mt-1">{t.detail}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Validation({ scanId }) {
  const [v, setV] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get(`/scans/${scanId}/validation`)
      .then((r) => setV(r.data)).catch((e) => setError(errMsg(e)))
  }, [scanId])
  if (error) return <ErrorBox message={error} />
  if (!v) return <Spinner />
  if (!v.has_known_list) {
    return <div className="text-slate-500">
      This target has no known-vulnerability list to validate against.</div>
  }
  return (
    <div>
      <div className="grid sm:grid-cols-3 gap-4 mb-5">
        <Stat label="Detection rate" value={`${v.detection_rate}%`}
          sub={`${v.detected_count}/${v.total_known} known vulns`} accent="brand" />
        <Stat label="Missed" value={v.missed_count} sub="not detected" accent="amber" />
        <Stat label="False positives" value={v.false_positive_count}
          sub="findings not in known list" accent="slate" />
      </div>
      <div className="grid sm:grid-cols-2 gap-4">
        <ListCard title="Detected" items={v.detected.map((d) => d.name)} tone="green" />
        <ListCard title="Missed" items={v.missed.map((d) => d.name)} tone="amber" />
      </div>
    </div>
  )
}

function Stat({ label, value, sub, accent }) {
  const color = { brand: 'text-brand-600', amber: 'text-amber-600', slate: 'text-slate-700' }[accent]
  return (
    <div className="card p-4">
      <div className="text-slate-500 text-sm">{label}</div>
      <div className={`text-3xl font-extrabold ${color}`}>{value}</div>
      <div className="text-xs text-slate-400">{sub}</div>
    </div>
  )
}

function ListCard({ title, items, tone }) {
  const dot = tone === 'green' ? 'bg-green-500' : 'bg-amber-500'
  return (
    <div className="card p-4">
      <h4 className="font-bold mb-2">{title}</h4>
      {items.length === 0 ? <p className="text-sm text-slate-400">None</p> : (
        <ul className="space-y-1 text-sm">
          {items.map((i) => (
            <li key={i} className="flex items-start gap-2">
              <span className={`w-2 h-2 rounded-full mt-1.5 ${dot}`} /> {i}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Reports({ scanId }) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')

  const openHtml = async () => {
    setBusy('html'); setError('')
    try {
      const r = await api.get(`/scans/${scanId}/report.html`, { responseType: 'text' })
      const url = URL.createObjectURL(new Blob([r.data], { type: 'text/html' }))
      window.open(url, '_blank')
    } catch (e) { setError(errMsg(e)) } finally { setBusy('') }
  }
  const downloadPdf = async () => {
    setBusy('pdf'); setError('')
    try {
      const r = await api.get(`/scans/${scanId}/report.pdf`, { responseType: 'blob' })
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a')
      a.href = url; a.download = `apisentry-scan-${scanId}.pdf`; a.click()
      URL.revokeObjectURL(url)
    } catch (e) { setError(errMsg(e)) } finally { setBusy('') }
  }

  return (
    <div>
      <p className="text-sm text-slate-600 mb-4">
        Share a full report with evidence, curl reproductions, OWASP mapping and fixes.
      </p>
      <ErrorBox message={error} />
      <div className="flex gap-3">
        <button className="btn-primary" onClick={openHtml} disabled={busy}>
          <FileText size={16} /> {busy === 'html' ? 'Opening…' : 'Open HTML report'}
        </button>
        <button className="btn-ghost" onClick={downloadPdf} disabled={busy}>
          <Download size={16} /> {busy === 'pdf' ? 'Preparing…' : 'Download PDF'}
        </button>
      </div>
    </div>
  )
}
