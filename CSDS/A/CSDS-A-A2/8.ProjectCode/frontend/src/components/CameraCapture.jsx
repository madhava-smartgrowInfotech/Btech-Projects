import { useCallback, useEffect, useRef, useState } from 'react'
import { Camera, CameraOff, RotateCcw } from 'lucide-react'
import { Button } from './ui'

/**
 * Webcam capture. Like Streamlit's camera widget the saved frame is selfie-mirrored when
 * `mirrored` is true (AM_CAMERA_MIRRORED), so the liveness maths sees the same orientation.
 */
export function CameraCapture({ label = 'Camera', mirrored = true, value, onCapture, disabled }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [state, setState] = useState('idle') // idle | starting | live | error
  const [error, setError] = useState('')
  const [preview, setPreview] = useState(null)

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
  }, [])

  useEffect(() => stop, [stop])

  useEffect(() => {
    if (!value) {
      setPreview(null)
      return undefined
    }
    const url = URL.createObjectURL(value)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [value])

  const start = async () => {
    setError('')
    if (!navigator.mediaDevices?.getUserMedia) {
      setState('error')
      setError('This browser cannot open the camera here. Camera access needs HTTPS or localhost — use “Upload photo” instead.')
      return
    }
    setState('starting')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      })
      streamRef.current = stream
      setState('live')
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play().catch(() => {})
        }
      })
    } catch (e) {
      setState('error')
      setError(
        e.name === 'NotAllowedError'
          ? 'Camera permission was blocked. Allow the camera in the browser address bar, then try again.'
          : e.name === 'NotFoundError'
            ? 'No camera was found on this device. Use “Upload photo” instead.'
            : `Could not start the camera (${e.name || 'error'}).`,
      )
    }
  }

  const capture = () => {
    const v = videoRef.current
    if (!v || !v.videoWidth) return
    const c = document.createElement('canvas')
    c.width = v.videoWidth
    c.height = v.videoHeight
    const ctx = c.getContext('2d')
    if (mirrored) {
      ctx.translate(c.width, 0)
      ctx.scale(-1, 1)
    }
    ctx.drawImage(v, 0, 0, c.width, c.height)
    c.toBlob(
      (blob) => {
        if (!blob) return
        stop()
        setState('idle')
        onCapture(new File([blob], 'capture.jpg', { type: 'image/jpeg' }))
      },
      'image/jpeg',
      0.92,
    )
  }

  const retake = () => {
    onCapture(null)
    start()
  }

  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="camera">
        {preview ? (
          <img src={preview} alt={`${label} — captured photo`} />
        ) : state === 'live' ? (
          <>
            <video ref={videoRef} className={mirrored ? 'mirror' : ''} playsInline muted aria-label={`${label} — live preview`} />
            <div className="camera-frame" aria-hidden="true" />
          </>
        ) : (
          <div className="camera-empty">
            <div className="stack" style={{ alignItems: 'center', '--gap': '8px' }}>
              {state === 'error' ? <CameraOff size={36} aria-hidden="true" /> : <Camera size={36} aria-hidden="true" />}
              <span className="small">{state === 'starting' ? 'Waiting for camera permission…' : state === 'error' ? error : 'Camera is off'}</span>
            </div>
          </div>
        )}
        <span className="camera-tag badge">{label}</span>
      </div>
      <div className="row">
        {preview ? (
          <Button icon={RotateCcw} onClick={retake} disabled={disabled}>
            Retake
          </Button>
        ) : state === 'live' ? (
          <Button variant="primary" icon={Camera} onClick={capture} disabled={disabled}>
            Take photo
          </Button>
        ) : (
          <Button icon={Camera} onClick={start} loading={state === 'starting'} disabled={disabled}>
            {state === 'error' ? 'Try camera again' : 'Start camera'}
          </Button>
        )}
      </div>
    </div>
  )
}
