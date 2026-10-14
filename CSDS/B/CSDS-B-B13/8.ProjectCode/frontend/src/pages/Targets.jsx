import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, FileJson, PencilLine, Play, Plus, Server, ShieldAlert, ShieldCheck, Trash2 } from 'lucide-react'
import api, { errMsg } from '../api'
import { useAsync } from '../lib/useAsync'
import {
  Badge, Button, Card, Checkbox, EmptyState, ErrorState, FileDrop, IconButton, Input, Modal,
  PageHeader, Skeleton, Tabs, Textarea, useToast,
} from '../components/ui'
import { FadeIn } from '../components/motion'

const SAMPLE_SPEC = `{
  "openapi": "3.0.0",
  "info": { "title": "My API", "version": "1.0.0" },
  "servers": [{ "url": "http://localhost:12130" }],
  "paths": {
    "/login": { "post": { "summary": "Login" } },
    "/accounts/{id}": { "get": { "summary": "Get account",
      "parameters": [{ "name": "id", "in": "path", "required": true }] } }
  }
}`

const SAMPLE_AUTH = `{
  "type": "login",
  "login_path": "/login",
  "username_field": "username",
  "password_field": "password",
  "token_field": "token",
  "scheme": "Bearer",
  "user_a": { "username": "alice", "password": "password123" },
  "user_b": { "username": "bob", "password": "password123" }
}`

const SAMPLE_VULNS = `[
  { "key": "bola:/accounts/{account_id}", "name": "BOLA on /accounts/{account_id}", "severity": "critical", "owasp": "API1" }
]`

const SAMPLE_ENDPOINTS = `[
  { "method": "GET", "path": "/accounts/{id}", "id_params": ["id"], "query_params": [], "body_fields": [], "summary": "Get account" }
]`

const IMPORT_MODES = [
  { value: 'spec', label: 'From spec', icon: FileJson },
  { value: 'manual', label: 'Manual', icon: PencilLine },
]

// Parses an optional JSON textarea. Empty means the default (an empty array or object).
function parseJson(text, kind, label) {
  const t = text.trim()
  if (!t) return kind === 'array' ? [] : {}
  let value
  try {
    value = JSON.parse(t)
  } catch {
    throw new Error(`${label} is not valid JSON.`)
  }
  const ok = kind === 'array' ? Array.isArray(value) : value !== null && typeof value === 'object' && !Array.isArray(value)
  if (!ok) throw new Error(`${label} must be a JSON ${kind === 'array' ? 'array' : 'object'}.`)
  return value
}

export default function Targets() {
  const toast = useToast()
  const navigate = useNavigate()
  const targets = useAsync(() => api.get('/targets').then((r) => r.data), [])
  const [importOpen, setImportOpen] = useState(false)
  const [scanTarget, setScanTarget] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)

  const rows = targets.data

  return (
    <FadeIn>
      <PageHeader
        title="Targets"
        description="Import an API spec, set auth, then scan."
        actions={
          <Button variant="primary" icon={Plus} onClick={() => setImportOpen(true)}>
            Import target
          </Button>
        }
      />

      {targets.error && !rows ? (
        <ErrorState title="Could not load targets" error={{ message: errMsg(targets.error) }} onRetry={targets.reload}>
          <p className="faint">Check that the backend is running on port 8213.</p>
        </ErrorState>
      ) : !rows ? (
        <div className="target-grid">
          {[0, 1].map((i) => (
            <Card key={i} pad spotlight={false}>
              <Skeleton width="60%" height={20} />
              <Skeleton width="85%" height={14} style={{ marginTop: 12 }} />
              <Skeleton width="100%" height={36} style={{ marginTop: 20 }} />
            </Card>
          ))}
        </div>
      ) : rows.length === 0 ? (
        <Card spotlight={false}>
          <EmptyState icon={Server} title="No targets yet" actions={<Button variant="primary" icon={Plus} onClick={() => setImportOpen(true)}>Import your first target</Button>}>
            Import an OpenAPI, Swagger or Postman spec to start.
          </EmptyState>
        </Card>
      ) : (
        <div className="target-grid">
          {rows.map((t) => (
            <TargetCard
              key={t.id}
              t={t}
              onScan={() => setScanTarget(t)}
              onView={(id) => navigate(`/app/scans/${id}`)}
              onDelete={() => setDeleteTarget(t)}
            />
          ))}
        </div>
      )}

      <Modal open={importOpen} onClose={() => setImportOpen(false)} title="Import target">
        <ImportForm
          onCancel={() => setImportOpen(false)}
          onDone={(t) => {
            setImportOpen(false)
            toast({ title: 'Target imported', message: `${t.name} · ${t.endpoint_count} endpoints` })
            targets.reload()
          }}
        />
      </Modal>

      <ScanConfirm
        target={scanTarget}
        onClose={() => setScanTarget(null)}
        onStarted={(scan) => {
          setScanTarget(null)
          toast({ title: `Scan #${scan.id} started`, message: scanTarget?.name })
          navigate(`/app/scans/${scan.id}`)
        }}
      />

      <DeleteConfirm
        target={deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onDeleted={(t) => {
          setDeleteTarget(null)
          toast({ title: 'Target deleted', message: t.name })
          targets.reload()
        }}
      />
    </FadeIn>
  )
}

