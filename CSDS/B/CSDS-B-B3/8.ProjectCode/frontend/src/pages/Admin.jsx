import { useState } from 'react'
import { BadgeCheck, Flag, GraduationCap, Mic, PackageOpen, ShoppingCart, Trash2, Users, Wallet, Code2 } from 'lucide-react'
import { AsyncView, CardSkeleton, PageSkeleton, useAction } from '../components/common'
import { Badge, Button, Card, CardHeader, EmptyState, Modal, PageHeader, StatCard, Table, Tabs } from '../components/ui'
import { ChartCard, GroupedBarChart } from '../components/charts'
import { Stagger } from '../components/motion'
import { inr, day } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

function Overview() {
  const state = useAsync(() => api.get('/admin/overview'), [])
  return (
    <AsyncView state={state} skeleton={<PageSkeleton />}>
      {(o) => (
        <div className="stack">
          <Stagger className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))' }}>
            <StatCard label="Students" value={o.total_students} icon={GraduationCap} />
            <StatCard label="Mentors" value={o.total_mentors} icon={Users} />
            <StatCard label="Resources" value={o.total_resources} icon={PackageOpen} />
            <StatCard label="Marketplace volume" value={inr(o.gross_marketplace_volume)} icon={Wallet} tone="info" />
            <StatCard label="Purchases" value={o.total_purchases} icon={ShoppingCart} />
            <StatCard label="Mock interviews" value={o.total_interviews} icon={Mic} />
            <StatCard label="Code submissions" value={o.total_submissions} icon={Code2} />
          </Stagger>
          <ChartCard title="Platform activity" subtitle="Totals across the whole platform">
            <GroupedBarChart
              xKey="name"
              yDomain={[0, 'auto']}
              data={[
                { name: 'Students', count: o.total_students },
                { name: 'Mentors', count: o.total_mentors },
                { name: 'Resources', count: o.total_resources },
                { name: 'Purchases', count: o.total_purchases },
                { name: 'Sessions', count: o.total_sessions },
                { name: 'Interviews', count: o.total_interviews },
                { name: 'Submissions', count: o.total_submissions },
              ]}
              series={[{ key: 'count', label: 'Count' }]}
            />
          </ChartCard>
        </div>
      )}
    </AsyncView>
  )
}

function UsersTab() {
  const state = useAsync(() => api.get('/admin/users'), [])
  const [target, setTarget] = useState(null)
  const { busy, run } = useAction()
  const toggle = async () => {
    const r = await run(
      () => api.post(`/admin/users/${target.id}/toggle`),
      (x) => ({ title: `${target.name} ${x.is_active ? 'reactivated' : 'deactivated'}` }),
    )
    setTarget(null)
    if (r.ok) state.reload({ quiet: true })
  }
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(rows) => (
        <Card>
          <Table
            caption="All users"
            rows={rows}
            rowKey={(r) => r.id}
            pageSize={10}
            initialSort={{ key: 'id', dir: 'asc' }}
            columns={[
              { key: 'name', label: 'Name' },
              { key: 'email', label: 'Email', className: 'break', hideSm: true },
              { key: 'role', label: 'Role', render: (r) => <span style={{ textTransform: 'capitalize' }}>{r.role}</span> },
              {
                key: 'is_active',
                label: 'Status',
                render: (r) => (
                  <Badge tone={r.is_active ? 'safe' : 'danger'} dot>
                    {r.is_active ? 'Active' : 'Deactivated'}
                  </Badge>
                ),
                sortValue: (r) => Number(r.is_active),
              },
              {
                key: 'actions',
                label: '',
                sortable: false,
                render: (r) =>
                  r.role === 'admin' ? (
                    <span className="faint">Protected</span>
                  ) : (
                    <Button size="sm" variant={r.is_active ? 'danger' : 'secondary'} onClick={() => setTarget(r)}>
                      {r.is_active ? 'Deactivate' : 'Reactivate'}
                    </Button>
                  ),
              },
            ]}
          />
          <Modal
            open={!!target}
            onClose={() => setTarget(null)}
            title={target?.is_active ? 'Deactivate this account?' : 'Reactivate this account?'}
            footer={
              <>
                <Button onClick={() => setTarget(null)}>Cancel</Button>
                <Button variant={target?.is_active ? 'danger' : 'primary'} loading={busy} onClick={toggle}>
                  {target?.is_active ? 'Deactivate' : 'Reactivate'}
                </Button>
              </>
            }
          >
            {target && (
              <p>
                {target.is_active
                  ? `${target.name} (${target.email}) will no longer be able to sign in until you reactivate the account.`
                  : `${target.name} (${target.email}) will be able to sign in again.`}
              </p>
            )}
          </Modal>
        </Card>
      )}
    </AsyncView>
  )
}

