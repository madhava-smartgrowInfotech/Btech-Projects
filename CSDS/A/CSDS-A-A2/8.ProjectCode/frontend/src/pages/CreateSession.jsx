import { useEffect, useState } from 'react'
import { ArrowRight, HelpCircle, PlusSquare, Sparkles } from 'lucide-react'
import { Alert, Breadcrumbs, Button, Card, Input, KeyValueList, PageHeader, SkeletonBlock, Stepper, Tooltip, useToast } from '../components/ui'
import { PageTransition, SlideUp } from '../components/motion'
import { LocationPicker } from '../components/LocationPicker'
import { LazyMap } from '../components/LazyMap'
import { SharePanel } from '../components/SharePanel'
import { api } from '../lib/api'
import { useConfig } from '../lib/config'

export default function CreateSession() {
  const toast = useToast()
  const { config, error: cfgErr } = useConfig()
  const [f, setF] = useState({ course_code: '', course_name: '', section: '', date: '', time: '', duration: 15, radius: 60, allowed: '*' })
  const [loc, setLoc] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [created, setCreated] = useState(null)

  // Default date/time = now in the server's configured time zone (like Streamlit's defaults).
  useEffect(() => {
    if (!config) return
    const [d, t] = config.now_local.split('T')
    setF((x) => ({ ...x, date: x.date || d, time: x.time || t, radius: x.radius === 60 ? Math.round(config.default_radius_m) : x.radius }))
  }, [config])

  const set = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!loc) {
      setError('Set the classroom location first to enable session creation.')
      return
    }
    const duration = Number(f.duration)
    if (!f.date || !f.time) {
      setError('Pick a date and start time.')
      return
    }
    if (!Number.isInteger(duration) || duration < 1 || duration > 600) {
      setError('Duration must be a whole number of minutes between 1 and 600.')
      return
    }
    setBusy(true)
    try {
      const s = await api('/api/sessions', {
        method: 'POST',
        body: {
          course_code: f.course_code,
          course_name: f.course_name,
          section: f.section,
          start_local: `${f.date}T${f.time}`,
          duration_min: duration,
          latitude: loc.lat,
          longitude: loc.lon,
          radius_m: Number(f.radius),
          allowed_rolls: f.allowed,
        },
      })
      setCreated(s)
      toast.success('Session created!')
      setTimeout(() => document.getElementById('share')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const step = created ? 2 : loc ? 1 : 0

  return (
    <PageTransition>
      <PageHeader
        crumbs={<Breadcrumbs items={[{ label: 'Sessions', to: '/app/sessions' }, { label: 'New session' }]} />}
        title="New session"
        description="Create a time-bound, geo-fenced attendance session and share the unique link."
      />
      <div style={{ marginBottom: 24 }}>
        <Stepper steps={['Details', 'Location', 'Share']} current={step} label="Session setup progress" />
      </div>
      {cfgErr && <Alert tone="error">Couldn't load settings: {cfgErr.message}</Alert>}
      {!config && !cfgErr ? (
        <SkeletonBlock rows={6} label="Loading form" />
      ) : (
        config && (
          <form onSubmit={submit} noValidate className="stack" style={{ '--gap': '24px' }}>
            <Card title="1 · Course & time window">
              <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))' }}>
                <Input label="Course code" placeholder="CS601" value={f.course_code} onChange={set('course_code')} />
                <Input label="Course name" placeholder="Machine Learning" value={f.course_name} onChange={set('course_name')} />
                <Input label="Section" placeholder="CSDS-A" value={f.section} onChange={set('section')} />
                <Input label="Date" type="date" value={f.date} onChange={set('date')} />
                <Input label="Start time" type="time" value={f.time} onChange={set('time')} hint={`Time zone: ${config.timezone}`} />
                <Input label="Duration (minutes)" type="number" min={1} max={600} value={f.duration} onChange={set('duration')} />
              </div>
            </Card>

            <Card title="2 · Classroom geo-fence">
              <div className="grid grid-2" style={{ alignItems: 'start' }}>
                <div className="stack">
                  <LocationPicker value={loc} onChange={setLoc} allowManual={config.allow_manual_location} />
                  <div className="field">
                    <label className="field-label" htmlFor="radius">
                      Geo-fence radius: <span className="mono">{f.radius} m</span>
                    </label>
                    <input id="radius" className="range" type="range" min={10} max={500} step={5} value={f.radius} onChange={set('radius')} />
                    <span className="field-hint">
                      10–500 m. Students get +{config.geofence_tolerance_m} m tolerance for GPS noise; fixes worse than ±{config.max_gps_accuracy_m} m are rejected.
                    </span>
                  </div>
                  <Input
                    label="Allowed roll numbers"
                    extra={
                      <Tooltip content="Examples: 23K91A67* (all with that prefix) or 23K91A6706,23K91A6740 (explicit list). * = anyone.">
                        <HelpCircle size={15} aria-label="Help: allowed roll numbers" tabIndex={0} />
                      </Tooltip>
                    }
                    hint="Comma-separated, wildcards ok. An explicit list also lets the export mark absentees."
                    value={f.allowed}
                    onChange={set('allowed')}
                  />
                </div>
                {loc ? (
                  <LazyMap center={loc} radius={Number(f.radius)} tolerance={config.geofence_tolerance_m} label="Geo-fence preview" />
                ) : (
                  <div className="state">
                    <h3>No location yet</h3>
                    <p>Set the classroom location to preview the geo-fence on the map.</p>
                  </div>
                )}
              </div>
            </Card>

            {error && <Alert tone="error">{error}</Alert>}
            <div className="row">
              <Button type="submit" variant="primary" size="lg" icon={PlusSquare} loading={busy} disabled={!loc}>
                Create session
              </Button>
              {!loc && <span className="small muted">Set the classroom location first to enable session creation.</span>}
            </div>
          </form>
        )
      )}

      {created && (
        <SlideUp>
          <section id="share" style={{ marginTop: 32, scrollMarginTop: 80 }}>
            <Card tone="lime" title="Share this link with students" actions={<Sparkles size={22} aria-hidden="true" />}>
              <div className="grid grid-2" style={{ alignItems: 'start' }}>
                <SharePanel token={created.token} />
                <div className="stack">
                  <KeyValueList
                    items={[
                      { label: 'Course', value: `${created.course_code} – ${created.course_name}` },
                      { label: 'Window', value: `${created.starts_local} → ${created.ends_local}` },
                      { label: 'Radius', value: `${Math.round(created.radius_m)} m` },
                      { label: 'Allowed', value: <code>{created.allowed_rolls}</code> },
                    ]}
                  />
                  <div>
                    <Button variant="secondary" to={`/app/sessions/${created.id}`} iconRight={ArrowRight}>
                      Open session records
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </section>
        </SlideUp>
      )}
    </PageTransition>
  )
}
