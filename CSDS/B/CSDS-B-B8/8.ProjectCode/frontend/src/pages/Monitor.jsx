import { useEffect, useRef, useState } from 'react'
import { EyeOff, Moon, Play, Square, Video, Disc } from 'lucide-react'
import { Badge, Button, Card, CardHeader, ErrorState, Input, PageHeader, Select, Skeleton, useToast } from '../components/ui'
import { Stagger } from '../components/motion'
import ActivityBadge from '../components/care/ActivityBadge'
import ActivityTimeline from '../components/care/ActivityTimeline'
import SkeletonView from '../components/care/SkeletonView'
import { api, authedUrl } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { useFastMonitor } from '../lib/monitor'
import { ACTIVITY_COLORS, CLIP_LABELS, activityColor, duration, humanize } from '../lib/format'

const FALL = {
  normal: { text: 'No fall detected', cls: '' },
  possible_fall: { text: 'Possible fall - confirming…', cls: 'possible' },
  confirmed: { text: 'Fall confirmed', cls: 'confirmed' },
}

export default function Monitor() {
  const { state: st, error: connErr, refresh } = useFastMonitor()
  const toast = useToast()
  const settings = useAsync(() => api.get('/settings'), [])
  const daily = useAsync(() => api.get('/reports/daily'), [], { poll: 5000 })
  const [source, setSource] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [clip, setClip] = useState({ label: 'walking', seconds: 5 })
  const [tick, setTick] = useState(0)
  const [frameOk, setFrameOk] = useState(true)
  const [videoReady, setVideoReady] = useState(false)
  const seeded = useRef(false)

  useEffect(() => {
    if (settings.data && !seeded.current) {
      seeded.current = true
      setSource(settings.data.camera_source)
    }
  }, [settings.data])

  const privacy = settings.data?.privacy_mode !== false
  const running = !!st?.running

  // the backend only keeps JPEG frames once privacy mode is off, which it re-reads every 2 s, so wait before asking
  useEffect(() => {
    if (privacy || !running) {
      setVideoReady(false)
      return undefined
    }
    const wait = setTimeout(() => setVideoReady(true), 2800)
    const id = setInterval(() => setTick((t) => t + 1), 250)
    return () => {
      clearTimeout(wait)
      clearInterval(id)
    }
  }, [privacy, running])

  const act = async (name, fn, okMsg) => {
    setBusy(name)
    setError('')
    try {
      await fn()
      if (okMsg) toast({ title: okMsg })
      await refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy('')
    }
  }
  const start = () => act('start', () => api.post('/monitor/start', { source }), 'Monitoring started')
  const stop = () => act('stop', () => api.post('/monitor/stop'), 'Monitoring stopped')
  const togglePrivacy = async () => {
    try {
      await api.put('/settings', { privacy_mode: !privacy })
      await settings.reload({ quiet: true })
      toast({ title: privacy ? 'Video view on' : 'Privacy mode on', message: privacy ? 'Frames are shown live and never stored.' : 'Only the skeleton is shown.', tone: 'info' })
    } catch (e) {
      setError(e.message)
    }
  }
  const record = () =>
    act('record', () => api.post('/monitor/record', clip), `Recording "${humanize(clip.label)}" keypoints for ${clip.seconds}s`)

  if (!st && !connErr) {
    return (
      <div aria-busy="true" aria-label="Connecting to the monitor">
        <PageHeader title="Live monitor" description="Connecting…" />
        <div className="split">
          <Skeleton height={420} />
          <div className="stack">
            <Skeleton height={190} />
            <Skeleton height={110} />
          </div>
        </div>
      </div>
    )
  }
  if (!st && connErr) {
    return (
      <>
        <PageHeader title="Live monitor" />
        <ErrorState title="Can't reach the CareWatch server" error={connErr} onRetry={refresh}>
          <p className="faint">Start it with run.bat, then try again.</p>
        </ErrorState>
      </>
    )
  }

  const now = new Date()
  const from = new Date(now.getTime() - 30 * 60 * 1000)
  const segments = [...(daily.data?.timeline || [])]
  if (st.segment) segments.push({ activity: st.segment.activity, start: st.segment.start, end: now.toISOString() })
  const fall = running ? FALL[st.fall_state] || FALL.normal : { text: 'Not monitoring', cls: 'idle' }
  const probs = running ? Object.entries(st.probs || {}).sort((a, b) => b[1] - a[1]) : []
  const actLabel = st.activity === 'no_person' ? 'Nobody in view' : humanize(st.activity)
  const room = settings.data?.room_name

  return (
    <div>
      <PageHeader
        title="Live monitor"
        description={room ? `${room} - continuous monitoring. It keeps running while the browser is closed.` : 'Continuous monitoring.'}
        actions={
          running ? (
            <Button variant="danger" icon={Square} loading={busy === 'stop'} onClick={stop}>
              Stop
            </Button>
          ) : (
            <Button variant="primary" icon={Play} loading={busy === 'start'} onClick={start}>
              {busy === 'start' ? 'Loading pose model…' : 'Start monitoring'}
            </Button>
          )
        }
      />

      <div className="stack" style={{ marginBottom: 18 }}>
        {connErr && (
          <div className="notice danger" role="alert">
            <span>Connection problem: {connErr.message} Showing the last known state.</span>
          </div>
        )}
        {(error || st.error) && (
          <div className="notice danger" role="alert">
            <span>
              {error || st.error} {!running && 'Check the camera source and try again.'}
            </span>
          </div>
        )}
        {!running && (
          <Card pad>
            <Input
              label="Camera source"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="0 or http://192.168.1.20:8080/video"
              hint={'0 = this computer\'s webcam. For a phone, install IP Webcam, tap "Start server" and enter its address followed by /video. For a demo, use the full path of data\\sample\\demo_fall.mp4.'}
              mono
            />
            {st.ended && <p className="faint" style={{ marginTop: 10 }}>The video source finished. Start again to replay it.</p>}
          </Card>
        )}
      </div>

      <Stagger className="split" gap={0.08}>
        <Card pad>
          <div className="view-bar">
            <Badge tone={running ? 'safe' : 'neutral'} dot>
              {running ? `Live · ${st.fps} fps` : 'Stopped'}
            </Badge>
            {running && st.enhanced && (
              <Badge tone="info">
                <Moon size={12} aria-hidden="true" /> Low-light enhancement on
              </Badge>
            )}
            {running && <span className="faint">Brightness {st.brightness}</span>}
            <Button size="sm" variant="ghost" className="push" icon={privacy ? EyeOff : Video} onClick={togglePrivacy}>
              {privacy ? 'Privacy mode: skeleton only' : 'Video view (not stored)'}
            </Button>
          </div>
          {privacy || !running || !videoReady ? (
            <SkeletonView
              keypoints={st.keypoints}
              width={st.frame_w || 640}
              height={st.frame_h || 480}
              color={st.fall_state === 'normal' || !running ? '#34d399' : '#f87171'}
              label={running ? `Live skeleton: ${actLabel}` : 'Monitoring is stopped'}
            />
          ) : (
            <img
              alt={`Live camera view: ${actLabel}`}
              className="live-frame"
              src={authedUrl('/monitor/frame.jpg', `&t=${tick}`)}
              style={{ opacity: frameOk ? 1 : 0.3 }}
              onError={() => setFrameOk(false)}
              onLoad={() => setFrameOk(true)}
            />
          )}
          {running && !st.person && <p className="faint" style={{ marginTop: 10 }}>Nobody in view.</p>}
          {!running && (
            <p className="faint" style={{ marginTop: 10 }}>
              Press <strong>Start monitoring</strong> to begin. Only a skeleton is ever shown in privacy mode.
            </p>
          )}
        </Card>

        <div className="stack">
          <Card pad>
            <div className="eyebrow-label">Current activity</div>
            <div className="act-now" style={{ color: running ? activityColor(st.activity) : 'var(--text-2)' }} aria-live="polite">
              {running ? actLabel : 'Not monitoring'}
            </div>
            {running && st.confidence > 0 && <div className="faint">{Math.round(st.confidence * 100)}% confidence</div>}
            {probs.length > 0 && (
              <div className="prob-list" aria-label="Activity probabilities">
                {probs.map(([k, v]) => (
                  <div className="prob-row" key={k}>
                    <span>{humanize(k)}</span>
                    <span className="bar">
                      <i style={{ width: `${v * 100}%`, background: ACTIVITY_COLORS[k] || 'var(--accent)' }} />
                    </span>
                    <span className="val">{Math.round(v * 100)}%</span>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card pad className={`fall-card ${fall.cls}`}>
            <div className="eyebrow-label">Fall detection</div>
            <div className="big-line" aria-live="polite">
              {fall.text}
            </div>
            {running && <div className="faint" style={{ marginTop: 6 }}>Still for {duration(st.inactive_seconds)}</div>}
          </Card>

          <Card>
            <CardHeader title="Record a training clip" subtitle="Saves keypoints only (no video) to improve the model. Record with the person's consent." />
            <div className="card-body stack" style={{ gap: 12 }}>
              <div className="form-grid">
                <Select
                  label="Activity"
                  value={clip.label}
                  onChange={(e) => setClip({ ...clip, label: e.target.value })}
                  options={CLIP_LABELS.map((l) => ({ value: l, label: humanize(l) }))}
                />
                <Input
                  label="Seconds (2-30)"
                  type="number"
                  min={2}
                  max={30}
                  value={clip.seconds}
                  onChange={(e) => setClip({ ...clip, seconds: Number(e.target.value) })}
                />
              </div>
              <Button icon={Disc} onClick={record} loading={busy === 'record'} disabled={!running || !!st.recording}>
                {st.recording ? `Recording ${humanize(st.recording.label)} - ${Math.ceil(st.recording.left)}s` : 'Record clip'}
              </Button>
              {!running && <p className="faint">Start monitoring to record a clip.</p>}
              {!st.recording && st.last_clip && <p className="faint">Saved: {st.last_clip}</p>}
            </div>
          </Card>
        </div>
      </Stagger>

      <Card className="mt">
        <CardHeader
          title="Activity timeline - last 30 minutes"
          actions={st.segment && <ActivityBadge activity={st.segment.activity} />}
        />
        <div className="card-body">
          {daily.loading && !daily.data ? (
            <Skeleton height={70} />
          ) : daily.error && !daily.data ? (
            <ErrorState title="Couldn't load the timeline" error={daily.error} onRetry={daily.reload} />
          ) : (
            <ActivityTimeline segments={segments} from={from} to={now} />
          )}
        </div>
      </Card>
    </div>
  )
}
