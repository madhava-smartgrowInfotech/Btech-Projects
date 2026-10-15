import { useEffect, useRef, useState } from 'react'
import { Mic, Square } from 'lucide-react'
import api, { errorText } from '../../api'
import { fmtTime } from '../../lib/format'
import { Alert, Button, useToast } from '../ui'

/** Record from the microphone in the browser, then upload it as a call (source=microphone). */
export default function Recorder({ agentId, onDone }) {
  const toast = useToast()
  const [rec, setRec] = useState(null)
  const [secs, setSecs] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const chunks = useRef([])
  const timer = useRef(null)

  useEffect(() => () => clearInterval(timer.current), [])

  const start = async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      chunks.current = []
      mr.ondataavailable = (e) => e.data.size && chunks.current.push(e.data)
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        clearInterval(timer.current)
        const blob = new Blob(chunks.current, { type: mr.mimeType || 'audio/webm' })
        const ext = (mr.mimeType || '').includes('ogg') ? 'ogg' : 'webm'
        const fd = new FormData()
        fd.append('files', blob, `microphone-${new Date().toISOString().slice(0, 16).replace(':', '')}.${ext}`)
        fd.append('source', 'microphone')
        fd.append('title', `Microphone recording ${new Date().toLocaleString()}`)
        if (agentId) fd.append('agent_id', agentId)
        setBusy(true)
        try {
          await api.post('/calls', fd)
          toast.success('Recording uploaded and queued for analysis.')
          onDone?.()
        } catch (err) {
          setError(errorText(err))
        } finally {
          setBusy(false)
          setRec(null)
        }
      }
      mr.start(1000)
      setSecs(0)
      timer.current = setInterval(() => setSecs((s) => s + 1), 1000)
      setRec(mr)
    } catch (err) {
      setError(`Microphone unavailable: ${err.message}. Allow microphone access in the browser, or upload a file instead.`)
    }
  }

  return (
    <div className="stack" style={{ '--gap': '8px' }}>
      {!rec ? (
        <Button block icon={Mic} onClick={start} loading={busy}>
          {busy ? 'Uploading…' : 'Record from microphone'}
        </Button>
      ) : (
        <Button block variant="danger" icon={Square} onClick={() => rec.stop()}>
          Stop and analyse ({fmtTime(secs)})
        </Button>
      )}
      {error && <Alert tone="error">{error}</Alert>}
    </div>
  )
}