function MentorsTab() {
  const state = useAsync(() => api.get('/admin/mentors/pending'), [])
  const { busy, run } = useAction()
  const verify = async (m) => {
    const r = await run(() => api.post(`/admin/mentors/${m.id}/verify`), (x) => ({ title: x.message }))
    if (r.ok) state.reload({ quiet: true })
  }
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(rows) =>
        rows.length === 0 ? (
          <Card>
            <EmptyState icon={BadgeCheck} title="No mentors pending verification">Newly registered mentors will appear here until you verify them.</EmptyState>
          </Card>
        ) : (
          <Card>
            {rows.map((m) => (
              <div className="list-item" key={m.id}>
                <div>
                  <h3>
                    {m.name} <span className="faint" style={{ fontWeight: 400 }}>· {m.domain || 'domain not set'}</span>
                  </h3>
                  <div className="meta-line">
                    <span>{m.email}</span>
                    <span>Expertise: {m.expertise || 'not set'}</span>
                    <span>{m.experience_years} yrs experience</span>
                  </div>
                </div>
                <Button size="sm" variant="primary" icon={BadgeCheck} disabled={busy} onClick={() => verify(m)}>
                  Verify mentor
                </Button>
              </div>
            ))}
          </Card>
        )
      }
    </AsyncView>
  )
}

function ResourcesTab() {
  const state = useAsync(() => api.get('/admin/resources'), [])
  const [target, setTarget] = useState(null)
  const { busy, run } = useAction()
  const remove = async () => {
    const r = await run(() => api.del(`/admin/resources/${target.id}`), (x) => ({ title: x.message }))
    setTarget(null)
    if (r.ok) state.reload({ quiet: true })
  }
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(rows) => (
        <Card>
          <Table
            caption="All resources"
            rows={rows}
            rowKey={(r) => r.id}
            pageSize={10}
            empty={<EmptyState icon={PackageOpen} title="No resources in the marketplace" />}
            columns={[
              { key: 'title', label: 'Title' },
              { key: 'category', label: 'Category', hideSm: true },
              { key: 'price', label: 'Price', num: true, render: (r) => (r.price === 0 ? 'Free' : inr(r.price)) },
              {
                key: 'flag',
                label: 'Flag',
                render: (r) =>
                  r.is_reported ? <Badge tone="danger" dot>Reported</Badge> : r.is_approved ? <Badge tone="safe" dot>Approved</Badge> : <Badge tone="warn" dot>Pending</Badge>,
                sortValue: (r) => Number(r.is_reported),
              },
              {
                key: 'actions',
                label: '',
                sortable: false,
                render: (r) => (
                  <Button size="sm" variant="danger" icon={Trash2} onClick={() => setTarget(r)}>
                    Remove
                  </Button>
                ),
              },
            ]}
          />
          <Modal
            open={!!target}
            onClose={() => setTarget(null)}
            title="Remove this resource?"
            footer={
              <>
                <Button onClick={() => setTarget(null)}>Cancel</Button>
                <Button variant="danger" icon={Trash2} loading={busy} onClick={remove}>
                  Remove permanently
                </Button>
              </>
            }
          >
            {target && <p><strong>{target.title}</strong> will be deleted from the marketplace. This cannot be undone.</p>}
          </Modal>
        </Card>
      )}
    </AsyncView>
  )
}

function ReportsTab() {
  const state = useAsync(() => api.get('/admin/reports'), [])
  const { busy, run } = useAction()
  const resolve = async (r0) => {
    const r = await run(() => api.post(`/admin/reports/${r0.id}/resolve`), (x) => ({ title: x.message }))
    if (r.ok) state.reload({ quiet: true })
  }
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(rows) =>
        rows.length === 0 ? (
          <Card>
            <EmptyState icon={Flag} title="No open reports">Reports about resources will appear here for review.</EmptyState>
          </Card>
        ) : (
          <Card>
            {rows.map((r) => (
              <div className="list-item" key={r.id}>
                <div>
                  <h3>Report #{r.id}</h3>
                  <p className="muted">{r.reason}</p>
                  <div className="meta-line" style={{ marginTop: 6 }}>
                    <span>Filed {day(r.created_at)}</span>
                    {r.resource_id && <span>Resource #{r.resource_id}</span>}
                  </div>
                </div>
                <Button size="sm" disabled={busy} onClick={() => resolve(r)}>
                  Mark resolved
                </Button>
              </div>
            ))}
          </Card>
        )
      }
    </AsyncView>
  )
}

export default function Admin() {
  const [tab, setTab] = useState('overview')
  return (
    <>
      <PageHeader title="Admin panel" description="Platform overview, user management, mentor verification and content moderation." />
      <div className="tab-gap">
        <Tabs
          label="Admin sections"
          value={tab}
          onChange={setTab}
          tabs={[
            { value: 'overview', label: 'Overview' },
            { value: 'users', label: 'Manage users' },
            { value: 'mentors', label: 'Verify mentors' },
            { value: 'resources', label: 'Moderate resources' },
            { value: 'reports', label: 'Reports' },
          ]}
        />
      </div>
      {tab === 'overview' && <Overview />}
      {tab === 'users' && <UsersTab />}
      {tab === 'mentors' && <MentorsTab />}
      {tab === 'resources' && <ResourcesTab />}
      {tab === 'reports' && <ReportsTab />}
    </>
  )
}
