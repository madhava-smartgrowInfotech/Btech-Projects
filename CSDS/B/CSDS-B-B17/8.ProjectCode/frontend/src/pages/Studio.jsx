import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FlaskConical, Loader2 } from 'lucide-react'
import api, { currentUser, errorText, label } from '../api.js'
import { ErrorBox, Spinner } from '../components/ui.jsx'

export default function Studio() {
  const nav = useNavigate()
  const user = currentUser()
  const [scripts, setScripts] = useState(null)
  const [agents, setAgents] = useState([])
  const [scriptId, setScriptId] = useState('')
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [agentId, setAgentId] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [loadError, setLoadError] = useState('')

  const load = async () => {
    setLoadError('')
    try {
      const [s, a] = await Promise.all([api.get('/studio/scripts'), api.get('/agents')])
      setScripts(s.data)
      setAgents(a.data)
      if (s.data.length) pick(s.data[0], a.data)
    } catch (err) {
      setLoadError(errorText(err))
    }
  }
  useEffect(() => {
    load()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const pick = (s, agentList = agents) => {
    setScriptId(s?.id || '')
    setText(s?.text || '')
    setTitle(s?.title || '')
    const a = agentList.find((x) => x.email === s?.agent)
    if (a && user.role === 'supervisor') setAgentId(String(a.id))
  }

  const generate = async () => {
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/studio/generate', {
        script_id: scriptId || null,
        script_text: text,
        title: title || null,
        agent_id: agentId ? Number(agentId) : null,
      })
      nav(`/calls/${data.id}`)
    } catch (err) {
      setError(errorText(err))
      setBusy(false)
    }
  }

  if (loadError) return <ErrorBox error={loadError} onRetry={load} />
  if (!scripts) return <Spinner />
  return (
    <div className="space-y-4">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <FlaskConical className="h-6 w-6 text-indigo-700" /> Sample call studio
        </h1>
        <p className="text-sm text-slate-500">
          Turn a script into a realistic two-voice call recording (offline voices: agent on the left channel, customer on the right),
          then run it through the full pipeline. Every call made here is labelled <b>Sample</b>.
        </p>
      </div>
      <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
        <div className="card p-3">
          <h2 className="h2 px-2">Scripts</h2>
          <div className="space-y-1">
            {scripts.map((s) => (
              <button
                key={s.id}
                onClick={() => pick(s)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm ${scriptId === s.id ? 'bg-indigo-50 text-indigo-900' : 'hover:bg-slate-50'}`}
              >
                <div className="font-medium">{s.title}</div>
                <div className="text-xs text-slate-500">{label(s.intent)}</div>
              </button>
            ))}
            <button
              onClick={() => pick({ id: '', title: 'Custom sample call', text: 'Agent: Thank you for calling, my name is Alex. How can I help?\nCustomer [negative]: ' })}
              className={`w-full rounded-lg border border-dashed border-slate-300 px-3 py-2 text-left text-sm ${scriptId === '' ? 'bg-indigo-50' : 'hover:bg-slate-50'}`}
            >
              + Write your own
            </button>
          </div>
        </div>
        <div className="card space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="title">Call title</label>
              <input id="title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            {user.role === 'supervisor' && (
              <div>
                <label className="label" htmlFor="agent">Agent</label>
                <select id="agent" className="input" value={agentId} onChange={(e) => setAgentId(e.target.value)}>
                  <option value="">Unassigned</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <div>
            <label className="label" htmlFor="script">
              Script - one line per turn: <code>Agent: ...</code> or <code>Customer [negative|neutral|positive]: ...</code>
            </label>
            <textarea
              id="script"
              className="input h-80 font-mono text-xs leading-relaxed"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <p className="mt-1 text-xs text-slate-500">
              The tone tag sets the customer&apos;s speaking rate and is kept as ground truth for evaluation; the pipeline never sees it.
            </p>
          </div>
          <ErrorBox error={error} />
          <button className="btn-primary" onClick={generate} disabled={busy || !text.trim()}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
            {busy ? 'Synthesising voices...' : 'Generate sample call and analyse'}
          </button>
        </div>
      </div>
    </div>
  )
}
