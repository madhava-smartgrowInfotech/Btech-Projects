import { useState } from 'react'
import { MapPin, Pencil, Plus, RotateCcw, Trash2 } from 'lucide-react'
import { Button, Card, EmptyState, ErrorState, Input, Modal, PageHeader, Table, useToast } from '../../components/ui'
import { Api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { money } from '../../lib/format'

const BLANK = { name: '', address: '', latitude: '12.9716', longitude: '77.5946', capacity: '15', price_per_hour: '3', buffer_size: '1' }

// Mirrors LocationIn in app/schemas.py so errors show next to the field before the request is sent.
function validate(f) {
  const e = {}
  const n = (v) => (v === '' ? NaN : Number(v))
  if (f.name.trim().length < 2) e.name = 'Name needs at least 2 characters.'
  if (!(n(f.latitude) >= -90 && n(f.latitude) <= 90)) e.latitude = 'Latitude is between -90 and 90.'
  if (!(n(f.longitude) >= -180 && n(f.longitude) <= 180)) e.longitude = 'Longitude is between -180 and 180.'
  if (!(Number.isInteger(n(f.capacity)) && n(f.capacity) >= 1 && n(f.capacity) <= 5000)) e.capacity = 'Capacity is a whole number from 1 to 5000.'
  if (!(n(f.price_per_hour) >= 0.5 && n(f.price_per_hour) <= 100)) e.price_per_hour = 'Price is between 0.50 and 100 per hour.'
  if (!(Number.isInteger(n(f.buffer_size)) && n(f.buffer_size) >= 0 && n(f.buffer_size) <= 20)) e.buffer_size = 'Buffer is a whole number from 0 to 20.'
  return e
}

export default function Locations() {
  const toast = useToast()
  const { data, error, loading, reload } = useAsync(() => Api.locations(), [])
  const [editing, setEditing] = useState(null) // null | 'new' | location
  const [form, setForm] = useState(BLANK)
  const [errs, setErrs] = useState({})
  const [saveErr, setSaveErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [del, setDel] = useState(null)
  const [resetOpen, setResetOpen] = useState(false)

  const openForm = (loc) => {
    setEditing(loc || 'new')
    setErrs({})
    setSaveErr('')
    setForm(loc ? { name: loc.name, address: loc.address, latitude: String(loc.latitude), longitude: String(loc.longitude), capacity: String(loc.capacity), price_per_hour: String(loc.price_per_hour), buffer_size: String(loc.buffer_size) } : BLANK)
  }
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const save = async (ev) => {
    ev.preventDefault()
    const e = validate(form)
    setErrs(e)
    if (Object.keys(e).length) return
    const body = { name: form.name.trim(), address: form.address.trim(), latitude: Number(form.latitude), longitude: Number(form.longitude), capacity: Number(form.capacity), price_per_hour: Number(form.price_per_hour), buffer_size: Number(form.buffer_size) }
    setBusy(true)
    setSaveErr('')
    try {
      if (editing === 'new') await Api.createLocation(body)
      else await Api.updateLocation(editing.id, body)
      toast({ tone: 'success', title: editing === 'new' ? 'Location added' : 'Location saved', message: body.name })
      setEditing(null)
      reload({ quiet: true })
    } catch (err) {
      setSaveErr(err.message)
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    const loc = del
    setBusy(true)
    try {
      await Api.deleteLocation(loc.id)
      toast({ tone: 'success', title: 'Location deleted', message: loc.name })
      setDel(null)
      reload({ quiet: true })
    } catch (err) {
      toast({ tone: 'error', title: 'Could not delete the location', message: `${err.message} It may still have reservations attached.`, duration: 8000 })
      setDel(null)
    } finally {
      setBusy(false)
    }
  }

  const resetBuffers = async () => {
    setBusy(true)
    try {
      const r = await Api.adminResetBuffers()
      toast({ tone: 'success', title: 'Buffers reset', message: r.forced ? `${r.forced} locations were set back to the policy default.` : `${r.reset_by_policy} locations were due and reset by policy.` })
      setResetOpen(false)
      reload({ quiet: true })
    } catch (err) {
      toast({ tone: 'error', title: 'Could not reset buffers', message: err.message })
    } finally {
      setBusy(false)
    }
  }

  const columns = [
    { key: 'name', label: 'Location', render: (r) => (<><strong>{r.name}</strong><div className="faint">{r.address || 'No address'}</div></>) },
    { key: 'capacity', label: 'Bays', num: true },
    { key: 'buffer_size', label: 'Buffer', num: true },
    { key: 'price_per_hour', label: 'Per hour', num: true, render: (r) => money(r.price_per_hour) },
    { key: 'coords', label: 'Coordinates', hideSm: true, sortable: false, render: (r) => <span className="mono">{r.latitude.toFixed(4)}, {r.longitude.toFixed(4)}</span> },
    {
      key: 'actions',
      label: '',
      sortable: false,
      render: (r) => (
        <div className="row" style={{ gap: 6 }}>
          <Button size="sm" icon={Pencil} onClick={() => openForm(r)}>
            Edit
          </Button>
          <Button size="sm" variant="ghost" icon={Trash2} onClick={() => setDel(r)}>
            Delete
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="container">
      <PageHeader
        title="Locations"
        description="Add, edit and remove parking locations. The buffer is how many bays are held back from reservations."
        actions={
          <>
            <Button icon={RotateCcw} onClick={() => setResetOpen(true)}>
              Reset all buffers
            </Button>
            <Button variant="primary" icon={Plus} onClick={() => openForm(null)}>
              Add location
            </Button>
          </>
        }
      />
      {error ? (
        <ErrorState title="Could not load locations" error={error} onRetry={() => reload()} />
      ) : (
        <Card>
          <Table
            caption="Parking locations"
            columns={columns}
            rows={data}
            rowKey={(r) => r.id}
            loading={loading && !data}
            initialSort={{ key: 'name', dir: 'asc' }}
            empty={
              <EmptyState icon={MapPin} title="No locations yet" actions={<Button variant="primary" icon={Plus} onClick={() => openForm(null)}>Add the first location</Button>}>
                Drivers cannot reserve until at least one location exists.
              </EmptyState>
            }
          />
        </Card>
      )}

      <Modal
        open={!!editing}
        onClose={() => !busy && setEditing(null)}
        title={editing === 'new' ? 'Add location' : 'Edit location'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditing(null)} disabled={busy}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" form="loc-form" loading={busy}>
              {editing === 'new' ? 'Add location' : 'Save changes'}
            </Button>
          </>
        }
      >
        <form id="loc-form" onSubmit={save} noValidate className="stack" style={{ gap: 14 }}>
          <Input data-autofocus label="Name" value={form.name} onChange={set('name')} error={errs.name} />
          <Input label="Address" value={form.address} onChange={set('address')} />
          <div className="grid grid-2">
            <Input label="Latitude" type="number" step="any" value={form.latitude} onChange={set('latitude')} error={errs.latitude} />
            <Input label="Longitude" type="number" step="any" value={form.longitude} onChange={set('longitude')} error={errs.longitude} />
          </div>
          <div className="grid grid-3">
            <Input label="Bays" type="number" value={form.capacity} onChange={set('capacity')} error={errs.capacity} />
            <Input label="Price per hour ($)" type="number" step="0.5" value={form.price_per_hour} onChange={set('price_per_hour')} error={errs.price_per_hour} />
            <Input label="Buffer" type="number" value={form.buffer_size} onChange={set('buffer_size')} error={errs.buffer_size} />
          </div>
          {saveErr && (
            <p className="field-error" role="alert">
              {saveErr}
            </p>
          )}
        </form>
      </Modal>

      <Modal
        open={!!del}
        onClose={() => setDel(null)}
        title="Delete this location?"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDel(null)}>
              Keep it
            </Button>
            <Button variant="danger" icon={Trash2} loading={busy} onClick={remove}>
              Delete location
            </Button>
          </>
        }
      >
        {del && <p><strong>{del.name}</strong> will be removed and drivers can no longer reserve there. This cannot be undone.</p>}
      </Modal>

      <Modal
        open={resetOpen}
        onClose={() => setResetOpen(false)}
        title="Reset all buffers?"
        footer={
          <>
            <Button variant="ghost" onClick={() => setResetOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" icon={RotateCcw} loading={busy} onClick={resetBuffers}>
              Reset buffers
            </Button>
          </>
        }
      >
        <p>Every location's buffer goes back to the policy starting value, even if its 24-hour window has not ended. Buffers then grow again with on-time checkouts.</p>
      </Modal>
    </div>
  )
}
