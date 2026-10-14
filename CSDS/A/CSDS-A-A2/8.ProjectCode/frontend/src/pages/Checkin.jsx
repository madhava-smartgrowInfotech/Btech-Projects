import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, Crosshair, LogOut, RotateCcw, ScanFace, ShieldCheck, UserPlus, LogIn } from 'lucide-react'
import {
  Alert,
  Badge,
  Button,
  Card,
  Container,
  ErrorState,
  KeyValueList,
  ProgressBar,
  SkeletonBlock,
  StatCard,
  StatusBadge,
  Stepper,
  Tabs,
  useToast,
} from '../components/ui'
import { MaskHeadline, PageTransition } from '../components/motion'
import { LoginForm, RegisterForm } from '../components/AuthForms'
import { FacePhotoInput } from '../components/FacePhotoInput'
import { LocationPicker } from '../components/LocationPicker'
import { LazyMap } from '../components/LazyMap'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useConfig } from '../lib/config'
import { useApi } from '../lib/useApi'
import { fmtNum } from '../lib/format'
import { useReducedMotion } from '../lib/motion'

const STEPS = ['Sign in', 'Eligibility', 'Location', 'Live challenge', 'Face match', 'Done']
const NOT_LIVE = {
  upcoming: 'This session has not started yet.',
  expired: 'This session has expired.',
  closed: 'This session has been closed by the faculty.',
}

function SessionHeader({ s }) {
  return (
    <Card tone="lime" style={{ marginBottom: 20 }}>
      <div className="row-between">
        <div style={{ minWidth: 0 }}>
          <span className="eyebrow">Attendance session</span>
          <h1 className="display-md" style={{ marginTop: 10, overflowWrap: 'anywhere' }}>
            {s.course_code} · {s.course_name}
          </h1>
        </div>
        <StatusBadge status={s.status} />
      </div>
      <p className="mono small" style={{ marginTop: 14 }}>
        {s.section && `${s.section} · `}
        {s.starts_local} → {s.ends_local} · faculty: {s.faculty_name}
      </p>
    </Card>
  )
}

function Burst() {
  const reduced = useReducedMotion()
  if (reduced) return null
  const colors = ['#C8FF2E', '#FF5C39', '#7CC6FF', '#FFD23F']
  return (
    <div className="burst" aria-hidden="true">
      {Array.from({ length: 22 }, (_, i) => {
        const angle = (i / 22) * Math.PI * 2
        const dist = 160 + (i % 5) * 40
        return (
          <motion.span
            key={i}
            style={{ left: '50%', top: '40%', background: colors[i % 4] }}
            initial={{ x: 0, y: 0, rotate: 0, opacity: 1 }}
            animate={{ x: Math.cos(angle) * dist, y: Math.sin(angle) * dist, rotate: 180 + i * 20, opacity: 0 }}
            transition={{ duration: 1.3, ease: [0.2, 0.9, 0.1, 1] }}
          />
        )
      })}
    </div>
  )
}

