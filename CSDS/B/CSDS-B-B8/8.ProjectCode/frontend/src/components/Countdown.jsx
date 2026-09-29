import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import api, { errMsg } from '../api.js'

// Global 'I'm OK' countdown - shown on every screen while a fall alert is pending.
export default function Countdown() {
  const [alert, setAlert] = useState(null)
  const [left, setLeft] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const lastId = useRef(null)

  useEffect(() => {
    let alive = true
    const poll = async () => {
      try {
        const { data } = await api.get('/monitor/state')
        if (!alive) return
        if (data.alert) {
          setAlert(data.alert)
          setLeft(data.alert.seconds_left)
          lastId.current = data.alert.id
        } else if (lastId.current) {
          const id = lastId.current
          lastId.current = null
          setAlert(null)
          const { data: list } = await api.get('/alerts', { params: { limit: 10 } })
          const a = list.find((x) => x.id === id)
          if (a && a.status !== 'cancelled') setNotice(`Alert #${id} ${a.status === 'sent' ? 'was sent to your contacts' : 'status: ' + a.status}`)
        }
      } catch { /* the monitor page shows connection errors */ }
    }
    poll()
    const id = setInterval(poll, 1000)
    return () => { alive = false; clearInterval(id) }
  }, [])

  useEffect(() => {
    if (!alert) return
    const id = setInterval(() => setLeft((l) => Math.max(0, l - 0.2)), 200)
    return () => clearInterval(id)
  }, [alert])

  const ok = async () => {
    setBusy(true)
    setError('')
    try {
      await api.post(`/alerts/${alert.id}/ok`)
      lastId.current = null
      setAlert(null)
      setNotice("Thanks - alert cancelled. Glad you're OK.")
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy(false)
    }
  }

  if (!alert) {
    return notice ? (
      <div className="fixed bottom-4 right-4 z-40 card px-4 py-3 text-sm flex items-center gap-3">
        {notice}
        <button className="text-teal-700 underline" onClick={() => setNotice('')}>Dismiss</button>
      </div>
    ) : null
  }
  return (
    <div className="fixed inset-0 z-50 bg-red-900/70 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center">
        <AlertTriangle className="w-14 h-14 text-red-600 mx-auto" />
        <h2 className="text-2xl font-bold text-slate-900 mt-3">Possible fall detected</h2>
        <p className="text-slate-600 mt-2">Emergency alerts go to your contacts in</p>
        <div className="text-7xl font-bold text-red-600 my-4 tabular-nums">{Math.ceil(left)}</div>
        <button onClick={ok} disabled={busy} className="btn btn-primary w-full text-xl py-4">
          {busy ? <Loader2 className="w-5 h-5 animate-spin" /> : null} I'm OK
        </button>
        {error && <p className="text-sm text-red-600 mt-3">{error}</p>}
      </div>
    </div>
  )
}
