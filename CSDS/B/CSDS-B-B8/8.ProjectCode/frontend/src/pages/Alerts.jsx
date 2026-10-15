import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BellOff, CheckCircle2, Mail, RefreshCw, Send, TriangleAlert, XCircle } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, KeyValueList, Modal, PageHeader, Table, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import { api, authedUrl } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { ALERT_STATUS, clock, ms, when } from '../lib/format'

function StatusBadge({ alert }) {
  const s = ALERT_STATUS[alert.status] || { label: alert.status, tone: 'neutral' }
  return (
    <Badge tone={s.tone} dot>
      {s.label}
      {alert.status === 'pending' && ` · ${Math.ceil(alert.seconds_left)} s`}
    </Badge>
  )
}

function ChannelLines({ icon: Icon, name, results }) {
  if (!results?.length) return null
  return (
    <>
      {results.map((r, i) => (
        <div className="ch-line" key={`${name}-${i}`}>
          <Icon size={14} aria-hidden="true" />
          {r.ok ? <CheckCircle2 size={14} color="var(--safe)" aria-label="delivered" /> : <XCircle size={14} color="var(--danger)" aria-label="failed" />}
          <span>
            {name} to {r.to}
          </span>
          <span className="faint">{r.ok ? ms(r.ms) : r.error}</span>
        </div>
      ))}
    </>
  )
}

function channelSummary(c = {}) {
  const parts = []
  for (const [key, label] of [['telegram', 'Telegram'], ['email', 'Email']]) {
    const list = c[key]
    if (list?.length) parts.push(`${label} ${list.filter((r) => r.ok).length}/${list.length}`)
  }
  return parts.length ? parts.join(' · ') : '-'
}

