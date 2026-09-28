import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Trash2, Play, ShieldCheck, ShieldAlert, Server } from 'lucide-react'
import api, { errMsg } from '../api'
import { ErrorBox, Spinner } from '../components/ui'

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

export default function Targets() {
  const [targets, setTargets] = useState(null)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const navigate = useNavigate()

  const load = () => {
    api.get('/targets').then((r) => setTargets(r.data)).catch((e) => setError(errMsg(e)))
  }
  useEffect(load, [])

  const startScan = async (t) => {
    if (!window.confirm(
      `Confirm you are AUTHORISED to security-test ${t.base_url}. ` +
      'Only scan systems you own or have permission to test.')) return
    try {
      const r = await api.post('/scans', { target_id: t.id, authorized: true })
      navigate(`/app/scans/${r.data.id}`)
    } catch (e) { setError(errMsg(e)) }
  }

  const remove = async (t) => {
    if (!window.confirm(`Delete target "${t.name}"?`)) return
    try { await api.delete(`/targets/${t.id}`); load() } catch (e) { setError(errMsg(e)) }
  }

  return (
    <div>
      <div className="flex items-center mb-5">
        <div>
          <h1 className="text-2xl font-extrabold">Targets</h1>
          <p className="text-slate-500 text-sm">Import an API spec, set auth, then scan.</p>
        </div>
        <button className="btn-primary ml-auto" onClick={() => setShowForm((s) => !s)}>
          <Plus size={18} /> Import target
        </button>
      </div>

      <ErrorBox message={error} />
      {showForm && <ImportForm onDone={() => { setShowForm(false); load() }} />}

      {targets === null ? <Spinner /> : (
        <div className="grid gap-4 sm:grid-cols-2 mt-4">
          {targets.length === 0 && (
            <div className="text-slate-500">No targets yet. Import one to get started.</div>
          )}
          {targets.map((t) => (
            <div key={t.id} className="card p-5">
              <div className="flex items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <Server size={18} className="text-brand-500" />
                    <h3 className="font-bold text-lg">{t.name}</h3>
                  </div>
                  <div className="text-sm text-slate-500 mt-1 break-all">{t.base_url}</div>
                </div>
                <button onClick={() => remove(t)}
                  className="ml-auto text-slate-400 hover:text-red-600" title="Delete">
                  <Trash2 size={18} />
                </button>
              </div>

              <div className="flex flex-wrap gap-2 mt-3 text-xs">
                <span className="bg-slate-100 rounded-full px-2 py-1 font-medium">
                  {t.endpoint_count} endpoints
                </span>
                <span className="bg-slate-100 rounded-full px-2 py-1 font-medium">
                  {t.known_vulns?.length || 0} known vulns
                </span>
                {t.in_scope ? (
                  <span className="inline-flex items-center gap-1 bg-green-50 text-green-700
                    border border-green-200 rounded-full px-2 py-1 font-medium">
                    <ShieldCheck size={13} /> In scope
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 bg-red-50 text-red-700
                    border border-red-200 rounded-full px-2 py-1 font-medium">
                    <ShieldAlert size={13} /> Out of scope
                  </span>
                )}
              </div>

              {t.last_scan && (
                <div className="text-sm text-slate-500 mt-3">
                  Last scan: #{t.last_scan.id} · {t.last_scan.status}
                  {t.last_scan.status === 'done' &&
                    ` · ${t.last_scan.score}/100 (${t.last_scan.grade})`}
                </div>
              )}

              <div className="flex gap-2 mt-4">
                <button className="btn-primary" disabled={!t.in_scope}
                  onClick={() => startScan(t)} title={t.in_scope ? '' : 'Host not allow-listed'}>
                  <Play size={16} /> Scan
                </button>
                {t.last_scan && (
                  <button className="btn-ghost"
                    onClick={() => navigate(`/app/scans/${t.last_scan.id}`)}>
                    View last result
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ImportForm({ onDone }) {
  const [name, setName] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [spec, setSpec] = useState('')
  const [auth, setAuth] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(''); setBusy(true)
    let authObj = {}
    try { authObj = auth.trim() ? JSON.parse(auth) : {} }
    catch { setError('Auth profile is not valid JSON'); setBusy(false); return }
    try {
      await api.post('/targets/import-spec', {
        name: name || 'Imported API', spec_text: spec,
        base_url: baseUrl || null, auth: authObj,
      })
      onDone()
    } catch (err) { setError(errMsg(err)) } finally { setBusy(false) }
  }

  return (
    <form onSubmit={submit} className="card p-5 space-y-3">
      <div className="grid sm:grid-cols-2 gap-3">
        <div>
          <label className="label">Target name</label>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="Payments API (staging)" />
        </div>
        <div>
          <label className="label">Base URL (optional if in spec)</label>
          <input className="input" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="http://localhost:12130" />
        </div>
      </div>
      <div>
        <div className="flex items-center gap-2">
          <label className="label mb-0">OpenAPI / Swagger / Postman collection (paste)</label>
          <button type="button" className="text-xs text-brand-600 ml-auto"
            onClick={() => setSpec(SAMPLE_SPEC)}>Insert example</button>
        </div>
        <textarea className="input font-mono text-xs h-40" value={spec}
          onChange={(e) => setSpec(e.target.value)} placeholder="Paste your API spec JSON/YAML" />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <label className="label mb-0">Auth profile (optional JSON)</label>
          <button type="button" className="text-xs text-brand-600 ml-auto"
            onClick={() => setAuth(SAMPLE_AUTH)}>Insert example</button>
        </div>
        <textarea className="input font-mono text-xs h-32" value={auth}
          onChange={(e) => setAuth(e.target.value)}
          placeholder="Bearer login flow or pre-supplied tokens for two test users" />
      </div>
      <ErrorBox message={error} />
      <div className="flex gap-2">
        <button className="btn-primary" disabled={busy}>
          {busy ? 'Importing…' : 'Import'}
        </button>
        <button type="button" className="btn-ghost" onClick={onDone}>Cancel</button>
      </div>
    </form>
  )
}
