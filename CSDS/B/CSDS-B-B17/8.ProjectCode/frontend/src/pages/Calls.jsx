import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Flag, FlaskConical, PackageOpen, PhoneCall, Upload } from 'lucide-react'
import api, { errorText } from '../api'
import { useAuth } from '../lib/auth'
import { cleanTitle, fmtDate, fmtTime, label, plural } from '../lib/format'
import {
  Alert, Button, Card, EmptyState, ErrorState, FileDrop, PageHeader, SearchField, Select, SkeletonBlock, StatCard, StatusBadge, Table, useToast,
} from '../components/ui'
import { SampleBadge, ScorePill, SentimentValue } from '../components/app/Bits'
import Recorder from '../components/app/Recorder'

export default function Calls() {
  const { user } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const sup = user?.role === 'supervisor'
  const [calls, setCalls] = useState(null)
  const [agents, setAgents] = useState([])
  const [q, setQ] = useState('')
  const [search, setSearch] = useState('')
  const [agentFilter, setAgentFilter] = useState('')
  const [error, setError] = useState('')
  const [files, setFiles] = useState([])
  const [uploadAgent, setUploadAgent] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [importing, setImporting] = useState(false)

  // Debounce the transcript search so every keystroke is not a request.
  useEffect(() => {
    const t = setTimeout(() => setSearch(q.trim()), 400)
    return () => clearTimeout(t)
  }, [q])

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/calls', { params: { q: search || undefined, agent_id: agentFilter || undefined } })
      setCalls(data.calls)
      setError('')
    } catch (err) {
      setError(errorText(err))
    }
  }, [search, agentFilter])

  useEffect(() => {
    load()
  }, [load])
  useEffect(() => {
    api.get('/agents').then((r) => setAgents(r.data)).catch(() => {})
  }, [])
  // Keep the list fresh while calls are being analysed.
  useEffect(() => {
    if (!calls?.some((c) => c.status === 'queued' || c.status === 'processing')) return undefined
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [calls, load])

  const upload = async () => {
    if (!files.length) return
    setUploading(true)
    setUploadError('')
    const fd = new FormData()
    files.forEach((f) => fd.append('files', f))
    if (uploadAgent) fd.append('agent_id', uploadAgent)
    try {
      const { data } = await api.post('/calls', fd)
      toast.success(`${plural(data.calls.length, 'recording')} queued for analysis.`)
      setFiles([])
      load()
    } catch (err) {
      setUploadError(errorText(err))
    } finally {
      setUploading(false)
    }
  }

  const importSamples = async () => {
    setImporting(true)
    setUploadError('')
    try {
      const { data } = await api.post('/studio/import-samples')
      if (data.added) toast.success(`${plural(data.added, 'sample call')} queued — each takes about a minute to analyse.`)
      else toast.info('All sample calls are already loaded.')
      load()
    } catch (err) {
      setUploadError(errorText(err))
    } finally {
      setImporting(false)
    }
  }

  const stats = useMemo(() => {
    if (!calls) return null
    return {
      total: calls.length,
      running: calls.filter((c) => c.status === 'queued' || c.status === 'processing').length,
      flagged: calls.filter((c) => c.flags > 0).length,
    }
  }, [calls])

  const columns = [
    {
      key: 'title',
      label: 'Call',
      sortValue: (c) => cleanTitle(c.title),
      render: (c) => (
        <div onClick={(e) => e.stopPropagation()}>
          <Link to={`/calls/${c.id}`} className="call-title">
            {cleanTitle(c.title)}
          </Link>
          <div className="meta-line">
            {c.is_sample && <SampleBadge />}
            {c.source === 'microphone' && <span>microphone</span>}
            <span>{fmtDate(c.recorded_at)}</span>
            {c.flags > 0 && (
              <span className="neg" style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
                <Flag size={12} aria-hidden="true" /> {plural(c.flags, 'flag')}
              </span>
            )}
          </div>
          {c.snippet && <div className="snippet">{c.snippet}</div>}
        </div>
      ),
    },
    { key: 'agent', label: 'Agent', render: (c) => c.agent || '—' },
    { key: 'duration', label: 'Length', numeric: true, render: (c) => fmtTime(c.duration) },
    { key: 'intent', label: 'Intent', render: (c) => <span style={{ textTransform: 'capitalize' }}>{label(c.intent)}</span> },
    { key: 'sentiment', label: 'Sentiment', numeric: true, render: (c) => <SentimentValue value={c.sentiment} /> },
    { key: 'score', label: 'Score', numeric: true, render: (c) => <ScorePill score={c.score} /> },
    { key: 'status', label: 'Status', render: (c) => <StatusBadge status={c.status} stage={c.stage} /> },
  ]

  const filtered = Boolean(search || agentFilter)

  return (
    <>
      <PageHeader
        eyebrow={sup ? 'All calls across the team' : 'Your calls'}
        title="Calls"
        description="Search across every transcript, then open a call for its emotion timeline, summary and scorecard."
        actions={
          <Button variant="primary" icon={FlaskConical} to="/studio">
            Sample studio
          </Button>
        }
      />
      <div className="split">
        <div className="stack" style={{ '--gap': '20px' }}>
          {stats && calls.length > 0 && (
            <div className="stat-row">
              <StatCard label={filtered ? 'Matching calls' : 'Calls'} value={stats.total} icon={PhoneCall} />
              <StatCard label="Analysing now" value={stats.running} tone={stats.running ? 'lime' : undefined} hint={stats.running ? 'refreshing every 4 s' : 'queue is empty'} />
              <StatCard label="With escalation flags" value={stats.flagged} icon={Flag} />
            </div>
          )}
          <div className="filters">
            <SearchField value={q} onChange={setQ} label="Search transcripts" placeholder="Search transcripts, e.g. refund" />
            {sup && (
              <div style={{ maxWidth: 220 }}>
                <Select label="Agent" value={agentFilter} onChange={(e) => setAgentFilter(e.target.value)}>
                  <option value="">All agents</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </Select>
              </div>
            )}
            {filtered && (
              <Button
                variant="ghost"
                onClick={() => {
                  setQ('')
                  setSearch('')
                  setAgentFilter('')
                }}
              >
                Clear filters
              </Button>
            )}
          </div>

          {error && !calls ? (
            <ErrorState title="Could not load calls" error={error} onRetry={load} />
          ) : calls == null ? (
            <SkeletonBlock rows={6} label="Loading calls" />
          ) : (
            <>
              {error && <Alert tone="error">{error}</Alert>}
              <Table
                caption="Calls"
                columns={columns}
                rows={calls}
                pageSize={10}
                initialSort={null}
                onRowClick={(c) => nav(`/calls/${c.id}`)}
                empty={
                  <EmptyState
                    icon={PhoneCall}
                    title={filtered ? 'No calls match' : 'No calls yet'}
                    action={
                      filtered ? (
                        <Button
                          onClick={() => {
                            setQ('')
                            setSearch('')
                            setAgentFilter('')
                          }}
                        >
                          Clear filters
                        </Button>
                      ) : sup ? (
                        <Button variant="primary" icon={PackageOpen} onClick={importSamples} loading={importing}>
                          Load sample calls
                        </Button>
                      ) : (
                        <Button variant="primary" icon={FlaskConical} to="/studio">
                          Make a sample call
                        </Button>
                      )
                    }
                  >
                    {search
                      ? `No call mentions “${search}”.`
                      : 'Upload a recording, record one from the microphone, or generate a sample call in the studio.'}
                  </EmptyState>
                }
              />
            </>
          )}
        </div>

        <aside className="stack" aria-label="Add calls">
          <Card title="Add calls">
            <div className="stack">
              <FileDrop multiple files={files} onFiles={setFiles} />
              {sup && (
                <Select label="Handled by agent" value={uploadAgent} onChange={(e) => setUploadAgent(e.target.value)}>
                  <option value="">Unassigned</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </Select>
              )}
              <Button variant="primary" block icon={Upload} disabled={!files.length} loading={uploading} onClick={upload}>
                {files.length > 1 ? `Upload ${files.length} recordings` : 'Upload recording'}
              </Button>
              <Recorder
                agentId={uploadAgent}
                onDone={() => {
                  load()
                }}
              />
              <p className="small muted">Stereo recordings are split by channel (agent and customer); single-channel audio uses a turn split. Max 60 MB per file.</p>
              {uploadError && <Alert tone="error">{uploadError}</Alert>}
            </div>
          </Card>
          {sup && (
            <Card title="Sample data" tone="lime">
              <p className="small" style={{ marginBottom: 12 }}>
                Load the 10 bundled sample calls (synthetic voices, clearly labelled) to populate analytics.
              </p>
              <Button block icon={PackageOpen} onClick={importSamples} loading={importing}>
                Load sample calls
              </Button>
            </Card>
          )}
        </aside>
      </div>
    </>
  )
}