export default function Checkin() {
  const { token } = useParams()
  const t = encodeURIComponent(token)
  const toast = useToast()
  const { user, meta, logout } = useAuth()
  const { config } = useConfig()
  const session = useApi(`/api/public/sessions/${t}`)
  const s = session.data
  const isStudent = user?.role === 'student'

  const [ck, setCk] = useState(null)
  const [ckError, setCkError] = useState(null)
  const [elig, setElig] = useState(null)
  const [busy, setBusy] = useState('')
  const [authTab, setAuthTab] = useState('signin')
  const [registered, setRegistered] = useState('')
  // step 2
  const [loc, setLoc] = useState(null)
  const [geo, setGeo] = useState(null)
  // step 3
  const [neutral, setNeutral] = useState(null)
  const [neutralNote, setNeutralNote] = useState(null)
  const [chal, setChal] = useState(null)
  const [live, setLive] = useState(null)
  // step 4
  const [face, setFace] = useState(null)
  const guard = useRef({})

  const run = useCallback(async (key, fn) => {
    if (guard.current[key]) return undefined
    guard.current[key] = true
    setBusy(key)
    try {
      return await fn()
    } finally {
      guard.current[key] = false
      setBusy('')
    }
  }, [])

  const start = useCallback(
    () =>
      run('start', async () => {
        try {
          const d = await api(`/api/checkin/${t}/start`, { method: 'POST' })
          setElig(d)
          setCk(d.state)
          if (d.ok) toast.success('Session is live, your roll number is allowed and this device is registered to you.')
        } catch (e) {
          setElig({ ok: false, reason: e.message })
        }
      }),
    [run, t, toast],
  )

  const loadState = useCallback(
    () =>
      run('state', async () => {
        try {
          const st = await api(`/api/checkin/${t}/state`)
          setCk(st)
          setCkError(null)
          return st
        } catch (e) {
          setCkError(e)
          return null
        }
      }),
    [run, t],
  )

  // Once a student is signed in, fetch the wizard state; step 1 runs the eligibility check straight away.
  const userId = user?.id
  useEffect(() => {
    if (!isStudent || !s) return
    setCk(null)
    setElig(null)
    loadState().then((st) => {
      if (st && st.step === 1) start()
    })
  }, [isStudent, userId, s?.token]) // eslint-disable-line react-hooks/exhaustive-deps

  const verifyLocation = () =>
    run('location', async () => {
      try {
        const d = await api(`/api/checkin/${t}/location`, { method: 'POST', body: loc })
        setGeo(d)
        setCk(d.state)
        if (d.inside) toast.success(d.reason)
      } catch (e) {
        setGeo({ inside: false, reason: e.message })
      }
    })

  const checkNeutral = async (file) => {
    setNeutral(file)
    setNeutralNote(null)
    if (!file) return
    const form = new FormData()
    form.append('image', file, 'neutral.jpg')
    try {
      const d = await api(`/api/checkin/${t}/neutral`, { method: 'POST', form })
      setNeutralNote(d)
    } catch (e) {
      setNeutralNote({ ok: false, message: e.message })
    }
  }

  const verifyChallenge = () =>
    run('liveness', async () => {
      const form = new FormData()
      form.append('neutral', neutral, 'neutral.jpg')
      form.append('challenge', chal, 'challenge.jpg')
      try {
        const d = await api(`/api/checkin/${t}/liveness`, { method: 'POST', form })
        setLive(d)
        setCk(d.state)
        if (!d.passed) {
          setNeutral(null)
          setNeutralNote(null)
          setChal(null)
        }
      } catch (e) {
        setLive({ passed: false, reason: e.message })
      }
    })

  const runFace = useCallback(
    () =>
      run('face', async () => {
        try {
          const d = await api(`/api/checkin/${t}/face`, { method: 'POST' })
          setFace(d)
          setCk(d.state)
        } catch (e) {
          setFace({ passed: false, reason: e.message, retake: false })
        }
      }),
    [run, t],
  )

  useEffect(() => {
    if (ck?.step === 4 && !face) runFace()
  }, [ck?.step]) // eslint-disable-line react-hooks/exhaustive-deps

  const retake = () =>
    run('retake', async () => {
      const d = await api(`/api/checkin/${t}/retake`, { method: 'POST' })
      setFace(null)
      setLive(null)
      setNeutral(null)
      setChal(null)
      setCk(d.state)
    })

  const startOver = () =>
    run('reset', async () => {
      const d = await api(`/api/checkin/${t}/reset`, { method: 'POST' })
      setFace(null)
      setLive(null)
      setGeo(null)
      setLoc(null)
      setNeutral(null)
      setNeutralNote(null)
      setChal(null)
      setElig(null)
      setCk(d.state)
      if (d.state.step === 1) {
        guard.current.start = false
        start()
      }
    })

  /* ------------------------------------------------------------- render */
  if (session.loading) {
    return (
      <Container style={{ padding: '40px 16px' }}>
        <SkeletonBlock rows={6} label="Loading session" />
      </Container>
    )
  }
  if (session.error) {
    return (
      <Container style={{ padding: '40px 16px 80px' }}>
        <ErrorState
          title={session.error.status === 404 ? 'Invalid session link' : 'Could not open the session'}
          error={session.error}
          hint={session.error.status === 404 ? 'Check the link with your faculty, or paste it again on the student portal.' : undefined}
          onRetry={session.error.status === 404 ? undefined : session.reload}
        />
        <div className="row" style={{ justifyContent: 'center', marginTop: 20 }}>
          <Button to="/checkin">Paste a different link</Button>
        </div>
      </Container>
    )
  }

  const stepIndex = !isStudent ? 0 : ck ? (ck.step === 99 ? 3 : ck.step) : 1
  const failedIndex = ck?.step === 99 ? 3 : undefined

  let body
  if (!user) {
    body = (
      <Card>
        <Tabs
          label="Sign in or register"
          value={authTab}
          onChange={setAuthTab}
          tabs={[
            { id: 'signin', label: 'Sign in', icon: LogIn },
            { id: 'register', label: 'New student? Register', icon: UserPlus },
          ]}
        />
        {authTab === 'signin' ? (
          <LoginForm role="student" defaultUsername={registered} key={registered} />
        ) : (
          <RegisterForm
            role="student"
            onRegistered={(u) => {
              setRegistered(u.roll_number || u.username)
              setAuthTab('signin')
            }}
          />
        )}
      </Card>
    )
  } else if (!isStudent) {
    body = (
      <>
        <ErrorState title="Students only" error="Faculty accounts cannot mark attendance. Sign out and use a student account." />
        <div className="row" style={{ justifyContent: 'center', marginTop: 16 }}>
          <Button icon={LogOut} onClick={logout}>
            Sign out
          </Button>
        </div>
      </>
    )
  } else if (ckError) {
    body = <ErrorState title="Could not load your check-in" error={ckError} onRetry={loadState} />
  } else if (!ck || (ck.step === 1 && !elig) || busy === 'start') {
    body = (
      <Card>
        <SkeletonBlock rows={3} label="Checking eligibility" />
        <p className="small muted" style={{ marginTop: 12 }}>
          Checking the session window, your roll number and this device…
        </p>
      </Card>
    )
  } else if (ck.step === 1) {
    body = (
      <Card title="Step 1 · Eligibility">
        <Alert tone="error">🚫 {elig?.reason}</Alert>
        <div className="row" style={{ marginTop: 16 }}>
          <Button
            icon={RotateCcw}
            onClick={() => {
              setElig(null)
              start()
            }}
          >
            Check again
          </Button>
        </div>
      </Card>
    )
  } else if (ck.step === 2) {
    body = (
      <Card title="Step 2 · Verify you are in the classroom">
        <div className="grid grid-2" style={{ alignItems: 'start' }}>
          <LocationPicker
            value={loc}
            onChange={(v) => {
              setLoc(v)
              setGeo(null)
            }}
            allowManual={config?.allow_manual_location}
            defaultLat={s.latitude}
            defaultLon={s.longitude}
          />
          <LazyMap
            center={{ lat: s.latitude, lon: s.longitude }}
            radius={s.radius_m}
            tolerance={config?.geofence_tolerance_m || 0}
            points={loc ? [{ lat: loc.lat, lon: loc.lon, label: 'You', color: '#7CC6FF' }] : []}
            label="Session geo-fence and your position"
          />
        </div>
        {geo && !geo.inside && (
          <div style={{ marginTop: 16 }}>
            <Alert tone="error">🚫 {geo.reason}</Alert>
          </div>
        )}
        <div className="row" style={{ marginTop: 20 }}>
          <Button variant="primary" size="lg" icon={Crosshair} disabled={!loc} loading={busy === 'location'} onClick={verifyLocation}>
            Verify my location
          </Button>
        </div>
      </Card>
    )
  } else if (ck.step === 3) {
    const mirrored = config?.camera_mirrored ?? true
    body = (
      <Card title="Step 3 · Live facial challenge" actions={<Badge tone={ck.tries_left > 1 ? 'info' : 'blocked'}>{ck.tries_left} tries left</Badge>}>
        <div className="card card-flat card-lime challenge-card" style={{ marginBottom: 20 }}>
          <span className="challenge-emoji" aria-hidden="true">
            {ck.challenge_emoji}
          </span>
          <div>
            <p className="mono tiny">YOUR RANDOM CHALLENGE</p>
            <p className="display-sm" style={{ marginTop: 6 }}>
              {ck.challenge_text}
            </p>
            <p className="small" style={{ marginTop: 8 }}>
              Photo 1: <strong>look straight</strong> at the camera, mouth closed. Photo 2: {ck.challenge_emoji} <strong>{ck.challenge_text}</strong> —
              then take the photo while holding the pose.
            </p>
          </div>
        </div>
        {live && !live.passed && (
          <div className="stack" style={{ '--gap': '8px', marginBottom: 16 }}>
            <Alert tone="error">🚫 Challenge failed — {live.reason}</Alert>
            {live.message && <Alert tone="warning">{live.message}</Alert>}
          </div>
        )}
        <div className="grid grid-2" style={{ alignItems: 'start' }}>
          <div className="stack" style={{ '--gap': '10px' }}>
            <span className="field-label">Photo 1 — neutral</span>
            <FacePhotoInput key={`n-${ck.challenge}-${ck.tries_left}`} label="Photo 1 — neutral" value={neutral} onChange={checkNeutral} mirrored={mirrored} />
            {neutralNote && <Alert tone={neutralNote.ok ? 'success' : 'warning'}>{neutralNote.message}</Alert>}
          </div>
          <div className="stack" style={{ '--gap': '10px' }}>
            <span className="field-label">Photo 2 — {ck.challenge_text}</span>
            <FacePhotoInput key={`c-${ck.challenge}-${ck.tries_left}`} label={`Photo 2 — challenge`} value={chal} onChange={setChal} mirrored={mirrored} />
          </div>
        </div>
        <div className="row" style={{ marginTop: 20 }}>
          <Button variant="primary" size="lg" icon={ShieldCheck} disabled={!neutral || !chal} loading={busy === 'liveness'} onClick={verifyChallenge}>
            {busy === 'liveness' ? 'Analysing landmarks…' : 'Verify challenge'}
          </Button>
        </div>
      </Card>
    )
  } else if (ck.step === 4) {
    body = (
      <Card title="Step 4 · Face verification">
        {!face || busy === 'face' ? (
          <div className="stack">
            <p>Comparing your face with the enrolled reference and this session's records…</p>
            <motion.div animate={{ opacity: [1, 0.4, 1] }} transition={{ repeat: Infinity, duration: 1.2 }}>
              <ProgressBar value={0.66} label="Face verification in progress" />
            </motion.div>
          </div>
        ) : (
          <div className="stack">
            <Alert tone="error">🚫 {face.reason}</Alert>
            <div className="row">
              {face.retake ? (
                <Button variant="primary" icon={RotateCcw} onClick={retake} loading={busy === 'retake'}>
                  Retake photos
                </Button>
              ) : (
                <Button
                  icon={RotateCcw}
                  onClick={() => {
                    setFace(null)
                    runFace()
                  }}
                >
                  Check again
                </Button>
              )}
              <Button variant="ghost" onClick={startOver} loading={busy === 'reset'}>
                Start over
              </Button>
            </div>
          </div>
        )}
      </Card>
    )
  } else if (ck.step === 5 && ck.result) {
    const r = ck.result
    body = (
      <div style={{ position: 'relative' }}>
        <Burst />
        <Card>
          <span className="eyebrow">Step 5 · Done</span>
          <MaskHeadline className="display-lg" lines={['Marked.', 'Present.']} />
          <div style={{ margin: '18px 0' }}>
            <Alert tone="success">
              🎉 Attendance marked for <strong>{r.roll_number} – {r.full_name}</strong>
            </Alert>
          </div>
          <div className="grid grid-4">
            <StatCard label="Distance" value={`${Math.round(r.distance_m)} m`} hint="from geo-fence centre" />
            <StatCard label="Liveness" value={fmtNum(r.liveness_score)} delta={`${r.challenge_emoji} ${r.challenge}`} />
            <StatCard label="Identity match" value={r.identity_similarity === null ? 'n/a' : fmtNum(r.identity_similarity)} hint={`required ≥ ${r.identity_threshold}`} />
            <StatCard
              label="Max duplicate sim."
              value={r.max_duplicate_similarity === null ? '—' : fmtNum(r.max_duplicate_similarity)}
              hint={`must stay < ${r.duplicate_threshold}`}
            />
          </div>
          <p className="small mono muted" style={{ marginTop: 16 }}>
            Recorded at {r.recorded_at} · device {r.device}… · thresholds: identity ≥ {r.identity_threshold}, duplicate &lt; {r.duplicate_threshold}
          </p>
        </Card>
      </div>
    )
  } else if (ck.step === 99) {
    body = (
      <>
        <ErrorState title="Check-in locked" error="Check-in locked after repeated failed liveness challenges." hint="Start over to get a fresh challenge, or contact your faculty." />
        <div className="row" style={{ justifyContent: 'center', marginTop: 16 }}>
          <Button variant="primary" icon={RotateCcw} onClick={startOver} loading={busy === 'reset'}>
            Start over
          </Button>
        </div>
      </>
    )
  } else {
    body = <SkeletonBlock rows={3} />
  }

  return (
    <PageTransition>
      <Container style={{ paddingTop: 32, paddingBottom: 80 }}>
        <SessionHeader s={s} />
        {s.status !== 'live' && (
          <div style={{ marginBottom: 20 }}>
            <Alert tone="warning">{NOT_LIVE[s.status]}</Alert>
          </div>
        )}
        <Stepper steps={STEPS} current={stepIndex} failed={failedIndex} label="Check-in progress" />
        <div style={{ marginTop: 24 }} className="grid" data-cols>
          {isStudent && (
            <div className="row-between card card-flat" style={{ padding: 12 }}>
              <div className="row" style={{ '--gap': '10px' }}>
                <ScanFace size={20} aria-hidden="true" />
                <strong>{user.full_name}</strong>
                <span className="badge">{user.roll_number}</span>
                {meta?.device && <span className="tiny mono muted">device {meta.device}…</span>}
              </div>
              <Button size="sm" icon={LogOut} onClick={logout}>
                Sign out
              </Button>
            </div>
          )}
          <AnimatePresence mode="wait">
            <motion.div
              key={`${user ? 'u' : 'a'}-${ck?.step ?? 'x'}`}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.28 }}
            >
              {body}
            </motion.div>
          </AnimatePresence>
          {isStudent && ck?.step >= 2 && ck.step <= 4 && ck.distance_m !== undefined && (
            <KeyValueList
              items={[
                { label: 'Location', value: `Inside geo-fence · ${Math.round(ck.distance_m)} m from centre` },
                ck.liveness_score !== undefined ? { label: 'Liveness', value: `Passed · score ${fmtNum(ck.liveness_score)}` } : null,
              ]}
            />
          )}
          {ck?.step === 5 && (
            <p className="small" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <CheckCircle2 size={16} aria-hidden="true" /> You can close this page.
            </p>
          )}
        </div>
      </Container>
    </PageTransition>
  )
}