function TargetCard({ t, onScan, onView, onDelete }) {
  const last = t.last_scan
  return (
    <Card as="article" pad className="target-card">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div style={{ minWidth: 0 }}>
          <h3>{t.name}</h3>
          <p className="mono break faint" style={{ marginTop: 4 }}>
            {t.base_url}
          </p>
        </div>
        <IconButton icon={Trash2} label={`Delete ${t.name}`} size="sm" onClick={onDelete} />
      </div>

      <div className="target-meta">
        <Badge>{t.endpoint_count} endpoints</Badge>
        <Badge>{t.known_vulns?.length || 0} known vulns</Badge>
        {t.in_scope ? (
          <Badge tone="safe" dot>
            <ShieldCheck size={12} aria-hidden="true" /> In scope
          </Badge>
        ) : (
          <Badge tone="danger" dot>
            <ShieldAlert size={12} aria-hidden="true" /> Out of scope
          </Badge>
        )}
      </div>

      {last ? (
        <p className="muted" style={{ marginTop: 14, fontSize: 14 }}>
          Last scan #{last.id} · {last.status}
          {last.status === 'done' && ` · ${last.score}/100 (${last.grade})`}
        </p>
      ) : (
        <p className="faint" style={{ marginTop: 14 }}>
          Not scanned yet
        </p>
      )}

      <div className="target-actions">
        <Button
          variant="primary"
          icon={Play}
          disabled={!t.in_scope}
          title={t.in_scope ? undefined : 'This host is not on the scope allow-list'}
          onClick={onScan}
        >
          Scan
        </Button>
        {last && (
          <Button variant="ghost" icon={Eye} onClick={() => onView(last.id)}>
            View last result
          </Button>
        )}
      </div>
    </Card>
  )
}

function ScanConfirm({ target, onClose, onStarted }) {
  const [authorised, setAuthorised] = useState(false)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')

  // Reset the checkbox each time a different target is opened.
  const key = target?.id
  const [lastKey, setLastKey] = useState(key)
  if (key !== lastKey) {
    setLastKey(key)
    setAuthorised(false)
    setError('')
  }

  const close = () => {
    if (starting) return
    onClose()
  }

  const start = async () => {
    setStarting(true)
    setError('')
    try {
      const r = await api.post('/scans', { target_id: target.id, authorized: true })
      onStarted(r.data)
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setStarting(false)
    }
  }

  return (
    <Modal
      open={!!target}
      onClose={close}
      title="Confirm you are authorised"
      footer={
        <>
          <Button variant="ghost" onClick={close} disabled={starting}>
            Cancel
          </Button>
          <Button variant="primary" icon={Play} onClick={start} disabled={!authorised} loading={starting}>
            Start scan
          </Button>
        </>
      }
    >
      <p>
        You are about to scan <strong className="break">{target?.base_url}</strong>.
      </p>
      <p className="muted" style={{ marginTop: 10 }}>
        Only scan systems you own or have written permission to test.
      </p>
      <div className="check-row">
        <Checkbox label="I confirm I am authorised to test this target" checked={authorised} onChange={(e) => setAuthorised(e.target.checked)} />
      </div>
      {error && (
        <p className="form-error" role="alert" style={{ marginTop: 12 }}>
          {error}
        </p>
      )}
    </Modal>
  )
}

function DeleteConfirm({ target, onClose, onDeleted }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const remove = async () => {
    setBusy(true)
    setError('')
    try {
      await api.delete(`/targets/${target.id}`)
      onDeleted(target)
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={!!target}
      onClose={() => !busy && onClose()}
      title="Delete target?"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button variant="danger" icon={Trash2} onClick={remove} loading={busy}>
            Delete
          </Button>
        </>
      }
    >
      <p>
        <strong className="break">{target?.name}</strong> will be removed from your targets. This cannot be undone.
      </p>
      {error && (
        <p className="form-error" role="alert" style={{ marginTop: 12 }}>
          {error}
        </p>
      )}
    </Modal>
  )
}

