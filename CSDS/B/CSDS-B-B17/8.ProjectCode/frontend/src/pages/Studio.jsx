import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FlaskConical, Plus } from 'lucide-react'
import api, { errorText } from '../api'
import { useAuth } from '../lib/auth'
import { label } from '../lib/format'
import { Alert, Button, Card, EmptyState, ErrorState, Input, PageHeader, Select, SkeletonBlock, Textarea, useToast } from '../components/ui'

const BLANK = { id: '', title: 'Custom sample call', text: 'Agent: Thank you for calling, my name is Alex. How can I help?\nCustomer [negative]: ' }

export default function Studio() {
  const nav = useNavigate()
  const toast = useToast()
  const { user } = useAuth()
  const sup = user?.role === 'supervisor'
  const [scripts, setScripts] = useState(null)
  const [agents, setAgents] = useState([])
  const [scriptId, setScriptId] = useState('')
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [agentId, setAgentId] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [loadError, setLoadError] = useState('')

  const pick = useCallback(
    (s, agentList) => {
      setScriptId(s?.id || '')
      setText(s?.text || '')
      setTitle(s?.title || '')
      const a = agentList.find((x) => x.email === s?.agent)
      if (a && sup) setAgentId(String(a.id))
    },
    [sup],
  )

  const load = useCallback(async () => {
    setLoadError('')
    try {
      const [s, a] = await Promise.all([api.get('/studio/scripts'), api.get('/agents')])
      setScripts(s.data)
      setAgents(a.data)
      if (s.data.length) pick(s.data[0], a.data)
      else pick(BLANK, a.data)
    } catch (err) {
      setLoadError(errorText(err))
    }
  }, [pick])

  useEffect(() => {
    load()
  }, [load])

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
      toast.success('Sample call created — analysis has started.')
      nav(`/calls/${data.id}`)
    } catch (err) {
      setError(errorText(err))
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Offline voices · two channels"
        title="Sample studio"
        description="Turn a script into a realistic two-voice call (agent on the left channel, customer on the right), then run it through the full pipeline. Every call made here is labelled Sample."
      />
      {loadError ? (
        <ErrorState title="Could not load the scripts" error={loadError} onRetry={load} />
      ) : !scripts ? (
        <SkeletonBlock rows={7} label="Loading scripts" />
      ) : (
        <div className="split wide-aside">
          <Card title="Script and settings">
            <div className="stack">
              <div className="grid grid-2">
                <Input label="Call title" value={title} onChange={(e) => setTitle(e.target.value)} />
                {sup && (
                  <Select label="Agent" value={agentId} onChange={(e) => setAgentId(e.target.value)}>
                    <option value="">Unassigned</option>
                    {agents.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name}
                      </option>
                    ))}
                  </Select>
                )}
              </div>
              <Textarea
                label="Script"
                className="script-area"
                rows={14}
                value={text}
                onChange={(e) => setText(e.target.value)}
                hint="One line per turn: “Agent: …” or “Customer [negative|neutral|positive]: …”. The tone tag sets the customer's speaking rate and is kept as ground truth for evaluation; the pipeline never sees it."
              />
              {error && <Alert tone="error">{error}</Alert>}
              <div>
                <Button variant="primary" size="lg" icon={FlaskConical} onClick={generate} loading={busy} disabled={!text.trim()}>
                  {busy ? 'Synthesising voices…' : 'Generate sample call and analyse'}
                </Button>
              </div>
            </div>
          </Card>

          <Card title="Scripts" aria-label="Scripts">
            {scripts.length === 0 ? (
              <EmptyState title="No bundled scripts">Write your own script to generate a call.</EmptyState>
            ) : null}
            <div className="stack" style={{ '--gap': '6px' }}>
              {scripts.map((s) => (
                <button key={s.id} className="script-btn" aria-pressed={scriptId === s.id} onClick={() => pick(s, agents)}>
                  <strong style={{ display: 'block' }}>{s.title}</strong>
                  <span className="tiny mono" style={{ textTransform: 'uppercase' }}>
                    {label(s.intent)}
                  </span>
                </button>
              ))}
              <button className="script-btn dashed" aria-pressed={scriptId === '' && title === BLANK.title} onClick={() => pick(BLANK, agents)}>
                <strong className="row" style={{ '--gap': '6px' }}>
                  <Plus size={16} aria-hidden="true" /> Write your own
                </strong>
              </button>
            </div>
          </Card>
        </div>
      )}
    </>
  )
}
