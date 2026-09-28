import { useCallback, useEffect, useRef, useState } from 'react'
import api, { errorText } from '../api'

const HAND_EDGES = [
  [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [17, 18], [18, 19], [19, 20], [0, 17],
]
const MIN_INTERVAL_MS = 66 // at most ~15 frames per second

function drawHands(canvas, video, landmarks) {
  if (!canvas || !video) return
  const w = (canvas.width = video.clientWidth)
  const h = (canvas.height = video.clientHeight)
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, w, h)
  if (!landmarks) return
  for (const [key, color] of [['left', '#22d3ee'], ['right', '#a78bfa']]) {
    const pts = landmarks[key]
    if (!pts) continue
    ctx.strokeStyle = color
    ctx.lineWidth = 3
    for (const [a, b] of HAND_EDGES) {
      ctx.beginPath()
      ctx.moveTo(pts[a][0] * w, pts[a][1] * h)
      ctx.lineTo(pts[b][0] * w, pts[b][1] * h)
      ctx.stroke()
    }
    ctx.fillStyle = '#fff'
    for (const p of pts) {
      ctx.beginPath()
      ctx.arc(p[0] * w, p[1] * h, 3, 0, Math.PI * 2)
      ctx.fill()
    }
  }
}

/** Webcam -> backend recognition loop. onEvent is called for each sign / letter event. */
export default function useSignRecognizer({ mode = 'words', onEvent }) {
  const videoRef = useRef(null)
  const overlayRef = useRef(null)
  const streamRef = useRef(null)
  const runningRef = useRef(false)
  const modeRef = useRef(mode)
  const onEventRef = useRef(onEvent)
  const sessionRef = useRef(Math.random().toString(36).slice(2, 12))
  const [running, setRunning] = useState(false)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const [frame, setFrame] = useState(null) // last backend response
  const [rtt, setRtt] = useState(null)

  useEffect(() => { onEventRef.current = onEvent }, [onEvent])
  useEffect(() => {
    modeRef.current = mode
    api.post(`/recognize/reset?session=${sessionRef.current}`).catch(() => {})
  }, [mode])

  const loop = useCallback(async () => {
    const grab = document.createElement('canvas')
    let failures = 0
    while (runningRef.current) {
      const started = performance.now()
      const video = videoRef.current
      if (!video || video.readyState < 2) { await new Promise((r) => setTimeout(r, 100)); continue }
      const scale = 480 / video.videoWidth
      grab.width = 480
      grab.height = Math.round(video.videoHeight * scale)
      grab.getContext('2d').drawImage(video, 0, 0, grab.width, grab.height)
      const blob = await new Promise((r) => grab.toBlob(r, 'image/jpeg', 0.75))
      try {
        const res = await api.post(`/recognize/frame?session=${sessionRef.current}&mode=${modeRef.current}`, blob, {
          headers: { 'Content-Type': 'image/jpeg' }, timeout: 10000,
        })
        failures = 0
        setError('')
        setRtt(Math.round(performance.now() - started))
        setFrame(res.data)
        drawHands(overlayRef.current, video, res.data.landmarks)
        for (const ev of res.data.events) onEventRef.current?.(ev)
      } catch (e) {
        failures += 1
        setError(errorText(e))
        if (failures > 20) { runningRef.current = false; setRunning(false); break }
        await new Promise((r) => setTimeout(r, 500))
      }
      const wait = MIN_INTERVAL_MS - (performance.now() - started)
      if (wait > 0) await new Promise((r) => setTimeout(r, wait))
    }
  }, [])

  const stop = useCallback(() => {
    runningRef.current = false
    setRunning(false)
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    drawHands(overlayRef.current, videoRef.current, null)
    setFrame(null)
  }, [])

  const start = useCallback(async () => {
    setStarting(true)
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' }, audio: false })
      streamRef.current = stream
      videoRef.current.srcObject = stream
      await videoRef.current.play()
      await api.post(`/recognize/reset?session=${sessionRef.current}`)
      runningRef.current = true
      setRunning(true)
      loop()
    } catch (e) {
      setError(e?.name === 'NotAllowedError' ? 'Camera permission was denied. Allow camera access in the browser.' :
        e?.name === 'NotFoundError' ? 'No camera found on this device.' : errorText(e))
      stop()
    } finally {
      setStarting(false)
    }
  }, [loop, stop])

  useEffect(() => stop, [stop])

  return { videoRef, overlayRef, running, starting, error, frame, rtt, start, stop }
}
