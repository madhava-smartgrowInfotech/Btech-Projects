import { Cpu, Database, ScanFace } from 'lucide-react'
import { Card, Container, ErrorState, KeyValueList, PageHeader, SkeletonBlock, Timeline } from '../components/ui'
import { InkRule, PageTransition, Reveal, Stagger } from '../components/motion'
import { useApi } from '../lib/useApi'
import { useConfig } from '../lib/config'

// The "How it works" tab of the Streamlit app.
const CHECKS = [
  ['Session', 'Faculty create a time window with a GPS geo-fence and a unique link.'],
  ['JWT authentication', 'Students sign in; the token is bound to their device fingerprint.'],
  ['Roll-number & device restrictions', 'Only allowed roll numbers, one device per student, one roll number per device per session.'],
  ['GPS verification', "The browser's location is checked against the geo-fence (haversine)."],
  ['Live challenge', "A random action (turn head, open mouth, …) is verified with MediaPipe Face Mesh landmarks, so photos and videos can't pass."],
  ['Face matching', 'InsightFace (ArcFace) embeddings confirm identity against the enrolled face and reject any face already recorded in the session under another roll number.'],
  ['Records & export', 'Faculty see live records, a verification log, and export to Excel.'],
]

export default function About() {
  const { config, error: cfgErr } = useConfig()
  const models = useApi('/api/models')

  return (
    <PageTransition>
      <Container style={{ paddingTop: 40, paddingBottom: 80 }}>
        <PageHeader
          eyebrow="How it works"
          title="Location. Liveness. Identity."
          description="Attendance Magic blocks proxy attendance by verifying location, liveness and identity together inside a time-bound session."
        />
        <div className="grid grid-2" style={{ alignItems: 'start' }}>
          <Card title="The seven checks">
            <Timeline items={CHECKS.map(([t, b], i) => ({ title: `${i + 1}. ${t}`, body: b, tone: 'ok' }))} />
          </Card>
          <div className="stack" style={{ '--gap': '24px' }}>
            <Card title="Models & storage" actions={<Cpu size={22} aria-hidden="true" />}>
              {models.error ? (
                <ErrorState title="Model info unavailable" error={models.error} onRetry={models.reload} />
              ) : models.loading || !models.data ? (
                <SkeletonBlock rows={3} label="Loading models (first run can take a minute)" />
              ) : (
                <KeyValueList
                  items={[
                    { label: 'Landmarks', value: <code>{models.data.landmarks}</code> },
                    { label: 'Recognition', value: <code>{models.data.recognition}</code> },
                    { label: 'Database', value: <code>{models.data.db}</code> },
                  ]}
                />
              )}
            </Card>
            <Card title="Live thresholds" actions={<Database size={22} aria-hidden="true" />}>
              {cfgErr ? (
                <ErrorState title="Settings unavailable" error={cfgErr} />
              ) : !config ? (
                <SkeletonBlock rows={4} />
              ) : (
                <KeyValueList
                  items={[
                    { label: 'Default radius', value: `${config.default_radius_m} m (+${config.geofence_tolerance_m} m tolerance)` },
                    { label: 'Max GPS accuracy', value: `±${config.max_gps_accuracy_m} m` },
                    { label: 'Identity', value: `cosine ≥ ${config.identity_threshold}` },
                    { label: 'Duplicate', value: `cosine < ${config.duplicate_threshold}` },
                    { label: 'Frame consistency', value: `cosine ≥ ${config.frame_consistency_threshold}` },
                    { label: 'Enrolment', value: config.require_enrollment ? 'Required' : 'Optional' },
                    { label: 'Devices / student', value: config.max_devices_per_student },
                    { label: 'Manual location', value: config.allow_manual_location ? 'Allowed (testing)' : 'Disabled' },
                  ]}
                />
              )}
            </Card>
          </div>
        </div>

        <InkRule style={{ margin: '56px 0 32px' }} />
        <Reveal>
          <h2 className="display-md" style={{ marginBottom: 20 }}>
            The random challenges
          </h2>
        </Reveal>
        {config && (
          <Stagger className="grid grid-4">
            {config.challenges.map((c) => (
              <Card key={c.code} hot flat style={{ height: '100%' }}>
                <div style={{ fontSize: '2.2rem' }} aria-hidden="true">
                  {c.emoji}
                </div>
                <div className="mono tiny" style={{ marginTop: 8 }}>
                  {c.code}
                </div>
                <p style={{ marginTop: 4, fontWeight: 600 }}>{c.text}</p>
              </Card>
            ))}
          </Stagger>
        )}
        <p className="small muted" style={{ marginTop: 20, display: 'flex', gap: 8, alignItems: 'center' }}>
          <ScanFace size={16} aria-hidden="true" /> Photo 1 is neutral, photo 2 holds the pose; landmark deltas (yaw, pitch, roll, mouth and eye aspect ratios) decide the result.
        </p>
      </Container>
    </PageTransition>
  )
}