export default function Alerts() {
  const toast = useToast()
  const alerts = useAsync(() => api.get('/alerts'), [], { poll: 3000 })
  const settings = useAsync(() => api.get('/settings'), [])
  const [busy, setBusy] = useState('')
  const [open, setOpen] = useState(null)

  const run = async (key, fn, okMsg) => {
    setBusy(key)
    try {
      const res = await fn()
      if (okMsg) toast(okMsg(res))
      await alerts.reload({ quiet: true })
    } catch (e) {
      toast({ title: 'That did not work', message: e.message, tone: 'error' })
    } finally {
      setBusy('')
    }
  }
  const imOk = (id) => run(`ok${id}`, () => api.post(`/alerts/${id}/ok`), () => ({ title: `Alert #${id} cancelled`, message: "Glad you're OK." }))
  const sendTest = () =>
    run('test', () => api.post('/alerts/test'), (a) => ({
      title: `Test alert #${a.id}: ${a.status}`,
      message: a.channels?.note || channelSummary(a.channels),
      tone: a.status === 'sent' ? 'success' : 'info',
    }))

  const ch = settings.data?.channels
  const detail = open && alerts.data?.find((a) => a.id === open)

  const columns = [
    {
      key: 'id',
      label: 'Alert',
      sortValue: (a) => a.id,
      render: (a) => (
        <strong>
          #{a.id} {a.kind === 'fall' ? 'Fall detected' : 'Test alert'}
        </strong>
      ),
    },
    { key: 'status', label: 'Status', sortValue: (a) => a.status, render: (a) => <StatusBadge alert={a} /> },
    { key: 'detected_at', label: 'Detected', sortValue: (a) => a.detected_at, render: (a) => when(a.detected_at) },
    { key: 'detected_to_sent_ms', label: 'Detected to sent', num: true, hideSm: true, sortValue: (a) => a.detected_to_sent_ms, render: (a) => ms(a.detected_to_sent_ms) },
    { key: 'channels', label: 'Delivery', sortable: false, hideSm: true, render: (a) => channelSummary(a.channels) },
    {
      key: 'act',
      label: '',
      sortable: false,
      render: (a) =>
        a.status === 'pending' ? (
          <Button
            size="sm"
            variant="primary"
            loading={busy === `ok${a.id}`}
            onClick={(e) => {
              e.stopPropagation()
              imOk(a.id)
            }}
          >
            I&apos;m OK
          </Button>
        ) : (
          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setOpen(a.id) }}>
            Details
          </Button>
        ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Alerts"
        description="Fall alerts, acknowledgements and delivery to your contacts."
        actions={
          <>
            <Button icon={RefreshCw} onClick={() => alerts.reload()} loading={alerts.loading && !!alerts.data}>
              Refresh
            </Button>
            <Button variant="primary" icon={Send} loading={busy === 'test'} onClick={sendTest}>
              Send test alert
            </Button>
          </>
        }
      />

      {ch && (!ch.telegram || !ch.email) && (
        <SlideUp>
          <div className="notice warn" style={{ marginBottom: 18 }}>
            <TriangleAlert size={18} aria-hidden="true" />
            <div>
              {!ch.telegram && 'Telegram is not configured (TELEGRAM_BOT_TOKEN). '}
              {!ch.email && 'Email is not configured (SMTP_USER / SMTP_PASSWORD). '}
              Alerts are still detected and logged; add the keys to <code>.env</code> and restart to deliver them. See{' '}
              <Link to="/app/contacts">Contacts &amp; settings</Link>.
            </div>
          </div>
        </SlideUp>
      )}

      <Card>
        {alerts.error && !alerts.data ? (
          <ErrorState title="Couldn't load alerts" error={alerts.error} onRetry={alerts.reload} />
        ) : (
          <Table
            caption="Alert history"
            columns={columns}
            rows={alerts.data}
            rowKey={(a) => a.id}
            loading={alerts.loading && !alerts.data}
            initialSort={{ key: 'id', dir: 'desc' }}
            onRowClick={(a) => setOpen(a.id)}
            empty={
              <EmptyState icon={BellOff} title="No alerts yet" actions={<Button icon={Send} onClick={sendTest} loading={busy === 'test'}>Send a test alert</Button>}>
                Falls confirmed by the live monitor appear here. Send a test alert to check that Telegram and email reach your contacts.
              </EmptyState>
            }
          />
        )}
      </Card>

      <Modal
        open={!!detail}
        onClose={() => setOpen(null)}
        title={detail ? `Alert #${detail.id} - ${detail.kind === 'fall' ? 'Fall detected' : 'Test alert'}` : 'Alert'}
        footer={
          <>
            {detail?.status === 'pending' && (
              <Button variant="primary" loading={busy === `ok${detail.id}`} onClick={() => imOk(detail.id)}>
                I&apos;m OK
              </Button>
            )}
            <Button onClick={() => setOpen(null)}>Close</Button>
          </>
        }
      >
        {detail && (
          <div className="stack" style={{ gap: 16 }}>
            {detail.has_snapshot ? (
              <img className="snap" alt={`Snapshot taken with alert ${detail.id}`} src={authedUrl(`/alerts/${detail.id}/snapshot`)} />
            ) : (
              <p className="faint">{detail.kind === 'test' ? 'Test alerts carry no snapshot.' : 'No snapshot was saved for this alert.'}</p>
            )}
            <KeyValueList
              items={[
                ['Status', <StatusBadge key="s" alert={detail} />],
                ['Detected', when(detail.detected_at)],
                detail.resolved_at && ['Acknowledged', `${when(detail.resolved_at)}${detail.resolved_by ? ` by ${detail.resolved_by}` : ''}`],
                detail.kind === 'fall' && ['Impact to confirmation', ms(detail.detection_latency_ms)],
                ['Delivery time', ms(detail.dispatch_ms)],
                ['Detected to sent', ms(detail.detected_to_sent_ms)],
                ['Sent at', detail.sent_at ? clock(detail.sent_at) : '-'],
              ]}
            />
            <div className="stack" style={{ gap: 8 }}>
              <ChannelLines icon={Send} name="Telegram" results={detail.channels?.telegram} />
              <ChannelLines icon={Mail} name="Email" results={detail.channels?.email} />
              {detail.channels?.note && <p className="faint">{detail.channels.note}</p>}
              {!detail.channels?.telegram?.length && !detail.channels?.email?.length && !detail.channels?.note && (
                <p className="faint">No delivery attempts recorded.</p>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
