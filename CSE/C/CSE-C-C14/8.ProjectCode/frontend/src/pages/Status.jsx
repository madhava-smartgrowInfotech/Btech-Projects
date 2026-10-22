import { useEffect, useState } from 'react'
import { Activity, CheckCircle2, RefreshCw, ServerCrash, XCircle } from 'lucide-react'
import { api } from '../lib/api'
import { useDocTitle, useLoad } from '../lib/hooks'
import { Badge, Button, Card, ErrorState, KeyValueList, PageHeader, PageSkeleton, StatCard, useToast } from '../components/ui'
import { SlideUp, Stagger } from '../components/motion'

export default function Status() {
  useDocTitle('System status · VeriVision AI')
  const toast = useToast()
  const health = useLoad((s) => api.health(s), [])
  const cfg = useLoad((s) => api.config(s), [])
  const [checkedAt, setCheckedAt] = useState(null)
  useEffect(() => {
    if (!health.loading) setCheckedAt(new Date())
  }, [health.loading])

  const header = (
    <PageHeader
      eyebrow="Health"
      icon={Activity}
      title="System status"
      lead="Live answer from the API's /health endpoint: are the four models loaded, and on which device?"
      actions={
        <Button
          variant="secondary"
          icon={RefreshCw}
          loading={health.loading}
          onClick={() => {
            health.reload()
            cfg.reload()
            toast({ kind: 'info', title: 'Re-checking…' })
          }}
        >
          Check again
        </Button>
      }
    />
  )
  if (health.loading && !health.data) return <div className="stack">{header}<PageSkeleton kpis={3} blocks={1} /></div>
  if (health.error) {
    return (
      <div className="stack">
        {header}
        <ErrorState title="The API is not reachable" error={health.error} onRetry={health.reload} />
      </div>
    )
  }
  const h = health.data
  const ok = h.status === 'ok'
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      {header}
      <Stagger className="grid-kpi">
        <Stagger.Item>
          <StatCard label="API" display={ok ? 'Online' : 'Degraded'} tone={ok ? 'mint' : 'rose'} icon={ok ? CheckCircle2 : ServerCrash} foot={`status: ${h.status}`} />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="Models" display={h.models_loaded ? 'Loaded' : 'Not loaded'} tone={h.models_loaded ? 'lavender' : 'rose'} icon={h.models_loaded ? CheckCircle2 : XCircle} foot="4 detector routes" />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="Device" display={String(h.device).toUpperCase()} tone="sky" icon={Activity} foot="auto-detected" />
        </Stagger.Item>
      </Stagger>

      {!ok && (
        <SlideUp>
          <div className="card tint-peach" role="alert">
            <strong>The models could not be loaded.</strong>
            <p style={{ marginTop: 6, overflowWrap: 'anywhere' }}>{h.error}</p>
            <p className="small" style={{ marginTop: 6 }}>Run the training workflow in HOW_TO_RUN.md (or re-run run.bat) to create the model files, then press “Check again”.</p>
          </div>
        </SlideUp>
      )}

      <div className="grid-2">
        <Card title="Health response" hover={false} actions={<Badge tone={ok ? 'mint' : 'rose'} dot>{ok ? 'ok' : 'degraded'}</Badge>}>
          <KeyValueList
            items={[
              ['status', h.status],
              ['models_loaded', String(h.models_loaded)],
              ['device', h.device],
              ['error', h.error || 'none'],
              ['last checked', checkedAt ? checkedAt.toLocaleTimeString() : '–'],
            ]}
          />
        </Card>
        <Card title="Upload rules" hover={false}>
          {cfg.data ? (
            <KeyValueList
              items={[
                ['Accepted types', cfg.data.allowed_extensions.join(', ').toUpperCase()],
                ['Maximum size', `${cfg.data.max_mb} MB`],
                ['Processing', 'On this machine only'],
              ]}
            />
          ) : cfg.error ? (
            <p className="small" role="alert" style={{ color: 'var(--rose-ink)' }}>Could not load the configuration: {cfg.error.message}</p>
          ) : (
            <PageSkeleton kpis={0} blocks={0} />
          )}
        </Card>
      </div>
    </div>
  )
}
