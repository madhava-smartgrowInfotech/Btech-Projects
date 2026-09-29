import { useEffect, useState } from 'react'
import { CheckCircle2, Loader2, Mail, RefreshCw, Send, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import api, { errMsg, token } from '../api.js'
import { ErrorBox, PageTitle, Spinner, StatusBadge } from '../components/ui.jsx'

const fmt = (iso) => (iso ? new Date(iso).toLocaleString() : '-')
const ms = (v) => (v == null ? '-' : v >= 1000 ? `${(v / 1000).toFixed(1)} s` : `${Math.round(v)} ms`)

function Channel({ icon: Icon, name, results }) {
  if (!results?.length) return null
  return (
    <div className="text-xs space-y-1">
      {results.map((r, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5 text-slate-400" />
          {r.ok ? <CheckCircle2 className="w-3.5 h-3.5 text-green-600" /> : <XCircle className="w-3.5 h-3.5 text-red-500" />}
          <span>{name} to {r.to}</span>
          <span className="text-slate-400">{r.ok ? ms(r.ms) : r.error}</span>
        </div>
      ))}
    </div>
  )
}

export default function Alerts() {
  const [alerts, setAlerts] = useState(null)
  const [channels, setChannels] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')

  const load = async () => {
    try {
      const [a, s] = await Promise.all([api.get('/alerts'), api.get('/settings')])
      setAlerts(a.data)
      setChannels(s.data.channels)
      setError('')
    } catch (e) { setError(errMsg(e)) }
  }
  useEffect(() => { load(); const id = setInterval(load, 3000); return () => clearInterval(id) }, [])

  const ok = async (id) => {
    setBusy(`ok${id}`)
    try { await api.post(`/alerts/${id}/ok`); await load() } catch (e) { setError(errMsg(e)) } finally { setBusy('') }
  }
  const test = async () => {
    setBusy('test')
    try { await api.post('/alerts/test'); await load() } catch (e) { setError(errMsg(e)) } finally { setBusy('') }
  }

  return (
    <div>
      <PageTitle title="Alerts" subtitle="Fall alerts, acknowledgements and delivery to your contacts">
        <button className="btn btn-secondary" onClick={load}><RefreshCw className="w-4 h-4" /> Refresh</button>
        <button className="btn btn-primary" onClick={test} disabled={busy === 'test'}>
          {busy === 'test' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Send test alert
        </button>
      </PageTitle>
      <div className="space-y-3 mb-4">
        <ErrorBox error={error} onRetry={load} />
        {channels && (!channels.telegram || !channels.email) && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
            {!channels.telegram && 'Telegram is not configured (TELEGRAM_BOT_TOKEN). '}
            {!channels.email && 'Email is not configured (SMTP_USER / SMTP_PASSWORD). '}
            Alerts are still detected and logged; add the keys to .env and restart to deliver them. See <Link className="underline" to="/contacts">Contacts & settings</Link>.
          </div>
        )}
      </div>
      {!alerts ? <Spinner /> : alerts.length === 0 ? (
        <div className="card p-10 text-center text-slate-500">No alerts yet. Falls confirmed by the live monitor appear here.</div>
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => (
            <div key={a.id} className="card p-4 flex flex-col md:flex-row gap-4">
              {a.has_snapshot
                ? <img alt="Alert snapshot" className="w-full md:w-48 h-32 object-cover rounded-lg bg-slate-100" src={`/api/alerts/${a.id}/snapshot?token=${token()}`} />
                : <div className="w-full md:w-48 h-32 rounded-lg bg-slate-100 flex items-center justify-center text-xs text-slate-400">{a.kind === 'test' ? 'Test alert' : 'No snapshot'}</div>}
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-slate-900">#{a.id} {a.kind === 'fall' ? 'Fall detected' : 'Test alert'}</span>
                  <StatusBadge status={a.status} />
                  {a.status === 'pending' && <span className="text-sm text-amber-700">sending in {Math.ceil(a.seconds_left)} s</span>}
                </div>
                <div className="text-sm text-slate-600 mt-1">{fmt(a.detected_at)}{a.resolved_by && ` - acknowledged by ${a.resolved_by}`}</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 text-xs">
                  {a.kind === 'fall' && <div><div className="text-slate-400">Impact to confirmation</div><div className="font-medium">{ms(a.detection_latency_ms)}</div></div>}
                  <div><div className="text-slate-400">Delivery time</div><div className="font-medium">{ms(a.dispatch_ms)}</div></div>
                  <div><div className="text-slate-400">Detected to sent</div><div className="font-medium">{ms(a.detected_to_sent_ms)}</div></div>
                  <div><div className="text-slate-400">Sent at</div><div className="font-medium">{a.sent_at ? new Date(a.sent_at).toLocaleTimeString() : '-'}</div></div>
                </div>
                <div className="mt-3 space-y-1">
                  <Channel icon={Send} name="Telegram" results={a.channels.telegram} />
                  <Channel icon={Mail} name="Email" results={a.channels.email} />
                  {a.channels.note && <div className="text-xs text-slate-500">{a.channels.note}</div>}
                </div>
              </div>
              {a.status === 'pending' && (
                <button className="btn btn-primary self-start" onClick={() => ok(a.id)} disabled={busy === `ok${a.id}`}>
                  {busy === `ok${a.id}` && <Loader2 className="w-4 h-4 animate-spin" />} I'm OK
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
