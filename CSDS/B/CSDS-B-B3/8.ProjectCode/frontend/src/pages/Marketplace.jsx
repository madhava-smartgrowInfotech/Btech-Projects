import { useEffect, useState } from 'react'
import { Download, PackageOpen, Plus, ShoppingBag, Star, Wallet } from 'lucide-react'
import { AsyncView, CardSkeleton, useAction } from '../components/common'
import {
  Badge, Button, Card, CardHeader, Checkbox, EmptyState, ErrorState, Input, Modal, PageHeader, SearchField, Select, Skeleton,
  StatCard, Tabs, Textarea,
} from '../components/ui'
import { inr, day } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

function useDebounced(value, ms = 300) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

function ResourceMeta({ r }) {
  return (
    <div className="meta-line">
      <span>By {r.author}</span>
      <span>{r.resource_type}</span>
      <span>
        <Star size={12} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-1px' }} /> {r.rating} ({r.rating_count})
      </span>
      <span>
        <Download size={12} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-1px' }} /> {r.downloads} downloads
      </span>
      {r.skill_tags && <span>Tags: {r.skill_tags}</span>}
    </div>
  )
}

/* ------------------------------------------------------------ browse */
function Browse({ meta, onChanged }) {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All')
  const [free, setFree] = useState(false)
  const q = useDebounced(search)
  const list = useAsync(
    () => api.get(`/marketplace/resources?category=${encodeURIComponent(category)}&search=${encodeURIComponent(q)}&only_free=${free}`),
    [q, category, free],
  )
  const [confirm, setConfirm] = useState(null)
  const { busy, run } = useAction()

  const buy = async (r) => {
    const res = await run(() => api.post(`/marketplace/resources/${r.id}/purchase`), (x) => ({ title: x.message }))
    setConfirm(null)
    if (res.ok) {
      list.reload({ quiet: true })
      onChanged()
    }
  }

  return (
    <>
      <div className="toolbar">
        <div className="grow">
          <SearchField value={search} onChange={setSearch} label="Search resources" placeholder="e.g. Machine Learning notes" />
        </div>
        <div style={{ minWidth: 180 }}>
          <Select
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={['All', ...meta.categories].map((c) => ({ value: c, label: c }))}
          />
        </div>
        <Checkbox label="Free only" checked={free} onChange={(e) => setFree(e.target.checked)} />
      </div>

      {list.loading && list.data === undefined ? (
        <Card aria-busy="true" aria-label="Loading">
          {[0, 1, 2].map((i) => (
            <div className="list-item" key={i}>
              <div style={{ flex: 1 }}>
                <Skeleton width="45%" height={18} />
                <Skeleton height={13} style={{ marginTop: 12 }} />
                <Skeleton width="70%" height={13} style={{ marginTop: 8 }} />
              </div>
              <Skeleton width={90} height={36} />
            </div>
          ))}
        </Card>
      ) : list.error ? (
        <ErrorState title="Couldn't load resources" error={list.error} onRetry={list.reload} />
      ) : list.data.resources.length === 0 ? (
        <Card>
          <EmptyState
            icon={PackageOpen}
            title="No resources match your filters"
            actions={
              <Button
                onClick={() => {
                  setSearch('')
                  setCategory('All')
                  setFree(false)
                }}
              >
                Clear filters
              </Button>
            }
          >
            Try a different search, or publish your own resource in the Upload tab.
          </EmptyState>
        </Card>
      ) : (
        <Card>
          {list.data.resources.map((r) => (
            <div className="list-item" key={r.id}>
              <div style={{ minWidth: 0 }}>
                <h3>{r.title}</h3>
                <p className="muted" style={{ marginBottom: 8 }}>{r.description}</p>
                <ResourceMeta r={r} />
              </div>
              <div className="item-side">
                <span className="price">{r.price === 0 ? 'FREE' : inr(r.price)}</span>
                {r.owned ? (
                  <Badge tone="safe" dot>Owned</Badge>
                ) : r.is_own ? (
                  <Badge>Your listing</Badge>
                ) : (
                  <Button size="sm" variant="primary" loading={busy && confirm?.id === r.id} onClick={() => (r.price > 0 ? setConfirm(r) : buy(r))}>
                    Get resource
                  </Button>
                )}
              </div>
            </div>
          ))}
        </Card>
      )}

      <Modal
        open={!!confirm}
        onClose={() => setConfirm(null)}
        title="Confirm purchase"
        footer={
          <>
            <Button onClick={() => setConfirm(null)}>Cancel</Button>
            <Button variant="primary" loading={busy} onClick={() => buy(confirm)}>
              Pay {confirm && inr(confirm.price)}
            </Button>
          </>
        }
      >
        {confirm && (
          <p>
            Buy <strong>{confirm.title}</strong> for {inr(confirm.price)} from your wallet (balance {inr(list.data?.wallet_balance)}). This is simulated currency; the seller
            receives 90%.
          </p>
        )}
      </Modal>
    </>
  )
}

