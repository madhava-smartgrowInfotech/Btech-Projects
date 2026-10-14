import { useMemo, useState } from 'react'
import { MonitorSmartphone, RotateCcw, Save, Settings2, UserPlus, Users } from 'lucide-react'
import {
  Alert,
  Badge,
  Button,
  Drawer,
  EmptyState,
  ErrorState,
  KeyValueList,
  Modal,
  PageHeader,
  SearchField,
  SkeletonBlock,
  Table,
  useToast,
} from '../components/ui'
import { InkRule, PageTransition } from '../components/motion'
import { FacePhotoInput } from '../components/FacePhotoInput'
import { api } from '../lib/api'
import { useApi } from '../lib/useApi'
import { useConfig } from '../lib/config'

function ManageStudent({ student, onChanged }) {
  const toast = useToast()
  const { config } = useConfig()
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState('')
  const [face, setFace] = useState(null)
  const [faceMsg, setFaceMsg] = useState(null)

  const reset = async () => {
    setBusy('reset')
    try {
      const d = await api(`/api/students/${student.id}/reset-devices`, { method: 'POST' })
      toast.success(d.message)
      setConfirm(false)
      onChanged()
    } catch (e) {
      toast.error(e.message)
    } finally {
      setBusy('')
    }
  }

  const enrol = async () => {
    setBusy('enrol')
    setFaceMsg(null)
    const form = new FormData()
    form.append('face', face, 'face.jpg')
    try {
      const d = await api(`/api/students/${student.id}/enroll`, { method: 'POST', form })
      setFaceMsg({ tone: 'success', text: d.message })
      toast.success(`${d.message} (${student.roll_number})`)
      setFace(null)
      onChanged()
    } catch (e) {
      setFaceMsg({ tone: 'error', text: e.message })
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="stack" style={{ '--gap': '20px' }}>
      <KeyValueList
        items={[
          { label: 'Roll', value: <span className="mono">{student.roll_number}</span> },
          { label: 'Name', value: student.full_name },
          { label: 'Username', value: student.username },
          { label: 'Face', value: student.enrolled ? <Badge tone="pass">Enrolled</Badge> : <Badge tone="blocked">Not enrolled</Badge> },
          { label: 'Devices', value: student.devices },
          { label: 'Registered', value: student.registered },
        ]}
      />
      <div className="stack" style={{ '--gap': '10px' }}>
        <h3 className="card-title">Device bindings</h3>
        <p className="small muted">Allow the student to check in from a new phone.</p>
        <div>
          <Button icon={MonitorSmartphone} onClick={() => setConfirm(true)}>
            Reset device bindings
          </Button>
        </div>
      </div>
      <InkRule />
      <div className="stack" style={{ '--gap': '10px' }}>
        <h3 className="card-title">Re-enrol reference face</h3>
        <p className="small muted">The student must be present. Look straight at the camera, good light, no mask/cap.</p>
        <FacePhotoInput label="Reference face" value={face} onChange={setFace} mirrored={config?.camera_mirrored ?? true} />
        {faceMsg && <Alert tone={faceMsg.tone}>{faceMsg.text}</Alert>}
        <div>
          <Button variant="primary" icon={Save} disabled={!face} loading={busy === 'enrol'} onClick={enrol}>
            Save reference face
          </Button>
        </div>
      </div>
      <Modal
        open={confirm}
        onClose={() => setConfirm(false)}
        title="Reset devices?"
        footer={
          <>
            <Button onClick={() => setConfirm(false)} data-autofocus>
              Cancel
            </Button>
            <Button variant="danger" icon={RotateCcw} loading={busy === 'reset'} onClick={reset}>
              Reset {student.devices} binding{student.devices === 1 ? '' : 's'}
            </Button>
          </>
        }
      >
        <p>
          {student.roll_number} ({student.full_name}) will be able to bind a new device on their next check-in.
        </p>
      </Modal>
    </div>
  )
}

export default function Students() {
  const { data, error, loading, reload } = useApi('/api/students')
  const [q, setQ] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const selected = data?.find((s) => s.id === selectedId) || null

  const rows = useMemo(() => {
    const t = q.trim().toLowerCase()
    return (data || []).filter((s) => !t || `${s.roll_number} ${s.full_name} ${s.username}`.toLowerCase().includes(t))
  }, [data, q])

  const columns = [
    { key: 'roll_number', label: 'Roll', render: (s) => <strong className="mono">{s.roll_number}</strong> },
    { key: 'full_name', label: 'Name' },
    { key: 'username', label: 'Username', render: (s) => <span className="mono small">{s.username}</span> },
    {
      key: 'enrolled',
      label: 'Face enrolled',
      sortValue: (s) => (s.enrolled ? 1 : 0),
      render: (s) => (s.enrolled ? <Badge tone="pass">Yes</Badge> : <Badge tone="blocked">No</Badge>),
    },
    { key: 'devices', label: 'Devices', numeric: true },
    { key: 'created_at', label: 'Registered', render: (s) => <span className="mono small">{s.registered}</span> },
    {
      key: 'actions',
      label: 'Actions',
      sortable: false,
      render: (s) => (
        <Button
          size="sm"
          icon={Settings2}
          onClick={(e) => {
            e.stopPropagation()
            setSelectedId(s.id)
          }}
        >
          Manage
        </Button>
      ),
    },
  ]

  const enrolled = (data || []).filter((s) => s.enrolled).length

  return (
    <PageTransition>
      <PageHeader
        eyebrow="Students"
        title="Students"
        description={data ? `${data.length} registered · ${enrolled} with an enrolled reference face.` : 'Registered students, face enrolment and device bindings.'}
        actions={
          <Button icon={RotateCcw} onClick={() => reload()}>
            Refresh
          </Button>
        }
      />
      {loading && !data ? (
        <SkeletonBlock rows={6} label="Loading students" />
      ) : error && !data ? (
        <ErrorState title="Couldn't load students" error={error} onRetry={reload} />
      ) : !data.length ? (
        <EmptyState
          icon={Users}
          title="No students registered yet"
          action={
            <Button variant="primary" to="/register?role=student" icon={UserPlus}>
              Open student registration
            </Button>
          }
        >
          Students register themselves (with a reference face photo) from the registration page or a session link.
        </EmptyState>
      ) : (
        <div className="stack">
          <SearchField value={q} onChange={setQ} label="Search students" placeholder="Search roll, name, username…" />
          <Table
            caption="Registered students"
            columns={columns}
            rows={rows}
            initialSort={{ key: 'roll_number', dir: 'asc' }}
            onRowClick={(s) => setSelectedId(s.id)}
            empty={<EmptyState title="No matching students" action={<Button onClick={() => setQ('')}>Clear search</Button>}>Nothing matches “{q}”.</EmptyState>}
          />
        </div>
      )}
      <Drawer open={Boolean(selected)} onClose={() => setSelectedId(null)} title={selected ? `Manage ${selected.roll_number}` : 'Manage'}>
        {selected && <ManageStudent key={selected.id} student={selected} onChanged={() => reload(true)} />}
      </Drawer>
    </PageTransition>
  )
}
