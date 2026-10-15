import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserPlus } from 'lucide-react'
import api from '../api.js'
import { PageHeader } from '../components/ui/Layout.jsx'
import { Button, EmptyState, ErrorState, Modal, SearchField, SkeletonBlock, Table } from '../components/ui/index.js'
import PatientForm from '../components/PatientForm.jsx'
import { SeverityBadge } from '../components/Badges.jsx'
import { failure, fmtDate } from '../lib/product.js'

export default function Patients() {
  const nav = useNavigate()
  const [patients, setPatients] = useState(null)
  const [error, setError] = useState(null)
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)

  const load = () => {
    setError(null)
    setPatients(null)
    api
      .get('/patients')
      .then((r) => setPatients(r.data))
      .catch(async (e) => setError(await failure(e)))
  }
  useEffect(load, [])

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return patients || []
    return (patients || []).filter((p) => `${p.name} ${p.code}`.toLowerCase().includes(needle))
  }, [patients, q])

  const columns = [
    { key: 'code', label: 'ID', render: (p) => <span className="mono">{p.code}</span> },
    { key: 'name', label: 'Name' },
    { key: 'age', label: 'Age', numeric: true },
    { key: 'sex', label: 'Sex' },
    { key: 'scan_count', label: 'Scans', numeric: true },
    {
      key: 'finding',
      label: 'Latest finding',
      sortValue: (p) => p.last_scan?.prediction || '',
      render: (p) =>
        p.last_scan ? (
          <span className="row" style={{ '--gap': '6px' }}>
            {p.last_scan.prediction} <SeverityBadge value={p.last_scan.severity} />
          </span>
        ) : (
          <span className="muted">No scans</span>
        ),
    },
    { key: 'created_at', label: 'Registered', render: (p) => fmtDate(p.created_at), sortValue: (p) => p.created_at },
  ]

  const addPatient = (p) => {
    setPatients((list) => [p, ...(list || [])])
    setOpen(false)
  }

  let body
  if (error) {
    body = <ErrorState title="Patients could not be loaded" error={error.message} onRetry={load} />
  } else if (!patients) {
    body = <SkeletonBlock rows={5} label="Loading patients" />
  } else if (patients.length === 0) {
    body = (
      <EmptyState
        icon={UserPlus}
        title="No patients yet"
        action={
          <Button variant="primary" icon={UserPlus} onClick={() => setOpen(true)}>
            Register the first patient
          </Button>
        }
      >
        Patients appear here once registered. Each one can then have scans uploaded.
      </EmptyState>
    )
  } else if (shown.length === 0) {
    body = (
      <EmptyState
        title="No matching patients"
        action={
          <Button onClick={() => setQ('')}>Clear search</Button>
        }
      >
        Nothing matches “{q}”. Search by name or patient ID.
      </EmptyState>
    )
  } else {
    body = <Table columns={columns} rows={shown} onRowClick={(p) => nav(`/patients/${p.id}`)} caption="Registered patients" />
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Records"
        title="Patients"
        description="Every registered patient and their scan history. Select a row to open the record."
        actions={
          <Button variant="primary" icon={UserPlus} onClick={() => setOpen(true)}>
            New patient
          </Button>
        }
      />

      <div className="filter-bar">
        <SearchField value={q} onChange={setQ} label="Search patients" placeholder="Search name or ID" />
        {patients && <span className="small mono muted">{shown.length} of {patients.length}</span>}
      </div>

      {body}

      <Modal open={open} onClose={() => setOpen(false)} title="Register a patient">
        <PatientForm idPrefix="modal-patient" onCreated={addPatient} />
      </Modal>
    </div>
  )
}
