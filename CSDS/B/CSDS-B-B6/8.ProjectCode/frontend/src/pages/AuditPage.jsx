import { useState } from 'react'
import { ScrollText, ShieldAlert, ShieldCheck } from 'lucide-react'
import api from '../api'
import { useAuth } from '../App.jsx'
import { Badge, Button, Card, ErrorBox, Spinner, useAsync } from '../components/ui'

const ACTION_COLOR = (a) => a.startsWith('access.denied') ? 'rose' : a.startsWith('consent') ? 'violet' : a.startsWith('record') || a.startsWith('risk') ? 'blue'
  : a.startsWith('assistant') ? 'teal' : a.startsWith('sync') || a.startsWith('hospital') ? 'green' : 'slate'

function detailText(d) {
  return Object.entries(d).filter(([, v]) => v !== null && v !== '' && !(Array.isArray(v) && !v.length))
    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : typeof v === 'object' ? JSON.stringify(v) : String(v).slice(0, 40)}`).join(' | ')
}

export default function AuditPage() {
  const { user } = useAuth()
  const audit = useAsync(async () => (await api.get('/audit')).data, [])
  const [filter, setFilter] = useState('')
  const v = audit.data?.verification
  const entries = (audit.data?.entries || []).filter((e) => !filter || `${e.action} ${e.actor} ${e.person_id}`.toLowerCase().includes(filter.toLowerCase()))
  const scope = { patient: 'Everything that happened to your record', doctor: 'Your own actions', staff: 'Your own actions', admin: 'All platform events' }[user.role]

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2"><ScrollText className="w-6 h-6 text-teal-600" /> Audit & consent log</h1>
      {audit.error && <ErrorBox error={audit.error} onRetry={audit.reload} />}
      {v && (
        <div className={`flex flex-wrap items-center gap-3 rounded-xl border p-4 ${v.intact ? 'border-emerald-200 bg-emerald-50' : 'border-rose-200 bg-rose-50'}`}>
          {v.intact ? <ShieldCheck className="w-8 h-8 text-emerald-600" /> : <ShieldAlert className="w-8 h-8 text-rose-600" />}
          <div className="flex-1">
            <div className={`font-semibold ${v.intact ? 'text-emerald-800' : 'text-rose-800'}`}>{v.intact ? 'Ledger verified intact' : `Tampering detected at entry #${v.broken_at}`}</div>
            <div className="text-xs text-slate-600">{v.entries} hash-chained entries (SHA-256). {v.intact && <>Head <span className="font-mono">{v.head.slice(0, 16)}...</span></>}</div>
          </div>
          <Button variant="secondary" loading={audit.loading} onClick={audit.reload}>Verify again</Button>
        </div>
      )}
      <Card title={scope} icon={ScrollText} actions={<input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter..." className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />}>
        {audit.loading && !audit.data ? <Spinner /> : (
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-slate-500 border-b">
                <th className="py-2 pr-3">#</th><th className="pr-3">Time</th><th className="pr-3">Actor</th><th className="pr-3">Action</th><th className="pr-3">Person</th><th className="pr-3">Detail</th><th>Hash</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {entries.map((e) => (
                  <tr key={e.id} className="align-top">
                    <td className="py-1.5 pr-3 text-slate-400">{e.id}</td>
                    <td className="pr-3 whitespace-nowrap text-xs text-slate-600">{new Date(e.ts).toLocaleString()}</td>
                    <td className="pr-3 text-xs">{e.actor}</td>
                    <td className="pr-3"><Badge color={ACTION_COLOR(e.action)}>{e.action}</Badge></td>
                    <td className="pr-3 font-mono text-xs">{e.person_id || '-'}</td>
                    <td className="pr-3 text-xs text-slate-600 max-w-md">{detailText(e.detail)}</td>
                    <td className="font-mono text-xs text-slate-400" title={`prev ${e.prev_hash}`}>{e.hash.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {entries.length === 0 && <p className="text-sm text-slate-500 py-4 text-center">No entries.</p>}
          </div>
        )}
      </Card>
    </div>
  )
}
