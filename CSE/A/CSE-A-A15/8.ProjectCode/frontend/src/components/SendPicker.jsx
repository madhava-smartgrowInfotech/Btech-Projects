import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api, { errText } from '../api'
import { ErrorBox, Spinner } from './ui'

/** Dropdown of the user's successful send operations; selection is mirrored to ?op= in the URL. */
export default function SendPicker({ onChange }) {
  const [params, setParams] = useSearchParams()
  const [ops, setOps] = useState(null)
  const [error, setError] = useState('')
  const current = params.get('op') || ''

  useEffect(() => {
    api.get('/log', { params: { op: 'send', limit: 100 } })
      .then((r) => {
        const ok = r.data.filter((x) => x.ok)
        setOps(ok)
        if (!current && ok[0]) setParams({ op: String(ok[0].id) }, { replace: true })
      })
      .catch((e) => setError(errText(e)))
  }, [])

  useEffect(() => {
    if (ops && current) onChange(ops.find((o) => String(o.id) === current) || null)
  }, [ops, current])

  if (error) return <ErrorBox>{error}</ErrorBox>
  if (ops === null) return <Spinner text="Loading sent messages..." />
  if (ops.length === 0) return <p className="text-sm text-slate-500">Nothing sent yet. Use the Send page first.</p>
  return (
    <div className="max-w-xl">
      <label className="label" htmlFor="op">Sent message</label>
      <select id="op" className="input" value={current} onChange={(e) => setParams({ op: e.target.value })}>
        {ops.map((o) => <option key={o.id} value={o.id}>#{o.id} - {o.details.filename} in {o.details.cover}</option>)}
      </select>
    </div>
  )
}