function ImportForm({ onDone, onCancel }) {
  const [mode, setMode] = useState('spec')
  const [name, setName] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [spec, setSpec] = useState('')
  const [endpoints, setEndpoints] = useState('')
  const [auth, setAuth] = useState('')
  const [vulns, setVulns] = useState('')
  const [formError, setFormError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setFormError('')
    let payload
    try {
      const trimmedName = name.trim()
      if (!trimmedName) throw new Error('Give the target a name.')
      const common = {
        name: trimmedName,
        auth: parseJson(auth, 'object', 'Auth profile'),
        known_vulns: parseJson(vulns, 'array', 'Known vulnerabilities'),
      }
      if (mode === 'spec') {
        if (!spec.trim()) throw new Error('Paste an API spec or upload a file.')
        payload = { ...common, spec_text: spec, base_url: baseUrl.trim() || null }
      } else {
        if (!baseUrl.trim()) throw new Error('A base URL is required for a manual target.')
        payload = { ...common, base_url: baseUrl.trim(), endpoints: parseJson(endpoints, 'array', 'Endpoints') }
      }
    } catch (err) {
      setFormError(err.message)
      return
    }
    setBusy(true)
    try {
      const r = await api.post(mode === 'spec' ? '/targets/import-spec' : '/targets', payload)
      onDone(r.data)
    } catch (err) {
      setFormError(errMsg(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} noValidate className="form-stack">
      <Tabs label="Import method" tabs={IMPORT_MODES} value={mode} onChange={(m) => { setMode(m); setFormError('') }} />

      <div className="form-grid">
        <Input label="Target name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Payments API (staging)" required />
        <Input
          label={mode === 'spec' ? 'Base URL (optional)' : 'Base URL'}
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          placeholder="http://localhost:12130"
          hint={mode === 'spec' ? 'Leave blank to use the server URL in the spec.' : 'Must be on the scope allow-list to scan.'}
        />
      </div>

      {mode === 'spec' ? (
        <>
          <FileDrop
            accept=".json,.yaml,.yml,.txt"
            label="Drop an OpenAPI, Swagger or Postman file here, or click to browse"
            hint="JSON or YAML, up to 512 KB"
            onFile={(info) => info && setSpec(info.text)}
          />
          <div className="field-head">
            <span className="field-label">Spec</span>
            <Button size="sm" variant="ghost" onClick={() => setSpec(SAMPLE_SPEC)}>
              Insert example
            </Button>
          </div>
          <Textarea aria-label="API spec" mono rows={8} value={spec} onChange={(e) => setSpec(e.target.value)} placeholder="Paste your API spec as JSON or YAML" />
        </>
      ) : (
        <>
          <div className="field-head">
            <span className="field-label">Endpoints (JSON array)</span>
            <Button size="sm" variant="ghost" onClick={() => setEndpoints(SAMPLE_ENDPOINTS)}>
              Insert example
            </Button>
          </div>
          <Textarea aria-label="Endpoints as JSON" mono rows={7} value={endpoints} onChange={(e) => setEndpoints(e.target.value)} placeholder="[]" />
        </>
      )}

      <div className="field-head">
        <span className="field-label">Auth profile (optional JSON)</span>
        <Button size="sm" variant="ghost" onClick={() => setAuth(SAMPLE_AUTH)}>
          Insert example
        </Button>
      </div>
      <Textarea
        aria-label="Auth profile as JSON"
        mono
        rows={6}
        value={auth}
        onChange={(e) => setAuth(e.target.value)}
        placeholder="Bearer login flow or pre-supplied tokens for two test users"
      />

      <div className="field-head">
        <span className="field-label">Known vulnerabilities (optional JSON array)</span>
        <Button size="sm" variant="ghost" onClick={() => setVulns(SAMPLE_VULNS)}>
          Insert example
        </Button>
      </div>
      <Textarea
        aria-label="Known vulnerabilities as JSON"
        mono
        rows={4}
        value={vulns}
        onChange={(e) => setVulns(e.target.value)}
        placeholder="Used by Validation to compare findings with a known list"
      />
      <p className="faint" style={{ marginTop: -6 }}>
        Known vulnerabilities let the Validation tab report what was detected, missed and falsely flagged.
      </p>

      {formError && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}
      <div className="row" style={{ justifyContent: 'flex-end', gap: 8 }}>
        <Button variant="ghost" onClick={onCancel} disabled={busy}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" icon={Plus} loading={busy}>
          Import target
        </Button>
      </div>
    </form>
  )
}
