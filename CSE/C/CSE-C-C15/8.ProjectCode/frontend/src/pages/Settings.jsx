import { Moon, Save, Sun } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import api, { describeError, errorMessage } from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Button, Input, Switch } from '../components/ui/controls'
import { Card, KeyValueList } from '../components/ui/display'
import { ErrorState, PageSkeleton, useToast } from '../components/ui/feedback'
import { DEMO_USER, useAuth } from '../lib/auth'
import { useLive } from '../lib/live'
import { useTheme } from '../lib/theme'

function check(win, quar) {
  const e = {}
  const w = Number(win)
  const q = Number(quar)
  if (!Number.isInteger(w) || w < 2 || w > 120) e.window = 'Use a whole number from 2 to 120 seconds.'
  if (!Number.isInteger(q) || q < 5 || q > 3600) e.quarantine = 'Use a whole number from 5 to 3600 seconds.'
  return e
}

export default function Settings() {
  const toast = useToast()
  const { theme, toggle } = useTheme()
  const { user, signOut } = useAuth()
  const { status, refresh } = useLive()
  const [cur, setCur] = useState(null)
  const [loadErr, setLoadErr] = useState(null)
  const [win, setWin] = useState('')
  const [quar, setQuar] = useState('')
  const [errs, setErrs] = useState({})
  const [saving, setSaving] = useState(false)
  const [serverErr, setServerErr] = useState(null)

  const load = useCallback(() => {
    setLoadErr(null)
    api.get('/settings').then((r) => {
      setCur(r.data)
      setWin(String(r.data.window_seconds))
      setQuar(String(r.data.quarantine_seconds))
    }).catch((e) => setLoadErr(describeError(e)))
  }, [])
  useEffect(() => { load() }, [load])

  async function save(e) {
    e.preventDefault()
    const v = check(win, quar)
    setErrs(v)
    setServerErr(null)
    if (Object.keys(v).length) return
    setSaving(true)
    try {
      const r = await api.post('/settings', { window_seconds: Number(win), quarantine_seconds: Number(quar) })
      setCur((c) => ({ ...c, window_seconds: r.data.window_seconds, quarantine_seconds: r.data.quarantine_seconds }))
      toast({ tone: 'ok', title: 'Settings saved', body: `${r.data.window_seconds}s window · ${r.data.quarantine_seconds}s quarantine` })
      refresh()
    } catch (err) {
      setServerErr(errorMessage(err))
      toast({ tone: 'alert', title: 'Settings not saved', body: errorMessage(err) })
    } finally {
      setSaving(false)
    }
  }

  if (loadErr) {
    return (
      <div className="space-y-5">
        <PageHeader eyebrow="console / settings" title="Settings" />
        <ErrorState error={loadErr} title="Settings unavailable" onRetry={load} />
      </div>
    )
  }
  if (!cur) return <PageSkeleton />

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="console / settings" title="Settings" subtitle="Monitoring parameters are applied by the backend immediately." />
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Monitoring">
          <form onSubmit={save} noValidate className="space-y-4">
            <Input label="Monitoring window (seconds)" type="number" inputMode="numeric" min={2} max={120} value={win} error={errs.window}
              hint="2 to 120. Used by live capture; takes effect on the next live session." onChange={(e) => setWin(e.target.value)} />
            <Input label="Quarantine duration (seconds)" type="number" inputMode="numeric" min={5} max={3600} value={quar} error={errs.quarantine}
              hint="5 to 3600. Critical windows quarantine for twice this long." onChange={(e) => setQuar(e.target.value)} />
            {serverErr && <ErrorState compact error={serverErr} title="Backend rejected the change" />}
            <div className="flex flex-wrap items-center gap-3">
              <Button type="submit" icon={Save} loading={saving}>Save settings</Button>
              <span className="font-mono text-[11px] text-dim">saved: {cur.window_seconds}s window · {cur.quarantine_seconds}s quarantine</span>
            </div>
          </form>
        </Card>
        <div className="space-y-5">
          <Card title="Appearance">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm text-fg">{theme === 'dark' ? <Moon size={16} aria-hidden="true" /> : <Sun size={16} aria-hidden="true" />}Dark mode</div>
              <Switch checked={theme === 'dark'} onChange={toggle} label={theme === 'dark' ? 'on' : 'off'} />
            </div>
            <p className="mt-2 text-xs text-muted">Saved in this browser. Motion follows your system reduced-motion setting.</p>
          </Card>
          <Card title="Session and account">
            <KeyValueList items={[
              ['Signed in as', user?.email], ['Capture interface', status?.interface || cur.interface || 'not set'],
              ['Mode', status?.mode || 'stopped'], ['Windows completed', status?.windows_completed ?? 0],
            ]} />
            <p className="mt-3 text-xs text-muted">Demo gate: {DEMO_USER.email}. SentinelFlow runs on localhost only and has no user database.</p>
            <Button className="mt-3" variant="secondary" onClick={signOut}>Sign out</Button>
          </Card>
        </div>
      </div>
    </div>
  )
}