/* ------------------------------------------------------------ purchases */
function Purchases() {
  const state = useAsync(() => api.get('/marketplace/purchases'), [])
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(rows) =>
        rows.length === 0 ? (
          <Card>
            <EmptyState icon={ShoppingBag} title="Nothing purchased yet">You haven't purchased or claimed any resources. Browse the marketplace to get started.</EmptyState>
          </Card>
        ) : (
          <Card>
            {rows.map((r) => (
              <div className="list-item" key={r.id}>
                <div>
                  <h3>{r.title} <span className="faint" style={{ fontWeight: 400 }}>· {r.resource_type}</span></h3>
                  <p className="muted">{r.description}</p>
                  <div className="meta-line" style={{ marginTop: 8 }}>
                    <span>Purchased {day(r.purchased_at)}</span>
                    <span>Paid {r.price_paid === 0 ? 'nothing (free)' : inr(r.price_paid)}</span>
                  </div>
                </div>
              </div>
            ))}
          </Card>
        )
      }
    </AsyncView>
  )
}

/* ------------------------------------------------------------ upload */
function Upload({ meta, onChanged }) {
  const blank = { title: '', description: '', category: meta.categories[0], resource_type: meta.resource_types[0], price: 0, skill_tags: '' }
  const [f, setF] = useState(blank)
  const [errors, setErrors] = useState({})
  const { busy, run } = useAction()
  const set = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!f.title.trim()) errs.title = 'Add a title'
    if (!f.description.trim()) errs.description = 'Add a description'
    if (f.price < 0 || f.price > 5000) errs.price = 'Price must be between 0 and 5000'
    setErrors(errs)
    if (Object.keys(errs).length) return
    const r = await run(() => api.post('/marketplace/resources', { ...f, price: Number(f.price) }), `"${f.title}" is now published`)
    if (r.ok) {
      setF(blank)
      onChanged()
    }
  }

  return (
    <Card>
      <CardHeader title="Share and monetize your knowledge" subtitle="Published resources appear in Browse immediately. Free uploads earn the Knowledge Sharer badge, paid ones Knowledge Seller." />
      <form className="card-body form-grid" onSubmit={submit} noValidate>
        <div className="span-2">
          <Input label="Title" value={f.title} onChange={set('title')} error={errors.title} />
        </div>
        <div className="span-2">
          <Textarea label="Description" value={f.description} onChange={set('description')} error={errors.description} />
        </div>
        <Select label="Category" value={f.category} onChange={set('category')} options={meta.categories.map((c) => ({ value: c, label: c }))} />
        <Select label="Resource type" value={f.resource_type} onChange={set('resource_type')} options={meta.resource_types.map((c) => ({ value: c, label: c }))} />
        <Input label="Price (₹, 0 = free)" type="number" min="0" max="5000" step="10" value={f.price} onChange={set('price')} error={errors.price} />
        <Input label="Skill tags" hint="Comma separated, e.g. Python, Machine Learning" value={f.skill_tags} onChange={set('skill_tags')} />
        <div className="span-2">
          <Button type="submit" variant="primary" icon={Plus} loading={busy}>
            Publish to marketplace
          </Button>
        </div>
      </form>
    </Card>
  )
}

/* ------------------------------------------------------------ seller */
function Seller() {
  const state = useAsync(() => api.get('/marketplace/seller'), [])
  return (
    <AsyncView state={state} skeleton={<CardSkeleton />}>
      {(d) => (
        <div className="stack">
          <div className="grid grid-3">
            <StatCard label="Resources listed" value={d.resources.length} icon={PackageOpen} />
            <StatCard label="Total sales" value={d.total_sales} icon={ShoppingBag} />
            <StatCard label="Total earnings" value={inr(d.total_earnings)} icon={Wallet} tone="info" />
          </div>
          <Card>
            <CardHeader title="Your listed resources" />
            {d.resources.length === 0 ? (
              <EmptyState icon={PackageOpen} title="You haven't listed anything yet">Use the Upload tab to publish your first resource.</EmptyState>
            ) : (
              d.resources.map((r) => (
                <div className="list-item" key={r.id}>
                  <div>
                    <h3>{r.title}</h3>
                    <div className="meta-line">
                      <span>{r.category}</span>
                      <span>⭐ {r.rating} ({r.rating_count})</span>
                      <span>{r.downloads} downloads</span>
                    </div>
                  </div>
                  <span className="price">{r.price === 0 ? 'FREE' : inr(r.price)}</span>
                </div>
              ))
            )}
          </Card>
        </div>
      )}
    </AsyncView>
  )
}

export default function Marketplace() {
  const meta = useAsync(() => api.get('/marketplace/meta'), [])
  const [tab, setTab] = useState('browse')
  const bump = () => meta.reload({ quiet: true }) // refresh the wallet badge
  return (
    <>
      <PageHeader
        title="Learn & earn marketplace"
        description="Buy and sell notes, projects, courses and more. Payments are simulated with your in-app wallet."
        actions={meta.data && <Badge tone="info" dot>Wallet {inr(meta.data.wallet_balance)}</Badge>}
      />
      <AsyncView state={meta} skeleton={<CardSkeleton />}>
        {(m) => (
          <>
            <div className="tab-gap">
              <Tabs
                label="Marketplace sections"
                value={tab}
                onChange={setTab}
                tabs={[
                  { value: 'browse', label: 'Browse' },
                  { value: 'purchases', label: 'My purchases' },
                  { value: 'upload', label: 'Upload resource' },
                  { value: 'seller', label: 'Seller dashboard' },
                ]}
              />
            </div>
            {tab === 'browse' && <Browse meta={m} onChanged={bump} />}
            {tab === 'purchases' && <Purchases />}
            {tab === 'upload' && <Upload meta={m} onChanged={bump} />}
            {tab === 'seller' && <Seller />}
          </>
        )}
      </AsyncView>
    </>
  )
}
