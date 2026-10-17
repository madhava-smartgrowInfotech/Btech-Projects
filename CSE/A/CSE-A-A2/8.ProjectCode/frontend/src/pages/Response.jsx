import { lazy, Suspense, useCallback, useEffect, useState } from 'react'
import { BellRing, Hospital, Phone, Siren } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, KeyValueList, PageHeader, Skeleton, Table } from '../components/ui'
import { PageTransition } from '../components/motion'
import { ContactsCard } from '../features/ContactsCard'
import { api } from '../lib/api'
import { useMonitor } from '../state/MonitorContext'

const MapView = lazy(() => import('../features/MapView'))

export default function Response() {
  const m = useMonitor()
  const [dir, setDir] = useState({ status: 'loading' }) // hospital directory preview around the default area
  const load = useCallback(async () => {
    setDir({ status: 'loading' })
    try {
      const d = await api.hospitals({ k: 5 })
      setDir({ status: 'ok', ...d })
    } catch (e) {
      setDir({ status: 'error', error: e })
    }
  }, [])
  useEffect(() => {
    load()
  }, [load])

  const d = m.dispatch
  // After a dispatch, the map shows the accident and its 3 nearest hospitals; before, the 5 closest to the default area.
  const hospitals = d ? d.nearest_hospitals : dir.hospitals || []
  const origin = d ? d.location : dir.origin
  const nearest = d?.nearest_hospitals?.[0]

  const columns = [
    { key: 'name', label: 'Hospital', render: (h) => <strong>{h.name}</strong> },
    { key: 'distance_km', label: 'Distance', numeric: true, render: (h) => `${h.distance_km} km` },
    { key: 'phone', label: 'Phone', sortable: false, render: (h) => <a href={`tel:${h.phone}`}>{h.phone}</a> },
    { key: 'emergency', label: 'Emergency', sortable: false, render: (h) => (h.emergency ? <Badge tone="pass">24h ER</Badge> : <Badge>No ER</Badge>) },
  ]

  return (
    <PageTransition>
      <PageHeader
        eyebrow="Emergency response"
        title={d ? 'Alert dispatched' : 'Response map'}
        description={d ? `Alert ${d.alert_id} was raised at ${d.at}. Responders see the location, the nearest hospital and the message below.` : 'Nearest hospitals in the demo directory. A confirmed Moderate or Severe accident plots its location here and drafts the dispatch message.'}
        actions={
          <Button variant="danger" icon={Siren} loading={m.busy} disabled={Boolean(m.pending) || m.dispatching} onClick={() => m.runScenario('severe')}>
            Simulate severe crash
          </Button>
        }
      />
      {dir.status === 'error' && !d ? (
        <ErrorState title="Could not load the hospital directory" error={dir.error} onRetry={load} />
      ) : (
        <div className="grid" style={{ '--gap': '24px' }}>
          <div className="grid grid-2" style={{ '--gap': '24px', alignItems: 'start' }}>
            <Card title={d ? 'Accident and nearest hospitals' : 'Hospitals near the default area'}>
              {dir.status === 'loading' && !d ? (
                <Skeleton height={340} />
              ) : (
                <Suspense fallback={<Skeleton height={340} />}>
                  <MapView center={origin} hospitals={hospitals} accident={d?.location} />
                </Suspense>
              )}
            </Card>
            <div className="stack" style={{ '--gap': '24px' }}>
              {d ? (
                <Card title="Dispatch summary" tone="coral">
                  <div className="stack">
                    <KeyValueList
                      items={[
                        { label: 'Alert ID', value: d.alert_id },
                        { label: 'Status', value: d.status },
                        { label: 'Severity', value: d.severity_label },
                        { label: 'Location', value: `${d.location.lat.toFixed(5)}, ${d.location.lon.toFixed(5)}` },
                        { label: 'Source', value: d.located ? 'Device GPS' : 'Default area (GPS unavailable)' },
                        nearest && { label: 'Nearest hospital', value: `${nearest.name}, ${nearest.distance_km} km` },
                      ].filter(Boolean)}
                    />
                    <div className="row">
                      {nearest && <Button icon={Phone} href={`tel:${nearest.phone}`}>Call {nearest.phone}</Button>}
                      <Button icon={BellRing} onClick={() => m.setDispatchOpen(true)}>View message</Button>
                    </div>
                  </div>
                </Card>
              ) : (
                <Card title="No alert dispatched">
                  <EmptyState icon={Siren} title="Nothing dispatched yet">
                    Run a moderate or severe scenario and let the 15 second confirmation expire, or press "Send alert now".
                  </EmptyState>
                </Card>
              )}
              <ContactsCard />
            </div>
          </div>
          <Card title={d ? 'Nearest hospitals to the accident' : 'Closest hospitals to the default area'} actions={<Hospital size={20} aria-hidden="true" />}>
            {dir.status === 'loading' && !d ? (
              <Skeleton height={160} />
            ) : (
              <Table columns={columns} rows={hospitals} rowKey={(h) => h.name} pageSize={5} initialSort={{ key: 'distance_km', dir: 'asc' }} caption="Hospitals sorted by distance" />
            )}
          </Card>
        </div>
      )}
    </PageTransition>
  )
}
