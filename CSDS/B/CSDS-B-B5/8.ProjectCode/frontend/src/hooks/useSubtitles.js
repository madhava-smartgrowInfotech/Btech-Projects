import { useCallback, useEffect, useRef, useState } from 'react'
import api, { errorText } from '../api'

const RATE = 16000
const PARTIAL_EVERY_MS = 1200
const SILENCE_END_MS = 800
const MAX_UTTERANCE_S = 12

function toInt16(chunks) {
  const len = chunks.reduce((n, c) => n + c.length, 0)
  const out = new Int16Array(len)
  let o = 0
  for (const c of chunks) {
    for (let i = 0; i < c.length; i++) out[o + i] = Math.max(-1, Math.min(1, c[i])) * 0x7fff
    o += c.length
  }
  return out
}

/**
 * Microphone -> offline speech recognition on the server.
 * While someone speaks, the growing utterance is re-sent every ~1.2 s for a live partial
 * subtitle; after a short silence the utterance is finalised and passed to onFinal.
 */
export default function useSubtitles({ language = 'en', onFinal }) {
  const [listening, setListening] = useState(false)
  const [partial, setPartial] = useState('')
  const [level, setLevel] = useState(0)
  const [error, setError] = useState('')
  const [lastLatency, setLastLatency] = useState(null)
  const ctxRef = useRef(null)
  const streamRef = useRef(null)
  const st = useRef({ chunks: [], speaking: false, lastVoice: 0, lastPartial: 0, busy: false, noise: 0.01 })
  const onFinalRef = useRef(onFinal)
  const langRef = useRef(language)
  useEffect(() => { onFinalRef.current = onFinal }, [onFinal])
  useEffect(() => { langRef.current = language }, [language])

  const send = async (chunks, final) => {
    const pcm = toInt16(chunks)
    const t = performance.now()
    const res = await api.post(`/speech/transcribe?language=${langRef.current}`, pcm.buffer, {
      headers: { 'Content-Type': 'application/octet-stream' }, timeout: 60000,
    })
    setLastLatency(Math.round(performance.now() - t))
    return res.data
  }

  const finalise = async () => {
    const s = st.current
    const chunks = s.chunks
    s.chunks = []
    s.speaking = false
    try {
      s.busy = true
      const data = await send(chunks, true)
      setPartial('')
      if (data.text) onFinalRef.current?.(data.text, data)
      setError('')
    } catch (e) {
      setError(errorText(e))
    } finally {
      s.busy = false
    }
  }

  const onAudio = (samples) => {
    const s = st.current
    let sum = 0
    for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i]
    const rms = Math.sqrt(sum / samples.length)
    setLevel(Math.min(1, rms * 12))
    const now = performance.now()
    const voice = rms > Math.max(0.012, s.noise * 3)
    if (!voice && !s.speaking) s.noise = s.noise * 0.95 + rms * 0.05
    if (voice) { s.lastVoice = now; if (!s.speaking) { s.speaking = true; s.lastPartial = now } }
    if (s.speaking) {
      s.chunks.push(samples)
    } else {
      s.chunks = [...s.chunks.slice(-1), samples] // keep a little lead-in
      return
    }
    const seconds = s.chunks.reduce((n, c) => n + c.length, 0) / RATE
    if (!s.busy && (now - s.lastVoice > SILENCE_END_MS || seconds > MAX_UTTERANCE_S)) {
      finalise()
    } else if (!s.busy && now - s.lastPartial > PARTIAL_EVERY_MS) {
      s.lastPartial = now
      s.busy = true
      send(s.chunks, false)
        .then((d) => { if (st.current.speaking && d.text) setPartial(d.text) })
        .catch((e) => setError(errorText(e)))
        .finally(() => { s.busy = false })
    }
  }

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    ctxRef.current?.close().catch(() => {})
    ctxRef.current = null
    setListening(false)
    setLevel(0)
    if (st.current.speaking && st.current.chunks.length) finalise()
  }, [])

  const start = useCallback(async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })
      streamRef.current = stream
      const ctx = new AudioContext({ sampleRate: RATE })
      ctxRef.current = ctx
      const src = ctx.createMediaStreamSource(stream)
      const proc = ctx.createScriptProcessor(4096, 1, 1)
      proc.onaudioprocess = (e) => onAudio(new Float32Array(e.inputBuffer.getChannelData(0)))
      src.connect(proc)
      proc.connect(ctx.destination)
      st.current = { chunks: [], speaking: false, lastVoice: 0, lastPartial: 0, busy: false, noise: 0.01 }
      setListening(true)
    } catch (e) {
      setError(e?.name === 'NotAllowedError' ? 'Microphone permission was denied.' : errorText(e))
      stop()
    }
  }, [stop])

  useEffect(() => stop, [stop])

  return { listening, partial, level, error, lastLatency, start, stop }
}
