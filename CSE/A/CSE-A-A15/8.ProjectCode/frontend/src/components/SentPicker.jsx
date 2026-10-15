import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Send } from 'lucide-react'
import api, { describeError } from '../api'
import { Select } from './ui/controls'
import { EmptyState, ErrorState, Skeleton } from './ui/feedback'

// Dropdown of successful send operations. The choice is mirrored to ?op= so links and reloads keep it.
export default function SentPicker({ onChange }) {
  const [params, setParams] = useSearchParams()
  const [ops, setOps] = useState(null)
  const [error, setError] = useState(null)
  const current = params.get('op') || ''

  const load = useCallback(() => {
    setError(null)
    return api.get('/log', { params: { op: 'send', limit: 100 } })
      .then((r) => {
        const ok = r.data.filter((x) => x.ok)
        setOps(ok)
        if (!params.get('op') && ok[0]) setParams({ op: String(ok[0].id) }, { replace: true })
      })
      .catch((e) => setError(describeError(e)))
    // runs once; the URL param is read from the first render
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (ops && current) onChange(ops.find((o) => String(o.id) === current) || null)
  }, [ops, current])

  if (error) return <ErrorState error={error} onRetry={load} />
  if (ops === null) return <Skeleton className="h-10 w-full" />
  if (ops.length === 0) {
    return (
      <EmptyState icon={Send} title="Nothing sent yet" body="Encrypt a file on the Send page first. Its result shows up here."
        action={<Link to="/send" className="inline-flex h-9 items-center gap-2 rounded-[6px] border border-line-strong bg-panel-2 px-3.5 text-sm text-fg hover:border-ok/60 hover:text-ok"><Send size={14} aria-hidden="true" /> Go to Send</Link>} />
    )
  }
  return (
    <Select label="Sent message" value={current} onChange={(e) => setParams({ op: e.target.value })}
      options={ops.map((o) => [String(o.id), `#${o.id} · ${o.details.filename} in ${o.details.cover}`])} />
  )
}
