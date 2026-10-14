import { Link, Navigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, CalendarClock, FileSpreadsheet, KeyRound, MapPin, ScanFace, ScanLine, UserCheck, Users } from 'lucide-react'
import { Alert, Button, Card, Container, ErrorState, Skeleton } from '../components/ui'
import { CountUp, InkRule, MagneticButton, MaskHeadline, Marquee, Parallax, PageTransition, Reveal, Stagger } from '../components/motion'
import { useApi } from '../lib/useApi'
import { useConfig } from '../lib/config'

const STEPS = [
  ['Session', 'Faculty open a time window with a GPS geo-fence, roll-number rules and a unique link + QR code.'],
  ['Sign in', 'Students sign in; the JWT is bound to their device fingerprint, one device per student.'],
  ['Eligibility', 'Session live? Roll number allowed? Not already marked? Device registered to this student?'],
  ['Location', 'Browser GPS is checked against the fence with the haversine distance (radius + tolerance).'],
  ['Live challenge', 'A random action — turn, tilt, look up, open mouth, close eyes — verified from MediaPipe Face Mesh landmarks.'],
  ['Face match', 'InsightFace ArcFace embeddings: same person in both photos, matches the enrolled face, no duplicate in the session.'],
]

const FEATURES = [
  [CalendarClock, 'Time-bound sessions', 'Each session has a start, a duration and a geo-fence. Outside the window, nobody checks in.'],
  [KeyRound, 'JWT + device binding', 'PBKDF2 passwords, device-bound JWTs, and a cap on devices per student. One roll per device per session.'],
  [MapPin, 'GPS geo-fencing', 'Haversine distance against the classroom centre, with an accuracy guard against vague fixes.'],
  [ScanLine, 'Random liveness', 'Eight possible challenges, chosen at random each try. A printed photo or a replayed video cannot respond.'],
  [Users, 'Duplicate-face guard', 'Every face is compared with all faces already recorded in the session under other roll numbers.'],
  [FileSpreadsheet, 'Excel export', 'Summary, attendance with absentees, and the full verification log in one workbook.'],
]

function ChecksStack({ config, error }) {
  if (error) return <Alert tone="warning">Live settings unavailable: {error.message}</Alert>
  if (!config) return <Skeleton height={260} />
  const items = [
    ['Geo-fence', `${Math.round(config.default_radius_m)} m`, `+${Math.round(config.geofence_tolerance_m)} m tolerance`],
    ['Challenges', `${config.challenges.length} random`, `${config.max_liveness_retries} tries, new each time`],
    ['Identity', `≥ ${config.identity_threshold.toFixed(2)}`, 'cosine vs enrolled face'],
    ['Duplicate', `< ${config.duplicate_threshold.toFixed(2)}`, 'vs faces in session'],
    ['Devices', `${config.max_devices_per_student} / student`, 'JWT bound to device'],
    ['Token', `${config.jwt_expiry_minutes} min`, `time zone ${config.timezone}`],
  ]
  return (
    <div className="checks-stack" aria-label="Live verification settings">
      {items.map(([k, v, s]) => (
        <div key={k}>
          <div className="k">{k}</div>
          <div className="v">{v}</div>
          <div className="tiny muted">{s}</div>
        </div>
      ))}
    </div>
  )
}

