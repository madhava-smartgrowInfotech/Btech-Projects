import { Fragment, useEffect, useState } from 'react'
import { ScrollText } from 'lucide-react'
import api, { errText } from '../api'
import { Badge, ErrorBox, PageHead, Spinner } from '../components/ui'

const OPS = ['', 'send', 'receive', 'key_generate', 'key_import', 'key_export_private', 'key_delete', 'robustness', 'benchmark', 'login']

function summary(e) {
  const d = e.details
  if (!e.ok) return d.error || 'failed'
  if (e.op === 'send') return `${d.filename} (${d.payload_bytes} B) into ${d.cover} - PSNR ${d.quality?.psnr_db} dB, SSIM ${d.quality?.ssim}`
  if (e.op === 'receive') return `${d.filename} (${d.output_bytes} B) - hash ${d.hash_match ? 'match' : 'MISMATCH'}`
  if (e.op.startsWith('key')) return `${d.bits ? d.bits + '-bit ' : ''}${d.fingerprint || ''}`
  if (e.op === 'robustness') return `survived: ${d.survived?.length ?? 0}, lost: ${d.lost?.length ?? 0}`
  if (e.op === 'benchmark') return `${d.covers} covers, ${d.rows} runs`
  return ''
}

export default function Log() {
  const [rows, setRows] = useState(null)
  const [filter, setFilter] = useState('')
  const [open, setOpen] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setRows(null)
    api.get('/log', { params: { op: filter || undefined, limit: 200 } })
      .then((r) => setRows(r.data)).catch((e) => setError(errText(e)))
  }, [filter])

  return (
    <>
      <PageHead icon={ScrollText} title="Operation log" sub="Every operation with sizes, timings and metrics. Keys, passwords and file contents are never recorded." />
      <div className="mb-4 max-w-xs">
        <label className="label" htmlFor="f">Filter</label>
        <select id="f" className="input" value={filter} onChange={(e) => setFilter(e.target.value)}>
          {OPS.map((o) => <option key={o} value={o}>{o || 'All operations'}</option>)}
        </select>
      </div>
      <ErrorBox>{error}</ErrorBox>
      <div className="card mt-2 overflow-x-auto p-0">
        <table className="w-full">
          <thead className="border-b border-slate-200"><tr>
            <th className="th">#</th><th className="th">When</th><th className="th">Operation</th><th className="th">Status</th><th className="th">Details</th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {rows === null && !error && <tr><td className="td" colSpan={5}><Spinner text="Loading log..." /></td></tr>}
            {rows?.length === 0 && <tr><td className="td text-slate-500" colSpan={5}>Nothing logged yet.</td></tr>}
            {rows?.map((e) => (
              <Fragment key={e.id}>
                <tr className="cursor-pointer align-top hover:bg-slate-50" onClick={() => setOpen(open === e.id ? null : e.id)}>
                  <td className="td text-slate-400">{e.id}</td>
                  <td className="td whitespace-nowrap">{new Date(e.created_at).toLocaleString()}</td>
                  <td className="td font-medium">{e.op}</td>
                  <td className="td"><Badge tone={e.ok ? 'good' : 'bad'}>{e.ok ? 'ok' : 'failed'}</Badge></td>
                  <td className="td text-slate-600">{summary(e)}</td>
                </tr>
                {open === e.id && (
                  <tr><td colSpan={5} className="bg-slate-50 px-3 py-2">
                    <pre className="overflow-x-auto text-xs">{JSON.stringify(e.details, null, 2)}</pre></td></tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