export default function Landing() {
  const [params] = useSearchParams()
  const token = params.get('session')
  const { data: stats, error: statsError, loading: statsLoading, reload } = useApi(token ? null : '/api/stats')
  const { config, error: configError } = useConfig()

  // Session links keep the Streamlit shape: /?session=TOKEN
  if (token) return <Navigate to={`/checkin/${encodeURIComponent(token)}`} replace />

  const ticker = stats
    ? [
        { label: 'Sessions created', value: stats.sessions },
        { label: 'Live right now', value: stats.live_sessions },
        { label: 'Check-ins verified', value: stats.records },
        { label: 'Proxy attempts blocked', value: stats.blocked },
        { label: 'Verification checks run', value: stats.attempts },
        { label: 'Faces enrolled', value: `${stats.enrolled}/${stats.students}` },
      ]
    : []

  return (
    <PageTransition>
      <section className="hero">
        <Container>
          <span className="eyebrow">Geo-fenced · live challenge · face verified</span>
          <MaskHeadline as="h1" className="display-xl hero-title" lines={['Attendance', "that can't", 'be faked.']} />
          <div className="hero-grid">
            <div style={{ minWidth: 0 }}>
              <p className="lead" style={{ marginTop: 8 }}>
                Faculty open a time-bound, geo-fenced session. Students prove they are <span className="hl">in the room</span>,{' '}
                <span className="hl">alive</span> and <span className="hl">themselves</span> — location, a random facial challenge and face
                matching, verified together.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to="/login?role=faculty" iconRight={ArrowRight}>
                    Faculty portal
                  </Button>
                </MagneticButton>
                <MagneticButton>
                  <Button size="lg" to="/checkin" icon={ScanFace}>
                    Student check-in
                  </Button>
                </MagneticButton>
              </div>
            </div>
            <div style={{ position: 'relative', minWidth: 0 }}>
              <Parallax speed={0.25} style={{ position: 'absolute', right: -10, top: -34, zIndex: 0 }}>
                <div aria-hidden="true" style={{ width: 90, height: 90, background: 'var(--coral)', border: '3px solid var(--ink)' }} />
              </Parallax>
              <div style={{ position: 'relative', zIndex: 1 }}>
                <ChecksStack config={config} error={configError} />
              </div>
            </div>
          </div>
        </Container>
      </section>

      {statsLoading && <Skeleton height={48} />}
      {stats && <Marquee items={ticker} label="Live statistics from this installation" />}

      <section className="section" aria-labelledby="how">
        <Container>
          <div className="section-head">
            <MaskHeadline as="h2" className="display-lg" lines={['How a', 'check-in works']} scroll />
            <p className="lead muted" id="how">
              Six checks, in order, each one logged with its reason. Fail any and attendance is not recorded.
            </p>
          </div>
          <div>
            {STEPS.map(([title, body], i) => (
              <Reveal key={title} className="how-step" y={36}>
                <span className="how-num" aria-hidden="true">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div>
                  <h3 className="display-sm">{title}</h3>
                  <p className="muted" style={{ marginTop: 8, maxWidth: '62ch' }}>
                    {body}
                  </p>
                </div>
              </Reveal>
            ))}
          </div>
        </Container>
      </section>

      <Container>
        <InkRule thick />
      </Container>

      <section className="section" aria-labelledby="features">
        <Container>
          <div className="section-head">
            <MaskHeadline as="h2" className="display-lg" lines={['Built to', 'stop proxies']} scroll />
            <p className="lead muted" id="features">
              Every objective of the project, implemented end to end.
            </p>
          </div>
          <Stagger className="grid grid-3">
            {FEATURES.map(([Icon, title, body]) => (
              <Card key={title} hot className="feature-card" style={{ height: '100%' }}>
                <div className="feature-icon" aria-hidden="true">
                  <Icon size={26} />
                </div>
                <h3 className="card-title">{title}</h3>
                <p className="muted" style={{ marginTop: 8 }}>
                  {body}
                </p>
              </Card>
            ))}
          </Stagger>
        </Container>
      </section>

      <Container>
        <InkRule thick />
      </Container>

      <section className="section" aria-labelledby="numbers">
        <Container>
          <div className="section-head">
            <h2 className="display-lg" id="numbers">
              By the numbers
            </h2>
            <p className="muted small mono">Live counts from this installation's database.</p>
          </div>
          {statsError ? (
            <ErrorState title="Couldn't load the numbers" error={statsError} onRetry={reload} />
          ) : !stats ? (
            <Skeleton height={160} />
          ) : (
            <Reveal className="stats-strip">
              {[
                ['Sessions', stats.sessions],
                ['Check-ins verified', stats.records],
                ['Attempts blocked', stats.blocked],
                ['Students enrolled', stats.enrolled],
              ].map(([k, v]) => (
                <div key={k} className="stat">
                  <span className="stat-label">{k}</span>
                  <CountUp className="stat-value" value={v} />
                </div>
              ))}
            </Reveal>
          )}
        </Container>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <Container>
          <Reveal className="cta-block">
            <span className="eyebrow">Ready when your class is</span>
            <h2 className="display-lg" style={{ marginTop: 14 }}>
              Run your next class behind a geo-fence.
            </h2>
            <div className="hero-actions">
              <Button variant="secondary" size="lg" to="/login?role=faculty" iconRight={ArrowRight}>
                Create a session
              </Button>
              <Button size="lg" to="/register?role=student" icon={UserCheck}>
                Register as a student
              </Button>
            </div>
          </Reveal>
        </Container>
      </section>

      <footer className="footer">
        <Container>
          <div className="footer-grid">
            <div>
              <h4>Attendance Magic</h4>
              <p className="small">A smart geo-fenced attendance system with live challenge verification. CSE (Data Science) · Batch A2.</p>
            </div>
            <div>
              <h4>Portals</h4>
              <ul className="small">
                <li><Link to="/login?role=faculty">Faculty sign in</Link></li>
                <li><Link to="/checkin">Student check-in</Link></li>
                <li><Link to="/register">Register</Link></li>
                <li><Link to="/about">How it works</Link></li>
              </ul>
            </div>
            <div>
              <h4>Base paper</h4>
              <p className="small">
                Real-Time Student Face Recognition Attendance System Using AI — IARJSET Vol. 12 Issue 5, 2025 (DOI 10.17148/IARJSET.2025.125183).
              </p>
            </div>
          </div>
          <p className="tiny mono" style={{ marginTop: 28, opacity: 0.8 }}>
            Python · FastAPI · MediaPipe · InsightFace · SQLAlchemy · React
          </p>
        </Container>
      </footer>
    </PageTransition>
  )
}
